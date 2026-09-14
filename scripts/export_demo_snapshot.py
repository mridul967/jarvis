from pathlib import Path

from backend.simulation.graph import build_bengaluru_graph
from backend.simulation.snapshots import export_snapshot


if __name__ == "__main__":
    print(export_snapshot(build_bengaluru_graph(), Path("data/artifacts/simulations/graph-snapshots")))
