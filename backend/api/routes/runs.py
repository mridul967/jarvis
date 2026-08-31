from typing import Annotated

from fastapi import APIRouter, Query

from backend.api.schemas import RunSummary
from backend.runs.repository import list_runs

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("", response_model=list[RunSummary])
def runs(limit: Annotated[int, Query(ge=1, le=100)] = 20) -> list[dict]:
    return list_runs(limit)
