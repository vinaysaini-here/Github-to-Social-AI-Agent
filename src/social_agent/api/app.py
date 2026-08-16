from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI

from social_agent.api.routes import router
from social_agent.queue.tasks import get_redis_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await create_pool(get_redis_settings())
    yield
    await app.state.arq_pool.close()


app = FastAPI(title="GitHub-to-Social AI Agent", lifespan=lifespan)
app.include_router(router)