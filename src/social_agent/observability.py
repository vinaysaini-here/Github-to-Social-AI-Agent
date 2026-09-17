import os

from social_agent.config import get_settings


def enable_langsmith_tracing() -> None:
    settings = get_settings()
    if not settings.langsmith_tracing or settings.langsmith_api_key is None:
        print("[langsmith] tracing NOT enabled — check LANGSMITH_TRACING / LANGSMITH_API_KEY in .env")
        return

    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGSMITH_ENDPOINT"] = settings.langsmith_endpoint
    os.environ["LANGSMITH_API_KEY"] = settings.langsmith_api_key.get_secret_value()
    os.environ["LANGSMITH_PROJECT"] = settings.langsmith_project
    # print(f"[langsmith] tracing enabled -> project '{settings.langsmith_project}'")