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
    redis_url: str = "redis://localhost:6379"
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db_name: str = "social_agent"
    max_media_size_mb: int = 10
    linkedin_client_id: str
    linkedin_client_secret: SecretStr
    linkedin_redirect_uri: str = "http://localhost:8000/auth/linkedin/callback"
    token_encryption_key: SecretStr
    linkedin_api_version: str = "202604"



@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore