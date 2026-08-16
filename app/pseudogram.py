import httpx

from .config import (
    PSEUDOGRAM_API_BASE_URL,
    PSEUDOGRAM_API_KEY,
)


def get_headers(idempotency_key: str | None = None):
    headers = {
        "X-API-Key": PSEUDOGRAM_API_KEY,
        "Content-Type": "application/json",
    }

    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key

    return headers


def send_dm(
    recipient_user_id: str,
    message: str,
    comment_id: str,
    idempotency_key: str,
):
    url = f"{PSEUDOGRAM_API_BASE_URL}/v1/dm/send"

    payload = {
        "recipient_user_id": recipient_user_id,
        "message": message,
        "comment_id": comment_id,
    }

    response = httpx.post(
        url,
        json=payload,
        headers=get_headers(idempotency_key),
        timeout=30,
    )

    return response


def get_dm_status(dm_id: str):
    url = f"{PSEUDOGRAM_API_BASE_URL}/v1/dm/{dm_id}"

    response = httpx.get(
        url,
        headers={
            "X-API-Key": PSEUDOGRAM_API_KEY,
        },
        timeout=30,
    )

    return response