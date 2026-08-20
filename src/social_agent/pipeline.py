import json
from pathlib import Path

from social_agent.collectors.git import collect_context
from social_agent.config import get_settings
from social_agent.graph import build_graph
from social_agent.models.context import CommitContext


def run_pipeline_from_context(context: CommitContext) -> dict:
    graph = build_graph()
    final_state = graph.invoke({"context": context})

    result = _build_result(context, final_state)
    output_path = _save_result(result)
    _print_summary(result, output_path)

    return result


def run_pipeline(repo_path: str, commit_sha: str = "HEAD") -> dict:
    context = collect_context(repo_path, commit_sha)
    return run_pipeline_from_context(context)


def _build_result(context: CommitContext, final_state: dict) -> dict:
    result = {
        "context": context.model_dump(),
        "repo_name": context.repo_name,
        "commit_sha": context.commit_sha,
        "commit_message": context.commit_message,
        "skip": final_state.get("skip", False),
        "skip_reason": final_state.get("skip_reason"),
        "error": final_state.get("error"),
        "media": None,  # placeholder — AI-generated images deferred, no free Gemini tier yet
    }

    for key in ("classification", "worthiness", "draft", "verification"):
        value = final_state.get(key)
        if value is not None:
            result[key] = value.model_dump()

    return result


def _save_result(result: dict) -> Path:
    settings = get_settings()
    output_dir = Path(settings.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{result['repo_name']}_{result['commit_sha'][:12]}.json"
    output_path = output_dir / filename
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return output_path


def _print_summary(result: dict, output_path: Path) -> None:
    if result["error"]:
        print(f"[error] {result['error']}")
    elif result["skip"]:
        print(f"[skipped] {result['skip_reason']}")
    elif result.get("verification", {}).get("verified") is False:
        print(f"[unverified] {result['verification']['issues']}")
    else:
        print(f"[ok] worthiness={result['worthiness']['score']}")

    print(f"Saved to {output_path}")