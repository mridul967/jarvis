"""OSMnx district import kept outside the deterministic routing loop."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import networkx as nx
import osmnx as ox

from backend.simulation.snapshots import export_snapshot


def import_district(place: str = "Koramangala, Bengaluru, India", directory: Path = Path("data/artifacts/road-snapshots")) -> dict[str, str | int]:
    graph = ox.graph_from_place(place, network_type="drive", simplify=True)
    graph = ox.convert.to_digraph(graph, weight="length")
    converted = nx.DiGraph()
    for node, data in graph.nodes(data=True):
        converted.add_node(str(node), latitude=float(data["y"]), longitude=float(data["x"]), node_type="intersection", signalized=bool(data.get("highway") == "traffic_signals"), zone_id=place)
    for source, target, data in graph.edges(data=True):
        length = float(data.get("length", 1.0))
        edge_id = f"{source}>{target}"
        converted.add_edge(str(source), str(target), edge_id=edge_id, length_m=length, free_flow_time_s=max(1.0, length / 11.11), capacity_veh_per_hour=900.0, road_class=str(data.get("highway", "road")))
    directory = directory / hashlib.sha256(place.encode()).hexdigest()[:12]
    paths = export_snapshot(converted, directory)
    metadata = {"place": place, "nodes": len(converted), "edges": len(converted.edges), "graphml": paths["graphml"], "geojson": paths["geojson"]}
    metadata_path = directory / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
    metadata["sha256"] = hashlib.sha256(metadata_path.read_bytes()).hexdigest()
    return metadata
