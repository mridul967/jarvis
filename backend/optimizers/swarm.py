from dataclasses import dataclass
from typing import Callable, Literal

import numpy as np

Objective = Callable[[np.ndarray], float]


@dataclass(frozen=True)
class SwarmResult:
    best_position: np.ndarray
    best_fitness: float
    convergence: list[float]
    evaluations: int


def optimize(
    objective: Objective,
    dimension: int,
    algorithm: Literal["pso", "qpso"],
    population_size: int,
    iterations: int,
    seed: int,
) -> SwarmResult:
    rng = np.random.default_rng(seed)
    positions = rng.random((population_size, dimension))
    personal_best = positions.copy()
    personal_fitness = np.array([objective(item) for item in positions])
    evaluations = population_size
    best_index = int(np.argmin(personal_fitness))
    global_best = personal_best[best_index].copy()
    global_fitness = float(personal_fitness[best_index])
    convergence = [global_fitness]
    velocities = rng.uniform(-1, 1, size=positions.shape)

    for iteration in range(iterations):
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

        fitness = np.array([objective(item) for item in positions])
        evaluations += population_size
        improved = fitness < personal_fitness
        personal_best[improved] = positions[improved]
        personal_fitness[improved] = fitness[improved]
        best_index = int(np.argmin(personal_fitness))
        if personal_fitness[best_index] < global_fitness:
            global_best = personal_best[best_index].copy()
            global_fitness = float(personal_fitness[best_index])
        convergence.append(global_fitness)

    return SwarmResult(global_best, global_fitness, convergence, evaluations)
