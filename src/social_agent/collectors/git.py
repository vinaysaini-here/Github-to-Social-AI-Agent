import subprocess
from pathlib import Path

from social_agent.models.context import CommitContext

README_SNIPPET_CHARS = 1000
README_CANDIDATES = ("README.md", "README.rst", "README.txt", "README")

class GitContextError(RuntimeError):
    """Raised when the local git repo can't produce the context we need."""


def _run_git(repo_path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        timeout=10,
    )
    if result.returncode != 0:
        raise GitContextError(
            f"git {' '.join(args)} failed in {repo_path}: {result.stderr.strip()}"
        )
    return result.stdout


def _read_readme_snippet(repo_path: Path) -> str | None:
    for name in README_CANDIDATES:
        candidate = repo_path / name
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8", errors="ignore")[:README_SNIPPET_CHARS]
    return None


def collect_context(repo_path: str | Path, commit_sha: str = "HEAD") -> CommitContext:
    resolved_repo_path = Path(repo_path).resolve()
    if not (resolved_repo_path / ".git").exists():
        raise GitContextError(f"{resolved_repo_path} is not a git repository")

    resolved_sha = _run_git(resolved_repo_path, "rev-parse", commit_sha).strip()
    commit_message = _run_git(resolved_repo_path, "log", "-1", "--pretty=%B", resolved_sha).strip()
    author = _run_git(resolved_repo_path, "log", "-1", "--pretty=%an", resolved_sha).strip()

    changed_files_raw = _run_git(
        resolved_repo_path, "show", "--name-only", "--pretty=format:", resolved_sha
    )
    changed_files = [line for line in changed_files_raw.splitlines() if line.strip()]

    diff = _run_git(resolved_repo_path, "show", resolved_sha)

    return CommitContext(
        repo_name=resolved_repo_path.name,
        commit_sha=resolved_sha,
        commit_message=commit_message,
        author=author,
        changed_files=changed_files,
        diff=diff,
        readme_snippet=_read_readme_snippet(resolved_repo_path),
    )