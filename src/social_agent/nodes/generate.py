from social_agent.llm.providers import get_llm
from social_agent.llm.prompts import GENERATE_SYSTEM_PROMPT, build_generate_prompt
from social_agent.models.classification import ChangeClassification
from social_agent.models.content import ContentDraft
from social_agent.models.context import CommitContext
from social_agent.models.worthiness import WorthinessScore


def generate_drafts(
    context: CommitContext,
    classification: ChangeClassification,
    worthiness: WorthinessScore,
    feedback: str | None = None,
) -> ContentDraft:
    llm = get_llm(schema=ContentDraft)

    user_prompt = build_generate_prompt(context, classification, worthiness)
    if feedback:
        user_prompt += (
            f"\n\n<verification_feedback>\n{feedback}\n</verification_feedback>\n"
            "The previous draft failed a grounding check for this reason. Fix it."
        )

    return llm.invoke(
        [
            ("system", GENERATE_SYSTEM_PROMPT),
            ("human", user_prompt),
        ]
    ) # type: ignore