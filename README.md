# MatchMind AI

A free, local **Premier League and La Liga** match prediction app. Choose a league, then a home and away team to see home/draw/away probabilities, a most likely scoreline, expected goals, and simple historical statistics. A React + Vite website calls a FastAPI backend running independent Python, pandas, scikit-learn, and Poisson goal models for each league. No API key, ChatGPT subscription, Gemini subscription, GPU, or paid service is needed.

Both bundled datasets cover 2020–21 through 2024–25:

| League | Completed matches | Last included result | Coverage note |
|---|---:|---|---|
| Premier League | 1,900 | 25 May 2025 | Five complete seasons |
| La Liga | 1,890 | 18 May 2025 | Ten final-round results are missing from the pinned upstream source |

These are historical snapshots, not a live forecast service. The available teams reflect each league's 2024–25 season; some current clubs may be absent. La Liga's ten missing Matchday 38 results are excluded explicitly rather than invented. This describes missing source data, not games that were unplayed.

## React website and Python predictions

The primary app is now the React website, with the football hero, WebGL atmosphere, credited local player photos, and a league selector connected to Python through `/api`. Switching leagues uses that league's teams, model, historical statistics, and evaluation. FastAPI serves both the built website and predictions at one address. Start the server and visit its URL; opening an HTML file directly does not start the model API.

The Premier League model and historical evaluation remain unchanged; La Liga has its own separately fitted artifacts. Photo attribution and licenses are in [assets/PHOTO_CREDITS.md](assets/PHOTO_CREDITS.md). Local photos work without an image service; if the theme requests Google Fonts, a system font remains available offline. Reduced-motion and WebGL fallback behavior are part of the frontend; browser/hardware differences can affect animation.

The earlier `app.py` Streamlit app remains an optional legacy interface. Its setup is separate below. When updating an existing Documents installation, keep a copy of your previous files; the migration backup location is `backups/react-20261115/` when the installer has created it. Backups are local recovery files, not files to publish.

## Start on Windows with Anaconda

Extract this project to `C:\Users\Afraz\Documents\matchmind-ai` (or use your own folder). Open **Anaconda Prompt** from the Start menu. Run these commands there, not in the Python console. Create the environment only if it does not already exist:

```bat
cd /d C:\Users\Afraz\Documents\matchmind-ai
conda create -n football-ai python=3.12 -y
conda activate football-ai
python -m pip install -r requirements.txt
python -m uvicorn matchmind.api:app --host 127.0.0.1 --port 8000
```

Open **http://localhost:8000** yourself; Uvicorn does not automatically open a browser. Leave the terminal open while using the app; press `Ctrl+C` in it to stop. On later runs, only change into the folder, activate `football-ai`, and run the final command again.

The delivery includes a built frontend, both datasets, and both saved models, so first launch does not require Node.js, a data download, or training. Python package installation requires internet access once. Predictions, data, and photos load locally.

**Cloning from GitHub:** compiled frontend files are excluded from Git. Run `npm ci` and `npm run build` in the project root before starting the Python server. The ready-to-run ZIP includes that build.

If you prefer Navigator, open **Environments**, select `football-ai`, and use its terminal. The Anaconda `base` environment does not need to be changed.

### Build the website from source

Install Node.js **22.12 or later in the 22 series, or Node 24 LTS**, from [nodejs.org](https://nodejs.org/en/download). Reopen Anaconda Prompt after installing it. [Vite's documented requirement](https://vite.dev/guide/) is Node 20.19+ or 22.12+; this project recommends the newer supported lines. From the project root, with Python dependencies installed:

```bat
node --version
npm --version
npm ci
npm run build
python -m uvicorn matchmind.api:app --host 127.0.0.1 --port 8000
```

`npm ci` installs the committed `package-lock.json` exactly; use it for normal setup. Use `npm install` when intentionally changing frontend dependencies, then commit the updated lock file. Run `npm run build` after editing React, styles, or frontend assets; its output is `frontend/dist/`. The root `package.json` contains the commands, so you do not need to change into `frontend/`. `.node-version` selects Node 24 for tools and hosts that support that file.

Once dependencies and the build are ready, **`npm start`** is a shortcut for the Uvicorn launch command above. Activate `football-ai` first so it uses the correct Python interpreter. It serves the complete app at port 8000; `npm run dev` is the separate live frontend development mode described below.

If PowerShell blocks `npm.ps1`, run `npm.cmd ci` and `npm.cmd run build`, or use Anaconda Prompt. There is no need to weaken your global PowerShell execution policy.

### Develop with two terminals

In the first Anaconda Prompt, from the project root:

```bat
conda activate football-ai
python -m uvicorn matchmind.api:app --host 127.0.0.1 --port 8000 --reload
```

In a second terminal, from the same root:

```bat
npm run dev
```

Open **http://localhost:5173**. Vite forwards `/api` requests to the Python server on port 8000. Both terminals must remain running. The production build uses one FastAPI address instead, so a separate cross-origin configuration is unnecessary. `--reload` is for development only, as explained in the [FastAPI server guide](https://fastapi.tiangolo.com/deployment/manually/).

## Reproduce the data and models

In the activated environment, from the project root:

```bat
python -m matchmind.data
python -m matchmind.train
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
npm ci
npm run test
npm run build
```

Commands without `--league` retain the original Premier League behavior. The data command obtains its five seasons from a fixed OpenFootball revision, validates the results against pinned SHA-256 hashes, and records provenance and checksums in `data/manifest.json`. It writes the processed matches to `data/matches.csv`. Training rebuilds `models/model.json` for the app, `models/evaluation_model.json` for the frozen evaluation model, `models/evaluation.json` for metrics and calibration reliability, and `models/test_predictions.csv` for individual test predictions.

To reproduce La Liga using the bundled raw files:

```bat
python -m matchmind.data --league la-liga --offline
python -m matchmind.train --league la-liga
```

Omit `--offline` to allow downloading missing raw files from the pinned source. La Liga raw inputs live in `data/la-liga/raw/`; its processed table and manifest are `data/la-liga/matches.csv` and `data/la-liga/manifest.json`. Its model, evaluation model, evaluation report, and test predictions use the same filenames under `models/la-liga/`. The manifest records the ten missing upstream results. Each league is trained independently; retraining La Liga does not overwrite Premier League artifacts.

Run training again after changing a league's data or model code, then restart the Python server. Keep the previous artifacts if you need to compare experiments.

`requirements.txt` pins the direct Python runtime dependencies; `requirements-dev.txt` adds tools for testing and linting. `requirements-lock.txt` records the resolved Python package set: use `python -m pip install -r requirements-lock.txt` in a fresh Python 3.12 environment when reproducing that set. `package-lock.json` records the frontend dependency tree. See [VALIDATION.md](VALIDATION.md) for the actual checks performed; the commands above are instructions, not a claim that every environment has been tested.

The saved models use JSON coefficients instead of executable pickle files. This avoids pickle deserialization; model files still need to come from a source you trust and match this app's schema.

### If the downloader cannot reach GitHub

The bundled snapshot can be used offline. You can also download these raw JSON files using a browser on a connected computer and copy them into `data/raw/`:

| Save as | Original pinned file |
|---|---|
| `data/raw/2020-21.json` | [2020–21](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2020-21/en.1.json) |
| `data/raw/2021-22.json` | [2021–22](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2021-22/en.1.json) |
| `data/raw/2022-23.json` | [2022–23](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2022-23/en.1.json) |
| `data/raw/2023-24.json` | [2023–24](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2023-24/en.1.json) |
| `data/raw/2024-25.json` | [2024–25](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2024-25/en.1.json) |

Save the raw JSON, not a GitHub HTML page. Then run:

```bat
python -m matchmind.data --offline
python -m matchmind.train
```

For La Liga, save the corresponding Spanish files under `data/la-liga/raw/`:

| Save as | Original pinned file |
|---|---|
| `data/la-liga/raw/2020-21.json` | [2020–21](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2020-21/es.1.json) |
| `data/la-liga/raw/2021-22.json` | [2021–22](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2021-22/es.1.json) |
| `data/la-liga/raw/2022-23.json` | [2022–23](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2022-23/es.1.json) |
| `data/la-liga/raw/2023-24.json` | [2023–24](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2023-24/es.1.json) |
| `data/la-liga/raw/2024-25.json` | [2024–25](https://raw.githubusercontent.com/openfootball/football.json/e6744429ee395bc86f247348c6184bb08d4eb361/2024-25/es.1.json) |

Then use the two La Liga commands above. Keep the exact source bytes, including the ten empty result records in the 2024–25 raw file; ingestion records and excludes those known missing scores. Unexpected missing results or invalid data should produce an error, never silently substitute made-up matches. Do not disable HTTPS certificate validation to bypass a download problem.

## What the model measures

The goal model estimates each side's scoring rate using team attack/defence information and home advantage. A Poisson score distribution gives possible scorelines and raw home/draw/away probabilities. A temperature calibration step adjusts the outcome probabilities using a later, separate calibration period.

Each league's evaluation respects time, with separate fitted parameters and calibration:

| Stage | Matches used | Purpose |
|---|---|---|
| Fit evaluation goal model | 2020–21 to 2022–23; before July 2023 | Learn parameters from earlier matches |
| Calibrate | 2023–24 | Fit the probability temperature |
| Test once | 2024–25: 380 Premier League matches or 370 scored La Liga matches | Measure performance on later, unseen outcomes |
| Fit app model | All available scored matches from five seasons | Use available history for the app's future-match estimates |

The test uses a frozen evaluation model. Its goal parameters and calibration do not learn the test results. Teams absent from the fitting period receive league-average attack/defence effects, and the report counts affected matches. The app uses a separately refitted model and retains the calibration temperature learned on 2023–24. **Test metrics therefore describe the evaluation pipeline, not an independently tested guarantee for the refitted app model.** Calibration can help or hurt on future data, particularly after a refit or changes in the league.

There is no random train/test split. No result from the test period should influence fitting, calibration, or model choices. Changing the model after inspecting these test scores makes that test set part of development; a fresh later holdout would then be needed for a new unbiased estimate.

The evaluation reports:

- **Accuracy:** fraction of matches where the largest outcome probability picked the actual result. Higher is better. It is not the probability that any individual prediction is correct.
- **Log loss:** evaluates the whole probability distribution and strongly penalizes confident mistakes. Lower is better.
- **Multiclass Brier score:** average sum of squared errors across home/draw/away probabilities, on a 0–2 scale. Lower is better; this is not the binary Brier definition.
- **Baseline comparisons:** training-period outcome frequencies and an always-home prediction provide context for deciding whether the model adds value. The always-home baseline assigns zero probability to draws and away wins, so its log loss is especially poor.

Read `models/evaluation.json` and `models/test_predictions.csv` for Premier League results, or the equivalent files under `models/la-liga/` for La Liga, and use the app's league-specific evaluation view. Each report includes five probability bins per outcome, with average predicted probabilities, observed frequencies, and counts for checking calibration. No accuracy target is promised. A most likely scoreline can still have a low individual probability; the outcome with the greatest total probability need not match the single most likely scoreline.

Premier League, measured on 380 held-out 2024–25 matches:

| Predictor | Accuracy | Log loss | Brier (0–2) |
|---|---:|---:|---:|
| Raw Poisson | 47.4% | 1.043 | 0.628 |
| Temperature-calibrated Poisson | 47.4% | 1.072 | 0.646 |
| Historical outcome frequencies | 40.8% | 1.079 | 0.654 |
| Always home | 40.8% | 21.342 | 1.184 |

Calibration worsened Premier League test log loss and Brier in this run.

La Liga, measured on the **370 available held-out matches from 15 August 2024 through 18 May 2025**, with the final ten results absent upstream:

| Predictor | Accuracy | Log loss | Brier (0–2) |
|---|---:|---:|---:|
| Raw Poisson | 52.2% | 0.988 | 0.588 |
| Temperature-calibrated Poisson | 52.2% | 0.986 | 0.587 |
| Historical outcome frequencies | 44.6% | 1.070 | 0.647 |
| Always home | 44.6% | 19.970 | 1.108 |

Calibration slightly improved La Liga's test log loss and Brier. Its training period contains 1,140 matches from 2020–21 through 2022–23; calibration uses 380 matches from 2023–24. This is a partial-season test, not a complete 380-match assessment. For both leagues, calibration was fitted on 2023–24 and has deliberately not been tuned against the test season. Treat the app probabilities as uncertain estimates, not evidence that calibration always helps. The transferred calibration temperature on each refitted production model still lacks an independent future evaluation. See [VALIDATION.md](VALIDATION.md) for completed checks and limits.

## Data provenance and limits

Source: [OpenFootball football.json](https://github.com/openfootball/football.json), commit `e6744429ee395bc86f247348c6184bb08d4eb361`, files `{season}/en.1.json` for Premier League and `{season}/es.1.json` for La Liga. Both datasets are CC0 1.0; see [DATA_LICENSE.md](DATA_LICENSE.md) for the source hashes. The loader checks dates, scores, team identifiers, duplicate fixtures, and the expected counts: 380 completed matches per season except the explicitly documented 370 for La Liga 2024–25. Checksums identify the exact input bytes used.

The default Premier League range deliberately excludes 2019–20: at this revision, some July 2020 matches are recorded with July 2019 dates. That would invalidate chronological training. La Liga 2024–25 has ten empty result records for Matchday 38, dated 23–25 May 2025; those records stay in the raw source but are excluded from training, statistics, and evaluation. No scores were invented. Adding older or newer seasons requires checking their dates and completeness, not just downloading a larger file.

These are match results, not shot-based expected-goals observations. The app's expected goals are estimates from its goal model. It has no live injuries, lineups, transfers, suspensions, player ratings, betting odds, or guaranteed automatic updates. Promoted teams, changed squads, and stale data reduce reliability. This is a learning and analysis tool; it cannot guarantee a match result or betting profit.

For future updates, choose and audit a newer source revision, update the downloader's pinned data configuration, rerun ingestion/training/tests, and review the new date splits before publishing the artifacts. Keep the source revision and checksums with every model. Do not label forecasts as current while using the bundled 2025 cutoff.

## API league selection

`GET /api/leagues` returns the supported IDs, `premier-league` and `la-liga`, and the default. Existing callers that omit a league still use Premier League. For example:

| Request | Result |
|---|---|
| `GET /api/meta?league=la-liga` | La Liga teams, snapshot, and metrics |
| `GET /api/evaluation?league=la-liga` | La Liga evaluation report |
| `GET /api/matches.csv?league=la-liga` | La Liga completed-match CSV |
| `POST /api/predict` | Prediction using the JSON body's optional `league` |

Example prediction body, using exact team names from `/api/meta`:

```json
{"league": "la-liga", "home": "FC Barcelona", "away": "Real Madrid CF"}
```

Only teams from the selected league's latest historical season are accepted. The API does not offer predictions between teams from different leagues.

## Work in Spyder

Use your existing Spyder installation to edit and explore the Python model files. Keep FastAPI running from Anaconda Prompt; use the browser for the website. Editing React is separate from running Python code in Spyder.

To run model code in Spyder, activate `football-ai` in Anaconda Prompt and find its interpreter:

```bat
python -c "import sys; print(sys.executable)"
```

In Spyder, select that environment through **Consoles → New console in environment**, or **Tools → Preferences → Python interpreter** and select the printed `python.exe`. Restart the kernel. If Spyder asks for `spyder-kernels`, execute the exact compatible installation command it displays in the activated `football-ai` terminal, then restart the kernel again. The required kernel version depends on your installed Spyder version, so it is intentionally not pinned into the web app's dependencies. Set Spyder's working directory to this project root.

See the [official Spyder environment instructions](https://docs.spyder-ide.org/current/faq.html#using-spyder). Use `python -m pip check` after installing optional development tools to detect dependency conflicts.

## Deployment and legacy interfaces

The primary website needs a Python web service. [DEPLOYMENT.md](DEPLOYMENT.md) gives GitHub upload instructions, a single-service FastAPI deployment, and the current Render free-tier option with its limits. GitHub Pages can serve frontend files but cannot run this Python prediction backend. Local operation remains the simplest zero-additional-cost option. No public deployment has been performed on your behalf.

The original root `index.html` remains a Premier League standalone design preview, not the React app entrypoint. Its historical links can point to the legacy Streamlit address. Use `http://localhost:8000` for the complete current app with both leagues.

To run the optional legacy Streamlit interface:

```bat
conda activate football-ai
python -m pip install -r requirements-streamlit.txt
python -m streamlit run app.py
```

Then visit `http://localhost:8501`. The legacy Streamlit interface remains Premier League only. Streamlit is not required by the React/FastAPI app, and the legacy interface does not supply the primary website's live JavaScript/WebGL runtime or league selector.

## Troubleshooting

| Problem | Next step |
|---|---|
| `conda` is not recognized | Open **Anaconda Prompt**, not an unconfigured terminal. |
| A package cannot be imported | Activate `football-ai`; rerun `python -m pip install -r requirements.txt`. |
| Browser does not open | Visit `http://localhost:8000` while the Uvicorn terminal is running. |
| Port 8000 is busy | Stop the other server, or use `--port 8001` and visit that port. Vite development proxy still expects port 8000 unless reconfigured. |
| Website build is missing or old | Run `npm ci` and `npm run build` from the project root, then restart Uvicorn. |
| `npm` is not recognized | Install Node 22.12+ or 24 LTS, reopen the terminal, and check `node --version`. |
| PowerShell blocks `npm.ps1` | Use `npm.cmd` or Anaconda Prompt; do not change global execution policy. |
| Development page opens but predictions fail | Start the Python backend on port 8000 as well as Vite on 5173. |
| Missing or invalid data/model | Run ingestion, then training, from the project root; read the first error. |
| Network unavailable | Use the bundled artifacts or the offline ingestion instructions above. |
| Cloud build uses unexpected packages | Confirm Python 3.12, Node 24, and the explicit build command in `DEPLOYMENT.md`. |
| A new club is missing | The app supports its historical snapshot; audit and retrain with newer data. |

The source code is MIT licensed; see [LICENSE](LICENSE). Third-party libraries and photos retain their own licenses. See [assets/PHOTO_CREDITS.md](assets/PHOTO_CREDITS.md) before reusing the images. Historical player photos do not imply endorsement or current club membership; no official league or club affiliation is claimed.
