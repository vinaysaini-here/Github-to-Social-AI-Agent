from pydantic import BaseModel, Field


class VerificationResult(BaseModel):
    """Whether a generated draft's claims are actually grounded in the diff."""

    verified: bool = Field(description="True if every claim in the drafts is supported by the diff/context")
    issues: list[str] = Field(
        default_factory=list,
        description="Specific unsupported or exaggerated claims found, if any. Empty if verified=True.",
    )