"""Generate a deterministic simulation fixture and audit stream.

Run from the repository root with:
    python scripts/generate_demo_fixture.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.simulation.engine import SimulationEngine


if __name__ == "__main__":
    result = SimulationEngine(seed=42, vehicle_count=16, ticks=30).run()
    print(f"run_id={result['run_id']} frames={len(result['frames'])} events={len(result['events'])}")
    print(f"audit={result['audit_path']}")
