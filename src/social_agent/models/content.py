from pydantic import BaseModel, Field


class ContentDraft(BaseModel):
    """Platform-specific social media drafts generated from a commit."""

    linkedin_post: str = Field(description="Descriptive, professional LinkedIn draft")
    x_post: str = Field(description="Concise X (Twitter) draft")