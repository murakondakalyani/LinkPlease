import hashlib
import hmac
import json
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request

from .config import PSEUDOGRAM_API_KEY
from .database import (
    dm_jobs_collection,
    events_collection,
    rules_collection,
    stats_collection,
)


router = APIRouter()


def verify_signature(raw_body: bytes, signature: str | None) -> bool:
    if not signature:
        return False

    expected = hmac.new(
        PSEUDOGRAM_API_KEY.encode(),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    expected_signature = f"sha256={expected}"

    return hmac.compare_digest(
        signature,
        expected_signature,
    )


def increment_duplicate_counter():
    stats_collection.update_one(
        {"_id": "counters"},
        {"$inc": {"duplicates_blocked": 1}},
        upsert=True,
    )


def process_event(event: dict):
    event_id = event["event_id"]
    event_type = event.get("event_type")

    # We currently process comment.created.
    if event_type != "comment.created":
        events_collection.update_one(
            {"event_id": event_id},
            {
                "$set": {
                    "processed": True,
                    "processed_at": datetime.now(timezone.utc),
                }
            },
        )
        return

    data = event["data"]

    comment_id = data["comment_id"]
    text = data.get("text", "")
    user_id = data["from"]["user_id"]

    # Find all rules whose keyword occurs anywhere
    # in the comment, case-insensitively.
    rules = rules_collection.find({})

    for rule in rules:
        keyword = rule["keyword"]

        if keyword.lower() not in text.lower():
            continue

        job = {
            "rule_id": rule["rule_id"],
            "user_id": user_id,
            "comment_id": comment_id,
            "message": rule["dm_message"],
            "status": "queued",
            "dm_id": None,
            "attempts": 0,
            "next_retry_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        try:
            dm_jobs_collection.insert_one(job)

        except Exception as exc:
            # Duplicate rule + user means this person
            # has already been handled for this rule.
            if "duplicate key error" in str(exc).lower():
                increment_duplicate_counter()
            else:
                raise

    events_collection.update_one(
        {"event_id": event_id},
        {
            "$set": {
                "processed": True,
                "processed_at": datetime.now(timezone.utc),
            }
        },
    )


@router.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    raw_body = await request.body()

    signature = request.headers.get(
        "X-PseudoGram-Signature"
    )

    if not verify_signature(raw_body, signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature",
        )

    try:
        event = json.loads(raw_body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    event_id = event.get("event_id")

    if not event_id:
        raise HTTPException(
            status_code=400,
            detail="Missing event_id",
        )

    event_document = {
        "event_id": event_id,
        "event_type": event.get("event_type"),
        "received_at": datetime.now(timezone.utc),
        "processed": False,
    }

    try:
        events_collection.insert_one(event_document)

    except Exception as exc:
        if "duplicate key error" in str(exc).lower():
            increment_duplicate_counter()

            return {
                "status": "accepted",
                "duplicate": True,
            }

        raise

    # Do the rule matching and job creation in the background.
    background_tasks.add_task(
        process_event,
        event,
    )

    return {
        "status": "accepted",
    }