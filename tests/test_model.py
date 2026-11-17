import json
from pathlib import Path
import shutil

import numpy as np
import pandas as pd
import pytest

from matchmind.model import (fit_goal_model, fit_temperature, labels, predict,
                             score_distribution, with_average_teams)
from matchmind.train import metrics, split_data, train
from matchmind.leagues import LEAGUES


@pytest.fixture
def matches():
    return pd.DataFrame({
        "date": pd.to_datetime(["2022-08-01", "2022-09-01", "2022-10-01", "2023-01-01"]),
        "home": ["A", "B", "A", "B"], "away": ["B", "A", "B", "A"],
        "home_goals": [2, 1, 0, 3], "away_goals": [0, 1, 1, 2],
        "season": ["2022-23"] * 4,
    })


def test_probability_and_serialization(matches):
    model = fit_goal_model(matches)
    result = predict(model, "A", "B")
    assert sum(result["probabilities"]) == pytest.approx(1)
    assert sum(result["raw_probabilities"]) == pytest.approx(1)
    assert all(0 <= p <= 1 for p in result["probabilities"])
    assert result == predict(json.loads(json.dumps(model)), "A", "B")
    matrix = score_distribution(result["home_goals"], result["away_goals"])
    assert tuple(result["score"]) == np.unravel_index(matrix.argmax(), matrix.shape)
    assert result["score_probability"] == matrix.max()


def test_team_validation(matches):
    model = fit_goal_model(matches)
    with pytest.raises(ValueError, match="different"):
        predict(model, "A", "A")
    with pytest.raises(ValueError, match="not in"):
        predict(model, "A", "Unknown")


def test_calibration_requires_later_period(matches):
    model = fit_goal_model(matches)
    with pytest.raises(ValueError, match="strictly later"):
        fit_temperature(model, matches)
    later = matches.copy()
    later["date"] += pd.Timedelta(days=730)
    original = json.dumps(model, sort_keys=True)
    assert 0.5 <= fit_temperature(model, later) <= 3.0
    assert json.dumps(model, sort_keys=True) == original


def test_chronological_split_keeps_dates_together(matches):
    calibration = matches.assign(date=pd.Timestamp("2023-08-01"))
    test = matches.assign(date=pd.Timestamp("2024-08-01"))
    all_matches = pd.concat([test, matches, calibration], ignore_index=True)
    fitting, calibrating, testing = split_data(all_matches)
    assert fitting.date.max() < calibrating.date.min()
    assert calibrating.date.max() < testing.date.min()
    assert len(fitting) + len(calibrating) + len(testing) == len(all_matches)
    with pytest.raises(ValueError, match="Need matches"):
        split_data(matches)


def test_new_team_fallback_does_not_mutate_model(matches):
    model = fit_goal_model(matches)
    future = matches.assign(home="Promoted")
    extended = with_average_teams(model, future)
    assert "Promoted" not in model["teams"]
    assert extended["attack"]["Promoted"] == 0
    assert predict(extended, "Promoted", "A")["home_goals"] > 0


def test_future_scores_do_not_change_fitting_split(matches):
    calibration = matches.assign(date=pd.Timestamp("2023-08-01"))
    test = matches.assign(date=pd.Timestamp("2024-08-01"))
    original = pd.concat([matches, calibration, test], ignore_index=True)
    changed = original.copy()
    changed.loc[changed.date >= pd.Timestamp("2024-07-01"), "home_goals"] = 20
    original_train, original_calibration, _ = split_data(original)
    changed_train, changed_calibration, _ = split_data(changed)
    pd.testing.assert_frame_equal(original_train, changed_train)
    pd.testing.assert_frame_equal(original_calibration, changed_calibration)


def test_metrics_known_values(matches):
    outcomes = labels(matches)
    assert outcomes.tolist() == [0, 1, 2, 0]
    assert metrics(outcomes, np.eye(3)[outcomes])["brier"] == 0
    assert metrics(outcomes, np.ones((4, 3)) / 3)["brier"] == pytest.approx(2 / 3)


def test_training_rejects_changed_csv(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "matches.csv").write_text("changed", encoding="utf-8")
    (data / "manifest.json").write_text(json.dumps({"csv_sha256": "incorrect"}), encoding="utf-8")
    with pytest.raises(ValueError, match="source manifest"):
        train(tmp_path)


def test_laliga_training_writes_only_its_own_models(tmp_path):
    root = Path(__file__).resolve().parents[1]
    config = LEAGUES["la-liga"]
    shutil.copytree(root / config["data_dir"], tmp_path / config["data_dir"])
    sentinel = tmp_path / "models/model.json"
    sentinel.parent.mkdir(parents=True)
    sentinel.write_text("preserve existing Premier League model", encoding="utf-8")
    report = train(tmp_path, league="la-liga")
    assert sentinel.read_text(encoding="utf-8") == "preserve existing Premier League model"
    assert report["league"] == {"id": "la-liga", "name": "La Liga"}
    assert report["splits"]["test"]["count"] == config["expected_matches"]["2024-25"]
    destination = tmp_path / config["model_dir"]
    for name in ["model.json", "evaluation_model.json", "evaluation.json"]:
        artifact = json.loads((destination / name).read_bytes())
        assert artifact["league"] == report["league"]
    predictions = pd.read_csv(destination / "test_predictions.csv")
    assert len(predictions) == report["splits"]["test"]["count"]


@pytest.mark.parametrize("rates", [(float("nan"), 1), (-1, 1), (101, 1)])
def test_invalid_goal_rates(rates):
    with pytest.raises(ValueError, match="goal rates"):
        score_distribution(*rates)
