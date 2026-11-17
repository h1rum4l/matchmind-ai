import json
from pathlib import Path
import shutil
import tomllib

from fastapi.testclient import TestClient
from packaging.specifiers import SpecifierSet

from matchmind.api import create_app
from matchmind.leagues import LEAGUES

ROOT = Path(__file__).resolve().parents[1]


def test_hosted_runtime_is_python_312_with_matching_dependencies():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    versions = SpecifierSet(project["project"]["requires-python"])
    assert "3.12.0" in versions
    assert "3.12.16" in versions
    assert "3.13.0" not in versions
    assert "3.14.8" not in versions
    requirements = set((ROOT / "requirements.txt").read_text().splitlines())
    assert set(project["project"]["dependencies"]) == requirements
    assert project["tool"]["vercel"]["entrypoint"] == "matchmind.api:app"


def test_vercel_builds_frontend_and_keeps_runtime_data():
    config = json.loads((ROOT / "vercel.json").read_bytes())
    assert config["framework"] == "fastapi"
    assert config["buildCommand"] == "npm ci && npm run build"
    exclusions = config["functions"]["matchmind/api.py"]["excludeFiles"]
    assert "data/raw/**" in exclusions
    assert "data/la-liga/raw/**" in exclusions
    assert "models/**" not in exclusions
    assert "frontend/dist/**" not in exclusions
    package = json.loads((ROOT / "package.json").read_bytes())
    lock = json.loads((ROOT / "package-lock.json").read_bytes())
    assert package["engines"]["node"] == lock["packages"][""]["engines"]["node"] == "24.x"


def test_both_leagues_run_without_excluded_training_inputs(tmp_path):
    for league in LEAGUES.values():
        data = tmp_path / league["data_dir"]
        data.mkdir(parents=True, exist_ok=True)
        for filename in ("matches.csv", "manifest.json"):
            shutil.copy2(ROOT / league["data_dir"] / filename, data / filename)
        model = tmp_path / league["model_dir"]
        model.mkdir(parents=True, exist_ok=True)
        for filename in ("model.json", "evaluation.json"):
            shutil.copy2(ROOT / league["model_dir"] / filename, model / filename)
    with TestClient(create_app(tmp_path)) as client:
        for league_id, teams in [("premier-league", ("Arsenal", "Chelsea")),
                                 ("la-liga", ("FC Barcelona", "Real Madrid CF"))]:
            assert client.get("/api/meta", params={"league": league_id}).status_code == 200
            response = client.post("/api/predict", json={"league": league_id, "home": teams[0], "away": teams[1]})
            assert response.status_code == 200
            assert response.json()["league"]["id"] == league_id
