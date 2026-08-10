from __future__ import annotations
from pydantic import BaseModel, Field


class CommitContext(BaseModel):
    repo_name: str = Field(description="Name of the repository , e.g. 'my-project'")
    commit_sha: str = Field(description="Full commit SHA")
    commit_message: str = Field(description="Raw commit message")
    author: str = Field(description="Commit author name")
    changed_files: list[str] = Field(default_factory=list , description="Paths of files touched by this commit")
    diff: str = Field(description="Unified diff of the commit")
    readme_snippet: str | None = Field(default=None ,description="Leading Portion of the repo's README, if one exists")
