from datetime import datetime, timezone

from social_agent.db.client import get_database


async def save_pipeline_result(result: dict) -> None:
    db = get_database()
    document = {**result, "stored_at": datetime.now(timezone.utc)}

    update = {"$set": document}
    if result.get("draft") is not None:
        update["$setOnInsert"] = {"approval_status": "pending"}

    await db.pipeline_results.update_one(
        {"repo_name": result["repo_name"], "commit_sha": result["commit_sha"]},
        update,
        upsert=True,
    )


async def list_drafts(status: str | None = None) -> list[dict]:
    db = get_database()
    query: dict = {"draft": {"$ne": None}}
    if status:
        query["approval_status"] = status
    return [doc async for doc in db.pipeline_results.find(query).sort("stored_at", -1)]


async def get_draft(repo_name: str, commit_sha: str) -> dict | None:
    db = get_database()
    return await db.pipeline_results.find_one({"repo_name": repo_name, "commit_sha": commit_sha})


async def update_approval_status(repo_name: str, commit_sha: str, status: str) -> bool:
    db = get_database()
    result = await db.pipeline_results.update_one(
        {"repo_name": repo_name, "commit_sha": commit_sha},
        {"$set": {"approval_status": status}},
    )
    return result.matched_count > 0


async def update_draft(repo_name: str, commit_sha: str, draft: dict, verification: dict) -> bool:
    db = get_database()
    result = await db.pipeline_results.update_one(
        {"repo_name": repo_name, "commit_sha": commit_sha},
        {"$set": {"draft": draft, "verification": verification, "approval_status": "pending"}},
    )
    return result.matched_count > 0

