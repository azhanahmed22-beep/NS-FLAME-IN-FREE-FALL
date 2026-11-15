"""Vercel serverless entrypoint for the FastAPI application."""

from alembic import command
from alembic.config import Config

from app.core.config import BACKEND_ROOT, get_settings
from app.main import app
from scripts.ingest import main as ingest_datasets


if get_settings().environment == "vercel":
    alembic_config = Config(str(BACKEND_ROOT / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    command.upgrade(alembic_config, "head")
    if ingest_datasets() != 0:
        raise RuntimeError("Dataset ingestion failed during Vercel function startup")
