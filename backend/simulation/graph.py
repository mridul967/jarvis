from pathlib import Path
import re

import networkx as nx


def load_vrp_metadata(path: Path) -> dict[str, int | str]:
    """Read the checked-in VRP file without making the simulator depend on it."""
    text = path.read_text(encoding="utf-8")
    dimension = re.search(r"DIMENSION:\s*(\d+)", text)
    capacity = re.search(r"CAPACITY:\s*(\d+)", text)
    return {
        "source_file": path.name,
        "dimension": int(dimension.group(1)) if dimension else 0,
        "capacity": int(capacity.group(1)) if capacity else 0,
    }


def build_bengaluru_graph() -> nx.DiGraph:
    """Build a compact 3x3 Bengaluru-like directed road mesh."""
    graph = nx.DiGraph()
    center_lat, center_lon = 12.9352, 77.6140
    for row in range(3):
        for col in range(3):
            node_id = f"j-{row * 3 + col + 1:02d}"
            graph.add_node(
                node_id,
                latitude=center_lat + (1 - row) * 0.006,
                longitude=center_lon + (col - 1) * 0.007,
                node_type="intersection",
                signalized=(row + col) % 2 == 0,
                zone_id=("koramangala" if row == 1 else "bengaluru-demo"),
            )
    for row in range(3):
        for col in range(3):
            source = f"j-{row * 3 + col + 1:02d}"
            for dr, dc, road_class in ((0, 1, "arterial"), (1, 0, "collector")):
                nr, nc = row + dr, col + dc
                if nr >= 3 or nc >= 3:
                    continue
                target = f"j-{nr * 3 + nc + 1:02d}"
                length = 620.0 if road_class == "arterial" else 540.0
                for a, b in ((source, target), (target, source)):
                    edge_id = f"{a}>{b}"
                    graph.add_edge(
                        a,
                        b,
                        edge_id=edge_id,
                        length_m=length,
                        # Demo-scale travel time: a 620 m urban link takes about
                        # two 30-second simulation ticks, so the shock is visible.
                        free_flow_time_s=length / (18_000 / 3_600),
                        capacity_veh_per_hour=900.0 if road_class == "arterial" else 650.0,
                        speed_limit_kmh=36.0 if road_class == "arterial" else 28.0,
                        road_class=road_class,
                    )
    return graph
