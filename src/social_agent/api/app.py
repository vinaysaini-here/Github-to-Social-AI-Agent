from contextlib import asynccontextmanager

from arq import create_pool
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path

from social_agent.api.drafts import router as drafts_router
from social_agent.api.routes import router as webhook_router
from social_agent.queue.tasks import get_redis_settings
from social_agent.config import get_settings



@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.arq_pool = await create_pool(get_redis_settings())
    yield
    await app.state.arq_pool.close()


app = FastAPI(title="GitHub-to-Social AI Agent", lifespan=lifespan)


media_dir = Path(get_settings().output_dir).parent / "media"
media_dir.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=media_dir), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default dev port
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(webhook_router)
app.include_router(drafts_router)