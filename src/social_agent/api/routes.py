from fastapi import APIRouter, Header, HTTPException, Request

from social_agent.webhook.idempotency import is_duplicate_delivery
from social_agent.webhook.parser import WebhookParseError, parse_push_event
from social_agent.webhook.security import verify_signature

router = APIRouter()


@router.post("/webhook/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
):
    body = await request.body()

    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="invalid signature")

    if x_github_event == "ping":
        return {"status": "pong"}

    if x_github_event != "push":
        return {"status": "ignored", "reason": f"event type '{x_github_event}' not handled"}

    if x_github_delivery is None:
        raise HTTPException(status_code=400, detail="missing X-GitHub-Delivery header")

    if await is_duplicate_delivery(request.app.state.arq_pool, x_github_delivery):
        return {"status": "duplicate", "delivery_id": x_github_delivery}

    payload = await request.json()

    try:
        context = parse_push_event(payload)
    except WebhookParseError as exc:
        return {"status": "ignored", "reason": str(exc)}

    await request.app.state.arq_pool.enqueue_job("process_push", context.model_dump())

    return {
        "status": "accepted",
        "delivery_id": x_github_delivery,
        "repo": context.repo_name,
        "commit_sha": context.commit_sha,
    }