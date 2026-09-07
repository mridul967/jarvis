from collections.abc import Callable
from dataclasses import dataclass

from backend.vrptw.evaluate import Evaluation, Score


@dataclass(frozen=True)
class SolverParameters:
    population_size: int
    iterations: int


@dataclass(frozen=True)
class EvaluationBudget:
    max_evaluations: int

    def __post_init__(self) -> None:
        if self.max_evaluations <= 0:
            raise ValueError("Evaluation budget must be positive")


@dataclass(frozen=True)
class ConvergencePoint:
    evaluations: int
    score: Score


@dataclass(frozen=True)
class SolverResult:
    algorithm: str
    algorithm_version: str
    parameters: SolverParameters
    seed: int
    budget: EvaluationBudget
    evaluation: Evaluation
    convergence: tuple[ConvergencePoint, ...]
    evaluations: int
    runtime_ms: float
    cancelled: bool


CancelCheck = Callable[[], bool]
