from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_demo_catalog_exposes_notebook_portfolio() -> None:
    response = client.get("/api/v1/demo/algorithms")
    assert response.status_code == 200
    ids = {item["id"] for item in response.json()}
    assert {"qpso", "qrg_qpso", "admr_qpso", "qaco_full", "dynamic_qaco", "ortools"} <= ids


def test_demo_scenario_is_a_historical_derived_graph() -> None:
    response = client.get("/api/v1/demo/scenario?traffic=incident")
    assert response.status_code == 200
    graph = response.json()
    assert graph["source_type"] == "historical-derived simulation"
    assert len(graph["nodes"]) == 16
    assert len(graph["edges"]) > len(graph["nodes"])
    assert any(edge["shocked"] for edge in graph["edges"])


def test_demo_run_returns_a_validated_complete_solution() -> None:
    response = client.post(
        "/api/v1/demo/run",
        json={
            "algorithm": "qaco_full",
            "traffic": "incident",
            "gat_enabled": False,
            "population_size": 4,
            "iterations": 2,
            "seed": 7,
        },
    )
    assert response.status_code == 200
    result = response.json()["result"]
    visited = [customer for route in result["routes"] for customer in route]
    assert result["feasible"] is True
    assert sorted(visited) == list(range(1, 16))
    assert result["score"]["coverage_errors"] == 0
    assert result["score"]["hard_violations"] == 0
    assert len(result["route_paths"]) == len(result["routes"])
    assert all(path[0] == 0 and path[-1] == 0 for path in result["route_paths"])


def test_demo_benchmark_uses_shared_run_contract() -> None:
    response = client.post(
        "/api/v1/demo/benchmark",
        json={
            "algorithms": ["nearest_neighbor", "qpso", "qaco_full"],
            "traffic": "peak",
            "gat_enabled": False,
            "population_size": 4,
            "iterations": 2,
            "seed": 11,
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["rows"]) == 3
    assert all(row["feasible"] for row in payload["rows"])
    assert {row["algorithm"]["id"] for row in payload["rows"]} == {
        "nearest_neighbor",
        "qpso",
        "qaco_full",
    }
