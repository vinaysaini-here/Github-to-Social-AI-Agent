from pydantic import BaseModel

from social_agent.llm.providers import get_llm
from social_agent.llm.prompts import CLASSIFY_SYSTEM_PROMPT, build_classify_prompt
from social_agent.models.classification import ChangeClassification
from social_agent.models.context import CommitContext
from social_agent.models.worthiness import WorthinessScore


class _ClassifyOutput(BaseModel):
    """Combined schema for one LLM call — split into two models afterward so
    ChangeClassification and WorthinessScore each stay single-purpose."""

    classification: ChangeClassification
    worthiness: WorthinessScore


def classify_and_score(context: CommitContext) -> tuple[ChangeClassification, WorthinessScore]:
    llm = get_llm(schema=_ClassifyOutput)

    result = llm.invoke(
        [
            ("system", CLASSIFY_SYSTEM_PROMPT),
            ("human", build_classify_prompt(context)),
        ]
    )

    return result.classification, result.worthiness # type: ignore