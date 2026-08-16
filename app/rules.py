from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, status

from .database import rules_collection
from .models import RuleCreate, RuleResponse


router = APIRouter()


@router.post(
    "/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_rule(rule: RuleCreate):
    keyword = rule.keyword.strip()
    dm_message = rule.dm_message.strip()

    rule_id = f"rule_{uuid4().hex}"

    document = {
        "rule_id": rule_id,
        "keyword": keyword,
        "dm_message": dm_message,
        "created_at": datetime.now(timezone.utc),
    }

    rules_collection.insert_one(document)

    return {
        "rule_id": rule_id,
        "keyword": keyword,
        "dm_message": dm_message,
    }