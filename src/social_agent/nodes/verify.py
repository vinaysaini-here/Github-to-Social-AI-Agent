from social_agent.config import get_settings
from social_agent.llm.providers import get_llm
from social_agent.llm.prompts import VERIFY_SYSTEM_PROMPT, build_verify_prompt
from social_agent.models.classification import ChangeClassification
from social_agent.models.content import ContentDraft
from social_agent.models.context import CommitContext
from social_agent.models.verification import VerificationResult
from social_agent.models.worthiness import WorthinessScore
from social_agent.nodes.generate import generate_drafts


def verify_draft(context: CommitContext, draft: ContentDraft) -> VerificationResult:
    llm = get_llm(schema=VerificationResult)
    return llm.invoke(
        [
            ("system", VERIFY_SYSTEM_PROMPT),
            ("human", build_verify_prompt(context, draft)),
        ]
    ) # type: ignore


def generate_and_verify(
    context: CommitContext,
    classification: ChangeClassification,
    worthiness: WorthinessScore,
) -> tuple[ContentDraft, VerificationResult]:
    """Generate drafts, verify grounding, and regenerate with feedback on failure.

    Capped at settings.max_verification_retries. If still unverified after
    that many attempts, returns the last draft along with its failed
    VerificationResult — the caller (graph.py) decides what to do with an
    unverified draft, this function never silently hides the failure.
    """
    settings = get_settings()
    feedback: str | None = None

    for _ in range(settings.max_verification_retries + 1):
        draft = generate_drafts(context, classification, worthiness, feedback=feedback)
        result = verify_draft(context, draft)

        if result.verified:
            return draft, result

        feedback = "; ".join(result.issues) or "Claims not grounded in the diff."

    return draft, result # type: ignore