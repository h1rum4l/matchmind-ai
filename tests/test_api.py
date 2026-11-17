import hashlib
import json
from pathlib import Path
import shutil

from fastapi.testclient import TestClient
import pytest

from matchmind.api import create_app
from matchmind.model import predict

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(ROOT, web_root=tmp_path / "not-built")) as connection:
        yield connection


def test_health_metadata_and_report(client):
    assert client.get("/api/health").json() == {"status": "ready"}
    metadata = client.get("/api/meta").json()
    assert len(metadata["teams"]) == 20
    assert metadata["teams"] == sorted(metadata["teams"])
    assert metadata["snapshot"]["matches"] == 1900
    assert metadata["snapshot"]["end"] == "2025-05-25"
    assert len(metadata["snapshot"]["seasons"]) == 5
    report = client.get("/api/evaluation").json()
    assert metadata["metrics"] == report["metrics"]
    assert metadata["splits"] == report["splits"]
    assert metadata["production_note"] == report["production_note"]


def test_prediction_parity_and_stats(client):
    response = client.post("/api/predict", json={"home": "Arsenal", "away": "Chelsea"})
    assert response.status_code == 200
    result = response.json()
    model = json.loads((ROOT / "models/model.json").read_bytes())
    expected = predict(model, "Arsenal", "Chelsea")
    for key, value in expected.items():
        assert result[key] == value
    assert sum(result["probabilities"]) == pytest.approx(1)
    assert result["home"] == "Arsenal" and result["away"] == "Chelsea"
    assert [row["team"] for row in result["stats"]] == ["Arsenal", "Chelsea"]
    for row in result["stats"]:
        assert row["matches"] == 10
        assert 0 <= row["points_per_match"] <= 3
        assert row["goals_per_match"] >= 0
        assert row["last_match"] == "2025-05-25"


@pytest.mark.parametrize("body", [
    {"home": "Arsenal", "away": "Arsenal"},
    {"home": "Unknown", "away": "Chelsea"},
    {"home": "<script>alert(1)</script>", "away": "Chelsea"},
    {"home": "../../models/model.json", "away": "Chelsea"},
    {"home": "Arsenal", "away": "Chelsea", "model": "other"},
    {"home": 1, "away": "Chelsea"},
    {"home": "Arsenal", "away": None},
    {"home": "", "away": "Chelsea"},
    {"home": "x" * 81, "away": "Chelsea"},
    {"home": "Arsenal"},
    {"home": "Leeds United", "away": "Chelsea"},
])
def test_strict_request_validation(client, body):
    assert client.post("/api/predict", json=body).status_code == 422


def test_download_and_unknown_api(client):
    response = client.get("/api/matches.csv")
    assert response.status_code == 200
    assert response.content == (ROOT / "data/matches.csv").read_bytes()
    assert 'filename="matches.csv"' in response.headers["content-disposition"]
    assert response.headers["content-type"].startswith("text/csv")
    for endpoint in ["/api/unknown", "/api/not-found/deeper", "/api"]:
        missing = client.get(endpoint)
        assert missing.status_code == 404
        assert missing.headers["content-type"] == "application/json"
    assert client.get("/").status_code == 503


def copy_artifacts(destination):
    for folder in ["data", "models"]:
        shutil.copytree(ROOT / folder, destination / folder)


@pytest.mark.parametrize("broken", ["missing_model", "checksum", "model_hash", "report_hash", "schema", "end", "empty", "metrics", "splits"])
def test_invalid_artifacts_are_safe_503(tmp_path, broken):
    copy_artifacts(tmp_path)
    if broken == "missing_model":
        (tmp_path / "models/model.json").unlink()
    elif broken == "checksum":
        (tmp_path / "data/matches.csv").write_text("corrupt")
    elif broken == "empty":
        path = tmp_path / "data/matches.csv"
        content = b"date,home,away,home_goals,away_goals,season\n"
        path.write_bytes(content)
        checksum = hashlib.sha256(content).hexdigest()
        for file, key in [("data/manifest.json", "csv_sha256"),
                          ("models/model.json", "data_csv_sha256")]:
            target = tmp_path / file
            value = json.loads(target.read_bytes())
            value[key] = checksum
            target.write_text(json.dumps(value))
        path = tmp_path / "models/evaluation.json"
        value = json.loads(path.read_bytes())
        value["data_provenance"]["csv_sha256"] = checksum
        path.write_text(json.dumps(value))
    else:
        path = tmp_path / ("models/evaluation.json" if broken in ["report_hash", "metrics", "splits"] else "models/model.json")
        value = json.loads(path.read_bytes())
        if broken == "report_hash":
            value["data_provenance"]["csv_sha256"] = "wrong"
        elif broken == "metrics":
            value["metrics"] = {"bad": {"accuracy": "invalid"}}
        elif broken == "splits":
            value["splits"]["test"]["end"] = "2030-01-01"
        elif broken == "model_hash":
            value["data_csv_sha256"] = "wrong"
        elif broken == "schema":
            value["schema_version"] = 99
        else:
            value["data_end"] = "2000-01-01"
        path.write_text(json.dumps(value))
    with TestClient(create_app(tmp_path)) as connection:
        health = connection.get("/api/health")
        assert health.status_code == 503
        assert health.json() == {"status": "unavailable"}
        for endpoint in ["/api/meta", "/api/evaluation", "/api/matches.csv"]:
            response = connection.get(endpoint)
            assert response.status_code == 503
            assert str(tmp_path) not in response.text
        assert connection.post("/api/predict", json={"home": "Arsenal", "away": "Chelsea"}).status_code == 503


def test_static_frontend_and_api_route_order(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>Fixture frontend</title>")
    (tmp_path / "app.js").write_text("console.log('frontend')")
    with TestClient(create_app(ROOT, web_root=tmp_path)) as connection:
        assert "Fixture frontend" in connection.get("/").text
        assert connection.get("/app.js").status_code == 200
        missing = connection.get("/api/not-real")
        assert missing.status_code == 404
        assert missing.json() == {"detail": "API route not found"}
        assert connection.get("/api/health").status_code == 200


def test_bundle_is_cached_until_restart(tmp_path):
    copy_artifacts(tmp_path)
    with TestClient(create_app(tmp_path)) as connection:
        original = connection.get("/api/matches.csv").content
        (tmp_path / "data/matches.csv").write_text("changed after startup")
        (tmp_path / "models/model.json").unlink()
        assert connection.get("/api/matches.csv").content == original
        assert connection.post("/api/predict", json={"home": "Arsenal", "away": "Chelsea"}).status_code == 200
