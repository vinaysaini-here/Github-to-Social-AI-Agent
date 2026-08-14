from pydantic import BaseModel, Field


class CommitContext(BaseModel):
    """Everything the pipeline knows about a single commit.

    Mirrors the shape a real GitHub webhook payload will provide in Phase 2,
    so swapping the source later is a small change, not a redesign.
    """

    repo_name: str = Field(description="Name of the repository, e.g. 'my-project'")
    commit_sha: str = Field(description="Full commit SHA")
    commit_message: str = Field(description="Raw commit message")
    author: str = Field(description="Commit author name")
    changed_files: list[str] = Field(
        default_factory=list, description="Paths of files touched by this commit"
    )
    diff: str = Field(description="Unified diff of the commit")
    readme_snippet: str | None = Field(
        default=None,
        description="Leading portion of the repo's README, if one exists",
    )