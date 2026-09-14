from typing import Literal

from backend.app.optimizers.model import EvaluationBudget, SolverParameters
from backend.app.optimizers.registry import get_solver
from backend.vrptw.evaluate import Score
from backend.vrptw.parser import parse_solomon


def solve_text(
    text: str,
    algorithm: Literal["pso", "qpso"],
    population_size: int,
    iterations: int,
    seed: int,
) -> dict:
    problem = parse_solomon(text)
    parameters = SolverParameters(population_size=population_size, iterations=iterations)
    result = get_solver(algorithm)(
        problem,
        parameters,
        seed,
        EvaluationBudget(max_evaluations=population_size * (iterations + 1)),
        None,
        None,
    )
    evaluation = result.evaluation
    score = evaluation.score
    return {
        "instance": problem.name,
        "algorithm": algorithm,
        "algorithm_version": result.algorithm_version,
        "distance": round(score.distance, 3),
        "vehicles": score.vehicles,
        "feasible": evaluation.feasible,
        "violations": evaluation.violations,
        "routes": [list(route) for route in evaluation.routes],
        # Keep the old distance series for the current chart; selection uses Score.
        "convergence": [round(point.score.distance, 3) for point in result.convergence],
        "convergence_points": [
            {"evaluations": point.evaluations, "score": _score_dict(point.score)}
            for point in result.convergence
        ],
        "score": _score_dict(score),
        "evaluations": result.evaluations,
        "runtime_ms": result.runtime_ms,
        "parameters": {
            "population_size": population_size,
            "iterations": iterations,
            "seed": seed,
        },
    }


def _score_dict(score: Score) -> dict:
    return {
        "hard_violations": score.hard_violations,
        "coverage_errors": score.coverage_errors,
        "vehicles": score.vehicles,
        "lateness": round(score.lateness, 3),
        "travel_time": round(score.travel_time, 3),
        "distance": round(score.distance, 3),
        "congestion": round(score.congestion, 3),
    }
