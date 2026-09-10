from pydantic import BaseModel, Field


class SafetyCheckResult(BaseModel):
    safe: bool = Field(description="True if the text is safe to publish publicly")
    reason: str = Field(description="Brief explanation, especially if unsafe")