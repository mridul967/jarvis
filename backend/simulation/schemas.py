from dataclasses import dataclass, field
from typing import Literal


@dataclass
class NodeAgent:
    node_id: str
    neighbors: tuple[str, ...]
    queue_length: float = 0.0
    occupancy: float = 0.0
    predicted_pressure: float = 0.0
    local_objectives: tuple[str, ...] = ("travel_time", "spillback", "fairness")
    current_policy: str = "heuristic_pareto_v1"
    last_decision_at: float = 0.0


@dataclass(frozen=True)
class AgentMessage:
    sender: str
    recipient: str
    tick: int
    queue_length: float
    occupancy: float
    predicted_pressure: float
    active_shocks: tuple[str, ...]


@dataclass
class VehicleState:
    vehicle_id: str
    vehicle_type: Literal["bike", "car", "bus", "truck"]
    current_edge: str
    progress: float
    destination_node: str
    capacity: float
    load: float
    energy_remaining: float
    available_from: float
    deadline: float | None
    route: tuple[str, ...]
    status: Literal["waiting", "moving", "arrived", "rerouting"] = "moving"
    origin_node: str = ""
    current_node: str = ""


@dataclass(frozen=True)
class Shock:
    shock_id: str
    start_s: float
    end_s: float
    affected_edges: tuple[str, ...]
    capacity_multiplier: float
    travel_time_multiplier: float
    type: Literal["incident", "peak", "closure", "event", "weather"]


@dataclass
class SimulationState:
    scenario_id: str
    tick: int
    timestamp_s: float
    graph_version: str
    traffic_version: str
    vehicles: dict[str, VehicleState]
    agents: dict[str, NodeAgent]
    active_shocks: list[str] = field(default_factory=list)
