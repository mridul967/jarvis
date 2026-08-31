from time import perf_counter
from typing import Literal

from backend.optimizers.swarm import optimize
from backend.vrptw.evaluate import decode, objective
from backend.vrptw.parser import parse_solomon


def solve_text(
    text: str,
    algorithm: Literal["pso", "qpso"],
    population_size: int,
    iterations: int,
    seed: int,
) -> dict:
    instance = parse_solomon(text)
    started = perf_counter()
    result = optimize(
        objective=lambda keys: objective(instance, keys),
        dimension=len(instance.customers),
        algorithm=algorithm,
        population_size=population_size,
        iterations=iterations,
        seed=seed,
    )
    evaluation = decode(instance, result.best_position)
    return {
        "instance": instance.name,
        "algorithm": algorithm,
        "distance": evaluation.distance,
        "vehicles": len(evaluation.routes),
        "feasible": evaluation.feasible,
        "violations": evaluation.violations,
        "routes": [list(route) for route in evaluation.routes],
        "convergence": [round(value, 3) for value in result.convergence],
        "evaluations": result.evaluations,
        "runtime_ms": round((perf_counter() - started) * 1_000, 2),
        "parameters": {
            "population_size": population_size,
            "iterations": iterations,
            "seed": seed,
        },
    }
