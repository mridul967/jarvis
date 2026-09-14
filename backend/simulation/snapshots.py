"""Offline graph snapshot import/export helpers for the next geography phase."""

import json
from pathlib import Path

import networkx as nx


def graph_to_geojson(graph: nx.DiGraph) -> dict:
    features = []
    for source, target, data in graph.edges(data=True):
        a, b = graph.nodes[source], graph.nodes[target]
        features.append({"type": "Feature", "properties": {"id": data.get("edge_id", f"{source}>{target}"), "source": source, "target": target, "road_class": data.get("road_class")}, "geometry": {"type": "LineString", "coordinates": [[a["longitude"], a["latitude"]], [b["longitude"], b["latitude"]]]}})
    for node, data in graph.nodes(data=True):
        features.append({"type": "Feature", "properties": {"id": node, "node_type": data.get("node_type", "intersection")}, "geometry": {"type": "Point", "coordinates": [data["longitude"], data["latitude"]]}})
    return {"type": "FeatureCollection", "features": features}


def export_snapshot(graph: nx.DiGraph, directory: Path) -> dict[str, str]:
    directory.mkdir(parents=True, exist_ok=True)
    graphml = directory / "bengaluru-demo.graphml"
    geojson = directory / "bengaluru-demo.geojson"
    nx.write_graphml(graph, graphml)
    geojson.write_text(json.dumps(graph_to_geojson(graph), indent=2), encoding="utf-8")
    return {"graphml": str(graphml), "geojson": str(geojson)}


def load_graphml(path: Path) -> nx.DiGraph:
    graph = nx.read_graphml(path)
    for _, data in graph.nodes(data=True):
        for key in ("latitude", "longitude"):
            if key in data:
                data[key] = float(data[key])
    return nx.DiGraph(graph)
