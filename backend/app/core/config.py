"""Application settings, read from environment variables / .env."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "ZYNTARA API"
    environment: str = "development"
    log_level: str = "INFO"
    # Required: no default so credentials are never baked into source.
    database_url: str
    data_dir: Path = BACKEND_ROOT / "data"

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
