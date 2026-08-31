from fastapi import APIRouter

from backend.api.schemas import InstanceResponse
from backend.vrptw.sample import SAMPLE_SOLOMON

router = APIRouter(prefix="/instances", tags=["instances"])


@router.get("/sample", response_model=InstanceResponse)
def sample_instance() -> InstanceResponse:
    return InstanceResponse(name="C101-mini", content=SAMPLE_SOLOMON)
