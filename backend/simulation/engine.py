from dataclasses import asdict
from pathlib import Path
import hashlib
import json
import math
import time
import uuid

import networkx as nx

from backend.simulation.agents import create_agents, neighbor_messages
from backend.simulation.audit import JsonlAuditWriter
from backend.simulation.generator import generate_vehicles
from backend.simulation.graph import build_bengaluru_graph, load_vrp_metadata
from backend.simulation.negotiation import RouteOffer, choose_offer, pareto_front
from backend.simulation.quantum_engines import ADMRQPSOEngine, QACO22Engine
from backend.simulation.shocks import active_shocks, demo_shocks
from backend.simulation.schemas import NodeAgent, Shock, SimulationState, VehicleState

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class SimulationEngine:
    tick_seconds = 30.0

    def __init__(self, seed: int = 42, vehicle_count: int = 16, ticks: int = 30) -> None:
        self.seed, self.vehicle_count, self.ticks = seed, max(1, min(vehicle_count, 50)), max(1, min(ticks, 60))
        self.graph = build_bengaluru_graph()
        self.vrp_metadata = load_vrp_metadata(PROJECT_ROOT / "data/vlsvrp/1040.vrp")
        self.shocks = demo_shocks()
        self.qaco = QACO22Engine(self.graph, seed)
        self.qpso = ADMRQPSOEngine(self.graph, seed)

    def run(self) -> dict:
        run_id = f"run-{uuid.uuid4().hex[:10]}"
        scenario_id = "blr-demo-001"
        audit = JsonlAuditWriter(Path("data/artifacts/simulations") / run_id / "events.jsonl")
        state = SimulationState(scenario_id, 0, 0.0, "blr-synth-9-v1", "bpr-v1", generate_vehicles(self.graph, self.seed, self.vehicle_count, self.vrp_metadata), create_agents(self.graph))
        frames = []
        all_events = []
        for tick in range(self.ticks):
            state.tick, state.timestamp_s = tick, tick * self.tick_seconds
            active = active_shocks(self.shocks, state.timestamp_s)
            state.active_shocks = [shock.shock_id for shock in active]
            flows = self._flows(state.vehicles)
            edge_state = self._edge_state(flows, active)
            self._update_agents(state.agents, state.vehicles, edge_state, active)
            for vehicle in state.vehicles.values():
                if vehicle.status == "arrived" or state.timestamp_s < vehicle.available_from:
                    continue
                if tick == 0 or tick % 3 == 0 or self._route_is_affected(vehicle, active):
                    event = self._negotiate(state, vehicle, edge_state, active, audit, run_id)
                    if event:
                        all_events.append(event)
                self._move(vehicle, edge_state)
            self._update_agents(state.agents, state.vehicles, edge_state, active)
            frames.append(self._frame(state, edge_state))
        return {
            "run_id": run_id,
            "scenario_id": scenario_id,
            "seed": self.seed,
            "generator_version": "0.1.0",
            "district": "Bengaluru",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "graph": self._graph_payload(),
            "shocks": [asdict(shock) for shock in self.shocks],
            "vrp_source": self.vrp_metadata,
            "frames": frames,
            "events": all_events,
            "audit_path": str(audit.path),
        }

    def _edge_state(self, flows: dict[str, int], active: list[Shock]) -> dict[str, dict]:
        state = {}
        for source, target, data in self.graph.edges(data=True):
            edge = data["edge_id"]
            incident = next((shock for shock in active if edge in shock.affected_edges), None)
            capacity = data["capacity_veh_per_hour"] * (incident.capacity_multiplier if incident else 1.0)
            peak = 1.15 if any(shock.type == "peak" for shock in active) else 1.0
            flow = flows.get(edge, 0)
            ratio = flow / max(capacity, 1.0)
            bpr = data["free_flow_time_s"] * (1 + 0.15 * ratio**4)
            travel = bpr * peak * (incident.travel_time_multiplier if incident else 1.0)
            state[edge] = {"edge_id": edge, "source": source, "target": target, "flow": flow, "capacity": capacity, "travel_time_s": round(travel, 2), "congestion": round(min(1.0, ratio), 3), "closed": incident is not None and incident.type == "closure"}
        return state

    def _flows(self, vehicles: dict[str, VehicleState]) -> dict[str, int]:
        flows: dict[str, int] = {}
        for vehicle in vehicles.values():
            if vehicle.status != "arrived":
                flows[vehicle.current_edge] = flows.get(vehicle.current_edge, 0) + 1
        return flows

    def _route_is_affected(self, vehicle: VehicleState, active: list[Shock]) -> bool:
        route_edges = {f"{a}>{b}" for a, b in zip(vehicle.route, vehicle.route[1:])}
        return any(route_edges.intersection(shock.affected_edges) for shock in active)

    def _negotiate(self, state: SimulationState, vehicle: VehicleState, edge_state: dict[str, dict], active: list[Shock], audit: JsonlAuditWriter, run_id: str) -> dict | None:
        origin, destination = vehicle.current_node, vehicle.destination_node
        try:
            engine = self.qaco if any(shock.type == "incident" for shock in active) else self.qpso if any(shock.type == "peak" for shock in active) or any(item["congestion"] > 0.25 for item in edge_state.values()) else None
            quantum_candidates = engine.propose(origin, destination, edge_state) if engine else []
            paths = [candidate.route for candidate in quantum_candidates]
            paths.extend(tuple(path) for path in list(nx.shortest_simple_paths(self.graph, origin, destination, weight=lambda a, b, d: edge_state[d["edge_id"]]["travel_time_s"]))[:4])
            paths = list(dict.fromkeys(paths))[:4]
            engine_name = engine.name if engine else "dijkstra_baseline"
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None
        offers = []
        affected = {edge for shock in active for edge in shock.affected_edges}
        for path in paths:
            route_edges = [f"{a}>{b}" for a, b in zip(path, path[1:])]
            travel = sum(edge_state[edge]["travel_time_s"] for edge in route_edges)
            queue = sum(edge_state[edge]["flow"] / max(edge_state[edge]["capacity"], 1) for edge in route_edges)
            offers.append(RouteOffer(origin, path[1] if len(path) > 1 else destination, vehicle.vehicle_id, tuple(path), state.timestamp_s + travel, queue, len(route_edges) * 0.04, sum(edge in affected for edge in route_edges)))
        front = pareto_front(offers)
        selected = choose_offer(front)
        vehicle.route, vehicle.status = selected.route, "rerouting" if selected.route != vehicle.route else "moving"
        vehicle.current_edge = f"{vehicle.route[0]}>{vehicle.route[1]}" if len(vehicle.route) > 1 else "arrived"
        agent = state.agents[origin]
        payload = audit.write({"run_id": run_id, "tick": state.tick, "timestamp_s": state.timestamp_s, "event_type": "negotiation_decision", "sender": origin, "recipients": list(agent.neighbors), "neighbor_messages": [asdict(message) for message in neighbor_messages(agent, state.tick, state.active_shocks)], "prediction": {"model": "heuristic_pressure_v1", "predicted_pressure": agent.predicted_pressure}, "vehicle_id": vehicle.vehicle_id, "offers_considered": len(offers), "pareto_offers": len(front), "selected_offer": asdict(selected), "utility_before": {}, "utility_after": {"arrival_s": selected.predicted_arrival_s, "queue": selected.predicted_queue}, "reason_codes": ["lower_spillback" if selected.spillback_risk == 0 else "avoid_incident", "deterministic_tiebreak"], "negotiation_policy": "pareto_lexicographic_v1", "engine": engine_name, "seed": self.seed})
        return payload

    def _move(self, vehicle: VehicleState, edge_state: dict[str, dict]) -> None:
        if len(vehicle.route) < 2:
            vehicle.status = "arrived"
            return
        edge = vehicle.current_edge
        vehicle.progress += self.tick_seconds / max(edge_state[edge]["travel_time_s"], 1.0)
        if vehicle.progress >= 1.0:
            next_index = vehicle.route.index(vehicle.current_node) + 1
            vehicle.current_node = vehicle.route[next_index]
            vehicle.progress = 0.0
            if vehicle.current_node == vehicle.destination_node:
                vehicle.status, vehicle.current_edge = "arrived", "arrived"
            else:
                vehicle.current_edge = f"{vehicle.current_node}>{vehicle.route[next_index + 1]}"

    def _update_agents(self, agents: dict[str, NodeAgent], vehicles: dict[str, VehicleState], edges: dict[str, dict], active: list[Shock]) -> None:
        # ponytail: heuristic prediction until a validated GAT checkpoint beats it.
        for agent in agents.values():
            waiting = sum(1 for vehicle in vehicles.values() if vehicle.current_node == agent.node_id and vehicle.status != "arrived")
            outgoing = [data for edge, data in edges.items() if data["source"] == agent.node_id]
            agent.queue_length = float(waiting)
            agent.occupancy = round(sum(item["flow"] for item in outgoing) / max(sum(item["capacity"] for item in outgoing), 1), 3)
            agent.predicted_pressure = round(min(1.0, agent.occupancy + waiting / 10), 3)
        for agent in agents.values():
            neighbor_pressure = sum(agents[node].predicted_pressure for node in agent.neighbors) / max(len(agent.neighbors), 1)
            incident = any(edge in shock.affected_edges for shock in active for edge in (f"{agent.node_id}>{node}" for node in agent.neighbors))
            agent.predicted_pressure = round(min(1.0, agent.predicted_pressure + 0.5 * neighbor_pressure + 0.3 * incident), 3)

    def _graph_payload(self) -> dict:
        return {"nodes": [{"id": node, **{key: data[key] for key in ("latitude", "longitude", "node_type", "signalized", "zone_id")}} for node, data in self.graph.nodes(data=True)], "edges": [{"id": data["edge_id"], "source": source, "target": target, "length_m": data["length_m"], "free_flow_time_s": data["free_flow_time_s"], "capacity_veh_per_hour": data["capacity_veh_per_hour"], "road_class": data["road_class"]} for source, target, data in self.graph.edges(data=True)]}

    def _frame(self, state: SimulationState, edges: dict[str, dict]) -> dict:
        return {"tick": state.tick, "timestamp_s": state.timestamp_s, "active_shocks": state.active_shocks, "edges": list(edges.values()), "vehicles": [asdict(vehicle) for vehicle in state.vehicles.values()], "agents": [asdict(agent) for agent in state.agents.values()]}
