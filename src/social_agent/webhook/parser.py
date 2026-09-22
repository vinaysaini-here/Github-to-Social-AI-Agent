import base64

import httpx

from social_agent.config import get_settings
from social_agent.models.context import CommitContext

GITHUB_API_BASE = "https://api.github.com"
NULL_SHA = "0000000000000000000000000000000000000000"  

class WebhookParseError(RuntimeError):
    """Raised when a push payload can't be turned into a CommitContext."""


def parse_push_event(payload: dict) -> CommitContext:
    head_commit = payload.get("head_commit")
    if head_commit is None:
        raise WebhookParseError("payload has no head_commit (empty push or branch delete?)")

    repository = payload.get("repository", {})
    repo_full_name = repository.get("full_name")
    if not repo_full_name:
        raise WebhookParseError("payload missing repository.full_name")

    commits = payload.get("commits", [])
    before_sha = payload.get("before")
    after_sha = payload.get("after") or head_commit["id"]

    changed_files = _collect_changed_files(commits, head_commit)
    diff = _fetch_diff_for_push(repo_full_name, before_sha, after_sha)

    return CommitContext(
        repo_name=repository.get("name", repo_full_name),
        repo_full_name=repo_full_name, 
        commit_sha=after_sha,
        commit_message=_combine_commit_messages(commits, head_commit),
        author=head_commit.get("author", {}).get("name", "unknown"),
        changed_files=changed_files,
        diff=diff,
        readme_snippet=_fetch_readme_snippet(repo_full_name),
    )


def _combine_commit_messages(commits: list[dict], head_commit: dict) -> str:
    if len(commits) <= 1:
        return head_commit.get("message", "")

    first_lines = [c.get("message", "").splitlines()[0] for c in commits if c.get("message")]
    return f"{len(commits)} commits in this push:\n" + "\n".join(f"- {line}" for line in first_lines)


def _collect_changed_files(commits: list[dict], head_commit: dict) -> list[str]:
    source = commits or [head_commit]
    all_files: set[str] = set()
    for commit in source:
        all_files |= set(commit.get("added", []))
        all_files |= set(commit.get("modified", []))
        all_files |= set(commit.get("removed", []))
    return sorted(all_files)


def _github_headers() -> dict:
    settings = get_settings()
    return {
        "Authorization": f"Bearer {settings.github_token.get_secret_value()}",
        "Accept": "application/vnd.github+json",
    }


def _fetch_diff_for_push(repo_full_name: str, before_sha: str | None, after_sha: str) -> str:
    """Diff for the whole push when possible, falling back to a single-commit diff
    for a brand-new branch (GitHub sends before=NULL_SHA, so there's nothing to compare against)."""
    if before_sha and before_sha != NULL_SHA:
        return _fetch_compare_diff(repo_full_name, before_sha, after_sha)
    return _fetch_single_commit_diff(repo_full_name, after_sha)


def _fetch_compare_diff(repo_full_name: str, base_sha: str, head_sha: str) -> str:
    url = f"{GITHUB_API_BASE}/repos/{repo_full_name}/compare/{base_sha}...{head_sha}"
    headers = {**_github_headers(), "Accept": "application/vnd.github.v3.diff"}

    response = httpx.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        raise WebhookParseError(f"GitHub API returned {response.status_code} comparing {base_sha}...{head_sha}")

    return response.text


def _fetch_single_commit_diff(repo_full_name: str, commit_sha: str) -> str:
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