import json
from pathlib import Path

from backend.simulation.engine import SimulationEngine


def test_simulation_is_replayable_for_same_seed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    first = SimulationEngine(seed=7, vehicle_count=4, ticks=8).run()
    second = SimulationEngine(seed=7, vehicle_count=4, ticks=8).run()
    assert first["graph"] == second["graph"]
    assert first["frames"] == second["frames"]
    assert [event["selected_offer"] for event in first["events"]] == [event["selected_offer"] for event in second["events"]]


def test_incident_creates_active_shock_and_audit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = SimulationEngine(seed=42, vehicle_count=6, ticks=12).run()
    assert "arterial-incident-0845" in result["frames"][10]["active_shocks"]
    assert result["events"]
    audit = Path(result["audit_path"])
    lines = [json.loads(line) for line in audit.read_text().splitlines()]
    assert lines[0]["event_type"] == "negotiation_decision"
    assert all(line["run_id"] == result["run_id"] for line in lines)
