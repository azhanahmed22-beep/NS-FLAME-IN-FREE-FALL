# ZYNTARA backend (NASA Space Apps 2026 – Flame in Freefall)

Research-grade backend for microgravity combustion data. **Status: Stages 1–3 of 8 are built and tested.**
Frontend is out of scope for this phase.

## What works (tested)
| Area | State |
|---|---|
| Project structure, config (env-only secrets), JSON logging | done |
| SQLAlchemy 2.0 models: all 14 requested tables + `ingestion_issues`; provenance columns on every scientific row | done |
| Alembic migration `0001` | up/down/up verified on **SQLite only** |
| Ingestion pipeline: SHA-256, byte-exact raw preservation, idempotent re-runs, failures logged not raised | done |
| Parsers: SAME-R table, SAME-R detection (per test / per material), PSI-115 summary, PSI-117 extinction | done |
| Unit normalization (original values kept beside normalized) | done |
| `GET /health`, `GET /api/v1/system/status` | done |
| `pytest`: 28 tests (units, parsers, ingestion, provenance, constraints, API, real-file end-to-end) | passing |

## Not built yet
Stage 4 analytics, Stage 5 ML + ranking, Stage 6 AI interpretation, Stage 7 the remaining REST endpoints, JWT auth,
rate limiting, upload validation, caching. Docker files are written but **never run** (no Docker in the build environment).
**PostgreSQL has not been tested**; everything was verified on SQLite.

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

## Run
```
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env            # set DATABASE_URL
alembic upgrade head
python -m scripts.ingest        # ingests everything in data/manifest.json
uvicorn app.main:app --reload   # Swagger at /docs
pytest
```
Add a new dataset: write a parser in `app/services/ingestion/parsers/`, register it in `registry.py`, add it to `data/manifest.json`.
