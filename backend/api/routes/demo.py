from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.demo import algorithm_catalog, run_benchmark, run_demo, scenario_response

router = APIRouter(prefix="/demo", tags=["research-demo"])


class DemoRunRequest(BaseModel):
    algorithm: str = "qaco_full"
    traffic: Literal["normal", "peak", "incident", "volatility"] = "incident"
    gat_enabled: bool = True
    population_size: int = Field(12, ge=4, le=60)
    iterations: int = Field(30, ge=1, le=300)
    seed: int = 42


class DemoBenchmarkRequest(BaseModel):
    algorithms: list[str] = Field(default_factory=list, max_length=20)
    traffic: Literal["normal", "peak", "incident", "volatility"] = "incident"
    gat_enabled: bool = True
    population_size: int = Field(12, ge=4, le=60)
    iterations: int = Field(30, ge=1, le=300)
    seed: int = 42


@router.get("/algorithms")
def algorithms() -> list[dict]:
    return algorithm_catalog()


@router.get("/scenario")
def scenario(
    traffic: Literal["normal", "peak", "incident", "volatility"] = "normal",
) -> dict:
    return scenario_response(traffic)


from backend.app.services.or_tools import run_dynamic_or_tools
import os

@router.post("/run")
def run(request: DemoRunRequest) -> dict:
    try:
        if request.algorithm == "dynamic_ors":
            matrix_limit = int(os.getenv("ORS_MATRIX_LIMIT", "4"))
            return run_dynamic_or_tools(matrix_limit, request.traffic, request.seed)
            
        return run_demo(
            algorithm=request.algorithm,
            traffic=request.traffic,
            gat_enabled=request.gat_enabled,
            population_size=request.population_size,
            iterations=request.iterations,
            seed=request.seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.post("/benchmark")
def benchmark(request: DemoBenchmarkRequest) -> dict:
    try:
        return run_benchmark(
            algorithms=request.algorithms,
            traffic=request.traffic,
            gat_enabled=request.gat_enabled,
            population_size=request.population_size,
            iterations=request.iterations,
            seed=request.seed,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
