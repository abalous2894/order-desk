from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://orderdesk:orderdesk@localhost:5432/orderdesk"
    cors_origins: str = "http://localhost:5174,http://127.0.0.1:5174"
    operator_token: str = "dev-operator-token"
    operator_token_file: str | None = None
    log_level: str = "INFO"
    disable_openapi: bool = False

    @model_validator(mode="after")
    def resolve_file_secrets(self) -> Self:
        if self.operator_token_file:
            token_path = Path(self.operator_token_file)
            if token_path.is_file():
                self.operator_token = token_path.read_text(encoding="utf-8").strip()
        return self


settings = Settings()
