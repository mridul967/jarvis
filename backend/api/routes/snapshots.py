from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    CostSnapshotCreateRequest,
    CostSnapshotDetailResponse,
    CostSnapshotResponse,
)
from backend.networks.ors import OrsRequestError
from backend.networks.snapshots import (
    CostSnapshotMetadata,
    create_snapshot,
    get_snapshot_metadata,
    list_snapshots,
)

router = APIRouter(prefix="/cost-snapshots", tags=["cost snapshots"])


@router.post("", response_model=CostSnapshotDetailResponse, status_code=201)
def create(payload: CostSnapshotCreateRequest) -> dict:
    try:
        return asdict(create_snapshot(payload.dataset_version_id, payload.profile))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except OrsRequestError as error:
        status = 503 if error.status_code in {None, 429, 503} else 502
        raise HTTPException(status_code=status, detail=str(error)) from error


@router.get("", response_model=list[CostSnapshotResponse])
def snapshots(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[dict]:
    return [_summary(snapshot) for snapshot in list_snapshots(limit)]


@router.get("/{snapshot_id}", response_model=CostSnapshotDetailResponse)
def snapshot(snapshot_id: str) -> dict:
    found = get_snapshot_metadata(snapshot_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Cost snapshot not found")
    return asdict(found)


def _summary(metadata: CostSnapshotMetadata) -> dict:
    values = asdict(metadata)
    values.pop("request")
    return values
