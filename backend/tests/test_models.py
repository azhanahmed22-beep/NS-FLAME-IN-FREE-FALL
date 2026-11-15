import pytest
from sqlalchemy.exc import IntegrityError

from app.models import DatasetVersion, Experiment, Investigation, NasaSource


def _version(session):
    inv = session.query(Investigation).first()
    src = NasaSource(investigation_id=inv.id, filename="f.csv", sha256="a" * 64, size_bytes=1,
                     origin="synthetic_test", is_derived=False, raw_path="x")
    session.add(src)
    session.flush()
    v = DatasetVersion(source_id=src.id, parser_name="p", parser_version="1")
    session.add(v)
    session.flush()
    return inv, v


def test_record_kind_check_constraint(session):
    inv, v = _version(session)
    session.add(Experiment(dataset_version_id=v.id, source_file="f.csv", record_kind="guessed",
                           investigation_id=inv.id, test_label="1"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_gravity_environment_check_constraint(session):
    inv, v = _version(session)
    session.add(Experiment(dataset_version_id=v.id, source_file="f.csv", record_kind="measured",
                           investigation_id=inv.id, test_label="1", gravity_environment="lunar"))
    with pytest.raises(IntegrityError):
        session.flush()


def test_unique_source_hash(session):
    inv, _ = _version(session)
    session.add(NasaSource(investigation_id=inv.id, filename="g.csv", sha256="a" * 64, size_bytes=1,
                           origin="synthetic_test", is_derived=False, raw_path="y"))
    with pytest.raises(IntegrityError):
        session.flush()
