from fastapi import APIRouter, HTTPException

from social_agent.db.repository import get_repo_config, upsert_repo_config
from social_agent.models.repo_config import RepoConfig

router = APIRouter(prefix="/repos")


@router.get("/{owner}/{repo}/config")
async def read_repo_config(owner: str, repo: str):
    repo_full_name = f"{owner}/{repo}"
    config = await get_repo_config(repo_full_name)
    if config is None:
        return RepoConfig(repo_full_name=repo_full_name).model_dump()
    config.pop("_id", None)
    return config


@router.put("/{owner}/{repo}/config")
async def write_repo_config(owner: str, repo: str, body: RepoConfig):
    repo_full_name = f"{owner}/{repo}"
    if body.repo_full_name != repo_full_name:
        raise HTTPException(status_code=422, detail="repo_full_name in body must match URL")
    await upsert_repo_config(body.model_dump())
    return {"status": "saved"}