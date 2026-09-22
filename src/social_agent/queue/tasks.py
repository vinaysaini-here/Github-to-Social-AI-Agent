import asyncio

from arq.connections import RedisSettings

from social_agent.config import get_settings
from social_agent.models.context import CommitContext
from social_agent.pipeline import run_pipeline_from_context
from social_agent.db.repository import save_pipeline_result, get_repo_config


async def process_push(ctx, context_dict: dict) -> dict:
    context = CommitContext(**context_dict)

    threshold = None
    if context.repo_full_name:
        config = await get_repo_config(context.repo_full_name)
        if config and config.get("enabled") is False:
            return {"status": "skipped", "reason": "repo disabled in config"}
        if config:
            threshold = config.get("worthiness_threshold")

    result = await asyncio.to_thread(run_pipeline_from_context, context, threshold)
    await save_pipeline_result(result)
    return result


def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    functions = [process_push]
    redis_settings = get_redis_settings()