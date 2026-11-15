"""Ingestion: preserve the raw file, hash it, parse it, store records with provenance,
and log every quality problem. Never invents values."""
import hashlib
import logging
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    CombustionMeasurement, DatasetVersion, Experiment, ExperimentalCondition, Fuel,
    IngestionIssue, Investigation, Material, NasaSource, SmokeMeasurement,
)
from app.services.ingestion.registry import get_parser
from app.services.ingestion.types import ExperimentRecord, Issue, ValueRecord
from app.services.processing.units import has_rule, normalize

log = logging.getLogger(__name__)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def preserve_raw(path: Path, raw_dir: Path, sha: str) -> Path:
    """Copy the original file, byte for byte, into raw_dir (no-op if already there)."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    dest = raw_dir / path.name
    if dest.exists() and sha256_of(dest) != sha:
        dest = raw_dir / f"{sha[:8]}_{path.name}"
    if not dest.exists():
        shutil.copy2(path, dest)
    return dest


def seed_investigations(session: Session, entries: list[dict]) -> None:
    for e in entries:
        inv = session.scalar(select(Investigation).where(Investigation.psi_id == e["psi_id"]))
        if inv is None:
            inv = Investigation(psi_id=e["psi_id"])
            session.add(inv)
        for key in ("acronym", "title", "research_area", "doi", "page_url", "license",
                    "id_verification", "availability_status", "availability_note"):
            if key in e:
                setattr(inv, key, e[key])
    session.commit()


class _Store:
    def __init__(self, session: Session, version: DatasetVersion, investigation: Investigation, filename: str):
        self.s, self.v, self.inv, self.filename = session, version, investigation, filename
        self.stored = 0
        self.issues: list[Issue] = []
        self._materials: dict[str, int] = {}
        self._fuels: dict[str, int] = {}
        self._unit_gaps: set[str] = set()

    def _ref(self, model, cache: dict[str, int], name: str | None) -> int | None:
        if name is None:
            return None
        if name not in cache:
            row = self.s.scalar(select(model).where(model.name == name))
            if row is None:
                row = model(name=name)
                self.s.add(row)
                self.s.flush()
            cache[name] = row.id
        return cache[name]

    def material_id(self, name):
        return self._ref(Material, self._materials, name)

    def fuel_id(self, name):
        return self._ref(Fuel, self._fuels, name)

    def value(self, model, rec: ValueRecord, experiment_id: int | None, **extra):
        norm, norm_unit = normalize(rec.value, rec.unit)
        if rec.unit is not None and not has_rule(rec.unit) and rec.unit not in self._unit_gaps:
            self._unit_gaps.add(rec.unit)
            self.issues.append(Issue("info", "no_unit_rule", f"No normalization rule for unit {rec.unit!r}; normalized value left NULL."))
        common = dict(
            dataset_version_id=self.v.id, source_file=self.filename, source_row=rec.source_row,
            upstream_file=rec.upstream_file, record_kind=rec.record_kind, value_original=rec.value,
            unit_original=rec.unit, value_normalized=norm, unit_normalized=norm_unit,
        )
        if model is ExperimentalCondition:
            self.s.add(model(experiment_id=experiment_id, name=rec.name, **common))
        else:
            self.s.add(model(experiment_id=experiment_id, variable=rec.name, variable_original=rec.name_original,
                             statistic=rec.statistic, qualifier=rec.qualifier, **common, **extra))
        self.stored += 1

    def experiment(self, rec: ExperimentRecord) -> Experiment | None:
        mid = self.material_id(rec.material)
        if rec.attach_only:
            exp = self.s.scalar(select(Experiment).where(
                Experiment.investigation_id == self.inv.id, Experiment.material_id == mid,
                Experiment.test_label == rec.test_label))
            if exp is None:
                other = self.s.scalar(select(Experiment).where(
                    Experiment.investigation_id == self.inv.id, Experiment.test_label == rec.test_label))
                code, msg = (("material_mismatch", f"Test {rec.test_label} exists but under a different material than {rec.material}.")
                             if other else ("orphan_test", f"Test {rec.test_label} ({rec.material}) not found in the experiment table; stored without experiment link."))
                self.issues.append(Issue("warning", code, msg, rec.source_row))
            return exp
        exp = Experiment(
            dataset_version_id=self.v.id, source_file=self.filename, source_row=rec.source_row,
            upstream_file=rec.upstream_file, record_kind=rec.record_kind, investigation_id=self.inv.id,
            test_label=rec.test_label, material_id=mid, fuel_id=self.fuel_id(rec.fuel),
            description=rec.description, date_text=rec.date_text,
        )
        self.s.add(exp)
        self.s.flush()
        self.stored += 1
        return exp


def ingest_file(session: Session, *, path: Path, psi_id: str, parser_name: str, is_derived: bool,
                origin: str, raw_dir: Path, doi: str | None = None, url: str | None = None) -> DatasetVersion:
    """Ingest one file. Parse/store failures are recorded on the DatasetVersion (status='failed')
    rather than raised, so one bad file never blocks the rest."""
    parser = get_parser(parser_name)
    inv = session.scalar(select(Investigation).where(Investigation.psi_id == psi_id))
    if inv is None:
        raise ValueError(f"Investigation {psi_id} is not seeded")
    sha = sha256_of(path)
    source = session.scalar(select(NasaSource).where(NasaSource.sha256 == sha))
    if source is None:
        raw = preserve_raw(path, raw_dir, sha)
        source = NasaSource(investigation_id=inv.id, filename=path.name, sha256=sha, size_bytes=path.stat().st_size,
                            origin=origin, is_derived=is_derived, doi=doi, url=url, raw_path=str(raw))
        session.add(source)
        session.flush()
    elif source.investigation_id != inv.id:
        raise ValueError(f"{path.name} was already ingested under a different investigation")

    version = session.scalar(select(DatasetVersion).where(
        DatasetVersion.source_id == source.id, DatasetVersion.parser_name == parser.name,
        DatasetVersion.parser_version == parser.version))
    if version is not None:
        if version.status == "completed":
            log.info("already ingested", extra={"ctx": {"file": path.name, "parser": parser.name}})
            return version
        for issue in list(version.issues):
            session.delete(issue)
        session.delete(version)
        session.flush()
    version = DatasetVersion(source_id=source.id, parser_name=parser.name, parser_version=parser.version)
    session.add(version)
    session.flush()

    store = _Store(session, version, inv, path.name)
    try:
        with session.begin_nested():
            result = parser.parse(path)
            created: dict[tuple[int | None, str], Experiment] = {}
            parents: list[tuple[Experiment, str]] = []
            for rec in result.experiments:
                exp = store.experiment(rec)
                if exp is None:  # attach_only but unmatched: keep the values, unlinked
                    for r in rec.smoke:
                        r.qualifier = f"unlinked_test={rec.test_label};material={rec.material}"
                        store.value(SmokeMeasurement, r, None)
                    continue
                if not rec.attach_only:
                    created[(exp.material_id, rec.test_label)] = exp
                    if rec.parent_label:
                        parents.append((exp, rec.parent_label))
                for r in rec.conditions:
                    store.value(ExperimentalCondition, r, exp.id)
                for r in rec.combustion:
                    store.value(CombustionMeasurement, r, exp.id)
                for r in rec.smoke:
                    store.value(SmokeMeasurement, r, exp.id)
            for exp, parent_label in parents:
                parent = created.get((exp.material_id, parent_label))
                if parent is not None:
                    exp.parent_experiment_id = parent.id
            for r in result.loose_combustion:
                store.value(CombustionMeasurement, r, None)
            for r in result.loose_smoke:
                store.value(SmokeMeasurement, r, None)
            version.rows_read = result.rows_read
            version.records_stored = store.stored
            version.status = "completed"
            store.issues = result.issues + store.issues
    except Exception as exc:  # recorded, not raised
        log.exception("ingestion failed", extra={"ctx": {"file": path.name, "parser": parser.name}})
        version.status = "failed"
        store.issues = [Issue("error", "processing_error", f"{type(exc).__name__}: {exc}")]
    version.finished_at = datetime.now(timezone.utc)
    for i in store.issues:
        session.add(IngestionIssue(dataset_version_id=version.id, severity=i.severity, code=i.code,
                                   message=i.message, source_row=i.source_row, column_name=i.column))
    session.commit()
    return version
