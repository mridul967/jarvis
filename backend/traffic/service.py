import json
from dataclasses import asdict, dataclass
from typing import Any, Literal

from backend.app.core.artifacts import read_artifact, write_artifact
from backend.app.core.database import connection, initialize_database
from backend.traffic.model import (
    ArcCongestion,
    ArcMultiplier,
    EndogenousTraffic,
    ExogenousTraffic,
)

ScenarioMode = Literal["exogenous", "endogenous", "combined"]


@dataclass(frozen=True)
class TrafficScenarioMetadata:
    scenario_id: str
    created_at: str
    name: str
    mode: ScenarioMode
    content_sha256: str
    artifact: str


def scenario_content(
    name: str,
    exogenous: ExogenousTraffic | None,
    endogenous: EndogenousTraffic | None,
) -> tuple[dict[str, Any], ScenarioMode]:
    if not name.strip():
        raise ValueError("Scenario name is required")
    if exogenous and endogenous:
        mode: ScenarioMode = "combined"
    elif exogenous:
        mode = "exogenous"
    elif endogenous:
        mode = "endogenous"
    else:
        raise ValueError("Scenario requires exogenous traffic, endogenous traffic, or both")
    return {
        "schema_version": 1,
        "name": name.strip(),
        "mode": mode,
        "exogenous": asdict(exogenous) if exogenous else None,
        "endogenous": asdict(endogenous) if endogenous else None,
    }, mode


def create_scenario(
    name: str,
    exogenous: ExogenousTraffic | None,
    endogenous: EndogenousTraffic | None,
) -> TrafficScenarioMetadata:
    content, mode = scenario_content(name, exogenous, endogenous)
    encoded = _json(content)
    artifact, digest = write_artifact(encoded)
    initialize_database()
    with connection() as database:
        database.execute(
            """INSERT OR IGNORE INTO traffic_scenarios
               (scenario_id, name, mode, content_sha256, artifact)
               VALUES (?, ?, ?, ?, ?)""",
            (digest, content["name"], mode, digest, artifact),
        )
    found = get_scenario(digest)
    if found is None:  # pragma: no cover - SQLite insert/select invariant
        raise RuntimeError("Traffic scenario was not saved")
    return found


def get_scenario(scenario_id: str) -> TrafficScenarioMetadata | None:
    initialize_database()
    with connection() as database:
        row = database.execute(
            "SELECT * FROM traffic_scenarios WHERE scenario_id = ?", (scenario_id,)
        ).fetchone()
    return TrafficScenarioMetadata(**dict(row)) if row else None


def list_scenarios(limit: int = 100) -> list[TrafficScenarioMetadata]:
    initialize_database()
    with connection() as database:
        rows = database.execute(
            """SELECT * FROM traffic_scenarios
               ORDER BY created_at DESC, scenario_id DESC LIMIT ?""",
            (limit,),
        ).fetchall()
    return [TrafficScenarioMetadata(**dict(row)) for row in rows]


def load_scenario(
    scenario_id: str,
) -> tuple[ExogenousTraffic | None, EndogenousTraffic | None]:
    metadata = get_scenario(scenario_id)
    if metadata is None:
        raise ValueError("Traffic scenario not found")
    payload = json.loads(read_artifact(metadata.artifact, metadata.content_sha256))
    exogenous_payload = payload["exogenous"]
    endogenous_payload = payload["endogenous"]
    if exogenous_payload:
        exogenous_values = exogenous_payload | {
            "intervals": tuple(ArcMultiplier(**item) for item in exogenous_payload["intervals"])
        }
        exogenous = ExogenousTraffic(**exogenous_values)
    else:
        exogenous = None
    if endogenous_payload:
        endogenous_values = endogenous_payload | {
            "arcs": tuple(ArcCongestion(**item) for item in endogenous_payload["arcs"])
        }
        endogenous = EndogenousTraffic(**endogenous_values)
    else:
        endogenous = None
    return exogenous, endogenous


def scenario_payload(scenario_id: str) -> dict[str, Any]:
    metadata = get_scenario(scenario_id)
    if metadata is None:
        raise ValueError("Traffic scenario not found")
    return json.loads(read_artifact(metadata.artifact, metadata.content_sha256))


def _json(payload: Any) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
