from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from social_agent.config import get_settings


def get_llm(schema: type | None = None):
    """Primary LLM (Groq) with an automatic Gemini fallback.

    Pass `schema` (a Pydantic model) to get structured output — it's applied
    to both providers *before* they're chained, since a fallback-wrapped
    runnable doesn't expose `.with_structured_output()` itself.
    """
    settings = get_settings()

    primary = ChatGroq(model=settings.groq_model, api_key=settings.groq_api_key, temperature=0)
    if schema is not None:
        primary = primary.with_structured_output(schema)
    primary = primary.with_retry(stop_after_attempt=2)

    if settings.gemini_api_key is None:
        return primary

    fallback = ChatGoogleGenerativeAI(model=settings.gemini_model, google_api_key=settings.gemini_api_key)
    if schema is not None:
        fallback = fallback.with_structured_output(schema)
    fallback = fallback.with_retry(stop_after_attempt=2)

    return primary.with_fallbacks([fallback]) # type: ignore