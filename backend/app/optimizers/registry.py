from collections.abc import Callable
from time import perf_counter
from typing import Literal

from backend.app.optimizers.model import (
    CancelCheck,
    EvaluationBudget,
    SolverParameters,
    SolverResult,
)
from backend.app.optimizers.swarm import optimize
from backend.vrptw.evaluate import decode_solution, objective, validate_solution
from backend.vrptw.model import Problem, Solution
from backend.app.optimizers.sbm import solve_sbm


Algorithm = Literal["pso", "qpso", "sbm"]
Solver = Callable[
    [Problem, SolverParameters, int, EvaluationBudget, Solution | None, CancelCheck | None],
    SolverResult,
]


def _solve_swarm(
    algorithm: Algorithm,
    problem: Problem,
    parameters: SolverParameters,
    seed: int,
    budget: EvaluationBudget,
    warm_start: Solution | None,
    should_cancel: CancelCheck | None,
) -> SolverResult:
    if warm_start is not None:
        raise ValueError("Warm starts are not implemented in Phase 1")
    started = perf_counter()
    result = optimize(
        objective=lambda keys: objective(problem, keys),
        dimension=len(problem.customers),
        algorithm=algorithm,
        population_size=parameters.population_size,
        iterations=parameters.iterations,
        seed=seed,
        budget=budget,
        should_cancel=should_cancel,
    )
    evaluation = validate_solution(problem, decode_solution(problem, result.best_position))
    return SolverResult(
        algorithm=algorithm,
        algorithm_version="1.0.0",
        parameters=parameters,
        seed=seed,
        budget=budget,
        evaluation=evaluation,
        convergence=result.convergence,
        evaluations=result.evaluations,
        runtime_ms=round((perf_counter() - started) * 1_000, 2),
        cancelled=result.cancelled,
    )


def solve_pso(
    problem: Problem,
    parameters: SolverParameters,
    seed: int,
    budget: EvaluationBudget,
    warm_start: Solution | None = None,
    should_cancel: CancelCheck | None = None,
) -> SolverResult:
    return _solve_swarm("pso", problem, parameters, seed, budget, warm_start, should_cancel)


def solve_qpso(
    problem: Problem,
    parameters: SolverParameters,
    seed: int,
    budget: EvaluationBudget,
    warm_start: Solution | None = None,
    should_cancel: CancelCheck | None = None,
) -> SolverResult:
    return _solve_swarm("qpso", problem, parameters, seed, budget, warm_start, should_cancel)


SOLVERS: dict[Algorithm, Solver] = {"pso": solve_pso, "qpso": solve_qpso, "sbm": solve_sbm}


def get_solver(algorithm: Algorithm) -> Solver:
    return SOLVERS[algorithm]
