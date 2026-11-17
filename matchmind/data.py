"""Download a checksummed CC0 snapshot; never silently substitute sample data."""
import argparse
from collections import Counter
from datetime import date
import hashlib
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

import pandas as pd

from matchmind.leagues import DEFAULT_LEAGUE, LEAGUES, SOURCE_COMMIT, get_league

ROOT = Path(__file__).resolve().parents[1]
COMMIT = SOURCE_COMMIT
HASHES = LEAGUES[DEFAULT_LEAGUE]["hashes"]


def canonical(name):
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Missing team name")
    return name.removesuffix(" FC").strip()


def parse_season(payload, season, league=DEFAULT_LEAGUE):
    config = get_league(league)
    expected = config["expected_matches"][season]
    rows, fixtures = [], []
    start = int(season[:4])
    for match in payload["matches"]:
        score = match.get("score", {}).get("ft")
        played = date.fromisoformat(match["date"])
        if not date(start, 7, 1) <= played < date(start + 1, 7, 1):
            raise ValueError(f"Date outside season {season}: {played}")
        home, away = canonical(match["team1"]), canonical(match["team2"])
        if home == away:
            raise ValueError("Team cannot play itself")
        fixtures.append((home, away))
        if score is None:
            if expected == 380:
                raise ValueError(f"Incomplete match in {season}")
            continue
        if len(score) != 2 or any(type(g) is not int or not 0 <= g <= 30 for g in score):
            raise ValueError("Invalid full-time goals")
        rows.append(dict(date=played.isoformat(), home=home, away=away,
                         home_goals=score[0], away_goals=score[1], season=season))
    frame = pd.DataFrame(rows)
    pairs = Counter(fixtures)
    teams = {team for pair in fixtures for team in pair}
    if (len(fixtures) != 380 or len(rows) != expected or len(teams) != 20
            or any(n != 1 for n in pairs.values())):
        raise ValueError(f"{season}: expected 380 unique fixtures, {expected} completed results and 20 teams")
    if any(sum(team in pair for pair in pairs) != 38 for team in teams):
        raise ValueError(f"{season}: expected 38 appearances per club")
    return frame


def source_url(season, league=DEFAULT_LEAGUE):
    config = get_league(league)
    commit = config.get("commits", {}).get(season, COMMIT)
    return f"https://raw.githubusercontent.com/openfootball/football.json/{commit}/{season}/{config['source_file']}"


def download(url):
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "MatchMindAI/1.0"})
            with urllib.request.urlopen(request, timeout=30) as response:
                content = response.read(2_000_001)
            if len(content) > 2_000_000:
                raise ValueError("Source exceeds expected size")
            return content
        except (urllib.error.URLError, TimeoutError, OSError):
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(content)
    temporary.replace(path)


def ingest(root=ROOT, offline=False, league=DEFAULT_LEAGUE):
    config = get_league(league)
    data_dir = root / config["data_dir"]
    frames, sources = [], []
    for season, expected in config["hashes"].items():
        path = data_dir / "raw" / f"{season}.json"
        if offline and not path.exists():
            raise ValueError(f"Offline file missing: {path}; see README manual download steps")
        content = path.read_bytes() if path.exists() else download(source_url(season, league))
        checksum = hashlib.sha256(content).hexdigest()
        if checksum != expected:
            raise ValueError(f"Checksum mismatch: {path}; restore exact pinned upstream bytes")
        parsed = parse_season(json.loads(content), season, league)
        frames.append(parsed)
        if not path.exists():
            atomic_write(path, content)
        sources.append(dict(season=season, url=source_url(season, league), sha256=checksum,
                            completed_matches=len(parsed), missing_results=380 - len(parsed)))
    frame = pd.concat(frames).sort_values(["date", "home"]).reset_index(drop=True)
    csv = frame.to_csv(index=False, lineterminator="\n").encode()
    manifest = dict(source="OpenFootball football.json", license="CC0-1.0", commit=COMMIT,
                    sources=sources, matches=len(frame), data_start=frame.date.min(),
                    data_end=frame.date.max(), csv_sha256=hashlib.sha256(csv).hexdigest(),
                    league={"id": league, "name": config["name"]},
                    missing_results=sum(item["missing_results"] for item in sources))
    atomic_write(data_dir / "matches.csv", csv)
    atomic_write(data_dir / "manifest.json", (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--offline", action="store_true", help="Use bundled, verified raw files only")
    parser.add_argument("--league", choices=LEAGUES, default=DEFAULT_LEAGUE)
    args = parser.parse_args()
    try:
        result = ingest(offline=args.offline, league=args.league)
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.exit(1, f"Data ingestion failed: {error}\nSee README for offline onboarding.\n")
    print(f"Verified {result['league']['name']}: {result['matches']} completed matches through "
          f"{result['data_end']}; {result['missing_results']} fixtures lack results")


if __name__ == "__main__":
    main()
