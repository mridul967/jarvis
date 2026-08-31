import json
from pathlib import Path
from urllib.error import HTTPError

import pytest
from fastapi.testclient import TestClient

import backend.core.artifacts as artifacts_module
import backend.core.database as database_module
import backend.networks.ors as ors_module
import backend.networks.snapshots as snapshots_module
from backend.core.artifacts import read_artifact
from backend.core.config import Settings
from backend.datasets.model import DatasetImport
from backend.datasets.service import import_dataset
from backend.main import app
from backend.networks.ors import OrsRequestError, fetch_matrix, matrix_blocks
from backend.networks.snapshots import create_snapshot, load_snapshot


@pytest.fixture
def network_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(
        environment="test",
        database_path=tmp_path / "test.db",
        artifact_root=tmp_path / "artifacts",
        allowed_origins=("http://localhost:3000",),
        ors_api_key="secret-key",
        ors_base_url="https://api.openrouteservice.org",
        ors_matrix_max_routes=4,
        ors_timeout_seconds=2,
    )
    monkeypatch.setattr(database_module, "settings", settings)
    monkeypatch.setattr(artifacts_module, "settings", settings)
    monkeypatch.setattr(ors_module, "settings", settings)
    monkeypatch.setattr(snapshots_module, "settings", settings)
    return settings


def test_matrix_blocks_never_exceed_declared_route_limit() -> None:
    blocks = matrix_blocks(10, 9)
    assert len(blocks) == 16
    assert all(len(sources) * len(destinations) <= 9 for sources, destinations in blocks)
    assert {index for sources, _ in blocks for index in sources} == set(range(10))
    assert {index for _, destinations in blocks for index in destinations} == set(range(10))


def test_ors_uses_authorization_header_and_preserves_null(
    network_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_: object) -> None:
            return None

        def read(self) -> bytes:
            return json.dumps(
                {
                    "distances": [[0, None]],
                    "durations": [[0, None]],
                    "metadata": {
                        "attribution": "openrouteservice.org | OpenStreetMap contributors"
                    },
                }
            ).encode()

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(ors_module, "urlopen", fake_urlopen)
    response = fetch_matrix("driving-car", [(77.1, 28.6), (77.2, 28.7)], (0,), (0, 1))
    request = captured["request"]
    assert request.get_header("Authorization") == network_settings.ors_api_key
    assert network_settings.ors_api_key not in request.full_url
    assert network_settings.ors_api_key.encode() not in request.data
    assert captured["timeout"] == 2
    assert response["durations"][0][1] is None


@pytest.mark.parametrize("status", [400, 403, 413, 429, 503])
def test_ors_http_errors_are_safe_and_typed(
    status: int, network_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(*_: object, **__: object):
        raise HTTPError("https://api.openrouteservice.org", status, "failure", {}, None)

    monkeypatch.setattr(ors_module, "urlopen", fail)
    with pytest.raises(OrsRequestError) as captured:
        fetch_matrix("driving-car", [(77.1, 28.6)], (0,), (0,))
    assert captured.value.status_code == status
    assert network_settings.ors_api_key not in str(captured.value)


def test_ors_timeout_is_not_retried(
    network_settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    def timeout(*_: object, **__: object):
        nonlocal calls
        calls += 1
        raise TimeoutError

    monkeypatch.setattr(ors_module, "urlopen", timeout)
    with pytest.raises(OrsRequestError, match="timed out"):
        fetch_matrix("driving-car", [(77.1, 28.6)], (0,), (0,))
    assert calls == 1


def test_snapshot_reassembles_blocks_and_contains_no_secret(network_settings: Settings) -> None:
    dataset = import_dataset(geographic_dataset())

    def fake_fetch(profile, locations, sources, destinations):
        assert profile == "driving-car"
        return {
            "distances": [
                [
                    None if (source, destination) == (3, 1) else abs(source - destination) * 100.0
                    for destination in destinations
                ]
                for source in sources
            ],
            "durations": [
                [
                    None if (source, destination) == (3, 1) else source * 10.0 + destination
                    for destination in destinations
                ]
                for source in sources
            ],
            "metadata": {
                "attribution": "openrouteservice.org | OpenStreetMap contributors",
                "engine": {"version": "test"},
            },
        }

    metadata = create_snapshot(dataset.version_id, "driving-car", fake_fetch)
    snapshot = load_snapshot(metadata.snapshot_id)
    assert metadata.block_count == 4
    assert metadata.unreachable_count == 1
    assert snapshot.durations[1][2] == 12
    assert snapshot.durations[2][1] == 21
    assert snapshot.durations[3][1] is None
    raw = read_artifact(metadata.raw_artifact, metadata.raw_sha256)
    assert network_settings.ors_api_key.encode() not in raw
    assert "Authorization" not in metadata.request
    with TestClient(app) as client:
        listed = client.get("/api/v1/cost-snapshots")
        detail = client.get(f"/api/v1/cost-snapshots/{metadata.snapshot_id}")
    assert listed.json()[0]["snapshot_id"] == metadata.snapshot_id
    assert "request" not in listed.json()[0]
    assert detail.json()["request"]["profile"] == "driving-car"


def test_snapshot_rejects_non_geographic_dataset(network_settings: Settings) -> None:
    from backend.vrptw.sample import SAMPLE_SOLOMON

    dataset = import_dataset(
        DatasetImport(
            format="solomon_text",
            filename="C101-mini.txt",
            content=SAMPLE_SOLOMON,
            family="solomon",
        )
    )
    with pytest.raises(ValueError, match="WGS84"):
        create_snapshot(dataset.version_id, "driving-car", lambda *_: {})


def test_snapshot_rejects_customer_that_cannot_be_reached(network_settings: Settings) -> None:
    dataset = import_dataset(geographic_dataset())

    def unreachable(_, locations, sources, destinations):
        return {
            "distances": [
                [None if (source, destination) == (0, 1) else 1 for destination in destinations]
                for source in sources
            ],
            "durations": [
                [None if (source, destination) == (0, 1) else 1 for destination in destinations]
                for source in sources
            ],
            "metadata": {"attribution": "openrouteservice.org | OpenStreetMap contributors"},
        }

    with pytest.raises(ValueError, match="impossible to serve alone with ORS"):
        create_snapshot(dataset.version_id, "driving-car", unreachable)


def geographic_dataset() -> DatasetImport:
    nodes = [
        {"id": 1, "x": 77.2, "y": 28.7, "demand": 1, "ready": 0, "due": 1_000, "service": 0},
        {"id": 2, "x": 77.3, "y": 28.7, "demand": 1, "ready": 0, "due": 1_000, "service": 0},
        {"id": 3, "x": 77.4, "y": 28.7, "demand": 1, "ready": 0, "due": 1_000, "service": 0},
    ]
    payload = {
        "schema_version": 1,
        "name": "Delhi-mini",
        "coordinate_system": "wgs84",
        "distance_unit": "metres",
        "time_unit": "seconds",
        "timezone": "Asia/Kolkata",
        "depot": {
            "id": 0,
            "x": 77.1,
            "y": 28.6,
            "demand": 0,
            "ready": 0,
            "due": 1_000,
            "service": 0,
        },
        "customers": nodes,
        "vehicles": [
            {
                "id": 0,
                "capacity": 10,
                "shift_start": 0,
                "shift_end": 1_000,
                "start_node": 0,
                "end_node": 0,
                "fixed_cost": 0,
            }
        ],
    }
    return DatasetImport(
        format="canonical_json",
        filename="delhi-mini.json",
        content=json.dumps(payload),
        family="geographic",
    )
