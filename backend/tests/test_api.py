from fastapi.testclient import TestClient

from app.database.session import get_db
from app.main import create_app


def test_health_and_status(session):
    app = create_app()
    app.dependency_overrides[get_db] = lambda: session
    client = TestClient(app)
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get("/api/v1/system/status").json()
    assert body["database"] == "ok" and body["investigations"] == 2
    assert body["dataset_versions"] == {"completed": 0, "failed": 0, "processing": 0}
