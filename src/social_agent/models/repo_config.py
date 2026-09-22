from pydantic import BaseModel, Field


class RepoConfig(BaseModel):
    repo_full_name: str
    enabled: bool = True
    worthiness_threshold: int = Field(default=60, ge=0, le=100)
    tone: str | None = None
    hashtags: list[str] = Field(default_factory=list)