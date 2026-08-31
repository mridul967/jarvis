from typing import Literal

from pydantic import BaseModel, Field

Algorithm = Literal["pso", "qpso"]


class SolveRequest(BaseModel):
    algorithm: Algorithm = "qpso"
    population_size: int = Field(30, ge=5, le=200)
    iterations: int = Field(80, ge=1, le=2_000)
    seed: int = 42
    instance: str | None = Field(default=None, min_length=1, max_length=1_000_000)


class SolveParameters(BaseModel):
    population_size: int
    iterations: int
    seed: int


class SolveResponse(BaseModel):
    id: int
    instance: str
    algorithm: Algorithm
    distance: float
    vehicles: int
    feasible: bool
    violations: int
    routes: list[list[int]]
    convergence: list[float]
    evaluations: int
    runtime_ms: float
    parameters: SolveParameters


class RunSummary(BaseModel):
    id: int
    created_at: str
    algorithm: Algorithm
    distance: float
    vehicles: int
    feasible: bool
    runtime_ms: float


class InstanceResponse(BaseModel):
    name: str
    content: str
