"""Train with a calibration season and an untouched chronological test season."""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, log_loss

from matchmind.leagues import DEFAULT_LEAGUE, LEAGUES, get_league
from matchmind.model import fit_goal_model, fit_temperature, labels, predict, with_average_teams

ROOT = Path(__file__).resolve().parents[1]


def split_data(matches):
    ordered = matches.sort_values("date").reset_index(drop=True)
    train = ordered.loc[ordered.date < pd.Timestamp("2023-07-01")].copy()
    calibration = ordered.loc[(ordered.date >= pd.Timestamp("2023-07-01"))
                              & (ordered.date < pd.Timestamp("2024-07-01"))].copy()
    test = ordered.loc[ordered.date >= pd.Timestamp("2024-07-01")].copy()
    if any(part.empty for part in (train, calibration, test)):
        raise ValueError("Need matches before July 2023, in 2023/24, and from July 2024 for evaluation.")
    if not train.date.max() < calibration.date.min() <= calibration.date.max() < test.date.min():
        raise ValueError("Training, calibration and test dates must not overlap.")
    return train, calibration, test


def metrics(outcomes, probabilities):
    probabilities = np.asarray(probabilities)
    truth = np.eye(3)[outcomes]
    return {
        "accuracy": float(accuracy_score(outcomes, probabilities.argmax(axis=1))),
        "log_loss": float(log_loss(outcomes, probabilities, labels=[0, 1, 2])),
        "brier": float(np.square(probabilities - truth).sum(axis=1).mean()),
    }


def reliability(outcomes, probabilities):
    rows = []
    for category, name in enumerate(["Home", "Draw", "Away"]):
        for index in range(5):
            lower, upper = index / 5, (index + 1) / 5
            selected = (probabilities[:, category] >= lower) & (
                probabilities[:, category] <= upper if index == 4 else probabilities[:, category] < upper)
            if selected.any():
                rows.append({"outcome": name, "bin_lower": lower, "bin_upper": upper,
                             "count": int(selected.sum()),
                             "mean_probability": float(probabilities[selected, category].mean()),
                             "observed_frequency": float((outcomes[selected] == category).mean())})
    return rows


def train(root=ROOT, league=DEFAULT_LEAGUE):
    root = Path(root)
    config = get_league(league)
    identity = {"id": league, "name": config["name"]}
    data_root = root / config["data_dir"]
    manifest_path = data_root / "manifest.json"
    provenance = json.loads(manifest_path.read_text(encoding="utf-8"))
    if "league" in provenance and provenance["league"] not in [league, identity]:
        raise ValueError("Data manifest belongs to a different league.")
    csv_path = data_root / "matches.csv"
    if hashlib.sha256(csv_path.read_bytes()).hexdigest() != provenance["csv_sha256"]:
        raise ValueError("Match CSV does not match its source manifest; rerun ingestion.")
    matches = pd.read_csv(csv_path, parse_dates=["date"])
    train_matches, calibration, test = split_data(matches)
    model = fit_goal_model(train_matches)
    model["temperature"] = fit_temperature(model, calibration)
    model["calibration_end"] = calibration.date.max().date().isoformat()
    scoring_model = with_average_teams(model, test)
    predictions = [predict(scoring_model, row.home, row.away) for row in test.itertuples()]
    raw = np.asarray([item["raw_probabilities"] for item in predictions])
    calibrated = np.asarray([item["probabilities"] for item in predictions])
    outcomes = labels(test)
    frequencies = np.bincount(labels(train_matches), minlength=3) / len(train_matches)
    baseline = np.tile(frequencies, (len(test), 1))
    always_home = np.tile([1.0, 0.0, 0.0], (len(test), 1))
    unseen = sorted(set(scoring_model["teams"]) - set(model["teams"]))
    unseen_calibration = sorted((set(calibration.home) | set(calibration.away)) - set(model["teams"]))
    report = {
        "league": identity,
        "data_provenance": provenance,
        "outcome_order": ["Home", "Draw", "Away"],
        "brier_definition": "Mean sum of squared errors over all 3 classes; range 0 to 2, lower is better.",
        "evaluation_protocol": "Fixed model trained before 2023-07-01; temperature fitted only on 2023/24; all test matches from July 2024 onward. No test tuning or in-season updating.",
        "splits": {name: {"count": len(part), "start": part.date.min().date().isoformat(),
                          "end": part.date.max().date().isoformat()}
                   for name, part in [("train", train_matches), ("calibration", calibration), ("test", test)]},
        "temperature": model["temperature"],
        "metrics": {"raw_poisson": metrics(outcomes, raw),
                    "calibrated_poisson": metrics(outcomes, calibrated),
                    "historical_frequency": metrics(outcomes, baseline),
                    "always_home": metrics(outcomes, always_home)},
        "unseen_test_teams": unseen,
        "unseen_calibration_teams": unseen_calibration,
        "unseen_calibration_matches": int((calibration.home.isin(unseen_calibration)
                                           | calibration.away.isin(unseen_calibration)).sum()),
        "unseen_team_matches": int((test.home.isin(unseen) | test.away.isin(unseen)).sum()),
        "unseen_team_policy": "Zero attack/defence effects (league average), without learning future scores.",
        "reliability": reliability(outcomes, calibrated),
        "production_note": "Production goal model is refit on all matches, including test data. Historical temperature is transferred unchanged; production calibration and future accuracy are not independently verified. Reported test metrics belong only to evaluation_model.json.",
    }
    production = fit_goal_model(matches)
    production["temperature"] = model["temperature"]
    production["calibration_end"] = model["calibration_end"]
    production["evaluation_metrics"] = report["metrics"]["calibrated_poisson"]
    production["calibration_note"] = report["production_note"]
    for artifact in (model, production):
        artifact["league"] = identity
        artifact["data_csv_sha256"] = provenance["csv_sha256"]
        artifact["source_commit"] = provenance["commit"]
    destination = root / config["model_dir"]
    destination.mkdir(parents=True, exist_ok=True)
    for filename, value in [("evaluation.json", report), ("evaluation_model.json", model),
                            ("model.json", production)]:
        path = destination / filename
        temporary = path.with_suffix(".tmp")
        temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n", encoding="utf-8")
        temporary.replace(path)
    exported = test.copy()
    for index, name in enumerate(["p_home", "p_draw", "p_away"]):
        exported[name] = calibrated[:, index]
    exported["predicted_home_goals"] = [item["score"][0] for item in predictions]
    exported["predicted_away_goals"] = [item["score"][1] for item in predictions]
    exported.to_csv(destination / "test_predictions.csv", index=False, lineterminator="\n")
    print(json.dumps(report["metrics"], indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--league", choices=list(LEAGUES), default=DEFAULT_LEAGUE,
                        help="Train only this league's independent model and evaluation.")
    arguments = parser.parse_args()
    try:
        train(league=arguments.league)
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(f"Training failed: {error}. Run python -m matchmind.data --league {arguments.league} first.") from error
