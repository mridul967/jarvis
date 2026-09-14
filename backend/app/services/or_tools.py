import logging
import os
from dataclasses import dataclass
from time import perf_counter

import openrouteservice
from dotenv import load_dotenv
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

# ponytail: minimal logger for standalone demo
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("or_tools")


@dataclass(frozen=True)
class Node:
    id: int
    lon: float
    lat: float
    demand: int
    ready_time: float
    due_time: float
    service_time: float


@dataclass(frozen=True)
class Vehicle:
    id: int
    capacity: int
    shift_start: float
    shift_end: float


def get_ors_matrix(
    client: openrouteservice.Client, coordinates: list[list[float]]
) -> tuple[list[list[float]], list[list[float]]]:
    """Fetch distance (meters) and duration (seconds) matrices from ORS."""
    logger.info(f"Fetching ORS distance matrix for {len(coordinates)} coordinates.")
    # openrouteservice expects [longitude, latitude]
    matrix = client.distance_matrix(
        locations=coordinates,
        profile="driving-car",
        metrics=["distance", "duration"],
        units="m",
    )
    return matrix["distances"], matrix["durations"]


def solve_vrp(
    nodes: list[Node],
    vehicles: list[Vehicle],
    durations: list[list[float]],
    distances: list[list[float]],
) -> dict:
    """Minimal OR-Tools CP-SAT solver utilizing a pre-computed duration matrix."""
    started = perf_counter()
    logger.info("Initializing OR-Tools Routing Model.")

    manager = pywrapcp.RoutingIndexManager(len(nodes), len(vehicles), 0)
    routing = pywrapcp.RoutingModel(manager)

    def time_callback(from_index: int, to_index: int) -> int:
        origin = manager.IndexToNode(from_index)
        destination = manager.IndexToNode(to_index)
        # OR-Tools works best with integers; durations in seconds
        return int(durations[origin][destination] + nodes[origin].service_time)

    transit_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

    # Add Capacity dimension
    def demand_callback(from_index: int) -> int:
        node = manager.IndexToNode(from_index)
        return nodes[node].demand

    demand_index = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_index,
        0,  # null capacity slack
        [v.capacity for v in vehicles],
        True,  # start cumul to zero
        "Capacity",
    )

    # Add Time dimension
    routing.AddDimension(
        transit_index,
        60000,  # allow waiting time
        60000,  # maximum time per vehicle
        False,  # Don't force start cumul to zero
        "Time",
    )
    time_dimension = routing.GetDimensionOrDie("Time")
    
    for node_index, node in enumerate(nodes):
        index = manager.NodeToIndex(node_index)
        time_dimension.CumulVar(index).SetRange(int(node.ready_time), int(node.due_time))

    for vehicle_index, vehicle in enumerate(vehicles):
        index = routing.Start(vehicle_index)
        time_dimension.CumulVar(index).SetRange(int(vehicle.shift_start), int(vehicle.shift_end))
        index = routing.End(vehicle_index)
        time_dimension.CumulVar(index).SetRange(int(vehicle.shift_start), int(vehicle.shift_end))

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.time_limit.FromMilliseconds(1000)

    logger.info("Solving with OR-Tools...")
    assignment = routing.SolveWithParameters(search)

    if assignment is None:
        logger.error("No solution found by OR-Tools.")
        return {"status": "infeasible"}

    routes = []
    total_time = 0
    for vehicle_index in range(len(vehicles)):
        index = routing.Start(vehicle_index)
        route_nodes = []
        while not routing.IsEnd(index):
            node_idx = manager.IndexToNode(index)
            route_nodes.append(nodes[node_idx].id)
            index = assignment.Value(routing.NextVar(index))
        # Add the depot at the end
        route_nodes.append(nodes[manager.IndexToNode(index)].id)
        
        # ponytail: Only save routes that actually visited a customer
        if len(route_nodes) > 2: 
            routes.append(route_nodes)
            total_time += assignment.Min(time_dimension.CumulVar(index))

    runtime = round((perf_counter() - started) * 1000, 2)
    logger.info(f"Solution found in {runtime} ms.")
    
    return {
        "status": "feasible",
        "routes": routes,
        "objective_time_sec": total_time,
        "runtime_ms": runtime,
    }


def run_dynamic_or_tools(matrix_limit: int, traffic: str = "normal", seed: int = 42) -> dict:
    import csv
    from pathlib import Path
    
    api_key = os.getenv("ORS_API_KEY")
    if not api_key:
        raise ValueError("ORS_API_KEY not found in environment.")

    # ponytail: load dynamic coordinates from demo dataset instead of hardcoding
    from backend.demo import COORDINATES, DATA_PATH
    
    unique_roads = []
    with DATA_PATH.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            road = row["Road/Intersection Name"]
            if road not in unique_roads and road in COORDINATES:
                unique_roads.append(road)

    selected_roads = unique_roads[:matrix_limit]
    if not selected_roads:
        raise ValueError("No valid roads found in dataset.")

    nodes = []
    for i, road in enumerate(selected_roads):
        lat, lon = COORDINATES[road]
        demand = 0 if i == 0 else 5
        service_time = 0 if i == 0 else 300
        nodes.append(
            Node(id=i, lon=lon, lat=lat, demand=demand, ready_time=0, due_time=60000, service_time=service_time)
        )

    total_demand = sum(n.demand for n in nodes)
    num_vehicles = max(1, (total_demand // 20) + 1)
    vehicles = [
        Vehicle(id=i, capacity=20, shift_start=0, shift_end=60000)
        for i in range(num_vehicles)
    ]

    client = openrouteservice.Client(key=api_key)
    coords_for_ors = [[n.lon, n.lat] for n in nodes]
    distances, durations = get_ors_matrix(client, coords_for_ors)
    
    result = solve_vrp(nodes, vehicles, durations, distances)
    
    # Scale coordinates for the frontend SVG (0-100)
    lats = [n.lat for n in nodes]
    lons = [n.lon for n in nodes]
    lat_min, lat_max = min(lats), max(lats)
    lon_min, lon_max = min(lons), max(lons)
    
    demo_nodes = []
    for i, n in enumerate(nodes):
        x = 5 + 90 * (n.lon - lon_min) / max((lon_max - lon_min), 1e-9)
        y = 95 - 90 * (n.lat - lat_min) / max((lat_max - lat_min), 1e-9)
        demo_nodes.append({
            "id": n.id,
            "road": selected_roads[i],
            "area": "Dynamic",
            "x": x,
            "y": y,
            "demand": n.demand,
            "is_depot": n.id == 0,
        })
        
    # Only send edges that are part of the solution to keep the UI clean
    demo_edges = []
    route_paths = []
    if result["status"] == "feasible":
        for route in result["routes"]:
            path = [0] + route + [0] if route[0] != 0 else route
            route_paths.append(path)
            for i in range(len(path) - 1):
                u, v = path[i], path[i+1]
                demo_edges.append({
                    "source": u,
                    "target": v,
                    "distance_km": distances[u][v] / 1000,
                    "travel_time_min": durations[u][v] / 60,
                    "utilization": 50,
                    "shocked": False,
                    "gat_score": None,
                })

    return {
        "scenario": {
            "id": "dynamic-ors-vrp",
            "name": f"Dynamic ORS ({matrix_limit} Nodes)",
            "source": "OpenRouteService API",
            "source_type": "dynamic-api",
            "nodes": demo_nodes,
            "edges": demo_edges,
        },
        "algorithm": {
            "id": "dynamic_ors",
            "name": "OR-Tools (Dynamic ORS)",
            "family": "Constraint Programming",
            "quantum_inspired": False,
            "mechanisms": ["capacity dimension", "time windows", "guided local search", "dynamic distance matrix"],
            "source_notebook": "or_tools.py",
        },
        "traffic": traffic,
        "gat": {"applied": False, "production_ready": False, "reason": "Not applicable for dynamic ORS"},
        "result": {
            "feasible": result["status"] == "feasible",
            "routes": result["routes"],
            "route_paths": route_paths,
            "score": {
                "hard_violations": 0,
                "coverage_errors": 0,
                "vehicles": len(result["routes"]),
                "lateness": 0,
                "travel_time": result.get("objective_time_sec", 0) / 60,
                "distance": 0,
                "congestion": 0,
            },
            "evaluations": 1,
            "runtime_ms": result.get("runtime_ms", 0),
            "seed": seed,
            "convergence": [{"evaluations": 1, "objective": result.get("objective_time_sec", 0)}],
            "diagnostics": {"status": result["status"]}
        },
        "events": [
            "Fetched distance/duration matrix from OpenRouteService API",
            "OR-Tools CP-SAT formulation complete",
            "OR-Tools optimization complete"
        ],
        "disclosure": "Uses live OpenRouteService Distance Matrix API. Matrix limits apply."
    }

if __name__ == "__main__":
    load_dotenv()
    try:
        matrix_limit = int(os.getenv("ORS_MATRIX_LIMIT", "4"))
    except ValueError:
        matrix_limit = 4
    
    try:
        res = run_dynamic_or_tools(matrix_limit)
        logger.info(f"Test run successful, returned {len(res['scenario']['nodes'])} nodes and {len(res['result']['routes'])} routes.")
    except Exception as e:
        logger.error(f"Error testing dynamic or-tools: {e}")

