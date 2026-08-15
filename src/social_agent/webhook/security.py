import hashlib
import hmac

from social_agent.config import get_settings


def verify_signature(payload_body: bytes, signature_header: str | None) -> bool:
    """Verify a GitHub webhook's X-Hub-Signature-256 header.

    GitHub signs the raw request body with the shared secret (HMAC-SHA256).
    This must run BEFORE the payload is parsed or trusted in any way.
    """
    if signature_header is None:
        return False

    settings = get_settings()
    secret = settings.github_webhook_secret.get_secret_value().encode()

    expected = "sha256=" + hmac.new(secret, payload_body, hashlib.sha256).hexdigest()

    return hmac.compare_digest(expected, signature_header)