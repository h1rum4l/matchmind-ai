"""Recency-weighted team attack/defence Poisson model; JSON-only inference."""

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar
from scipy.special import softmax
from scipy.stats import poisson
from sklearn.linear_model import PoissonRegressor
from sklearn.preprocessing import OneHotEncoder


def labels(matches):
    difference = matches.home_goals.to_numpy() - matches.away_goals.to_numpy()
    return np.where(difference > 0, 0, np.where(difference == 0, 1, 2))


def fit_goal_model(matches):
    if matches.empty:
        raise ValueError("At least one completed match is required.")
    teams = sorted(set(matches.home) | set(matches.away))
    features = pd.DataFrame({
        "attack": list(matches.home) + list(matches.away),
        "defence": list(matches.away) + list(matches.home),
    })
    encoder = OneHotEncoder(categories=[teams, teams], sparse_output=False)
    encoded = encoder.fit_transform(features)
    home_indicator = np.r_[np.ones(len(matches)), np.zeros(len(matches))]
    design = np.column_stack([encoded, home_indicator])
    target = np.r_[matches.home_goals, matches.away_goals]
    age = (matches.date.max() - matches.date).dt.days.to_numpy()
    weights = np.tile(np.exp(-np.log(2) * age / 730), 2)
    estimator = PoissonRegressor(alpha=0.01, max_iter=1000, tol=1e-8)
    estimator.fit(design, target, sample_weight=weights)
    count = len(teams)
    return {
        "schema_version": 1,
        "method": "Poisson attack/defence, alpha=0.01, 730-day half-life",
        "teams": teams,
        "attack": dict(zip(teams, estimator.coef_[:count].tolist())),
        "defence": dict(zip(teams, estimator.coef_[count:2 * count].tolist())),
        "intercept": float(estimator.intercept_),
        "home_advantage": float(estimator.coef_[-1]),
        "temperature": 1.0,
        "train_end": matches.date.max().date().isoformat(),
        "data_end": matches.date.max().date().isoformat(),
    }


def score_distribution(home_mean, away_mean):
    means = np.asarray([home_mean, away_mean], dtype=float)
    if not np.isfinite(means).all() or (means <= 0).any() or (means > 100).any():
        raise ValueError("Expected goal rates must be finite and between 0 and 100.")
    maximum = int(max(poisson.ppf(1 - 1e-12, means)))
    goals = np.arange(maximum + 1)
    matrix = np.outer(poisson.pmf(goals, home_mean), poisson.pmf(goals, away_mean))
    matrix /= matrix.sum()
    return matrix


def predict(model, home, away):
    if home == away:
        raise ValueError("Choose two different teams.")
    if home not in model["teams"] or away not in model["teams"]:
        raise ValueError("Team is not in this model's historical data.")
    rates = np.exp([
        model["intercept"] + model["attack"][home] + model["defence"][away]
        + model["home_advantage"],
        model["intercept"] + model["attack"][away] + model["defence"][home],
    ])
    matrix = score_distribution(*rates)
    raw = np.asarray([np.tril(matrix, -1).sum(), np.trace(matrix), np.triu(matrix, 1).sum()])
    temperature = float(model["temperature"])
    if not np.isfinite(temperature) or temperature <= 0:
        raise ValueError("Model calibration temperature must be positive and finite.")
    calibrated = softmax(np.log(np.clip(raw, 1e-15, 1)) / temperature)
    score = np.unravel_index(matrix.argmax(), matrix.shape)
    return {
        "probabilities": calibrated.tolist(),
        "raw_probabilities": raw.tolist(),
        "home_goals": float(rates[0]),
        "away_goals": float(rates[1]),
        "score": [int(score[0]), int(score[1])],
        "score_probability": float(matrix[score]),
    }


def with_average_teams(model, matches):
    """Zero team effects for promoted clubs unseen during fitting; never learn results."""
    missing = sorted((set(matches.home) | set(matches.away)) - set(model["teams"]))
    return {
        **model,
        "teams": sorted(set(model["teams"]) | set(missing)),
        "attack": {**model["attack"], **dict.fromkeys(missing, 0.0)},
        "defence": {**model["defence"], **dict.fromkeys(missing, 0.0)},
    }


def fit_temperature(model, calibration):
    if calibration.empty or calibration.date.min() <= pd.Timestamp(model["train_end"]):
        raise ValueError("Calibration matches must be strictly later than goal-model training.")
    extended = with_average_teams(model, calibration)
    raw = np.asarray([predict(extended, row.home, row.away)["raw_probabilities"]
                      for row in calibration.itertuples()])
    log_probabilities = np.log(np.clip(raw, 1e-15, 1))
    outcomes = labels(calibration)

    def loss(temperature):
        probabilities = softmax(log_probabilities / temperature, axis=1)
        return -np.log(probabilities[np.arange(len(outcomes)), outcomes]).mean()

    result = minimize_scalar(loss, bounds=(0.5, 3.0), method="bounded")
    if not result.success:
        raise ValueError("Calibration optimization did not converge.")
    return float(result.x)
