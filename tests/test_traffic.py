from dataclasses import asdict, replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.core.artifacts as artifacts_module
import backend.core.database as database_module
from backend.core.config import Settings
from backend.main import app
from backend.networks.snapshots import CostSnapshot
from backend.traffic.costs import (
    Costs,
    MissingTrafficDataError,
    UnreachableArcError,
    assign_congestion,
    evaluate_solution,
)
from backend.traffic.model import ArcCongestion, ArcMultiplier, EndogenousTraffic, ExogenousTraffic
from backend.traffic.service import create_scenario, load_scenario
from backend.vrptw.model import Customer, Problem, Route, Solution, Vehicle


@pytest.fixture
def traffic_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(
        environment="test",
        database_path=tmp_path / "test.db",
        artifact_root=tmp_path / "artifacts",
        allowed_origins=("http://localhost:3000",),
    )
    monkeypatch.setattr(database_module, "settings", settings)
    monkeypatch.setattr(artifacts_module, "settings", settings)
    return settings


def test_static_exogenous_endogenous_and_combined_costs() -> None:
    static = Costs(snapshot())
    exogenous = Costs(snapshot(), exogenous=exogenous_traffic())
    endogenous = Costs(snapshot(), endogenous=endogenous_traffic(capacity=10))
    combined = Costs(
        snapshot(),
        exogenous=exogenous_traffic(),
        endogenous=endogenous_traffic(capacity=10),
    )
    assert static.distance(0, 1) == 100
    assert static.travel_time(0, 1, 0) == 10
    assert static.travel_time(0, 1, 0) != static.travel_time(1, 0, 0)
    assert exogenous.travel_time(1, 2, 10) == 20
    assert endogenous.travel_time(0, 1, 0, flow=0) == 10
    assert endogenous.travel_time(0, 1, 0, flow=10) == pytest.approx(11.5)
    assert combined.travel_time(1, 2, 10, flow=10) == pytest.approx(23)
    solution = Solution((Route(0, (1, 2)),))
    flows = {(0, 1, 0): 10.0, (1, 2, 0): 10.0, (2, 0, 0): 10.0}
    evaluations = (
        evaluate_solution(problem(), solution, static),
        evaluate_solution(problem(), solution, exogenous),
        evaluate_solution(problem(), solution, endogenous, flows),
        evaluate_solution(problem(), solution, combined, flows),
    )
    assert all(evaluation.feasible for evaluation in evaluations)
    assert len({evaluation.score.travel_time for evaluation in evaluations}) == 4


def test_exogenous_intervals_are_start_inclusive_and_missing_data_fails() -> None:
    costs = Costs(snapshot(), exogenous=exogenous_traffic())
    assert costs.travel_time(1, 2, 9.999) == 10
    assert costs.travel_time(1, 2, 10) == 20
    with pytest.raises(MissingTrafficDataError, match="Missing exogenous"):
        costs.travel_time(0, 2, 10)
    with pytest.raises(MissingTrafficDataError, match="outside"):
        costs.travel_time(1, 2, 1_000)


def test_unreachable_arc_is_preserved_as_failure() -> None:
    base = snapshot()
    unreachable = CostSnapshot(
        **asdict(base) | {"distances": ((0.0, None, 200.0), *base.distances[1:])}
    )
    costs = Costs(unreachable)
    assert costs.reachable(0, 1) is False
    with pytest.raises(UnreachableArcError, match="0 -> 1"):
        costs.distance(0, 1)


def test_schedule_crosses_traffic_interval_boundary() -> None:
    evaluation = evaluate_solution(
        problem(),
        Solution((Route(0, (1, 2)),)),
        Costs(snapshot(), exogenous=exogenous_traffic()),
    )
    assert evaluation.feasible
    assert evaluation.traversals[0].departure == 0
    assert evaluation.traversals[1].departure == 10
    assert evaluation.traversals[1].arrival == 30
    assert evaluation.score.travel_time == 92
    assert evaluation.score.congestion == 41


def test_closed_loop_bpr_assignment_is_bounded_and_converges() -> None:
    costs = Costs(snapshot(), endogenous=endogenous_traffic(capacity=1, alpha=1, beta=1))
    result = assign_congestion(problem(), Solution((Route(0, (1, 2)),)), costs)
    assert result.converged
    assert result.rounds == 2
    assert result.residual == 0
    assert result.evaluation.score.travel_time == 102
    assert set(result.flows.values()) == {1.0}


def test_closed_loop_reports_non_convergence_at_the_declared_limit() -> None:
    traffic = replace(endogenous_traffic(capacity=1, alpha=1, beta=1), max_rounds=1)
    result = assign_congestion(
        problem(),
        Solution((Route(0, (1, 2)),)),
        Costs(snapshot(), endogenous=traffic),
    )
    assert result.converged is False
    assert result.rounds == 1
    assert result.residual == 1


def test_traffic_validation_rejects_gaps_and_bad_bpr_parameters() -> None:
    with pytest.raises(ValueError, match="full horizon"):
        ExogenousTraffic(
            source_type="simulated",
            timezone="Asia/Kolkata",
            horizon_start=0,
            horizon_end=100,
            intervals=(ArcMultiplier(0, 1, 10, 100, 1),),
            source="test",
        )
    with pytest.raises(ValueError, match="capacity > 0"):
        ArcCongestion(0, 1, 0, 0.15, 4)


def test_scenarios_are_immutable_and_available_through_api(traffic_storage: Settings) -> None:
    exogenous = exogenous_traffic()
    endogenous = endogenous_traffic(capacity=10)
    first = create_scenario("rush-hour", exogenous, endogenous)
    second = create_scenario("rush-hour", exogenous, endogenous)
    restored_exogenous, restored_endogenous = load_scenario(first.scenario_id)
    assert first.scenario_id == second.scenario_id
    assert first.mode == "combined"
    assert restored_exogenous == exogenous
    assert restored_endogenous == endogenous

    payload = {
        "name": "rush-hour-api",
        "exogenous": asdict(exogenous),
        "endogenous": asdict(endogenous),
    }
    with TestClient(app) as client:
        validated = client.post("/api/v1/traffic/scenarios/validate", json=payload)
        created = client.post("/api/v1/traffic/scenarios", json=payload)
        listed = client.get("/api/v1/traffic/scenarios")
        detail = client.get(f"/api/v1/traffic/scenarios/{created.json()['scenario_id']}")
    assert validated.json()["valid"] is True
    assert validated.json()["content_sha256"] == created.json()["scenario_id"]
    assert len(listed.json()) == 2
    assert detail.json()["content"]["mode"] == "combined"


def snapshot() -> CostSnapshot:
    return CostSnapshot(
        snapshot_id="snapshot",
        dataset_version_id="dataset",
        profile="driving-car",
        node_ids=(0, 1, 2),
        distances=((0.0, 100.0, 200.0), (110.0, 0.0, 100.0), (210.0, 120.0, 0.0)),
        durations=((0.0, 10.0, 30.0), (11.0, 0.0, 10.0), (31.0, 12.0, 0.0)),
        attribution="openrouteservice.org | OpenStreetMap contributors",
    )


def problem() -> Problem:
    depot = Customer(0, 77.1, 28.6, 0, 0, 1_000, 0)
    return Problem(
        name="traffic-test",
        depot=depot,
        customers=(
            Customer(1, 77.2, 28.7, 1, 0, 1_000, 0),
            Customer(2, 77.3, 28.7, 1, 0, 1_000, 0),
        ),
        vehicles=(Vehicle(0, 10, 0, 1_000),),
    )


def exogenous_traffic() -> ExogenousTraffic:
    intervals = tuple(
        ArcMultiplier(origin, destination, start, end, multiplier)
        for origin, destination in ((0, 1), (1, 2), (2, 0))
        for start, end, multiplier in ((0, 10, 1), (10, 1_000, 2))
    )
    return ExogenousTraffic(
        source_type="simulated",
        timezone="Asia/Kolkata",
        horizon_start=0,
        horizon_end=1_000,
        intervals=intervals,
        source="phase-3-test",
        generator_seed=7,
        generator_parameters={"peak_multiplier": 2.0},
    )


def endogenous_traffic(
    capacity: float,
    alpha: float = 0.15,
    beta: float = 4,
) -> EndogenousTraffic:
    return EndogenousTraffic(
        arcs=tuple(
            ArcCongestion(origin, destination, capacity, alpha, beta)
            for origin, destination in ((0, 1), (1, 2), (2, 0))
        ),
        flow_unit="vehicles_per_interval",
        interval_seconds=1_000,
        assignment_rule="simultaneous_vehicle_count",
        tolerance=0,
        max_rounds=5,
    )
