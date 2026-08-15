from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: SecretStr
    gemini_api_key: SecretStr | None = None

    groq_model: str = "openai/gpt-oss-120b"
    gemini_model: str = "gemini-3.6-flash"

    max_diff_chars: int = 4000
    prefilter_trivial_line_threshold: int = 2
    worthiness_threshold: int = 60
    max_verification_retries: int = 3
    output_dir: str = "output/drafts"
    github_webhook_secret: SecretStr
    github_token: SecretStr



@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore