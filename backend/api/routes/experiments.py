from fastapi import APIRouter, HTTPException

from backend.api.schemas import SolveRequest, SolveResponse
from backend.runs.repository import save_run
from backend.vrptw.sample import SAMPLE_SOLOMON
from backend.vrptw.service import solve_text

router = APIRouter(tags=["experiments"])


@router.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest) -> dict:
    try:
        result = solve_text(
            request.instance or SAMPLE_SOLOMON,
            algorithm=request.algorithm,
            population_size=request.population_size,
            iterations=request.iterations,
            seed=request.seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    result["id"] = save_run(result)
    return result
