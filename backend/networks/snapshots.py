import json
from collections.abc import Callable
from dataclasses import dataclass
from math import isfinite
from typing import Any

from backend.app.core.artifacts import read_artifact, sha256, write_artifact
from backend.app.core.config import settings
from backend.app.core.database import connection, initialize_database
from backend.datasets.repository import get_dataset
from backend.networks import ors

Matrix = tuple[tuple[float | None, ...], ...]
MatrixFetcher = Callable[
    [str, list[tuple[float, float]], tuple[int, ...], tuple[int, ...]], dict[str, Any]
]


@dataclass(frozen=True)
class CostSnapshot:
    snapshot_id: str
    dataset_version_id: str
    profile: str
    node_ids: tuple[int, ...]
    distances: Matrix
    durations: Matrix
    attribution: str

    def __post_init__(self) -> None:
        size = len(self.node_ids)
        if size < 2 or len(set(self.node_ids)) != size:
            raise ValueError("Cost snapshot node ids must be unique and include at least two nodes")
        if not self.attribution.strip():
            raise ValueError("Cost snapshot attribution is required")
        for matrix in (self.distances, self.durations):
            if len(matrix) != size or any(len(row) != size for row in matrix):
                raise ValueError("Cost snapshot matrices must be square and match node ids")
            if any(
                value is not None and (not isfinite(value) or value < 0)
                for row in matrix
                for value in row
            ):
                raise ValueError("Cost snapshot values must be finite and non-negative")


@dataclass(frozen=True)
class CostSnapshotMetadata:
    snapshot_id: str
    created_at: str
    dataset_version_id: str
    profile: str
    provider: str
    provider_url: str
    attribution: str
    request_sha256: str
    raw_sha256: str
    normalized_sha256: str
    raw_artifact: str
    normalized_artifact: str
    node_count: int
    block_count: int
    unreachable_count: int
    request: dict[str, Any]


def create_snapshot(
    dataset_version_id: str,
    profile: str,
    fetcher: MatrixFetcher | None = None,
) -> CostSnapshotMetadata:
    if profile not in ors.ORS_PROFILES:
        raise ValueError(f"Unsupported ORS profile: {profile}")
    ors.validate_base_url()
    dataset = get_dataset(dataset_version_id)
    if dataset is None:
        raise ValueError("Dataset version not found")
    if dataset.coordinate_system != "wgs84":
        raise ValueError("ORS snapshots require a validated WGS84 dataset")
    canonical = json.loads(
        read_artifact(dataset.canonical_artifact, dataset.canonical_sha256).decode("utf-8")
    )
    nodes = [canonical["depot"], *canonical["customers"]]
    node_ids = [int(node["id"]) for node in nodes]
    locations = [(float(node["x"]), float(node["y"])) for node in nodes]
    blocks = ors.matrix_blocks(len(nodes), settings.ors_matrix_max_routes)
    request_document = {
        "schema_version": 1,
        "provider": "openrouteservice",
        "provider_url": settings.ors_base_url,
        "endpoint": f"/v2/matrix/{profile}",
        "profile": profile,
        "locations": locations,
        "metrics": ["distance", "duration"],
        "units": {"distance": "metres", "duration": "seconds"},
        "blocks": [
            {"sources": list(sources), "destinations": list(destinations)}
            for sources, destinations in blocks
        ],
    }
    request_json = _json(request_document)
    request_sha256 = sha256(request_json)
    distances: list[list[float | None]] = [[None] * len(nodes) for _ in nodes]
    durations: list[list[float | None]] = [[None] * len(nodes) for _ in nodes]
    responses = []
    attributions: set[str] = set()
    fetch = fetcher or ors.fetch_matrix
    for sources, destinations in blocks:
        response = fetch(profile, locations, sources, destinations)
        ors.validate_matrix_response(response, len(sources), len(destinations))
        attribution = _attribution(response)
        attributions.add(attribution)
        for row_index, source in enumerate(sources):
            for column_index, destination in enumerate(destinations):
                distances[source][destination] = response["distances"][row_index][column_index]
                durations[source][destination] = response["durations"][row_index][column_index]
        responses.append(
            {
                "sources": sources,
                "destinations": destinations,
                "response": response,
            }
        )
    if len(attributions) != 1:
        raise ValueError("ORS blocks returned inconsistent attribution")
    _validate_static_admission(canonical, durations)
    unreachable = [
        [node_ids[row], node_ids[column]]
        for row in range(len(nodes))
        for column in range(len(nodes))
        if distances[row][column] is None or durations[row][column] is None
    ]
    normalized_document = {
        "schema_version": 1,
        "dataset_version_id": dataset_version_id,
        "profile": profile,
        "provider": "openrouteservice",
        "attribution": attributions.pop(),
        "node_ids": node_ids,
        "distance_unit": "metres",
        "duration_unit": "seconds",
        "distances": distances,
        "durations": durations,
        "unreachable_pairs": unreachable,
        "request_sha256": request_sha256,
    }
    raw_artifact, raw_sha256 = write_artifact(
        _json({"request": request_document, "blocks": responses})
    )
    normalized_artifact, normalized_sha256 = write_artifact(_json(normalized_document))
    snapshot_id = normalized_sha256
    initialize_database()
    with connection() as database:
        database.execute(
            """INSERT OR IGNORE INTO cost_snapshots (
                snapshot_id, dataset_version_id, profile, provider, provider_url,
                attribution, request_sha256, raw_sha256, normalized_sha256,
                raw_artifact, normalized_artifact, node_count, block_count,
                unreachable_count, request_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                snapshot_id,
                dataset_version_id,
                profile,
                "openrouteservice",
                settings.ors_base_url,
                normalized_document["attribution"],
                request_sha256,
                raw_sha256,
                normalized_sha256,
                raw_artifact,
                normalized_artifact,
                len(nodes),
                len(blocks),
                len(unreachable),
                request_json.decode("utf-8"),
            ),
        )
    found = get_snapshot_metadata(snapshot_id)
    if found is None:  # pragma: no cover - SQLite insert/select invariant
        raise RuntimeError("Cost snapshot was not saved")
    return found


def get_snapshot_metadata(snapshot_id: str) -> CostSnapshotMetadata | None:
    initialize_database()
    with connection() as database:
        row = database.execute(
            "SELECT * FROM cost_snapshots WHERE snapshot_id = ?", (snapshot_id,)
        ).fetchone()
    if row is None:
        return None
    values = dict(row)
    values["request"] = json.loads(values.pop("request_json"))
    return CostSnapshotMetadata(**values)


def list_snapshots(limit: int = 100) -> list[CostSnapshotMetadata]:
    initialize_database()
    with connection() as database:
        rows = database.execute(
            """SELECT * FROM cost_snapshots
               ORDER BY created_at DESC, snapshot_id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [_metadata(dict(row)) for row in rows]


def load_snapshot(snapshot_id: str) -> CostSnapshot:
    metadata = get_snapshot_metadata(snapshot_id)
    if metadata is None:
        raise ValueError("Cost snapshot not found")
    payload = json.loads(
        read_artifact(metadata.normalized_artifact, metadata.normalized_sha256).decode("utf-8")
    )
    return CostSnapshot(
        snapshot_id=snapshot_id,
        dataset_version_id=metadata.dataset_version_id,
        profile=metadata.profile,
        node_ids=tuple(payload["node_ids"]),
        distances=tuple(tuple(row) for row in payload["distances"]),
        durations=tuple(tuple(row) for row in payload["durations"]),
        attribution=metadata.attribution,
    )


def _metadata(values: dict[str, Any]) -> CostSnapshotMetadata:
    values["request"] = json.loads(values.pop("request_json"))
    return CostSnapshotMetadata(**values)


def _attribution(response: dict[str, Any]) -> str:
    metadata = response.get("metadata")
    attribution = metadata.get("attribution") if isinstance(metadata, dict) else None
    if not isinstance(attribution, str) or not attribution.strip():
        raise ValueError("ORS response is missing attribution")
    return attribution.strip()


def _validate_static_admission(
    canonical: dict[str, Any], durations: list[list[float | None]]
) -> None:
    depot = canonical["depot"]
    impossible = []
    for index, customer in enumerate(canonical["customers"], start=1):
        outbound = durations[0][index]
        inbound = durations[index][0]
        if outbound is None or inbound is None:
            impossible.append(customer["id"])
            continue
        if not any(
            customer["demand"] <= vehicle["capacity"]
            and (
                service_start := max(
                    depot["ready"] + outbound,
                    vehicle["shift_start"] + outbound,
                    customer["ready"],
                )
            )
            <= customer["due"]
            and service_start + customer["service"] + inbound
            <= min(depot["due"], vehicle["shift_end"])
            for vehicle in canonical["vehicles"]
        ):
            impossible.append(customer["id"])
    if impossible:
        raise ValueError(f"Customers impossible to serve alone with ORS costs: {impossible}")


def _json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
