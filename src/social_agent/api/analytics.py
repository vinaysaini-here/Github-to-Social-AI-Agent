from fastapi import APIRouter

from social_agent.db.repository import get_event_counts, get_status_counts, list_audit_logs

router = APIRouter(prefix="/analytics")

MAX_LOG_LIMIT = 200


@router.get("/summary")
async def analytics_summary():
    return {
        "events": await get_event_counts(),
        "drafts_by_status": await get_status_counts(),
    }


@router.get("/audit-log")
async def audit_log(repo_name: str | None = None, limit: int = 50):
    logs = await list_audit_logs(repo_name, min(limit, MAX_LOG_LIMIT))
    for entry in logs:
        entry["_id"] = str(entry["_id"])
    return logs