import copy
import hashlib
import json
from pathlib import Path

import pytest

from matchmind.data import HASHES, ingest, parse_season

ROOT = Path(__file__).resolve().parents[1]


def payload():
    return json.loads((ROOT / "data/raw/2024-25.json").read_bytes())


def test_snapshot_and_reproducible_ingestion():
    before = (ROOT / "data/matches.csv").read_bytes()
    manifest = ingest(offline=True)
    assert manifest["matches"] == 1900
    assert hashlib.sha256(before).hexdigest() == manifest["csv_sha256"]
    assert len(HASHES) == 5


@pytest.mark.parametrize("mutation", ["date", "negative", "duplicate", "missing", "self"])
def test_reject_malformed_matches(mutation):
    source = copy.deepcopy(payload())
    match = source["matches"][0]
    if mutation == "date":
        match["date"] = "2019-01-01"
    elif mutation == "negative":
        match["score"]["ft"][0] = -1
    elif mutation == "duplicate":
        source["matches"][1] = copy.deepcopy(match)
    elif mutation == "self":
        match["team2"] = match["team1"]
    else:
        match["score"].pop("ft")
    with pytest.raises(ValueError):
        parse_season(source, "2024-25")


def test_checksum_failure_preserves_existing_data(tmp_path):
    raw = tmp_path / "data/raw"
    raw.mkdir(parents=True)
    (raw / "2020-21.json").write_text("{}")
    csv = tmp_path / "data/matches.csv"
    csv.write_text("keep this")
    with pytest.raises(ValueError, match="Checksum"):
        ingest(tmp_path, offline=True)
    assert csv.read_text() == "keep this"


def test_offline_missing_file(tmp_path):
    with pytest.raises(ValueError, match="Offline file missing"):
        ingest(tmp_path, offline=True)
