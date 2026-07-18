from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "RazaMind API"
    app_env: str = "development"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    temperature: float = 0.2
    langsmith_tracing: bool = False
    langsmith_api_key: str = ""
    langsmith_project: str = "razamind"
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    database_url: str = (
        "postgres://assistant:assistant@localhost:5432/ali_raza_assistant"
    )
    generate_schemas: bool = False
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def normalize_database_url(cls, value: object) -> object:
        if isinstance(value, str) and value.startswith("postgresql://"):
            return "postgres://" + value.removeprefix("postgresql://")
        return value

    @property
    def allowed_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def langsmith_enabled(self) -> bool:
        return self.langsmith_tracing and bool(self.langsmith_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
