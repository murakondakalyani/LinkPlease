from pymongo import MongoClient

from .config import MONGODB_URL, DATABASE_NAME


client = MongoClient(MONGODB_URL)

db = client[DATABASE_NAME]

rules_collection = db["rules"]
events_collection = db["events"]
dm_jobs_collection = db["dm_jobs"]
stats_collection = db["stats"]


# Prevent the same webhook event from being processed twice.
events_collection.create_index(
    "event_id",
    unique=True,
)

# Prevent the same user from receiving the same rule DM twice.
dm_jobs_collection.create_index(
    [("rule_id", 1), ("user_id", 1)],
    unique=True,
)