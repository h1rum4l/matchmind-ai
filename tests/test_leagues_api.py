import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest

from matchmind.api import create_app
from matchmind.leagues import DEFAULT_LEAGUE, LEAGUES
from matchmind.model import predict
from matchmind.train import train

ROOT = Path(__file__).resolve().parents[1]


def copy_artifacts(destination):
    for folder in ["data", "models"]:
        shutil.copytree(ROOT / folder, destination / folder)


def test_league_list_and_premier_league_default():
    with TestClient(create_app(ROOT)) as client:
        registry = client.get("/api/leagues").json()
        assert registry["default"] == DEFAULT_LEAGUE == "premier-league"
        assert {item["id"]: item["name"] for item in registry["leagues"]} == {
            "premier-league": "Premier League", "la-liga": "La Liga"}
        default = client.get("/api/meta").json()
        explicit = client.get("/api/meta", params={"league": DEFAULT_LEAGUE}).json()
        assert default == explicit
        assert default["league"] == {"id": DEFAULT_LEAGUE, "name": "Premier League"}
        assert "Arsenal" in default["teams"]


@pytest.mark.parametrize("league", ["unknown", "../../models", "", "LA-LIGA"])
def test_unknown_leagues_are_rejected(league):
    with TestClient(create_app(ROOT)) as client:
        for endpoint in ["/api/meta", "/api/health", "/api/evaluation", "/api/matches.csv"]:
            assert client.get(endpoint, params={"league": league}).status_code == 422
        assert client.post("/api/predict", json={
            "league": league, "home": "Arsenal", "away": "Chelsea"}).status_code == 422


@pytest.mark.parametrize("league", [None, 1, "a" * 41])
def test_prediction_league_field_is_strict(league):
    with TestClient(create_app(ROOT)) as client:
        assert client.post("/api/predict", json={
            "league": league, "home": "Arsenal", "away": "Chelsea"}).status_code == 422


def test_laliga_real_data_prediction_and_download_scope():
    config = LEAGUES["la-liga"]
    manifest = json.loads((ROOT / config["data_dir"] / "manifest.json").read_bytes())
    with TestClient(create_app(ROOT)) as client:
        assert client.get("/api/health", params={"league": "la-liga"}).json() == {"status": "ready"}
        response = client.get("/api/meta", params={"league": "la-liga"})
        assert response.status_code == 200
        metadata = response.json()
        assert metadata["league"] == {"id": "la-liga", "name": "La Liga"}
        assert len(metadata["teams"]) == 20
        assert "Arsenal" not in metadata["teams"]
        assert metadata["snapshot"]["matches"] == manifest["matches"]
        assert metadata["snapshot"]["end"] == manifest["data_end"]
        home, away = metadata["teams"][:2]
        response = client.post("/api/predict", json={"home": home, "away": away, "league": "la-liga"})
        assert response.status_code == 200
        result = response.json()
        expected = predict(json.loads((ROOT / config["model_dir"] / "model.json").read_bytes()), home, away)
        assert result["league"] == metadata["league"]
        for key, value in expected.items():
            assert result[key] == value
        assert sum(result["probabilities"]) == pytest.approx(1)
        assert all(row["matches"] == 10 for row in result["stats"])
        download = client.get("/api/matches.csv", params={"league": "la-liga"})
        assert download.content == (ROOT / config["data_dir"] / "matches.csv").read_bytes()
        assert "la-liga-matches.csv" in download.headers["content-disposition"]
        assert download.content != client.get("/api/matches.csv").content
        report = client.get("/api/evaluation", params={"league": "la-liga"}).json()
        assert report["league"] == metadata["league"]
        assert report["metrics"] == metadata["metrics"]
        assert report["data_provenance"]["csv_sha256"] == manifest["csv_sha256"]


def test_cross_league_fixtures_are_rejected():
    with TestClient(create_app(ROOT)) as client:
        spanish_team = client.get("/api/meta", params={"league": "la-liga"}).json()["teams"][0]
        assert client.post("/api/predict", json={
            "league": "la-liga", "home": "Arsenal", "away": spanish_team}).status_code == 422
        assert client.post("/api/predict", json={
            "home": spanish_team, "away": "Chelsea"}).status_code == 422


@pytest.mark.parametrize("broken_league,healthy_league", [
    ("la-liga", "premier-league"), ("premier-league", "la-liga")])
def test_league_failure_is_isolated(tmp_path, broken_league, healthy_league):
    copy_artifacts(tmp_path)
    (tmp_path / LEAGUES[broken_league]["model_dir"] / "model.json").unlink()
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/api/health", params={"league": healthy_league}).status_code == 200
        assert client.get("/api/meta", params={"league": healthy_league}).status_code == 200
        assert client.get("/api/health", params={"league": broken_league}).status_code == 503
        for endpoint in ["/api/meta", "/api/evaluation", "/api/matches.csv"]:
            response = client.get(endpoint, params={"league": broken_league})
            assert response.status_code == 503
            assert str(tmp_path) not in response.text


def test_copied_premier_model_cannot_serve_as_laliga(tmp_path):
    copy_artifacts(tmp_path)
    destination = tmp_path / LEAGUES["la-liga"]["model_dir"] / "model.json"
    destination.write_bytes((tmp_path / "models/model.json").read_bytes())
    with TestClient(create_app(tmp_path)) as client:
        assert client.get("/api/meta").status_code == 200
        assert client.get("/api/meta", params={"league": "la-liga"}).status_code == 503


def test_unknown_league_training_fails_before_writing(tmp_path):
    with pytest.raises(ValueError):
        train(tmp_path, league="not-a-league")
    assert not list(tmp_path.iterdir())
