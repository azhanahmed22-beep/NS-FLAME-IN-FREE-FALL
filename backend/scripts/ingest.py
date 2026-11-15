"""Ingest the datasets listed in data/manifest.json.  Usage: python -m scripts.ingest"""
import json
import logging
import sys
from pathlib import Path

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.session import get_session_factory
from app.services.ingestion.pipeline import ingest_file, seed_investigations


def main(manifest_path: Path | None = None) -> int:
    settings = get_settings()
    configure_logging(settings.log_level)
    manifest = json.loads((manifest_path or settings.data_dir / "manifest.json").read_text())
    failed = 0
    with get_session_factory()() as session:
        seed_investigations(session, manifest["investigations"])
        for d in manifest["datasets"]:
            path = settings.raw_dir / d["file"]
            if not path.exists():
                logging.getLogger("ingest").error("file missing: %s", path)
                failed += 1
                continue
            v = ingest_file(session, path=path, psi_id=d["psi_id"], parser_name=d["parser"], is_derived=d["is_derived"],
                            origin=d["origin"], raw_dir=settings.raw_dir, doi=d.get("doi"), url=d.get("url"))
            print(f"{d['file']}: {v.status}  rows={v.rows_read} records={v.records_stored}")
            failed += v.status == "failed"
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
