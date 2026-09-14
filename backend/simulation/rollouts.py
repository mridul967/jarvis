"""Generate supervised future-edge targets from deterministic rollouts."""

import json
from pathlib import Path

from backend.simulation.engine import SimulationEngine


def generate_rollout_dataset(path: Path, seed: int = 42, runs: int = 3) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for run_number in range(runs):
            result = SimulationEngine(seed=seed + run_number, vehicle_count=16, ticks=30).run()
            for current, future in zip(result["frames"], result["frames"][1:]):
                future_edges = {edge["edge_id"]: edge for edge in future["edges"]}
                for edge in current["edges"]:
                    target = future_edges[edge["edge_id"]]
                    handle.write(json.dumps({"run_id": result["run_id"], "seed": seed + run_number, "tick": current["tick"], "edge_id": edge["edge_id"], "features": {"flow": edge["flow"], "capacity": edge["capacity"], "congestion": edge["congestion"]}, "travel_time_target_s": target["travel_time_s"]}) + "\n")
    return path
