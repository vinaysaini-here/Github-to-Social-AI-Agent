import asyncio

from arq.connections import RedisSettings

from social_agent.config import get_settings
from social_agent.models.context import CommitContext
from social_agent.pipeline import run_pipeline_from_context
from social_agent.db.repository import save_pipeline_result


async def process_push(ctx, context_dict: dict) -> dict:
    context = CommitContext(**context_dict)
    result = await asyncio.to_thread(run_pipeline_from_context, context)
    await save_pipeline_result(result)
    return result


def get_redis_settings() -> RedisSettings:
    return RedisSettings.from_dsn(get_settings().redis_url)


class WorkerSettings:
    functions = [process_push]
    redis_settings = get_redis_settings()