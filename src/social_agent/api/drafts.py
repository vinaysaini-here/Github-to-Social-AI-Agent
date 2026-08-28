from fastapi import APIRouter, HTTPException , File ,UploadFile
import asyncio
from pydantic import BaseModel

from social_agent.db.repository import get_draft, list_drafts, update_approval_status

from social_agent.db.repository import update_draft , attach_media
from social_agent.models.classification import ChangeClassification
from social_agent.models.context import CommitContext
from social_agent.models.worthiness import WorthinessScore
from social_agent.nodes.verify import generate_and_verify
from social_agent.media.storage import save_media_bytes


router = APIRouter(prefix="/drafts")

@router.get("")
async def list_all_drafts(status: str | None = None):
    drafts = await list_drafts(status=status)
    for draft in drafts:
        draft["_id"] = str(draft["_id"])
    return drafts


@router.get("/{repo_name}/{commit_sha}")
async def get_one_draft(repo_name: str, commit_sha: str):
    draft = await get_draft(repo_name, commit_sha)
    if draft is None:
        raise HTTPException(status_code=404, detail="draft not found")
    draft["_id"] = str(draft["_id"])
    return draft


@router.post("/{repo_name}/{commit_sha}/approve")
async def approve_draft(repo_name: str, commit_sha: str):
    if not await update_approval_status(repo_name, commit_sha, "approved"):
        raise HTTPException(status_code=404, detail="draft not found")
    return {"status": "approved"}


@router.post("/{repo_name}/{commit_sha}/reject")
async def reject_draft(repo_name: str, commit_sha: str):
    if not await update_approval_status(repo_name, commit_sha, "rejected"):
        raise HTTPException(status_code=404, detail="draft not found")
    return {"status": "rejected"}



class RegenerateRequest(BaseModel):
    note: str | None = None


@router.post("/{repo_name}/{commit_sha}/regenerate")
async def regenerate_draft(repo_name: str, commit_sha: str, body: RegenerateRequest = RegenerateRequest()):
    stored = await get_draft(repo_name, commit_sha)
    if stored is None:
        raise HTTPException(status_code=404, detail="draft not found")
    if not all(stored.get(k) for k in ("context", "classification", "worthiness")):
        raise HTTPException(status_code=422, detail="stored record is missing data needed to regenerate")

    context = CommitContext(**stored["context"])
    classification = ChangeClassification(**stored["classification"])
    worthiness = WorthinessScore(**stored["worthiness"])

    draft, verification = await asyncio.to_thread(
        generate_and_verify, context, classification, worthiness, body.note
    )

    await update_draft(repo_name, commit_sha, draft.model_dump(), verification.model_dump())

    return {"status": "regenerated", "verified": verification.verified, "draft": draft.model_dump()}




from fastapi import File, UploadFile

from social_agent.db.repository import attach_media  # existing imports me add karo
from social_agent.guardrails.media_validation import MediaValidationError, validate_media_upload
from social_agent.media.storage import save_media_bytes


@router.post("/{repo_name}/{commit_sha}/media")
async def upload_media(repo_name: str, commit_sha: str, file: UploadFile = File(...)):
    stored = await get_draft(repo_name, commit_sha)
    if stored is None:
        raise HTTPException(status_code=404, detail="draft not found")

    try:
        content = await validate_media_upload(file)
    except MediaValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    destination = save_media_bytes(content, file.filename)
    media = {
        "filename": file.filename,
        "content_type": file.content_type,
        "url": f"/media/{destination.name}",
    }

    await attach_media(repo_name, commit_sha, media)
    return {"status": "attached", "media": media}