import asyncio

from arq.connections import RedisSettings

from social_agent.config import get_settings
from social_agent.models.context import CommitContext
from social_agent.pipeline import run_pipeline_from_context


async def process_push(ctx, context_dict: dict) -> dict:
    """arq task: runs the AI pipeline for one push event in a worker process."""
    context = CommitContext(**context_dict)
    return await asyncio.to_thread(run_pipeline_from_context, context)


def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    functions = [process_push]
    redis_settings = get_redis_settings()