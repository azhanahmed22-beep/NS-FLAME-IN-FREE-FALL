"""Application settings, read from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ZYNTARA API"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Required: no default so credentials are never baked into source.
    database_url: str
    data_dir: Path = BACKEND_ROOT / "data"
    gemini_api_key: SecretStr | None = None
    gemini_model: str = "gemini-2.5-flash"

    @property
    def sqlalchemy_database_url(self) -> str:
        for prefix in ("postgres://", "postgresql://"):
            if self.database_url.startswith(prefix):
                return "postgresql+psycopg://" + self.database_url[len(prefix):]
        return self.database_url

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
