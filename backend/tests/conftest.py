import os

os.environ.setdefault("DATABASE_URL", "sqlite://")  # tests never touch a real database

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.models import Base
from app.services.ingestion.pipeline import seed_investigations

SYNTHETIC_INVESTIGATIONS = [
    {"psi_id": "PSI-TEST-1", "acronym": "SYNTH", "id_verification": "synthetic_test_fixture"},
    {"psi_id": "PSI-TEST-2", "acronym": "SYNTH2", "id_verification": "synthetic_test_fixture"},
]


@pytest.fixture
def session():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        seed_investigations(s, SYNTHETIC_INVESTIGATIONS)
        yield s
    engine.dispose()


# ---- SYNTHETIC FIXTURES: software tests only, not NASA data ----
SYNTH_TABLE = (
    "Sample Type,SAME Test #,Description,Date,Inlet velocity (cm/s),Rt/R0,Duration (sec),Primary aging time (sec),Primary mixing time (sec),Net aging time (sec)\n"
    "MatA,1,synthetic run,1-Jan,5.0,1.5,60,10,8,40\n"
    "MatA,1a,synthetic aged,1-Jan,5.0,1.5,,,,300\n"
    "MatB,1,same label other material,2-Jan,5.0,1.5,60,10,8,\n"
    "MatB,9a,orphan child,2-Jan,5.0,1.5,60,,,\n"
    "MatB,1,repeated,2-Jan,5.0,1.5,60,10,8,\n"
)
SYNTH_DETECT = (
    "test_no,material,n_samples,duration_s,baseline_obsc_med_V,smoke_window_obsc_med_V,obsc_drop_med_V,pct_window_below_3.30V,smoke_window_scat_med_V,smoke_window_ionA_med_V,ionA_max_V\n"
    "1,MatA,100,90,3.4,3.3,0.1,0.0,-0.2,0.03,0.1\n"
    "77,MatA,100,90,3.4,3.3,0.1,0.0,-0.2,0.03,0.1\n"
    "1,MatC,100,90,3.4,3.3,0.1,0.0,-0.2,0.03,0.1\n"
)
SYNTH_117 = (
    "source_file,fuel,pressure_atm,dext_cool,dext_hot,kb_mm2_s,value_type\n"
    "up.csv,fuelX,1.0,1.5,3.5,,model\n"
    "up.csv,fuelX,1.0,1.5,3.5,,model\n"
    "up.csv,fuelX,1.0,1.9,,,experiment\n"
    "up.csv,fuelX,2.0,,,12.0,bogus\n"
)
SYNTH_115 = (
    "file,case,gravity,variable,n_values,min,max,mean,pct_above_zero\n"
    "a.dat,10cm,Earth,Numden,10,0.0,2.0,1.0,50.0\n"
    "b.dat,,,U,10,-1.0,2.0,0.5,60.0\n"
)


@pytest.fixture
def write(tmp_path):
    def _write(name: str, text: str):
        p = tmp_path / "src" / name
        p.parent.mkdir(exist_ok=True)
        p.write_text(text)
        return p
    return _write
