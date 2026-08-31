import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import backend.core.artifacts as artifacts_module
import backend.core.database as database_module
from backend.core.config import Settings
from backend.datasets.importers import parse_dataset
from backend.datasets.model import DatasetImport
from backend.datasets.service import MAX_DATASET_BYTES, import_dataset
from backend.main import app
from backend.vrptw.sample import SAMPLE_SOLOMON

CSV_HEADER = "CUST NO.,XCOORD.,YCOORD.,DEMAND,READY TIME,DUE DATE,SERVICE TIME\n"
CSV_ROWS = "1,40,50,0,0,500,0\n2,45,50,10,0,200,10\n3,50,50,20,0,220,10\n"


@pytest.fixture
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Settings:
    settings = Settings(
        environment="test",
        database_path=tmp_path / "test.db",
        artifact_root=tmp_path / "artifacts",
        allowed_origins=("http://localhost:3000",),
    )
    monkeypatch.setattr(database_module, "settings", settings)
    monkeypatch.setattr(artifacts_module, "settings", settings)
    return settings


def csv_request(content: str = CSV_HEADER + CSV_ROWS, **changes: object) -> DatasetImport:
    values: dict[str, object] = {
        "format": "solomon_csv",
        "filename": "C101.csv",
        "content": content,
        "family": "solomon",
        "name": "C101",
        "vehicle_count": 25,
        "capacity": 200,
        "depot_id": 1,
        "coordinate_system": "euclidean",
        "distance_unit": "coordinate_units",
        "time_unit": "coordinate_units",
    }
    values.update(changes)
    return DatasetImport(**values)  # type: ignore[arg-type]


def test_native_text_and_csv_normalize_to_canonical_models() -> None:
    text = parse_dataset(
        DatasetImport(
            format="solomon_text",
            filename="C101-mini.txt",
            content=SAMPLE_SOLOMON,
            family="solomon",
        )
    )
    csv = parse_dataset(csv_request())
    assert text.problem.name == "C101-mini"
    assert len(text.problem.customers) == 10
    assert csv.problem.depot.id == 0
    assert [customer.id for customer in csv.problem.customers] == [2, 3]
    assert json.loads(csv.canonical_json)["schema_version"] == 1


@pytest.mark.parametrize(
    ("filename", "capacity"),
    [
        ("C101.csv", 200),
        ("C201.csv", 700),
        ("R101.csv", 200),
        ("R201.csv", 1_000),
        ("RC101.csv", 200),
        ("RC201.csv", 1_000),
    ],
)
def test_all_practice_dataset_families(filename: str, capacity: int) -> None:
    path = Path("/Users/vinodpandey/practice concepts/data/solomon_instances") / filename
    if not path.exists():
        pytest.skip("optional practice-concepts fixtures are not present")
    parsed = parse_dataset(
        csv_request(
            path.read_text(encoding="utf-8"),
            filename=filename,
            name=path.stem,
            capacity=capacity,
        )
    )
    assert len(parsed.problem.customers) == 100
    assert len(parsed.problem.vehicles) == 25


def test_csv_accepts_harmless_header_variations() -> None:
    content = (
        " customer_id , x_coordinate , y_coordinate , demand , earliest , latest , service_duration\n"
        "1,40,50,0,0,500,0\n2,45,50,10,0,200,10\n"
    )
    assert len(parse_dataset(csv_request(content)).problem.customers) == 1


@pytest.mark.parametrize(
    ("import_request", "message"),
    [
        (
            DatasetImport(
                format="solomon_csv",
                filename="bad.csv",
                content=CSV_HEADER + CSV_ROWS,
                family="solomon",
            ),
            "requires vehicle_count, capacity, and depot_id",
        ),
        (csv_request(depot_id=99), "exactly one row"),
        (csv_request(content=CSV_HEADER + CSV_ROWS + "2,55,50,10,0,250,10\n"), "unique"),
        (
            csv_request(content=CSV_HEADER + "1,40,50,0,0,500,0\n2,45,50,10,300,200,10\n"),
            "Ready time",
        ),
        (
            csv_request(content=CSV_HEADER + "1,40,50,0,0,500,0\n2,1000,50,201,0,200,10\n"),
            "impossible to serve alone",
        ),
    ],
)
def test_malformed_csv_is_rejected(import_request: DatasetImport, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        parse_dataset(import_request)


def test_wgs84_requires_valid_coordinates_and_timezone() -> None:
    payload = canonical_payload()
    payload["customers"][0]["x"] = 181
    with pytest.raises(ValueError, match="WGS84 coordinates"):
        parse_dataset(
            DatasetImport(
                format="canonical_json",
                filename="geo.json",
                content=json.dumps(payload),
                family="custom",
            )
        )
    payload["customers"][0]["x"] = 77.2
    payload["timezone"] = None
    with pytest.raises(ValueError, match="require a timezone"):
        parse_dataset(
            DatasetImport(
                format="canonical_json",
                filename="geo.json",
                content=json.dumps(payload),
                family="custom",
            )
        )


def test_import_is_content_addressed_and_idempotent(isolated_storage: Settings) -> None:
    request = csv_request(
        source_url="https://example.test/C101.csv",
        license="CC BY 4.0",
        attribution="Solomon (1987)",
    )
    first = import_dataset(request)
    second = import_dataset(request)
    assert first.version_id == second.version_id
    assert first.canonical_sha256 == second.canonical_sha256
    assert first.validation_status == "valid"
    assert first.validation_errors == ()
    assert (isolated_storage.artifact_root / first.original_artifact).read_text() == request.content
    canonical = isolated_storage.artifact_root / first.canonical_artifact
    assert json.loads(canonical.read_text())["name"] == "C101"


def test_dataset_api_validates_imports_and_lists_versions(isolated_storage: Settings) -> None:
    payload = {
        "format": "solomon_text",
        "filename": "C101-mini.txt",
        "content": SAMPLE_SOLOMON,
        "family": "solomon",
        "source_url": "https://example.test/C101-mini.txt",
    }
    with TestClient(app) as client:
        validated = client.post("/api/v1/datasets/validate", json=payload)
        created = client.post("/api/v1/datasets", json=payload)
        duplicate = client.post("/api/v1/datasets", json=payload)
        listed = client.get("/api/v1/datasets")
        detail = client.get(f"/api/v1/datasets/{created.json()['version_id']}")
        missing = client.get("/api/v1/datasets/not-found")
    assert validated.json()["valid"] is True
    assert created.status_code == 201
    assert duplicate.json()["version_id"] == created.json()["version_id"]
    assert len(listed.json()) == 1
    assert detail.json()["customer_count"] == 10
    assert missing.status_code == 404


def test_import_rejects_paths_and_oversized_content(isolated_storage: Settings) -> None:
    with pytest.raises(ValueError, match="plain filename"):
        import_dataset(csv_request(filename="../C101.csv"))
    with pytest.raises(ValueError, match="import limit"):
        import_dataset(csv_request(content="x" * (MAX_DATASET_BYTES + 1)))


def canonical_payload() -> dict:
    return {
        "schema_version": 1,
        "name": "Delhi-mini",
        "coordinate_system": "wgs84",
        "distance_unit": "metres",
        "time_unit": "seconds",
        "timezone": "Asia/Kolkata",
        "depot": {"id": 0, "x": 77.1, "y": 28.6, "demand": 0, "ready": 0, "due": 500, "service": 0},
        "customers": [
            {"id": 1, "x": 77.2, "y": 28.7, "demand": 1, "ready": 0, "due": 300, "service": 10}
        ],
        "vehicles": [
            {
                "id": 0,
                "capacity": 10,
                "shift_start": 0,
                "shift_end": 500,
                "start_node": 0,
                "end_node": 0,
                "fixed_cost": 0,
            }
        ],
    }
