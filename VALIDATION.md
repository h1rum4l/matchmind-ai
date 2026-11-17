# Verification record

Verified locally on Windows with Python 3.12.16 on 14 November 2026.

- `python -m matchmind.data --offline`: verified all five pinned SHA-256 inputs, 1,900 matches; deterministic processed CSV with LF newlines.
- The Python HTTPS downloader fetched the pinned 2024–25 file successfully and its SHA-256 matched the configured value.
- `python -m matchmind.train`: generated both safe JSON models, chronological evaluation report, reliability bins and 380 test predictions.
- `python -m pytest -q`: 22 passed. Covers bad dates/scores/duplicates, checksum failures without overwriting existing processed data, missing offline files, chronology, future-label isolation, probability normalization, scoreline mode, serialization, promoted-club fallback, known metric values and interactive app states.
- `python -m ruff check .`: passed.
- `python -m compileall -q matchmind app.py tests`: passed.
- `uv pip check`: all 46 installed packages compatible; exact installed set in `requirements-lock.txt`.
- Streamlit started on localhost; forecast and evaluation visually checked in browser. Responsive views inspected at 390, 768 and 1440 pixels. The browser viewport was restored afterward.

One upstream Streamlit/Altair deprecation warning appeared in the tests; it did not affect results. No warning suppression or third-party library patch was applied.

The layout inspector failed with a Chrome CDP timeout, so visual QA used the in-app browser. Native Streamlit controls and system sans-serif typography were retained for offline operation instead of the design sheet's externally loaded font. The Achromatic ledger direction (seed 2057650765) informed the neutral controls, blue probability bars, sage control surfaces and compact tables; no external image assets or invented sample data were used.

The GitHub Actions workflow is supplied but has not run on GitHub. Streamlit Community Cloud deployment and the user's separate Anaconda/Spyder installations have not been tested. This is an app folder ready to create/upload as a repository, not a published remote repository.

The independent test is one frozen 2024–25 season: fitting ends May 2023, calibration ends May 2024. Calibrated accuracy 47.37%, log loss 1.07228, multiclass Brier 0.64611. Raw Poisson log loss 1.04318 and Brier 0.62805 were better; neither variant was selected or tuned using those results. Historical frequency baseline accuracy 40.79%, log loss 1.07893, Brier 0.65394.

The app's refit uses all available matches through 25 May 2025. Its reused calibration temperature has no separate future validation. No live injuries, lineups, transfers, odds, automated refresh, guarantees of profitability, or current-season accuracy claims are included. Inputs were not cross-checked fixture by fixture against another independent provider. The upstream 2019–20 date problem is excluded, not silently repaired.

## Football redesign — 15 November 2026

Taste and Anti-slop skills applied to the user's explicit Flowstate reference. UI/UX Pro was not found in the installed skill catalog or local skill directories; direct accessibility and layout checks were used. No new dependencies, retraining or data changes were introduced.

Existing app regression tests passed before changes. The revised suite adds offline photo/credit checks, optional-motion guards, missing-design recovery and truncated-design recovery. Browser checks cover the hero, working predictor shortcut, visible model explanation and pause-motion checkbox. At 390px the checkbox was verified checked and the background's computed animation state was `paused`; no document-level horizontal overflow was present. Desktop and tablet views were inspected too. The standalone WebGL preview rendered without browser warnings/errors; the Streamlit version intentionally uses CSS background motion because its HTML API sanitizes scripts.

A separate read-only Anti-slop review found four issues: a model link without visible method content, unhandled truncated hero HTML, no pause-motion control and outdated network wording. All four were addressed. Gradients, glass, pill buttons, purple and entrance animation are intentional reference requirements rather than accidental template styling. The photographs are real, locally bundled and visibly attributed. No email waitlist, fake live features, pricing or placeholder dashboard content was added.

The existing Streamlit/Altair deprecation warning remains. OS-level reduced-motion mode has a code-level guard and CSS checks; the manual pause path was exercised in browser. Public deployment remains untested. Optional Google Fonts requests have a system-font fallback. See `assets/PHOTO_CREDITS.md` for separate image licensing and `assets/LICENSE-fluid.txt` for the animation licence.

## React / FastAPI migration — 15 November 2026

Primary stack: React 19.3.1, Vite 8.3.8, FastAPI 0.163.0 and Uvicorn 0.54.0. Verified using Node 24.22.1 / npm 11.19.1 and Python 3.12.16 on Windows. No training, probability adjustment, data replacement or paid API was introduced during migration. Streamlit remains an optional legacy interface with a separate requirements file.

- Baseline before migration: the existing 26 tests passed.
- Complete workspace suite with the optional legacy packages installed: **51 passed** (including 25 API tests). Ruff and Python compilation passed.
- Fresh environment installed from the primary lockfile and dev requirements: **46 passed, 3 skipped**. The three skips represent optional Streamlit test collection/cases, not missing primary-app coverage. Verified that `streamlit` is absent and all 33 installed packages are compatible.
- `npm test`: **6 passed**, covering JSON requests, validation/service errors, HTML responses, network failure and cancellation.
- `npm run build`: passed; produced a browser bundle and copied local public photos/credits into `frontend/dist/`.
- npm install audit: **0 known vulnerabilities** in the 19-package resolved tree at verification time. A committed `package-lock.json` and primary-only Python `requirements-lock.txt` are supplied.
- Browser: production app at port 8000 loaded metadata and original-model predictions. Changing to Liverpool / Manchester City updated the result through the API; same-team validation and recovery were exercised. Data and evaluation sections rendered real results. Vite development mode at port 5173 fetched the same API through its proxy. Desktop and mobile/tablet views were inspected; 390px had no document horizontal overflow. Pause motion was checked and the canvas was hidden with the CSS background paused. No browser warning/error was observed in the inspected console output.

The backend rejects same/unknown teams, wrong types, extra fields and long strings; checks model/CSV/evaluation provenance at startup; and returns safe 503 responses for missing or stale artifacts. Predictions match the original `predict()` function in parity tests. Downloads and unknown API routes are covered. Startup reads local files and does not fetch match data.

The separate read-only review found no current-dataset integration/security blocker. Its future-data warning about a hardcoded calibration sentence was resolved with neutral wording backed by the dynamic metrics table. A misleading connection-retry button on fixture validation was removed. Model inference and all previously required error handling remain intact. React renders escaped text and uses no HTML injection or iframe.

Current Starlette issues a non-failing warning that its TestClient will prefer `httpx2` over `httpx` in future; the pinned httpx test setup passes. Optional legacy Streamlit still emits its earlier Altair deprecation warning. Public hosting, Linux CI execution, and the OS-level reduced-motion preference have not been verified; manual pause and code guards were checked. No live injury/news feed or current-season accuracy claim has been added.

The migration was also applied to `C:\Users\Afraz\Documents\matchmind-ai`, with original entry/config/docs/tests backed up under `backups/react-20261115/`. Its model/data files were preserved. Locked npm packages and the new backend dependencies were installed in that folder and the existing `football-ai` Anaconda environment. Anaconda `pip check` reported no broken requirements. `npm start` was launched through that environment and reached ready state on port 8000. A real HTTP smoke test returned 20 teams, 1,900 matches and Arsenal/Chelsea probabilities `[0.6203529961, 0.1920246306, 0.1876223733]`, summing to one. This verifies the installed copy, in addition to the isolated workspace tests.

## La Liga — 15 November 2026

Added an explicit league selector and independent Spanish data/model artifacts. No dependencies or Premier League model parameters changed. The original Premier League production model SHA-256 remains `f4f286e387466911953c7a035a1f32fa949957b1f177b79ed1ee0210359dd2bf`.

OpenFootball's pinned 2024–25 Spanish file has all 380 fixtures but only 370 recorded results; the ten final-round scores are missing upstream. The latest upstream HEAD was checked and has the same gap. These are missing historical results, not unplayed games. Ingestion validates the full fixture schedule, its checksums and exactly the known completed-result count, and excludes those ten rather than generating scores. La Liga totals 1,890 completed matches, ending 18 May 2025. Raw inputs and per-source completion counts are retained in `data/la-liga/`.

La Liga fitting uses 2020–21 through 2022–23, calibration uses 2023–24, and the partial final test contains 370 matches from 2024–25. Calibrated accuracy **52.16%**, log loss **0.98601**, multiclass Brier **0.58714**; raw Poisson log loss **0.98825**, Brier **0.58813**. Historical-frequency baseline accuracy **44.59%**, log loss **1.07032**, Brier **0.64708**. Production refits and calibration-transfer limitations are unchanged; these scores do not establish current-season accuracy.

Verification: **70 Python tests passed**, Ruff passed, **6 JavaScript tests passed**, and the Vite production build passed. Added tests cover league-scoped inference/downloads, both directions of per-league startup failure isolation, wrong/cross-league requests, copied-model rejection, La Liga source checksums/counts, missing-result fixture validation, path rejection and training-directory isolation. Existing default Premier League API tests remain passing.

Browser checks: selected La Liga, saw its 20-team list and FC Barcelona / Real Madrid CF prediction, submitted Club Atlético de Madrid / Real Madrid CF, switched back to the original Arsenal / Chelsea prediction, and switched to La Liga again. The selected league's evaluation URL and CSV download were scoped correctly. The mobile selector, cutoff and missing-results notice rendered with no document-level horizontal overflow at 390px. A separate read-only integration review found no material issue. The two previously documented upstream test warnings remain; no public deployment was performed.

## Football in the hero — 15 November 2026 (subsequently removed)

Added a locally drawn SVG football behind the home-screen title, rotating slowly alongside the existing fluid flare. This adds no dependency, extra WebGL scene, tracking or external asset request. It is decorative, hidden from screen readers, non-interactive and scaled for mobile. The existing pause checkbox pauses both the football and atmosphere; the existing reduced-motion CSS stops the football animation.

Verified the installed app in browser: SVG loaded, rotation animation was running, pause changed both computed animation states to `paused`, and the 390px layout had no document horizontal overflow. The headline, player photographs and action remained visible. Six JavaScript tests and the Vite build passed. Backend tests were not rerun for this visual-only change; no prediction code, data or models changed. Previous hero/build files are backed up under `backups/football-20261115/`.

The user clarified that the requested change concerns the flare, not a separate football. Removed the football image, SVG asset and its animation rules; retained the existing fluid flare and controls. The production frontend was rebuilt after removal. No backend or model changes were made.

## Vercel build repair — 17 November 2026

The supplied Vercel log used CPython 3.14.8 and attempted source compilation of NumPy 2.2.6, pandas 2.2.3, scikit-learn 1.6.1 and SciPy 1.15.3. SciPy failed because no Fortran compiler was installed. Added a bounded Python 3.12 requirement, explicit FastAPI entry point, Node 24.x pin, React build command and function bundle exclusions. The scientific package pins and saved models are unchanged.

Verified via pip's Linux/cp312 binary-only dry run that all four scientific packages resolve to prebuilt manylinux2014 wheels. No packages were installed by that check. Submitted Vercel configuration fields validated against the provider's schema. New regression tests enforce runtime-manifest agreement, exclude Python 3.14, verify entry/build settings, and run predictions for both leagues from only processed runtime artifacts without raw training inputs.

Local verification: **73 Python tests passed**, Ruff passed, **6 JavaScript tests passed**, and the production frontend build passed. These checks do not independently prove a Vercel deployment; the actual remote build and runtime must be checked after the commit is deployed. The existing upstream test warnings remain.
