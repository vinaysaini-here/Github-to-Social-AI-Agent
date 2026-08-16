from arq.connections import ArqRedis

IDEMPOTENCY_KEY_PREFIX = "webhook:delivery:"
IDEMPOTENCY_TTL_SECONDS = 24 * 60 * 60  


async def is_duplicate_delivery(redis: ArqRedis, delivery_id: str) -> bool:
    """True if this delivery_id was already seen — and marks it seen either way.

    Uses Redis SET NX (set-if-not-exists): the check and the mark happen in
    one atomic operation, so two requests with the same delivery_id arriving
    at the same instant can't both slip through as "not a duplicate."
    """
    key = f"{IDEMPOTENCY_KEY_PREFIX}{delivery_id}"
    was_newly_set = await redis.set(key, "1", nx=True, ex=IDEMPOTENCY_TTL_SECONDS)
    return not was_newly_set