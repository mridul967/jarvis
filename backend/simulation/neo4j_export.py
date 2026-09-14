"""Optional audit export; NetworkX remains the operational graph."""

from __future__ import annotations

import json
import os
from pathlib import Path

from neo4j import GraphDatabase


def export_audit(path: Path, run_id: str) -> int:
    uri, user, password = os.getenv("NEO4J_URI"), os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD")
    if not all((uri, user, password)):
        raise ValueError("Set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD to export audit events")
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            session.run("MERGE (r:SimulationRun {id: $run_id})", run_id=run_id)
            for event in events:
                session.run("MATCH (r:SimulationRun {id: $run_id}) MERGE (e:AuditEvent {id: $id}) SET e += $event MERGE (r)-[:HAS_EVENT]->(e)", run_id=run_id, id=event["event_id"], event={key: value for key, value in event.items() if isinstance(value, (str, int, float, bool)) or value is None})
    return len(events)
