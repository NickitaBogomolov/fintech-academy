from functools import cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DFA_", env_file=".env", extra="ignore")

    data_dir: Path = BACKEND_ROOT / "data"
    llm_provider: Literal["rules", "openai"] = "rules"
    llm_base_url: str = "http://localhost:8000/v1"
    llm_model: str = "Qwen/Qwen2.5-7B-Instruct"
    llm_api_key: str = "local"
    llm_label: str = "Локальная модель (vLLM)"
    llm_timeout: float = 60.0
    solc_dir: Path = BACKEND_ROOT / "toolchain" / "solc"
    slither_enabled: bool = True
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def database_path(self) -> Path:
        return self.data_dir / "studio.sqlite3"


@cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
