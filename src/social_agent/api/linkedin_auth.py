import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request

from social_agent.config import get_settings
from social_agent.db.repository import save_linkedin_token
from social_agent.security.token_encryption import encrypt_token

router = APIRouter(prefix="/auth/linkedin")

AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
STATE_TTL_SECONDS = 300


@router.get("/login")
async def linkedin_login(request: Request):
    settings = get_settings()
    state = secrets.token_urlsafe(24)
    await request.app.state.arq_pool.set(f"linkedin:oauth_state:{state}", "1", ex=STATE_TTL_SECONDS)

    params = {
        "response_type": "code",
        "client_id": settings.linkedin_client_id,
        "redirect_uri": settings.linkedin_redirect_uri,
        "scope": "openid profile email w_member_social",
        "state": state,
    }
    return {"authorization_url": f"{AUTHORIZATION_URL}?{urlencode(params)}"}


@router.get("/callback")
async def linkedin_callback(request: Request, code: str, state: str):
    settings = get_settings()

    state_key = f"linkedin:oauth_state:{state}"
    if not await request.app.state.arq_pool.delete(state_key):
        raise HTTPException(status_code=400, detail="invalid or expired state")

    async with httpx.AsyncClient(timeout=10) as client:
        token_response = await client.post(
            TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.linkedin_redirect_uri,
                "client_id": settings.linkedin_client_id,
                "client_secret": settings.linkedin_client_secret.get_secret_value(),
            },
        )
        if token_response.status_code != 200:
            raise HTTPException(status_code=502, detail="LinkedIn token exchange failed")

        token_data = token_response.json()
        access_token = token_data["access_token"]

        userinfo_response = await client.get(
            USERINFO_URL, headers={"Authorization": f"Bearer {access_token}"}
        )
        if userinfo_response.status_code != 200:
            raise HTTPException(status_code=502, detail="LinkedIn userinfo fetch failed")

    person_urn = f"urn:li:person:{userinfo_response.json()['sub']}"

    await save_linkedin_token(
        person_urn=person_urn,
        encrypted_access_token=encrypt_token(access_token),
        expires_in=token_data["expires_in"],
    )

    return {"status": "connected", "person_urn": person_urn}