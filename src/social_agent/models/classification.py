from typing import Literal

from pydantic import BaseModel, Field


class ChangeClassification(BaseModel):
    """The LLM's classification of a commit's change type."""

    change_type: Literal[
        "feature", "bugfix", "refactor", "docs", "test", "deploy", "ui", "performance", "other"
    ] = Field(description="What kind of change this commit represents")
    reasoning: str = Field(description="Brief justification for the chosen change_type")