# MatchMind football redesign

Reference: the supplied Flowstate design, adapted to Premier League history. Keep its immersive dark hero, Onest typography, word reveals and translucent navigation. The standalone HTML also keeps pointer-reactive WebGL ink; Streamlit uses CSS atmosphere because its HTML API sanitizes scripts. Replace the waitlist with a direct route to the working match predictor. No email collection, pricing, invented testimonials or claimed live data.

The hero answers: which match should I explore? Haaland and Mohamed Salah portraits frame the title like opposing sides of a fixture. Green and cyan ink sit against deep plum; the native prediction and evaluation controls continue beneath the hero in the same dark palette. Player photos are historical portraits, not evidence of current squads or endorsements.

Scope: new self-contained hero `index.html`, local photo assets/credits, native app CSS, Streamlit embedding, README and UI regression coverage. Preserve model, ingestion, probabilities, saved data, validation errors, downloads and evaluation splits. Existing UI tests passed before changes. No dependencies added.

Cleanup order: remove the original light CSS; reuse existing app controls and error handling; build only real navigation targets; run regression tests; have a separate reviewer check changed files. WebGL-unavailable and reduced-motion modes are grounded display compatibility paths: content and predictor remain present, motion is optional, and initialization failure remains visible in browser diagnostics. Test the static path as well as animated rendering.

## React / FastAPI migration

Scope: React/Vite frontend, a small FastAPI boundary around the unchanged Python predictor, API/frontend regression tests, pinned npm/Python dependencies, startup/deployment docs and CI. The existing 26 tests lock model, data and legacy UI behavior before migration. Streamlit stays an optional legacy entry point; its packages are removed from the default installation. Avoid UI duplication in React: one hero, one forecast form, one performance table, one method section. Preserve all input validation, provenance checks, calibrated/raw disclosure, licences and file downloads. No model retraining, live injury claims, paid APIs, state framework, router or chart library.

The primary website gets the real WebGL scene without an iframe or injected HTML. The existing simulation is reused as a module with lifecycle cleanup, pause and reduced-motion support. Native React forms and CSS probability bars replace Streamlit controls/charts. Development uses Vite's `/api` proxy; the production Python process serves the built frontend and API on one origin. Backend failure is an explicit retry state, never fabricated probabilities. A separate read-only review follows implementation.

## La Liga

Add one league selector above the team form. Selecting a league clears the previous teams/result/report before fetching the new league's metadata and prediction; errors cannot leave another league's probabilities on screen. Scope both downloads and the performance table to the selected league. The hero keeps the supplied Salah photo and existing Haaland photo, describes them as football icons and labels the match count with its league.

One fixed league registry selects pinned sources and artifact directories. Preserve the original Premier League file locations, model bytes, default APIs and CLI behavior. Reuse the Poisson implementation but train/calibrate/evaluate La Liga independently. The Spanish snapshot has 1,890 completed matches because ten final-round 2024–25 results are missing upstream; display that limitation and evaluate the partial 370-match test set. Do not fabricate scores or call these historical fixtures unplayed. No new packages, photo changes, live-data feed or cross-league match prediction.

Taste skill exceptions are intentional reference requirements: glass, pill navigation, gradients, purple ground and word animation. No randomized design direction replaces the user's explicit reference. UI/UX Pro was requested but not installed; mobile, contrast, keyboard/focus, reduced-motion and honest data states are checked directly. Anti-slop pass stays within changed UI files.
