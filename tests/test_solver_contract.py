import numpy as np
import pytest

from backend.optimizers.model import EvaluationBudget, SolverParameters
from backend.optimizers.registry import Algorithm, get_solver, solve_qpso
from backend.vrptw.evaluate import decode_solution
from backend.vrptw.parser import parse_solomon
from backend.vrptw.sample import SAMPLE_SOLOMON


def test_solver_obeys_partial_evaluation_budget() -> None:
    result = solve_qpso(
        parse_solomon(SAMPLE_SOLOMON),
        SolverParameters(population_size=5, iterations=10),
        seed=7,
        budget=EvaluationBudget(7),
    )

    assert result.evaluations == 7
    assert result.convergence[-1].evaluations == 7
    assert all(
        later.score <= earlier.score
        for earlier, later in zip(result.convergence, result.convergence[1:], strict=False)
    )


def test_solver_cancellation_stops_after_initial_population() -> None:
    result = solve_qpso(
        parse_solomon(SAMPLE_SOLOMON),
        SolverParameters(population_size=5, iterations=10),
        seed=7,
        budget=EvaluationBudget(55),
        should_cancel=lambda: True,
    )

    assert result.cancelled
    assert result.evaluations == 5


@pytest.mark.parametrize("algorithm", ["pso", "qpso"])
def test_solver_is_deterministic_for_a_fixed_seed(algorithm: Algorithm) -> None:
    instance = parse_solomon(SAMPLE_SOLOMON)
    solve = get_solver(algorithm)
    arguments = (
        instance,
        SolverParameters(population_size=5, iterations=2),
        7,
        EvaluationBudget(15),
    )

    first = solve(*arguments)
    second = solve(*arguments)

    assert first.evaluation == second.evaluation
    assert first.convergence == second.convergence
    assert first.parameters == second.parameters
    assert first.seed == second.seed


def test_phase_one_rejects_unimplemented_warm_start() -> None:
    instance = parse_solomon(SAMPLE_SOLOMON)
    warm_start = decode_solution(instance, keys=np.arange(10))

    with pytest.raises(ValueError, match="Warm starts"):
        solve_qpso(
            instance,
            SolverParameters(population_size=5, iterations=1),
            seed=7,
            budget=EvaluationBudget(10),
            warm_start=warm_start,
        )
