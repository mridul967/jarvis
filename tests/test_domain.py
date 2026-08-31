import numpy as np
import pytest

from backend.vrptw.evaluate import Score, decode, validate_solution
from backend.vrptw.model import Customer, Problem, Route, Solution, Vehicle


def problem(capacity: int = 8, shift_end: float = 100) -> Problem:
    return Problem(
        name="tiny",
        depot=Customer(0, 0, 0, 0, 0, 100, 0),
        customers=(
            Customer(1, 3, 4, 4, 10, 20, 5),
            Customer(2, 6, 8, 4, 0, 50, 0),
        ),
        vehicles=(Vehicle(0, capacity, 0, shift_end),),
    )


def test_validator_recomputes_waiting_load_distance_and_coverage() -> None:
    result = validate_solution(problem(), Solution((Route(0, (1, 2)),)))

    assert result.feasible
    assert result.score == Score(0, 0, 1, 0, 20, 20, 0)
    assert result.route_evaluations[0].load == 8


def test_validator_reports_missing_duplicate_and_unknown_visits() -> None:
    result = validate_solution(problem(), Solution((Route(0, (1, 1, 99)),)))

    assert not result.feasible
    assert result.score.coverage_errors == 3


def test_validator_reports_capacity_and_vehicle_shift_violations() -> None:
    result = validate_solution(
        problem(capacity=7, shift_end=25),
        Solution((Route(0, (1, 2)),)),
    )

    assert result.score.hard_violations == 2
    assert result.score.lateness == 5


def test_score_uses_direct_lexicographic_order() -> None:
    feasible_long = Score(0, 0, 2, 0, 100, 100)
    infeasible_short = Score(1, 0, 1, 0, 1, 1)

    assert feasible_long < infeasible_short


def test_problem_rejects_non_finite_node_values() -> None:
    with pytest.raises(ValueError, match="finite"):
        Problem(
            name="bad",
            depot=Customer(0, float("nan"), 0, 0, 0, 10, 0),
            customers=(Customer(1, 1, 1, 1, 0, 10, 0),),
            vehicles=(Vehicle(0, 1, 0, 10),),
        )


def test_decoder_skips_a_vehicle_that_cannot_serve_a_customer() -> None:
    instance = Problem(
        name="heterogeneous",
        depot=Customer(0, 0, 0, 0, 0, 100, 0),
        customers=(Customer(1, 1, 0, 5, 0, 100, 0),),
        vehicles=(Vehicle(0, 3, 0, 100), Vehicle(1, 5, 0, 100)),
    )

    result = decode(instance, np.array([0.5]))

    assert result.feasible
    assert result.solution.routes == (Route(1, (1,)),)
