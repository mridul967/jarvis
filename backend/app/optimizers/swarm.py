from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal

import numpy as np

from backend.optimizers.model import CancelCheck, ConvergencePoint, EvaluationBudget
from backend.vrptw.evaluate import Score

Objective = Callable[[np.ndarray], Score]


@dataclass(frozen=True)
class SwarmResult:
    best_position: np.ndarray
    best_fitness: Score
    convergence: tuple[ConvergencePoint, ...]
    evaluations: int
    cancelled: bool


def optimize(
    objective: Objective,
    dimension: int,
    algorithm: Literal["pso", "qpso"],
    population_size: int,
    iterations: int,
    seed: int,
    budget: EvaluationBudget,
    should_cancel: CancelCheck | None = None,
) -> SwarmResult:
    if budget.max_evaluations < population_size:
        raise ValueError("Evaluation budget must cover the initial population")
    rng = np.random.default_rng(seed)
    positions = rng.random((population_size, dimension))
    personal_best = positions.copy()
    personal_fitness = [objective(item) for item in positions]
    evaluations = population_size
    best_index = min(range(population_size), key=personal_fitness.__getitem__)
    global_best = personal_best[best_index].copy()
    global_fitness = personal_fitness[best_index]
    convergence = [ConvergencePoint(evaluations, global_fitness)]
    velocities = rng.uniform(-1, 1, size=positions.shape)
    cancelled = False

    for iteration in range(iterations):
        if should_cancel and should_cancel():
            cancelled = True
            break
        remaining = budget.max_evaluations - evaluations
        if remaining <= 0:
            break
        if algorithm == "pso":
            r1, r2 = rng.random(positions.shape), rng.random(positions.shape)
            velocities = (
                0.729 * velocities
                + 1.49445 * r1 * (personal_best - positions)
                + 1.49445 * r2 * (global_best - positions)
            )
            positions = np.clip(positions + np.clip(velocities, -1, 1), 0, 1)
        else:
            mbest = personal_best.mean(axis=0)
            phi = rng.random(positions.shape)
            attractor = phi * personal_best + (1 - phi) * global_best
            u = rng.uniform(np.finfo(float).eps, 1, size=positions.shape)
            beta = 1.0 - 0.5 * iteration / max(iterations, 1)
            step = beta * np.abs(mbest - positions) * np.log(1 / u)
            positions = np.clip(
                np.where(rng.random(positions.shape) < 0.5, attractor - step, attractor + step),
                0,
                1,
            )

        batch_size = min(population_size, remaining)
        fitness = [objective(item) for item in positions[:batch_size]]
        evaluations += batch_size
        for index, score in enumerate(fitness):
            if score < personal_fitness[index]:
                personal_best[index] = positions[index]
                personal_fitness[index] = score
        best_index = min(range(population_size), key=personal_fitness.__getitem__)
        if personal_fitness[best_index] < global_fitness:
            global_best = personal_best[best_index].copy()
            global_fitness = personal_fitness[best_index]
        convergence.append(ConvergencePoint(evaluations, global_fitness))

    return SwarmResult(
        global_best,
        global_fitness,
        tuple(convergence),
        evaluations,
        cancelled,
    )
