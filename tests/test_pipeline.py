import numpy as np
from fastapi.testclient import TestClient

from backend.main import app
from backend.vrptw.evaluate import decode
from backend.vrptw.parser import parse_solomon
from backend.vrptw.sample import SAMPLE_SOLOMON


def test_parser_and_decoder_cover_every_customer_once() -> None:
    instance = parse_solomon(SAMPLE_SOLOMON)
    result = decode(instance, np.arange(len(instance.customers)))
    visited = [customer for route in result.routes for customer in route]
    assert sorted(visited) == list(range(1, 11))
    assert result.feasible


def test_solve_endpoint() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/solve",
            json={"algorithm": "qpso", "population_size": 8, "iterations": 3, "seed": 7},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["algorithm"] == "qpso"
    assert payload["algorithm_version"] == "1.0.0"
    assert payload["feasible"] is True
    assert payload["score"]["hard_violations"] == 0
    assert payload["convergence_points"][-1]["evaluations"] == payload["evaluations"]
    assert len({item for route in payload["routes"] for item in route}) == 10


def test_health_checks_database() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_run_limit_is_validated() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/runs?limit=0")
    assert response.status_code == 422
