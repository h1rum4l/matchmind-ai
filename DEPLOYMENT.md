# Deploy MatchMind AI

The React website and Python prediction API can run as **one Python web service**. Build the frontend once; FastAPI serves `frontend/dist/` and handles `/api` at the same origin. No separate frontend host, database, Docker setup, AI API key, or data download at startup is needed.

This guide is a deployment recipe, not evidence that a public deployment has been tested. The local Windows app needs no hosting payment. Provider terms and free allowances below were checked on **15 November 2026** and can change.

## Before publishing

From the project root, run the checks and build:

```bat
conda activate football-ai
python -m pip install -r requirements-dev.txt
python -m pytest
python -m ruff check .
npm ci
npm run test
npm run build
python -m uvicorn matchmind.api:app --host 127.0.0.1 --port 8000
```

Open `http://localhost:8000`, select Premier League or La Liga, choose two teams, and check the predictions and evaluation view. Check [VALIDATION.md](VALIDATION.md) for the recorded verification scope. Rebuild after frontend changes. Keep both cutoffs visible: Premier League ends **25 May 2025**; La Liga ends **18 May 2025** and excludes ten missing upstream results. Commit the complete `data/la-liga/` and `models/la-liga/` directories alongside the original Premier League artifacts.

## Put the project on GitHub

Create a repository named `matchmind-ai`. Upload the source and configuration, including `frontend/`, root `package.json` and `package-lock.json`, `matchmind/`, `requirements.txt`, `.python-version`, `.node-version`, `data/`, `models/`, documentation, and credited assets. A source deployment builds `frontend/dist/` itself; the distribution ZIP also contains a ready-built copy for local startup.

Exclude `node_modules/`, Conda or virtual environments, caches, local backups, credentials, and unrelated personal files. Preserve photo credits and license files. The saved data and JSON models are needed at runtime; do not ignore them.

If Git is already installed, the initial commands for a new local repository are:

```bat
git init
git add .
git status
git commit -m "Add React and FastAPI football prediction app"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/matchmind-ai.git
git push -u origin main
```

Replace the remote URL with your repository. Review `git status` before committing. For an existing repository, preserve its history and remote rather than repeating initialization. GitHub authentication may open in your browser.

## Vercel

The repository includes `pyproject.toml` and `vercel.json` for a single FastAPI deployment that also builds and serves the React frontend. The Python manifest pins **3.12**, selects **`matchmind.api:app`**, and matches `requirements.txt`. This avoids selecting the optional Streamlit `app.py`. Node is pinned to **24.x**.

Use these Vercel settings:

- **Root Directory:** the repository root, containing `pyproject.toml`, `vercel.json`, and `package.json`.
- **Framework:** FastAPI; use the committed configuration rather than a Vite-only preset.
- **Build Command:** `npm ci && npm run build` (already set in `vercel.json`).
- **Install Command:** leave the default; Vercel installs the Python dependencies.
- **Output Directory:** disable an old custom override. FastAPI serves `frontend/dist/`; it is not a standalone Vite-only deployment.

Push the configuration and allow the connected Git deployment to rebuild. A fresh build must show Python **3.12**, not 3.14. If retrying the earlier failure manually, redeploy without reusing the old build cache. No custom Uvicorn start command is needed on Vercel.

The earlier failure used Python 3.14 and attempted to compile SciPy 1.15.3, then failed because no Fortran compiler was present. The existing pinned NumPy, pandas, SciPy and scikit-learn packages have prebuilt Python 3.12 Linux wheels. Installing a compiler or changing the model is not required to resolve that mismatch.

Runtime CSVs, manifests, model JSONs, evaluation JSONs, and `frontend/dist/` must remain available. The function configuration excludes raw training inputs, local dependencies, tests, caches, backups and the legacy interface to keep the bundle smaller. The raw data remains in Git for reproducibility. FastAPI lifespan startup and mounted static files are supported by Vercel; keep the mounted directory in the bundle rather than enabling static-source exclusion.

After deployment, test `/api/health`, the league selector, a prediction for each league, and both downloads. A successful build alone does not prove runtime startup is working. Stay on the existing Hobby/free setup; no paid upgrade is needed to address this compiler error.

References: [Python version selection](https://vercel.com/docs/functions/runtimes/python/python-version), [FastAPI entry points, lifespan and static files](https://vercel.com/docs/frameworks/backend/fastapi), [Python runtime and bundle settings](https://vercel.com/docs/functions/runtimes/python).

## Free-tier example: Render

Render currently offers a Free Python web service suitable for a hobby demonstration. Select the **Free** compute plan explicitly. This app needs no paid database or disk. [Render's free service documentation](https://render.com/docs/free).

1. Sign in to Render and create a **Web Service** connected to your GitHub repository.
2. Choose the branch to publish, **Python 3** as the runtime, and the repository root as the working directory.
3. Keep the committed `.python-version` set to `3.12` and `.node-version` set to `24`. Remove any dashboard version overrides that conflict with them. Render accepts a minor version in `.python-version`; its `PYTHON_VERSION` environment variable instead requires a full patch version. [Python version configuration](https://render.com/docs/python-version), [Node version configuration](https://render.com/docs/node-version).
4. Set the following build and start commands, then confirm the Free plan before deploying.

**Build command** — this is a Linux hosting command, not an Anaconda Prompt command:

```sh
npm ci && npm run build && python -m pip install -r requirements.txt
```

**Start command:**

```sh
python -m uvicorn matchmind.api:app --host 0.0.0.0 --port $PORT
```

Render's Python runtime also includes Node and npm, so the frontend build can run in the same service. [Available runtime tools](https://render.com/docs/native-runtimes). The start command follows Render's [FastAPI deployment guide](https://render.com/docs/deploy-fastapi), with this project's module name. `$PORT` is supplied by the host; do not paste it unchanged into a local Windows launch command.

When the service is ready, open its HTTPS URL, select a fixture, and check that predictions load. If the page loads but predictions fail, inspect the service logs for missing `data/` or `models/` files and Python import errors. If the frontend is missing, check that the build log shows a successful `npm run build` and that `frontend/dist/` exists in the deployment.

### Staying within zero additional cost

Render's Free service sleeps after 15 minutes without traffic; the next request can take about a minute to wake it. The workspace receives 750 free instance hours per month, shared across services. Bandwidth and build allowances also apply. Extra usage can be billed when a payment method is present; without one, the documented behavior is suspension or disabled builds. Review the account's billing and spending settings before publishing. Keep the service on Free and avoid adding paid resources. [Current free-tier limits](https://render.com/docs/free).

The filesystem is ephemeral: changes made while running can disappear on restart or redeploy. This app reads its committed data/model artifacts, so there is no need for persistent storage. Train and audit updates locally, commit the resulting artifacts, then redeploy. Free hosting can change, suspend, or sleep; it is not a permanent availability guarantee. [Filesystem limitations](https://render.com/docs/free).

## Another host or an existing server

Use Python 3.12 and Node 24, run the same build steps, and start Uvicorn on the host's required port. Serve it behind the host's HTTPS endpoint. Keep the compiled frontend and the Python API in the same deployment so relative `/api` requests work without a separate CORS policy.

Use `--host 0.0.0.0` only when the service must accept external connections. For a local laptop, keep `127.0.0.1`. Do not use `--reload` on a public service; FastAPI documents it as a development feature. [FastAPI server deployment](https://fastapi.tiangolo.com/deployment/manually/).

GitHub Pages hosts static HTML, CSS, and JavaScript; it does not run this FastAPI application. Publishing only `frontend/dist/` there would still require a separately deployed Python API and frontend URL/proxy configuration. The single-service setup above is simpler for this project. [What GitHub Pages provides](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Updates and recovery

Commit source changes and rebuild before publishing. Model updates must retain each league's provenance, cutoff, calibration notes, and evaluation report. A successful web deployment does not establish new predictive accuracy. The 2024–25 test scores apply to each league's frozen evaluation model. Production models were refitted independently: 1,900 Premier League matches and 1,890 La Liga matches. La Liga's 370-match final holdout has partial coverage because ten historical scores are missing in the source.

For a local migration, keep `backups/react-20261115/` if it exists until the new app works. Restore files from that backup only when intentionally returning to the old interface. Do not upload backups to the public repository.

The optional legacy Streamlit app uses `app.py` and `requirements-streamlit.txt`; it is separate from this deployment. Streamlit Community Cloud does not run this React/FastAPI service using its normal Streamlit entrypoint workflow.
