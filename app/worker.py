import asyncio
from datetime import datetime, timedelta, timezone

from pymongo import ReturnDocument

from .database import dm_jobs_collection
from .pseudogram import get_dm_status, send_dm


# Maximum allowed by PseudoGram:
# 10 requests per rolling 60 seconds.
#
# We intentionally send no faster than one request every
# 6.5 seconds to stay safely below the limit.
SEND_INTERVAL_SECONDS = 6.5

MAX_ATTEMPTS = 5


last_send_time = 0.0


def utc_now():
    return datetime.now(timezone.utc)


def claim_job():
    now = utc_now()

    job = dm_jobs_collection.find_one_and_update(
        {
            "status": "queued",
            "$or": [
                {"next_retry_at": None},
                {"next_retry_at": {"$lte": now}},
            ],
        },
        {
            "$set": {
                "status": "sending",
                "updated_at": now,
            }
        },
        sort=[("created_at", 1)],
        return_document=ReturnDocument.AFTER,
    )

    return job


def update_job(job_id, update):
    update["updated_at"] = utc_now()

    dm_jobs_collection.update_one(
        {"_id": job_id},
        {"$set": update},
    )


async def wait_for_rate_limit():
    global last_send_time

    now = asyncio.get_running_loop().time()

    elapsed = now - last_send_time

    if elapsed < SEND_INTERVAL_SECONDS:
        await asyncio.sleep(
            SEND_INTERVAL_SECONDS - elapsed
        )

    last_send_time = asyncio.get_running_loop().time()


def process_job(job):
    job_id = job["_id"]

    try:
        response = send_dm(
            recipient_user_id=job["user_id"],
            message=job["message"],
            comment_id=job["comment_id"],
            idempotency_key=str(job_id),
        )

        if response.status_code == 202:
            data = response.json()

            dm_id = data["dm_id"]

            update_job(
                job_id,
                {
                    "status": "accepted",
                    "dm_id": dm_id,
                    "attempts": job.get("attempts", 0) + 1,
                    "next_retry_at": utc_now()
                    + timedelta(seconds=10),
                },
            )

            return

        if response.status_code == 429:
            retry_after = int(
                response.headers.get(
                    "Retry-After",
                    "10",
                )
            )

            update_job(
                job_id,
                {
                    "status": "queued",
                    "next_retry_at": utc_now()
                    + timedelta(seconds=retry_after),
                },
            )

            return

        if response.status_code >= 500:
            attempts = job.get("attempts", 0) + 1

            if attempts >= MAX_ATTEMPTS:
                update_job(
                    job_id,
                    {
                        "status": "failed",
                        "attempts": attempts,
                        "next_retry_at": None,
                    },
                )
                return

            delay = 2 ** attempts

            update_job(
                job_id,
                {
                    "status": "queued",
                    "attempts": attempts,
                    "next_retry_at": utc_now()
                    + timedelta(seconds=delay),
                },
            )

            return

        # 400 and other non-retryable responses.
        update_job(
            job_id,
            {
                "status": "failed",
                "attempts": job.get("attempts", 0) + 1,
                "next_retry_at": None,
            },
        )

    except Exception:
        attempts = job.get("attempts", 0) + 1

        if attempts >= MAX_ATTEMPTS:
            update_job(
                job_id,
                {
                    "status": "failed",
                    "attempts": attempts,
                    "next_retry_at": None,
                },
            )
            return

        delay = 2 ** attempts

        update_job(
            job_id,
            {
                "status": "queued",
                "attempts": attempts,
                "next_retry_at": utc_now()
                + timedelta(seconds=delay),
            },
        )


def reconcile_accepted_jobs():
    jobs = dm_jobs_collection.find(
        {
            "status": "accepted",
            "dm_id": {"$ne": None},
        }
    )

    for job in jobs:
        try:
            response = get_dm_status(
                job["dm_id"]
            )

            if response.status_code != 200:
                continue

            data = response.json()

            status = data.get("status")

            if status == "delivered":
                update_job(
                    job["_id"],
                    {
                        "status": "delivered",
                        "next_retry_at": None,
                    },
                )

            elif status == "failed":
                attempts = job.get("attempts", 0)

                if attempts >= MAX_ATTEMPTS:
                    update_job(
                        job["_id"],
                        {
                            "status": "failed",
                            "next_retry_at": None,
                        },
                    )
                else:
                    update_job(
                        job_id,
                        {
                            "status": "failed",
                            "attempts": attempts,
                            "next_retry_at": None,
                            "last_error": str(exc),
                        },
                    )

        except Exception:
            continue


async def worker_loop():
    while True:
        try:
            # First reconcile DMs that were accepted previously.
            await asyncio.to_thread(
                reconcile_accepted_jobs
            )

            job = await asyncio.to_thread(
                claim_job
            )

            if job:
                await wait_for_rate_limit()

                await asyncio.to_thread(
                    process_job,
                    job,
                )
            else:
                await asyncio.sleep(1)

        except Exception as exc:
            print(
                f"Worker error: {exc}"
            )

            await asyncio.sleep(2)