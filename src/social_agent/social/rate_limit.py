from datetime import date

DAILY_LIMIT = 100
SAFETY_MARGIN = 10


class RateLimitExceededError(RuntimeError):
    """Raised when the daily LinkedIn publish quota has been reached."""


def _quota_key(person_urn: str) -> str:
    return f"linkedin:publish_count:{person_urn}:{date.today().isoformat()}"


async def check_and_increment_quota(redis, person_urn: str) -> None:
    key = _quota_key(person_urn)
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 60 * 60 * 26)  # ~24h + buffer for clock drift
    if count > DAILY_LIMIT - SAFETY_MARGIN:
        raise RateLimitExceededError(
            f"LinkedIn daily publish quota reached ({count}/{DAILY_LIMIT}) for {person_urn}"
        )

