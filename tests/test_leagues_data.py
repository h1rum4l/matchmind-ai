import copy
import hashlib
import json
from pathlib import Path
import shutil

import pytest

from matchmind.data import ingest, parse_season, source_url
from matchmind.leagues import get_league

ROOT = Path(__file__).resolve().parents[1]


def spanish_source():
    return json.loads((ROOT / "data/la-liga/raw/2024-25.json").read_bytes())


def test_la_liga_ingestion_is_reproducible_and_separate(tmp_path):
    shutil.copytree(ROOT / "data/la-liga/raw", tmp_path / "data/la-liga/raw")
    sentinel = tmp_path / "data/matches.csv"
    sentinel.write_bytes(b"keep Premier League data")
    report = ingest(tmp_path, offline=True, league="la-liga")
    assert report["league"] == {"id": "la-liga", "name": "La Liga"}
    assert report["matches"] == 1890
    assert report["missing_results"] == 10
    assert report["data_end"] == "2025-05-18"
    actual = (tmp_path / "data/la-liga/matches.csv").read_bytes()
    assert actual == (ROOT / "data/la-liga/matches.csv").read_bytes()
    assert report["csv_sha256"] == hashlib.sha256(actual).hexdigest()
    assert report["sources"][-1]["completed_matches"] == 370
    assert sentinel.read_bytes() == b"keep Premier League data"


def test_only_the_known_missing_results_are_excluded():
    payload = spanish_source()
    completed = parse_season(payload, "2024-25", league="la-liga")
    assert len(completed) == 370
    assert "FC Barcelona" in set(completed.home)
    assert "Arsenal" not in set(completed.home)
    altered = copy.deepcopy(payload)
    next(match for match in altered["matches"] if match.get("score", {}).get("ft"))["score"].pop("ft")
    with pytest.raises(ValueError, match="370 completed results"):
        parse_season(altered, "2024-25", league="la-liga")


def test_missing_result_fixture_still_requires_valid_date():
    payload = spanish_source()
    pending = next(match for match in payload["matches"] if match.get("score", {}).get("ft") is None)
    pending["date"] = "2018-01-01"
    with pytest.raises(ValueError, match="Date outside"):
        parse_season(payload, "2024-25", league="la-liga")


def test_league_selection_never_becomes_a_path(tmp_path):
    with pytest.raises(ValueError, match="supported league"):
        ingest(tmp_path, offline=True, league="../../other")
    assert list(tmp_path.iterdir()) == []
    assert source_url("2024-25", "la-liga").endswith("/2024-25/es.1.json")
    assert get_league()["source_file"] == "en.1.json"
