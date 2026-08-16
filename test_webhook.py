import hashlib
import hmac
import json

import httpx
from dotenv import load_dotenv
import os


load_dotenv()

api_key = os.getenv("PSEUDOGRAM_API_KEY")

if not api_key:
    raise RuntimeError("PSEUDOGRAM_API_KEY is missing")

print("API key loaded:", True)
print("API key length:", len(api_key))


payload = {
    "event_id": "test-event-002",
    "event_type": "comment.created",
    "data": {
        "comment_id": "test-comment-002",
        "post_id": "test-post-002",
        "text": "PRICE please",
        "created_at": "2026-08-16T19:00:00Z",
        "from": {
            "user_id": "test-user-002",
            "username": "testuser",
        },
    },
}


raw_body = json.dumps(
    payload,
    separators=(",", ":"),
).encode("utf-8")


signature = hmac.new(
    api_key.encode("utf-8"),
    raw_body,
    hashlib.sha256,
).hexdigest()


headers = {
    "Content-Type": "application/json",
    "X-PseudoGram-Signature": f"sha256={signature}",
}


response = httpx.post(
    "http://127.0.0.1:8000/webhook",
    content=raw_body,
    headers=headers,
)

print("Status:", response.status_code)
print("Response:", response.text)