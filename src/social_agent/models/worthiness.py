from pydantic import BaseModel, Field


class WorthinessScore(BaseModel):
    """The LLM's judgment on whether a commit is worth turning into a post."""

    score: int = Field(ge=0, le=100, description="0 (definitely ignore) to 100 (definitely post)")
    reason: str = Field(description="Short, specific explanation — shown in the dashboard later")