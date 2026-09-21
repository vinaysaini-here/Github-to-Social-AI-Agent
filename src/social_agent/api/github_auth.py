import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request

from social_agent.config import get_settings
from social_agent.db.repository import save_github_user
from social_agent.security.token_encryption import encrypt_token

router = APIRouter(prefix="/auth/github")

AUTHORIZATION_URL = "https://github.com/login/oauth/authorize"
TOKEN_URL = "https://github.com/login/oauth/access_token"
USER_URL = "https://api.github.com/user"
STATE_TTL_SECONDS = 300


@router.get("/login")
async def github_login(request: Request):
    settings = get_settings()
    state = secrets.token_urlsafe(24)
    await request.app.state.arq_pool.set(f"github:oauth_state:{state}", "1", ex=STATE_TTL_SECONDS)

    params = {
        "client_id": settings.github_oauth_client_id,
        "redirect_uri": settings.github_oauth_redirect_uri,
        "scope": "repo",
        "state": state,
    }
    return {"authorization_url": f"{AUTHORIZATION_URL}?{urlencode(params)}"}


@router.get("/callback")
async def github_callback(request: Request, code: str, state: str):
    settings = get_settings()

    state_key = f"github:oauth_state:{state}"
    if not await request.app.state.arq_pool.delete(state_key):
        raise HTTPException(status_code=400, detail="invalid or expired state")

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.github_oauth_client_id,
                "client_secret": settings.github_oauth_client_secret.get_secret_value(),
                "code": code,
                "redirect_uri": settings.github_oauth_redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub token exchange failed")

        token_data = token_response.json()
        if "error" in token_data:
            raise HTTPException(status_code=502, detail=f"GitHub OAuth error: {token_data['error']}")
        access_token = token_data["access_token"]

        user_response = await client.get(
            USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/vnd.github+json"},
        )
        if user_response.status_code != 200:
            raise HTTPException(status_code=502, detail="GitHub user fetch failed")

    github_login = user_response.json()["login"]

    await save_github_user(
        github_login=github_login,
        encrypted_access_token=encrypt_token(access_token),
    )

    return {"status": "connected", "github_login": github_login}