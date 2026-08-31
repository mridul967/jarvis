import hashlib
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    DatasetImportRequest,
    DatasetValidationResponse,
    DatasetVersionResponse,
)
from backend.datasets.model import DatasetImport
from backend.datasets.repository import get_dataset, list_datasets
from backend.datasets.service import import_dataset, validate_import

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/validate", response_model=DatasetValidationResponse)
def validate_dataset(payload: DatasetImportRequest) -> DatasetValidationResponse:
    try:
        parsed = validate_import(_request(payload))
    except ValueError as error:
        return DatasetValidationResponse(valid=False, errors=[str(error)])
    return DatasetValidationResponse(
        valid=True,
        errors=[],
        name=parsed.problem.name,
        vehicle_count=len(parsed.problem.vehicles),
        customer_count=len(parsed.problem.customers),
        canonical_sha256=hashlib.sha256(parsed.canonical_json.encode("utf-8")).hexdigest(),
    )


@router.post("", response_model=DatasetVersionResponse, status_code=201)
def create_dataset(payload: DatasetImportRequest) -> dict:
    try:
        return asdict(import_dataset(_request(payload)))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[DatasetVersionResponse])
def datasets(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[dict]:
    return [asdict(dataset) for dataset in list_datasets(limit)]


@router.get("/{version_id}", response_model=DatasetVersionResponse)
def dataset(version_id: str) -> dict:
    found = get_dataset(version_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Dataset version not found")
    return asdict(found)


def _request(payload: DatasetImportRequest) -> DatasetImport:
    return DatasetImport(**payload.model_dump())
