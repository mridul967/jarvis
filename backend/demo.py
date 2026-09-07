"""Bengaluru research MVP: graph, GAT prior, dynamic costs, and solver orchestration."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from functools import lru_cache
from itertools import pairwise
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

import networkx as nx
import numpy as np
import torch

from backend.app.gat.models import SearchSpaceGAT
from backend.optimizers.model import SolverParameters
from backend.optimizers.research_portfolio import ALGORITHMS, PortfolioResult, solve_research
from backend.vrptw.model import Customer, Problem, Vehicle

DATA_PATH = Path(__file__).resolve().parents[1] / "data/Banglore_traffic_Dataset.csv"

# Approximate corridor coordinates, checked in so the demo is reproducible and
# does not depend on a geocoder during the presentation.
COORDINATES = {
    "Hosur Road": (12.8452, 77.6602),
    "Silk Board Junction": (12.9177, 77.6238),
    "Ballari Road": (13.0174, 77.5923),
    "Hebbal Flyover": (13.0358, 77.5970),
    "100 Feet Road": (12.9784, 77.6408),
    "CMH Road": (12.9789, 77.6469),
    "Jayanagar 4th Block": (12.9250, 77.5938),
    "South End Circle": (12.9369, 77.5800),
    "Sarjapur Road": (12.9249, 77.6385),
    "Sony World Junction": (12.9365, 77.6267),
    "Anil Kumble Circle": (12.9757, 77.6011),
    "Trinity Circle": (12.9721, 77.6172),
    "ITPL Main Road": (12.9857, 77.7376),
    "Marathahalli Bridge": (12.9569, 77.7011),
    "Tumkur Road": (13.0285, 77.5402),
    "Yeshwanthpur Circle": (13.0232, 77.5514),
}

TRAFFIC_FACTORS = {"normal": 1.0, "peak": 1.25, "incident": 1.1, "volatility": 1.15}


@dataclass(frozen=True)
class MatrixCosts:
    node_ids: tuple[int, ...]
    distances: tuple[tuple[float, ...], ...]
    durations: tuple[tuple[float, ...], ...]
    free_flow: tuple[tuple[float, ...], ...]

    def _pair(self, origin: int, destination: int) -> tuple[int, int]:
        return self.node_ids.index(origin), self.node_ids.index(destination)

    def distance(self, origin: int, destination: int) -> float:
        row, column = self._pair(origin, destination)
        return self.distances[row][column]

    def travel_time(
        self, origin: int, destination: int, departure: float, flow: float = 0.0
    ) -> float:
        row, column = self._pair(origin, destination)
        return self.durations[row][column]

    def base_travel_time(self, origin: int, destination: int) -> float:
        row, column = self._pair(origin, destination)
        return self.free_flow[row][column]


@dataclass(frozen=True)
class Scenario:
    graph: nx.DiGraph
    problem: Problem
    costs: MatrixCosts
    nodes: tuple[dict[str, Any], ...]


def algorithm_catalog() -> list[dict[str, Any]]:
    return [
        {
            "id": spec.id,
            "name": spec.name,
            "family": spec.family,
            "quantum_inspired": spec.quantum_inspired,
            "mechanisms": list(spec.mechanisms),
            "source_notebook": spec.notebook,
        }
        for spec in ALGORITHMS.values()
    ]


@lru_cache(maxsize=1)
def _observations() -> tuple[dict[str, Any], ...]:
    aggregate: dict[str, dict[str, Any]] = {}
    with DATA_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            road = row["Road/Intersection Name"]
            item = aggregate.setdefault(
                road,
                {
                    "road": road,
                    "area": row["Area Name"],
                    "volume": 0.0,
                    "speed": 0.0,
                    "tti": 0.0,
                    "utilization": 0.0,
                    "incidents": 0.0,
                    "count": 0,
                },
            )
            item["volume"] += float(row["Traffic Volume"])
            item["speed"] += float(row["Average Speed"])
            item["tti"] += float(row["Travel Time Index"])
            item["utilization"] += float(row["Road Capacity Utilization"])
            item["incidents"] += float(row["Incident Reports"])
            item["count"] += 1
    rows = []
    for road in sorted(aggregate):
        item = aggregate[road]
        count = item.pop("count")
        rows.append(
            item
            | {
                key: item[key] / count
                for key in ("volume", "speed", "tti", "utilization", "incidents")
            }
        )
    return tuple(rows)


def _haversine(left: tuple[float, float], right: tuple[float, float]) -> float:
    lat1, lon1, lat2, lon2 = map(radians, (*left, *right))
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(value))


def build_scenario(traffic: str = "normal") -> Scenario:
    if traffic not in TRAFFIC_FACTORS:
        raise ValueError(f"Unknown traffic condition: {traffic}")
    observations = _observations()
    graph = nx.DiGraph(name="Bengaluru historical-derived industrial routing demo")
    node_payloads = []
    for node_id, observation in enumerate(observations):
        lat, lon = COORDINATES[observation["road"]]
        demand = 0 if node_id == 0 else 1 + (node_id * 3) % 7
        payload = observation | {
            "id": node_id,
            "lat": lat,
            "lon": lon,
            "x": lon,
            "y": lat,
            "demand": demand,
            "is_depot": node_id == 0,
        }
        node_payloads.append(payload)
        graph.add_node(node_id, **payload)

    for origin, source in enumerate(node_payloads):
        nearest = sorted(
            (
                (
                    _haversine((source["lat"], source["lon"]), (target["lat"], target["lon"])),
                    destination,
                )
                for destination, target in enumerate(node_payloads)
                if destination != origin
            ),
        )[:4]
        for distance, destination in nearest:
            target = node_payloads[destination]
            speed = max(12.0, (source["speed"] + target["speed"]) / 2)
            free_time = distance / speed * 60
            tti = (source["tti"] + target["tti"]) / 2
            utilization = (source["utilization"] + target["utilization"]) / 200
            bpr = 1 + 0.15 * utilization**4
            attributes = {
                "distance": distance,
                "free_time": free_time,
                "travel_time": free_time * tti * bpr * TRAFFIC_FACTORS[traffic],
                "speed": speed,
                "utilization": utilization,
                "shocked": False,
            }
            graph.add_edge(origin, destination, **attributes)
            graph.add_edge(destination, origin, **attributes)

    # Four-nearest topology is connected for this fixed dataset; keep a clear
    # failure instead of silently inserting fictional links if data changes.
    if not nx.is_strongly_connected(graph):
        raise ValueError("Bengaluru demo graph is not strongly connected")

    if traffic in {"incident", "volatility"}:
        centrality = nx.edge_betweenness_centrality(graph, weight="travel_time")
        shock_count = 3 if traffic == "incident" else 6
        for origin, destination in sorted(centrality, key=centrality.get, reverse=True)[
            :shock_count
        ]:
            factor = 2.4 if traffic == "incident" else 1.35 + ((origin + destination) % 4) * 0.2
            graph[origin][destination]["travel_time"] *= factor
            graph[origin][destination]["shocked"] = True

    node_ids = tuple(graph.nodes)
    distances = _all_pairs(graph, "distance")
    durations = _all_pairs(graph, "travel_time")
    free_flow = _all_pairs(graph, "free_time")
    costs = MatrixCosts(node_ids, distances, durations, free_flow)
    depot_data = node_payloads[0]
    depot = Customer(0, depot_data["lon"], depot_data["lat"], 0, 0, 600, 0)
    customers = tuple(
        Customer(item["id"], item["lon"], item["lat"], item["demand"], 0, 600, 5)
        for item in node_payloads[1:]
    )
    vehicles = tuple(Vehicle(vehicle_id, 15, 0, 600) for vehicle_id in range(5))
    return Scenario(
        graph,
        Problem("Bengaluru-16-road-demo", depot, customers, vehicles),
        costs,
        tuple(node_payloads),
    )


def _all_pairs(graph: nx.DiGraph, weight: str) -> tuple[tuple[float, ...], ...]:
    paths = dict(nx.all_pairs_dijkstra_path_length(graph, weight=weight))
    return tuple(
        tuple(float(paths[origin][destination]) for destination in graph.nodes)
        for origin in graph.nodes
    )


_GAT_MODEL: SearchSpaceGAT | None = None
_GAT_LOSS = 0.0


def _graph_tensors(
    graph: nx.DiGraph,
) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, list[tuple[int, int]]]:
    edges = list(graph.edges)
    latitudes = np.asarray([graph.nodes[node]["lat"] for node in graph.nodes])
    longitudes = np.asarray([graph.nodes[node]["lon"] for node in graph.nodes])
    x = torch.tensor(
        np.column_stack(
            (
                (latitudes - latitudes.mean()) / max(latitudes.std(), 1e-9),
                (longitudes - longitudes.mean()) / max(longitudes.std(), 1e-9),
                np.asarray([graph.degree(node) for node in graph.nodes]) / 10,
            )
        ),
        dtype=torch.float32,
    )
    edge_index = torch.tensor(edges, dtype=torch.long).t().contiguous()
    edge_attr = torch.tensor(
        [
            [graph[u][v]["distance"] / 10, graph[u][v]["speed"] / 60, graph[u][v]["utilization"]]
            for u, v in edges
        ],
        dtype=torch.float32,
    )
    return x, edge_index, edge_attr, edges


def gat_prior(graph: nx.DiGraph) -> tuple[dict[tuple[int, int], float], dict[str, Any]]:
    """Train once on NetworkX shortest-path supervision, then infer edge priors."""
    global _GAT_MODEL, _GAT_LOSS
    torch.manual_seed(42)
    x, edge_index, edge_attr, edges = _graph_tensors(graph)
    if _GAT_MODEL is None:
        model = SearchSpaceGAT(3, 3, hidden_dim=24, heads=2, layers=2)
        selected = set()
        for path in nx.single_source_dijkstra_path(graph, 0, weight="travel_time").values():
            selected.update(pairwise(path))
        labels = torch.tensor([float(edge in selected) for edge in edges])
        optimizer = torch.optim.Adam(model.parameters(), lr=0.02, weight_decay=1e-5)
        loss_fn = torch.nn.BCELoss()
        model.train()
        for _ in range(80):
            optimizer.zero_grad()
            prediction = model(x, edge_index, edge_attr)
            loss = loss_fn(prediction, labels)
            loss.backward()
            optimizer.step()
        _GAT_MODEL, _GAT_LOSS = model, float(loss.item())
    _GAT_MODEL.eval()
    with torch.no_grad():
        scores = _GAT_MODEL(x, edge_index, edge_attr).tolist()
    return dict(zip(edges, scores, strict=True)), {
        "applied": True,
        "training_source": "demo self-supervision from NetworkX shortest-path edges",
        "production_ready": False,
        "loss": round(_GAT_LOSS, 6),
        "scored_edges": len(edges),
    }


def run_demo(
    algorithm: str,
    traffic: str,
    gat_enabled: bool,
    population_size: int,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    scenario = build_scenario(traffic)
    base = build_scenario("normal")
    prior: dict[tuple[int, int], float] | None = None
    gat = {"applied": False, "reason": "disabled", "production_ready": False}
    if gat_enabled:
        prior, gat = gat_prior(scenario.graph)
    result = solve_research(
        scenario.problem,
        scenario.costs,
        algorithm,
        SolverParameters(population_size, iterations),
        seed,
        prior,
        base.costs,
    )
    return _response(scenario, result, prior, gat, traffic, seed)


def run_benchmark(
    algorithms: list[str],
    traffic: str,
    gat_enabled: bool,
    population_size: int,
    iterations: int,
    seed: int,
) -> dict[str, Any]:
    selected = algorithms or list(ALGORITHMS)
    unknown = sorted(set(selected) - set(ALGORITHMS))
    if unknown:
        raise ValueError(f"Unknown research algorithms: {', '.join(unknown)}")
    rows = []
    for algorithm in selected:
        response = run_demo(algorithm, traffic, gat_enabled, population_size, iterations, seed)
        points = response["result"]["convergence"]
        start = points[0]["objective"]
        finish = points[-1]["objective"]
        rows.append(
            {
                "algorithm": response["algorithm"],
                "feasible": response["result"]["feasible"],
                "score": response["result"]["score"],
                "runtime_ms": response["result"]["runtime_ms"],
                "evaluations": response["result"]["evaluations"],
                "initial_objective": start,
                "final_objective": finish,
                "improvement_percent": round(100 * (start - finish) / max(abs(start), 1e-9), 2),
            }
        )
    rows.sort(
        key=lambda row: (
            not row["feasible"],
            row["score"]["hard_violations"],
            row["score"]["coverage_errors"],
            row["score"]["travel_time"],
        )
    )
    return {
        "traffic": traffic,
        "gat_enabled": gat_enabled,
        "population_size": population_size,
        "iterations": iterations,
        "seed": seed,
        "rows": rows,
        "disclosure": "Same scenario, budget, and seed; stochastic results require repeated-seed statistics for research claims.",
    }


def scenario_response(traffic: str = "normal") -> dict[str, Any]:
    scenario = build_scenario(traffic)
    return _graph_response(scenario, None)


def _graph_response(
    scenario: Scenario,
    prior: dict[tuple[int, int], float] | None,
) -> dict[str, Any]:
    latitudes = [node["lat"] for node in scenario.nodes]
    longitudes = [node["lon"] for node in scenario.nodes]
    lat_min, lat_max = min(latitudes), max(latitudes)
    lon_min, lon_max = min(longitudes), max(longitudes)
    nodes = [
        node
        | {
            "x": 5 + 90 * (node["lon"] - lon_min) / (lon_max - lon_min),
            "y": 95 - 90 * (node["lat"] - lat_min) / (lat_max - lat_min),
        }
        for node in scenario.nodes
    ]
    edges = [
        {
            "source": origin,
            "target": destination,
            "distance_km": round(data["distance"], 3),
            "travel_time_min": round(data["travel_time"], 3),
            "utilization": round(data["utilization"], 3),
            "shocked": data["shocked"],
            "gat_score": round(prior[(origin, destination)], 5) if prior else None,
        }
        for origin, destination, data in scenario.graph.edges(data=True)
    ]
    return {
        "id": "bengaluru-historical-derived-16",
        "name": scenario.graph.graph["name"],
        "source": "Banglore_traffic_Dataset.csv; approximate checked-in corridor coordinates",
        "source_type": "historical-derived simulation",
        "nodes": nodes,
        "edges": edges,
    }


def _response(
    scenario: Scenario,
    result: PortfolioResult,
    prior: dict[tuple[int, int], float] | None,
    gat: dict[str, Any],
    traffic: str,
    seed: int,
) -> dict[str, Any]:
    score = result.evaluation.score
    spec = ALGORITHMS[result.algorithm]
    return {
        "scenario": _graph_response(scenario, prior),
        "algorithm": {
            "id": spec.id,
            "name": spec.name,
            "family": spec.family,
            "quantum_inspired": spec.quantum_inspired,
            "mechanisms": list(spec.mechanisms),
            "source_notebook": spec.notebook,
        },
        "traffic": traffic,
        "gat": gat,
        "result": {
            "feasible": result.evaluation.feasible,
            "routes": [list(route) for route in result.evaluation.routes],
            "route_paths": _route_paths(scenario.graph, result.evaluation.routes),
            "score": {
                "hard_violations": score.hard_violations,
                "coverage_errors": score.coverage_errors,
                "vehicles": score.vehicles,
                "lateness": round(score.lateness, 3),
                "travel_time": round(score.travel_time, 3),
                "distance": round(score.distance, 3),
                "congestion": round(score.congestion, 3),
            },
            "evaluations": result.evaluations,
            "runtime_ms": result.runtime_ms,
            "seed": seed,
            "convergence": [
                {"evaluations": point.evaluations, "objective": round(_score_value(point.score), 3)}
                for point in result.convergence
            ],
            "diagnostics": result.diagnostics,
        },
        "events": [
            "NetworkX directed graph assembled",
            "historical traffic and BPR edge costs applied",
            "GAT search-space prior applied" if prior else "GAT prior disabled",
            f"{spec.name} optimization completed",
            "independent capacity, coverage, time-window, and depot-return validation completed",
        ],
        "disclosure": "Quantum-inspired algorithms execute classically; this run is a PoC, not proof of quantum advantage.",
    }


def _score_value(score: Any) -> float:
    return (
        score.hard_violations * 1e9
        + score.coverage_errors * 1e8
        + score.vehicles * 1e6
        + score.lateness * 1e4
        + score.travel_time * 100
        + score.distance
        + score.congestion
    )


def _route_paths(graph: nx.DiGraph, routes: tuple[tuple[int, ...], ...]) -> list[list[int]]:
    expanded = []
    for route in routes:
        stops = [0, *route, 0]
        path = [stops[0]]
        for origin, destination in pairwise(stops):
            leg = nx.shortest_path(graph, origin, destination, weight="travel_time")
            path.extend(leg[1:])
        expanded.append(path)
    return expanded
