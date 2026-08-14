from typing import NotRequired, TypedDict

from langgraph.graph import END, START, StateGraph

from social_agent.config import get_settings
from social_agent.guardrails.prefilter import should_skip
from social_agent.models.classification import ChangeClassification
from social_agent.models.content import ContentDraft
from social_agent.models.context import CommitContext
from social_agent.models.verification import VerificationResult
from social_agent.models.worthiness import WorthinessScore
from social_agent.nodes.classify import classify_and_score
from social_agent.nodes.verify import generate_and_verify


class PipelineState(TypedDict):
    context: CommitContext
    skip: NotRequired[bool]
    skip_reason: NotRequired[str | None]
    classification: NotRequired[ChangeClassification]
    worthiness: NotRequired[WorthinessScore]
    draft: NotRequired[ContentDraft]
    verification: NotRequired[VerificationResult]
    error: NotRequired[str]


def _prefilter_node(state: PipelineState) -> dict:
    try:
        skip, reason = should_skip(state["context"])
        return {"skip": skip, "skip_reason": reason}
    except Exception as exc:
        return {"error": f"prefilter failed: {exc}"}


def _classify_node(state: PipelineState) -> dict:
    try:
        classification, worthiness = classify_and_score(state["context"])
        return {"classification": classification, "worthiness": worthiness}
    except Exception as exc:
        return {"error": f"classify failed: {exc}"}


def _generate_verify_node(state: PipelineState) -> dict:
    classification = state.get("classification")
    worthiness = state.get("worthiness")
    if classification is None or worthiness is None:
        return {"error": "generate_verify called without classification/worthiness"}

    try:
        draft, verification = generate_and_verify(state["context"], classification, worthiness)
        return {"draft": draft, "verification": verification}
    except Exception as exc:
        return {"error": f"generate/verify failed: {exc}"}


def _route_after_classify(state: PipelineState) -> str:
    if state.get("error"):
        return END
    worthiness = state.get("worthiness")
    if worthiness is None:
        return END 
    settings = get_settings()
    return "generate_verify" if worthiness.score >= settings.worthiness_threshold else END

def _route_after_prefilter(state: PipelineState) -> str:
    if state.get("error") or state.get("skip"):
        return END
    return "classify"




def build_graph():
    builder = StateGraph(PipelineState)

    builder.add_node("prefilter", _prefilter_node)
    builder.add_node("classify", _classify_node)
    builder.add_node("generate_verify", _generate_verify_node)

    builder.add_edge(START, "prefilter")
    builder.add_conditional_edges("prefilter", _route_after_prefilter, {"classify": "classify", END: END})
    builder.add_conditional_edges(
        "classify", _route_after_classify, {"generate_verify": "generate_verify", END: END}
    )
    builder.add_edge("generate_verify", END)

    return builder.compile()