"""Local prediction API and production frontend host. No startup downloads."""

from contextlib import asynccontextmanager
import hashlib
from io import BytesIO
import json
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from matchmind.leagues import DEFAULT_LEAGUE, LEAGUES, get_league
from matchmind.model import predict

ROOT = Path(__file__).resolve().parents[1]
LOGGER = logging.getLogger(__name__)
UNAVAILABLE = "Prediction data is unavailable. Rebuild the local data and models, then restart the server."


class Fixture(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    home: str = Field(min_length=1, max_length=80)
    away: str = Field(min_length=1, max_length=80)
    league: str = Field(default=DEFAULT_LEAGUE, min_length=1, max_length=40)


def _read_json(path):
    def reject_constant(value):
        raise ValueError(f"Non-finite JSON number: {value}")

    return json.loads(path.read_bytes(), parse_constant=reject_constant)


def _load_bundle(root, league=DEFAULT_LEAGUE):
    config = get_league(league)
    identity = {"id": league, "name": config["name"]}
    data_root, model_root = root / config["data_dir"], root / config["model_dir"]
    model = _read_json(model_root / "model.json")
    report = _read_json(model_root / "evaluation.json")
    manifest = _read_json(data_root / "manifest.json")
    for artifact in [model, report]:
        if artifact.get("league") != identity and not (league == DEFAULT_LEAGUE and "league" not in artifact):
            raise ValueError("Model or evaluation belongs to a different league")
    if "league" in manifest and manifest["league"] not in [league, identity]:
        raise ValueError("Data manifest belongs to a different league")
    csv = (data_root / "matches.csv").read_bytes()
    checksum = hashlib.sha256(csv).hexdigest()
    if not (checksum == manifest["csv_sha256"] == model["data_csv_sha256"]
            == report["data_provenance"]["csv_sha256"]):
        raise ValueError("CSV, manifest, model and evaluation checksums differ")
    matches = pd.read_csv(BytesIO(csv), parse_dates=["date"])
    required = {"date", "home", "away", "home_goals", "away_goals", "season"}
    if not required.issubset(matches.columns) or matches.empty or matches[list(required)].isna().any().any():
        raise ValueError("Match table is missing required fields or completed results")
    matches["date"] = pd.to_datetime(matches.date, errors="raise")
    if (matches.home == matches.away).any() or matches.duplicated(["season", "home", "away"]).any():
        raise ValueError("Invalid or duplicate fixtures")
    for field in ["home", "away", "season"]:
        if not matches[field].map(lambda value: isinstance(value, str) and bool(value.strip())).all():
            raise ValueError("Invalid team or season identifier")
    goals = matches[["home_goals", "away_goals"]].to_numpy(dtype=float)
    if not np.isfinite(goals).all() or (goals < 0).any() or (goals > 30).any() or (goals != np.floor(goals)).any():
        raise ValueError("Invalid goal counts")
    matches = matches.sort_values(["date", "home"]).reset_index(drop=True)
    start, end = matches.date.min().date().isoformat(), matches.date.max().date().isoformat()
    if (manifest["data_start"] != start or manifest["data_end"] != end
            or manifest["matches"] != len(matches) or model["data_end"] != end
            or model["train_end"] != end or model["schema_version"] != 1):
        raise ValueError("Snapshot dates, counts or model schema do not match")
    model_teams = model["teams"]
    if not isinstance(model_teams, list) or not model_teams or len(set(model_teams)) != len(model_teams):
        raise ValueError("Invalid model team list")
    if set(model_teams) != set(matches.home) | set(matches.away):
        raise ValueError("Model team list does not match historical matches")
    coefficients = [model["intercept"], model["home_advantage"], model["temperature"]]
    coefficients += [model[effect][team] for effect in ["attack", "defence"] for team in model_teams]
    if not all(type(value) in (int, float) and np.isfinite(value) for value in coefficients):
        raise ValueError("Invalid model coefficients")
    if model["temperature"] <= 0:
        raise ValueError("Invalid calibration temperature")
    seasons = sorted(matches.season.unique().tolist())
    latest = matches[matches.season == seasons[-1]]
    teams = sorted(set(latest.home) | set(latest.away))
    expected_matches = config.get("expected_matches", {}).get(seasons[-1], 380)
    if len(teams) != 20 or len(latest) != expected_matches:
        raise ValueError("Latest season must contain 20 clubs and its expected completed fixture count")
    if not isinstance(report["metrics"], dict) or not report["metrics"] or not report["splits"]:
        raise ValueError("Evaluation report is incomplete")
    for measured in report["metrics"].values():
        for name in ["accuracy", "log_loss", "brier"]:
            value = measured[name]
            if type(value) not in (int, float) or not np.isfinite(value):
                raise ValueError("Invalid evaluation metric")
    for name in ["train", "calibration", "test"]:
        part = report["splits"][name]
        if type(part["count"]) is not int or part["count"] <= 0:
            raise ValueError("Invalid evaluation split count")
        if not start <= part["start"] <= part["end"] <= end:
            raise ValueError("Evaluation split lies outside the snapshot")
    if not isinstance(report["production_note"], str) or not report["production_note"]:
        raise ValueError("Production evaluation note is missing")
    # Verify the exported coefficient schema is usable before accepting traffic.
    predict(model, teams[0], teams[1])
    return {"model": model, "report": {**report, "league": identity}, "matches": matches,
            "csv": csv, "teams": teams, "league": identity,
            "meta": {"league": identity, "teams": teams, "snapshot": {"start": start, "end": end,
                     "matches": len(matches), "seasons": seasons,
                     "missing_results": manifest.get("missing_results", 0)}, "metrics": report["metrics"],
                     "splits": report["splits"], "production_note": report["production_note"]}}


def _stats(matches, team):
    recent = matches[(matches.home == team) | (matches.away == team)].tail(10)
    at_home = recent.home == team
    scored = recent.home_goals.where(at_home, recent.away_goals)
    conceded = recent.away_goals.where(at_home, recent.home_goals)
    return {"team": team, "matches": len(recent), "goals_per_match": float(scored.mean()),
            "conceded_per_match": float(conceded.mean()),
            "points_per_match": float(((scored > conceded) * 3 + (scored == conceded)).mean()),
            "last_match": recent.date.max().date().isoformat()}


def create_app(root=ROOT, web_root=None):
    root = Path(root)
    web_root = Path(web_root) if web_root is not None else root / "frontend/dist"

    @asynccontextmanager
    async def lifespan(application):
        application.state.bundles = {}
        for league in LEAGUES:
            try:
                application.state.bundles[league] = _load_bundle(root, league)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                LOGGER.exception("MatchMind could not validate local artifacts for league %s", league)
        yield
        application.state.bundles.clear()

    application = FastAPI(title="MatchMind AI", version="1.0.0", lifespan=lifespan)

    def bundle(request, league=DEFAULT_LEAGUE):
        if league not in LEAGUES:
            raise HTTPException(status_code=422, detail="Choose a league from /api/leagues.")
        loaded = getattr(request.app.state, "bundles", {}).get(league)
        if loaded is None:
            raise HTTPException(status_code=503, detail=UNAVAILABLE)
        return loaded

    @application.get("/api/health")
    def health(request: Request, league: str = DEFAULT_LEAGUE):
        if league not in LEAGUES:
            raise HTTPException(status_code=422, detail="Choose a league from /api/leagues.")
        if getattr(request.app.state, "bundles", {}).get(league) is None:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ready"}

    @application.get("/api/leagues")
    def leagues():
        return {"leagues": [{"id": key, "name": value["name"]} for key, value in LEAGUES.items()],
                "default": DEFAULT_LEAGUE}

    @application.get("/api/meta")
    def metadata(request: Request, league: str = DEFAULT_LEAGUE):
        return bundle(request, league)["meta"]

    @application.post("/api/predict")
    def prediction(fixture: Fixture, request: Request):
        loaded = bundle(request, fixture.league)
        if fixture.home == fixture.away:
            raise HTTPException(status_code=422, detail="Choose two different teams.")
        if fixture.home not in loaded["teams"] or fixture.away not in loaded["teams"]:
            raise HTTPException(status_code=422, detail="Choose teams from the latest historical season's team list.")
        try:
            result = predict(loaded["model"], fixture.home, fixture.away)
        except (ValueError, KeyError, TypeError):
            LOGGER.exception("Prediction failed with validated local model")
            raise HTTPException(status_code=503, detail=UNAVAILABLE) from None
        return {"home": fixture.home, "away": fixture.away, "league": loaded["league"], **result,
                "stats": [_stats(loaded["matches"], team) for team in [fixture.home, fixture.away]]}

    @application.get("/api/evaluation")
    def evaluation(request: Request, league: str = DEFAULT_LEAGUE):
        return bundle(request, league)["report"]

    @application.get("/api/matches.csv")
    def download_matches(request: Request, league: str = DEFAULT_LEAGUE):
        loaded = bundle(request, league)
        filename = "matches.csv" if league == DEFAULT_LEAGUE else f"{league}-matches.csv"
        return Response(loaded["csv"], media_type="text/csv",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

    @application.api_route("/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    @application.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
    def unknown_api(path: str = ""):
        raise HTTPException(status_code=404, detail="API route not found")

    if (web_root / "index.html").is_file():
        application.mount("/", StaticFiles(directory=web_root, html=True), name="frontend")
    else:
        @application.get("/")
        def missing_frontend():
            return JSONResponse({"detail": "Frontend is not built. Run npm ci and npm run build in the project root, then restart the server."},
                                status_code=503)

    return application


app = create_app()
