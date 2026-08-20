import hashlib
import hmac
import json
import os
import httpx

WEBHOOK_URL = "http://localhost:8000/webhook/github"
SECRET = "forjeofworhwiej3oirhoojfe23y584632ru8r28gdiehdy2943u0e"

PAYLOAD = {
    "repository": {"name": "AI Email Assistant", "full_name": "vinaysaini-here/AI-Email-Assistant"},
    "head_commit": {
        "id": "8c25d040d845c7cc340f160dce0d08ed8bf97299",
        "message": "Implement Gmail API authentication functionality",
        "author": {"name": "Vinay Saini"},
        "added": ["auth.py"],
        "modified": [],
        "removed": [],
    },
}

body = json.dumps(PAYLOAD).encode()
signature = "sha256=" + hmac.new(SECRET.encode(), body, hashlib.sha256).hexdigest()

response = httpx.post(
    WEBHOOK_URL,
    content=body,
    headers={
        "X-Hub-Signature-256": signature,
        "X-GitHub-Event": "push",
        "X-GitHub-Delivery": "test-delivery-001",
        "Content-Type": "application/json",
    },
)
print(response.status_code, response.json())