
from fastapi import APIRouter

from app.llm.usage_tracker import get_daily_usage

router = APIRouter(tags=["usage"])


@router.get("/usage")
def daily_usage():
    return get_daily_usage()
