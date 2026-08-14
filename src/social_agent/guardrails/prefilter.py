from social_agent.config import get_settings
from social_agent.models.context import CommitContext

LOCKFILE_NAMES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "uv.lock",
    "poetry.lock", "Cargo.lock", "Gemfile.lock", "composer.lock", "go.sum",
}

TRIVIAL_MESSAGE_KEYWORDS = ("typo", "whitespace", "format", "lint")


def _changed_diff_line_count(diff: str) -> int:
    count = 0
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            count += 1
    return count


def should_skip(context: CommitContext) -> tuple[bool, str | None]:
    """Returns (True, reason) to skip, or (False, None) to proceed to classification."""
    if context.changed_files and all(
        f.rsplit("/", 1)[-1] in LOCKFILE_NAMES for f in context.changed_files
    ):
        return True, "lockfile-only change"

    settings = get_settings()
    message_lower = context.commit_message.lower()
    is_trivial_message = any(kw in message_lower for kw in TRIVIAL_MESSAGE_KEYWORDS)
    line_count = _changed_diff_line_count(context.diff)

    if is_trivial_message and line_count <= settings.prefilter_trivial_line_threshold:
        return True, f"trivial change ({line_count} changed lines)"

    return False, None