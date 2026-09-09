import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from social_agent.config import get_settings

POSTS_URL = "https://api.linkedin.com/rest/posts"


class LinkedInPublishError(RuntimeError):
    """Raised when LinkedIn rejects a publish request outright (not retryable)."""


class LinkedInTransientError(LinkedInPublishError):
    """A LinkedIn failure that might succeed on retry (429 / 5xx)."""


@retry(
    retry=retry_if_exception_type(LinkedInTransientError),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    reraise=True,
)
async def publish_text_post(access_token: str, person_urn: str, text: str) -> str:
    settings = get_settings()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": settings.linkedin_api_version,
    }
    body = {
        "author": person_urn,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.post(POSTS_URL, headers=headers, json=body)

    if response.status_code == 429 or response.status_code >= 500:
        raise LinkedInTransientError(f"LinkedIn returned {response.status_code}: {response.text}")

    if response.status_code != 201:
        raise LinkedInPublishError(f"LinkedIn returned {response.status_code}: {response.text}")

    post_urn = response.headers.get("x-restli-id")
    if not post_urn:
        raise LinkedInPublishError("LinkedIn accepted the post but returned no post URN")

    return post_urn