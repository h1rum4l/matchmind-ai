"""Streamlit entry point. Reads local JSON/CSV only; no API keys or runtime downloads."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import streamlit as st

from matchmind.model import predict

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="MatchMind AI | Premier League", layout="wide")


@st.cache_data
def load_assets(model_bytes, report_bytes, match_bytes, manifest_bytes):
    model, report, manifest = [json.loads(b) for b in (model_bytes, report_bytes, manifest_bytes)]
    if hashlib.sha256(match_bytes).hexdigest() != manifest["csv_sha256"]:
        raise ValueError("Match CSV differs from the verified manifest; run data ingestion again")
    if (model["data_csv_sha256"] != manifest["csv_sha256"]
            or report["data_provenance"]["csv_sha256"] != manifest["csv_sha256"]):
        raise ValueError("Model or evaluation belongs to different data; rerun training")
    from io import BytesIO
    matches = pd.read_csv(BytesIO(match_bytes), parse_dates=["date"])
    return model, report, matches, manifest


def form_stats(matches, team):
    recent = matches[(matches.home == team) | (matches.away == team)].tail(10)
    home = recent.home == team
    scored = recent.home_goals.where(home, recent.away_goals)
    conceded = recent.away_goals.where(home, recent.home_goals)
    return dict(Team=team, Matches=len(recent), **{
        "Goals per match": round(float(scored.mean()), 2),
        "Conceded per match": round(float(conceded.mean()), 2),
        "Points per match": round(float(((scored > conceded) * 3 + (scored == conceded)).mean()), 2),
    })


try:
    stylesheet = (ROOT / "assets/app.css").read_text(encoding="utf-8")
    landing = (ROOT / "index.html").read_text(encoding="utf-8")
    if (landing.count("<!-- STREAMLIT_START -->") != 1
            or landing.count("<!-- STREAMLIT_END -->") != 1
            or landing.index("<!-- STREAMLIT_END -->") < landing.index("<!-- STREAMLIT_START -->")):
        raise ValueError("Design preview is incomplete; restore index.html from the full download")
    hero = landing.split("<!-- STREAMLIT_START -->", 1)[1].split("<!-- STREAMLIT_END -->", 1)[0]
    model, report, matches, manifest = load_assets(
        (ROOT / "models/model.json").read_bytes(),
        (ROOT / "models/evaluation.json").read_bytes(),
        (ROOT / "data/matches.csv").read_bytes(),
        (ROOT / "data/manifest.json").read_bytes(),
    )
except (OSError, ValueError, KeyError, TypeError) as error:
    st.error(f"Local project assets could not be loaded: {error}")
    st.write("If design files are missing, restore the full project download.")
    st.code("python -m matchmind.data --offline\npython -m matchmind.train")
    st.stop()

st.html(f"<style>{stylesheet}</style>")
# Streamlit sanitizes scripts: share the static hero, retaining CSS motion and native controls.
st.html(hero.replace("http://localhost:8501/", ""))
st.header("Pick your fixture", anchor="predict-match")
st.markdown('<p id="model-notes" class="mm-model-note"><strong>How predictions work.</strong> '
            'Historical team scoring, defence and home advantage estimate goal rates. A Poisson model '
            'turns them into scorelines and outcome probabilities, adjusted on a separate calibration season.</p>',
            unsafe_allow_html=True)
st.caption(f"Historical snapshot: {manifest['data_start']} to {manifest['data_end']} · "
           f"{len(matches):,} matches · OpenFootball / CC0")
st.info("This is a historical model, not a live match feed. No current injuries, lineups, transfers or odds are included.")
forecast, evaluation, data_tab = st.tabs(["Predict a match", "Historical evaluation", "Data & method"])

with forecast:
    latest = matches[matches.season == matches.season.max()]
    teams = sorted(set(latest.home) | set(latest.away))
    with st.form("match"):
        left, right = st.columns(2)
        home = left.selectbox("Home team", teams, index=teams.index("Arsenal"))
        away = right.selectbox("Away team", teams, index=teams.index("Chelsea"))
        st.form_submit_button("Predict match", type="primary")
    if home == away:
        st.warning("Choose two different teams.")
    else:
        try:
            result = predict(model, home, away)
        except (ValueError, KeyError, TypeError) as error:
            st.error(f"Prediction unavailable: {error}. Rebuild the local model.")
        else:
            st.subheader(f"{home} at home against {away}")
            for column, label, probability in zip(st.columns(3), ["Home win", "Draw", "Away win"], result["probabilities"]):
                column.metric(label, f"{probability:.1%}")
            chart = pd.DataFrame({"Outcome": ["Home win", "Draw", "Away win"],
                                  "Probability": result["probabilities"]}).set_index("Outcome")
            st.bar_chart(chart, color="#9fe8bd", height=180)
            st.write(f"Most likely exact score: **{result['score'][0]} – {result['score'][1]}** "
                     f"({result['score_probability']:.1%} under the uncalibrated goal model).")
            st.write(f"Model expected goals: **{result['home_goals']:.2f}** home / "
                     f"**{result['away_goals']:.2f}** away. These are goal-rate estimates, not shot-based xG.")
            st.caption("Outcome probabilities receive temperature calibration. The exact score uses the raw "
                       "Poisson distribution; its implied winner can differ from the most likely outcome.")
            st.subheader("Recent historical form")
            st.dataframe(pd.DataFrame([form_stats(matches, home), form_stats(matches, away)]), hide_index=True,
                         use_container_width=True)
            st.caption(f"Last 10 recorded matches per team, through {manifest['data_end']}. "
                       "Descriptive context only; these averages are not additional model inputs.")

with evaluation:
    st.subheader("A future season held out from training")
    st.write("Goal fitting: before July 2023. Calibration: 2023–24. Test: 2024–25. "
             "The test season is used only for final scoring, with no match-by-match refitting.")
    st.caption("These scores belong to the frozen evaluation model. The prediction model is refitted on "
               "all five seasons with the historical calibration temperature; its future accuracy is unmeasured.")
    comparison = pd.DataFrame(report["metrics"]).T.rename(columns={
        "accuracy": "Accuracy", "log_loss": "Log loss", "brier": "Brier score"})
    st.dataframe(comparison.style.format({"Accuracy": "{:.1%}", "Log loss": "{:.3f}",
                                         "Brier score": "{:.3f}"}), use_container_width=True)
    st.subheader("Calibration check")
    st.caption("Within each probability bin, compare mean prediction with actual outcome frequency. "
               "Small bin counts are noisy; calibration can worsen unseen-season performance.")
    st.dataframe(pd.DataFrame(report["reliability"]), hide_index=True, use_container_width=True)
    with st.expander("Split dates, provenance and full report"):
        st.json(report)
    st.download_button("Download evaluation report", json.dumps(report, indent=2),
                       file_name="matchmind-evaluation.json", mime="application/json")
    st.write("Accuracy measures the most likely outcome. Log loss penalizes confident mistakes. "
             "Multiclass Brier score sums squared errors across all three outcomes (0–2). "
             "Lower log loss and Brier are better. Calibration does not guarantee reliability on future seasons.")

with data_tab:
    st.subheader("Reproducible, free and local")
    st.write("A regularized Poisson regression estimates goal rates using the scoring team, opponent and "
             "home advantage. Older matches receive less weight, with a fixed two-year half-life. "
             "Independent goal counts yield home/draw/away probabilities. A held-out season learns "
             "one calibration temperature. Promoted teams unseen during evaluation receive league-average strengths.")
    st.write("The selector contains the 20 teams in the 2024–25 snapshot. Results do not represent the "
             "current Premier League membership. This MVP omits live updates, player-level features and betting advice.")
    st.dataframe(matches.tail(20), hide_index=True, use_container_width=True)
    st.download_button("Download historical matches", (ROOT / "data/matches.csv").read_bytes(),
                       file_name="matches.csv", mime="text/csv")
    st.markdown("Data: [OpenFootball](https://github.com/openfootball/football.json) · "
                "[CC0 dedication](https://creativecommons.org/publicdomain/zero/1.0/)")
