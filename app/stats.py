from fastapi import APIRouter

from .database import dm_jobs_collection, stats_collection


router = APIRouter()


@router.get("/stats")
def get_stats():
    sent = dm_jobs_collection.count_documents(
        {"status": "delivered"}
    )

    failed = dm_jobs_collection.count_documents(
        {"status": "failed"}
    )

    queued = dm_jobs_collection.count_documents(
        {
            "status": {
                "$in": [
                    "queued",
                    "sending",
                    "accepted",
                ]
            }
        }
    )

    counters = stats_collection.find_one(
        {"_id": "counters"}
    )

    duplicates_blocked = 0

    if counters:
        duplicates_blocked = counters.get(
            "duplicates_blocked",
            0,
        )

    return {
        "sent": sent,
        "failed": failed,
        "queued": queued,
        "duplicates_blocked": duplicates_blocked,
    }