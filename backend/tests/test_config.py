import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    ("database_url", "expected"),
    [
        (
            "postgresql://user:password@db.example/app?sslmode=require",
            "postgresql+psycopg://user:password@db.example/app?sslmode=require",
        ),
        (
            "postgres://user:password@db.example/app",
            "postgresql+psycopg://user:password@db.example/app",
        ),
        (
            "postgresql+psycopg://user:password@db.example/app",
            "postgresql+psycopg://user:password@db.example/app",
        ),
        ("sqlite:///zyntara.db", "sqlite:///zyntara.db"),
    ],
)
def test_sqlalchemy_database_url_uses_psycopg_for_postgres(
    database_url: str, expected: str
) -> None:
    settings = Settings(database_url=database_url)

    assert settings.sqlalchemy_database_url == expected
