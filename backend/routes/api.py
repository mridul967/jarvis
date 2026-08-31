from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.runs.db import list_runs, save_run
from backend.vrptw.sample import SAMPLE_SOLOMON
from backend.vrptw.service import solve_text

router = APIRouter()


class SolveRequest(BaseModel):
    algorithm: Literal["pso", "qpso"] = "qpso"
    population_size: int = Field(30, ge=5, le=200)
    iterations: int = Field(80, ge=1, le=2_000)
    seed: int = 42
    instance: str | None = None


@router.get("/instances/sample")
def sample_instance() -> dict[str, str]:
    return {"name": "C101-mini", "content": SAMPLE_SOLOMON}


@router.post("/solve")
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


@router.get("/runs")
def runs() -> list[dict]:
    return list_runs()
