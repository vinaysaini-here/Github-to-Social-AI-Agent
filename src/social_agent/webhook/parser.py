import base64

import httpx

from social_agent.config import get_settings
from social_agent.models.context import CommitContext

GITHUB_API_BASE = "https://api.github.com"


class WebhookParseError(RuntimeError):
    """Raised when a push payload can't be turned into a CommitContext."""


def parse_push_event(payload: dict) -> CommitContext:
    """Turn a GitHub push webhook payload into a CommitContext.

    Only the push's `head_commit` is used — multiple commits landing in one
    push are summarized as a single unit (the "commit grouping" guardrail
    from the roadmap), instead of posting once per individual commit.
    """
    head_commit = payload.get("head_commit")
    if head_commit is None:
        raise WebhookParseError("payload has no head_commit (empty push or branch delete?)")

    repository = payload.get("repository", {})
    repo_full_name = repository.get("full_name")
    if not repo_full_name:
        raise WebhookParseError("payload missing repository.full_name")

    commit_sha = head_commit["id"]
    changed_files = sorted(
        set(head_commit.get("added", []))
        | set(head_commit.get("modified", []))
        | set(head_commit.get("removed", []))
    )

    return CommitContext(
        repo_name=repository.get("name", repo_full_name),
        commit_sha=commit_sha,
        commit_message=head_commit.get("message", ""),
        author=head_commit.get("author", {}).get("name", "unknown"),
        changed_files=changed_files,
        diff=_fetch_diff(repo_full_name, commit_sha),
        readme_snippet=_fetch_readme_snippet(repo_full_name),
    )


def _github_headers() -> dict:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
        "Accept": "application/vnd.github+json",
    }


def _fetch_diff(repo_full_name: str, commit_sha: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/commits/{commit_sha}"
    headers = {**_github_headers(), "Accept": "application/vnd.github.v3.diff"}

    response = httpx.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise WebhookParseError(f"GitHub API returned {response.status_code} fetching diff for {commit_sha}")

    return response.text


def _fetch_readme_snippet(repo_full_name: str) -> str | None:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/readme"
    response = httpx.get(url, headers=_github_headers(), timeout=10)
    if response.status_code != 200:
        return None

    content_b64 = response.json().get("content", "")
    try:
        return base64.b64decode(content_b64).decode("utf-8", errors="ignore")[:1000]
    except Exception:
        return None