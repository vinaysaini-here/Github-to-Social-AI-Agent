from datetime import datetime, timezone

from social_agent.db.client import get_database


async def save_pipeline_result(result: dict) -> None:
    """Persist one pipeline run's result, upserted by (repo_name, commit_sha)."""
    db = get_database()
    document = {**result, "stored_at": datetime.now(timezone.utc)}

    await db.pipeline_results.update_one(
        {"repo_name": result["repo_name"], "commit_sha": result["commit_sha"]},
        {"$set": document},
        upsert=True,
    )