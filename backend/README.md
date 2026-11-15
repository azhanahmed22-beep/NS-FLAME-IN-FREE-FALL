# ZYNTARA backend (NASA Space Apps 2026 – Flame in Freefall)

Research backend for microgravity combustion data.

## What works (tested)
| Area | State |
|---|---|
| Project structure, config (env-only secrets), JSON logging | done |
| SQLAlchemy 2.0 models: all 14 requested tables + `ingestion_issues`; provenance columns on every scientific row | done |
| Alembic migration `0001` | up/down/up verified on **SQLite only** |
| Ingestion pipeline: SHA-256, byte-exact raw preservation, idempotent re-runs, failures logged not raised | done |
| Parsers: SAME-R table, SAME-R detection (per test / per material), PSI-115 summary, PSI-117 extinction | done |
| Unit normalization (original values kept beside normalized) | done |
| Health, system status, dataset, investigation, experiment, and material APIs | done |
| Combustion, smoke, materials, microgravity, and dataset-count chart APIs | done |
| Evidence-based material comparison (not a safety rating) | done |
| Local source-grounded assistant; optional Gemini integration | done |
| `pytest`: ingestion, provenance, analytics, workspace API, and real-file tests | passing |

## Limitations
The material comparison reports only observed derived smoke evidence; it is not an ML score or a spacecraft safety rating.
Gemini-generated answers are optional and require `GEMINI_API_KEY`; without it, the assistant returns a local evidence summary.
Only the five owner-supplied CSVs listed below are available; the original NASA raw files were not downloaded.
JWT auth, upload validation, rate limiting, caching, and PostgreSQL have not been implemented or verified.
Docker files are present but have not been tested.

`GET /api/v1/datasets` lists ingested dataset versions with source hashes, parser/row counts, investigation identity, and issue counts. It supports `status`, `psi_id`, `limit`, and `offset` query parameters; server filesystem paths are not returned.

## Data honesty
* Only facts confirmed on NASA pages are filled in `data/manifest.json`. PSI-102 (SAME) has a confirmed DOI (10.60555/gd4k-8h62) and CC0-1.0 license.
  PSI-25 (BASS-II) and PSI-102 pages were confirmed to exist. The other PSI ids come from the project brief and are marked `user_brief`.
  PSI-101 is corroborated because the PSI-102 page lists it as its related investigation.
* The five CSVs in `data/raw/` were supplied by the project owner. Four are **derived** summaries, not NASA's original files. They are stored with `is_derived=true`.
* The original NASA data have **not** been downloaded: PSI pages are JavaScript-rendered and `psi.nasa.gov` / the AWS bucket were unreachable from the build environment.
  Download from the PSI repository (https://psi.nasa.gov, investigation pages) or the open bucket `s3://nasa-psi` (`aws s3 ls --no-sign-request s3://nasa-psi/`;
  the AWS listing only names DSI and OASIS data, so combustion files may not be there). Then add a parser or manifest entry per file.
* The files do not say whether a SAME-R test was flight or ground, nor the year of each date; `gravity_environment` stays NULL and dates stay text.
* PSI-117 extinction-diameter columns have no unit in the file; unit is NULL. PSI-115 summary statistics have no units either.
* `record_kind`: `measured`, `simulated` or `derived`. PSI-117 experiment rows are `measured`, model rows `simulated`. Aggregates are tagged `aggregate=...` in `qualifier`.
  Do not train on aggregates.

## Run on Windows

Copy `.env.example` to `.env` in the `backend` folder. Its default SQLite URL uses the included `zyntara.db` and needs no credentials.
In one PowerShell terminal:

```powershell
Set-Location backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
Set-Location frontend
npm install
npm run dev -- --host 127.0.0.1
```

Open the Vite URL it prints (normally `http://127.0.0.1:5173`) or the API docs at `http://127.0.0.1:8000/docs`.

## Database setup

For a fresh database, run from the `backend` folder:

```
alembic upgrade head
python -m scripts.ingest
python -m pytest
```

`python -m scripts.ingest` is idempotent and loads the files in `data/manifest.json`.

The API allows the local Vite frontend origins by default. Set `CORS_ORIGINS` in `.env` to a JSON array of trusted origins when deploying the frontend elsewhere; avoid wildcard origins when credentials are enabled. To enable Gemini, set `GEMINI_API_KEY` in `backend/.env`; never put the key in frontend code or commit it.

Add a new dataset: write a parser in `app/services/ingestion/parsers/`, register it in `registry.py`, add it to `data/manifest.json`.
