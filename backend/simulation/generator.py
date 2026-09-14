from pathlib import Path
import random

import networkx as nx

from backend.simulation.schemas import VehicleState


def generate_vehicles(graph: nx.DiGraph, seed: int, count: int, vrp_metadata: dict[str, int | str]) -> dict[str, VehicleState]:
    rng = random.Random(seed)
    nodes = list(graph.nodes)
    types = ("bike", "car", "bus", "truck")
    vehicles: dict[str, VehicleState] = {}
    for index in range(count):
        origin = nodes[index % len(nodes)]
        destination = nodes[(index * 4 + 5) % len(nodes)]
        if origin == destination:
            destination = nodes[(index + 1) % len(nodes)]
        route = tuple(nx.shortest_path(graph, origin, destination))
        vehicles[f"veh-{index + 1:02d}"] = VehicleState(
            vehicle_id=f"veh-{index + 1:02d}",
            vehicle_type=types[index % len(types)],
            current_edge=f"{route[0]}>{route[1]}",
            progress=0.0,
            destination_node=destination,
            capacity=float(250 + (int(vrp_metadata["capacity"]) % 400)),
            load=float(20 + rng.randrange(80)),
            energy_remaining=100.0,
            available_from=float((index % 3) * 30),
            deadline=900.0,
            route=route,
            origin_node=origin,
            current_node=origin,
        )
    return vehicles
