from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AutoApply Agent"
    api_prefix: str = "/api/v1"
    database_url: str = Field(
        default="postgresql+asyncpg://autoapply:autoapply@localhost:5432/autoapply"
    )
    llm_provider: str = "openai"
    llm_api_key: str | None = None
    llm_model: str | None = None
    llm_base_url: str | None = None
    gmail_client_id: str | None = None
    gmail_client_secret: str | None = None
    gmail_redirect_uri: str | None = "http://127.0.0.1:8000/api/v1/gmail/oauth/callback"
    gmail_token_encryption_key: str | None = None

    # Kept for existing local .env files. Prefer the provider-neutral LLM_* settings.
    openai_api_key: str | None = None
    openai_model: str | None = None
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    def resolved_llm_api_key(self) -> str | None:
        return self.llm_api_key or self.openai_api_key

    def resolved_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        if self.llm_provider == "openai" and self.openai_model:
            return self.openai_model
        return default_model_for(self.llm_provider)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def default_model_for(provider: str) -> str:
    defaults = {
        "openai": "gpt-4.1-mini",
        "gemini": "gemini-2.5-flash-lite",
        "groq": "openai/gpt-oss-20b",
        "deepseek": "deepseek-v4-flash",
    }
    return defaults.get(provider, "")
