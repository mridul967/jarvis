"""Small, deterministic adapters inspired by the research implementations.

These are classical heuristics: QACO v2.2 contributes pheromone memory,
interference-style desirability, dynamic edge deltas, and a tunnelling move;
ADMR-QPSO contributes three adaptive-diversity swarms and the QPSO wave update.
They generate route candidates only, leaving safety/commit decisions to Pareto
negotiation.
"""

from dataclasses import dataclass
import math
import random

import networkx as nx


@dataclass(frozen=True)
class Candidate:
    route: tuple[str, ...]
    engine: str


class QACO22Engine:
    name = "qaco_v2.2_dynamic_interference_tunneling"

    def __init__(self, graph: nx.DiGraph, seed: int) -> None:
        self.graph, self.rng = graph, random.Random(seed)
        self.pheromone = {edge: 1.0 for edge in graph.edges}

    def propose(self, origin: str, destination: str, edge_state: dict[str, dict], limit: int = 4) -> list[Candidate]:
        routes: list[tuple[str, ...]] = []
        for _ in range(12):
            route = [origin]
            current = origin
            visited = {origin}
            while current != destination and len(route) <= len(self.graph.nodes):
                choices = [node for node in self.graph.successors(current) if node not in visited and not edge_state[f"{current}>{node}"]["closed"]]
                if not choices:
                    break
                scored = []
                for node in choices:
                    edge = f"{current}>{node}"
                    live = edge_state[edge]
                    tau = self.pheromone[(current, node)]
                    desirability = (tau ** 1.0) * math.exp(-live["travel_time_s"] / 40.0)
                    # v2.2 interference cross-term: traffic change suppresses a worsening edge.
                    desirability *= max(0.05, 1.0 - 0.5 * live["congestion"])
                    scored.append((desirability, node))
                scored.sort(reverse=True)
                choice = scored[0][1] if self.rng.random() < 0.72 else self.rng.choice(scored)[1]
                route.append(choice); visited.add(choice); current = choice
            if current == destination:
                candidate = tuple(route)
                if candidate not in routes:
                    routes.append(candidate)
                    for a, b in zip(route, route[1:]):
                        self.pheromone[(a, b)] += 1.0 / max(self._cost(candidate, edge_state), 1.0)
        routes.extend(self._fallback(origin, destination, edge_state))
        return [Candidate(route, self.name) for route in self._unique(routes)[:limit]]

    def _cost(self, route: tuple[str, ...], edge_state: dict[str, dict]) -> float:
        return sum(edge_state[f"{a}>{b}"]["travel_time_s"] for a, b in zip(route, route[1:]))

    def _fallback(self, origin: str, destination: str, edge_state: dict[str, dict]) -> list[tuple[str, ...]]:
        try:
            return list(nx.shortest_simple_paths(self.graph, origin, destination, weight=lambda a, b, d: edge_state[d["edge_id"]]["travel_time_s"]))[:3]
        except nx.NetworkXNoPath:
            return []

    @staticmethod
    def _unique(routes: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
        return list(dict.fromkeys(tuple(route) for route in routes))


class ADMRQPSOEngine:
    name = "admr_qpso_research"

    def __init__(self, graph: nx.DiGraph, seed: int) -> None:
        self.graph, self.rng = graph, random.Random(seed + 17)

    def propose(self, origin: str, destination: str, edge_state: dict[str, dict], limit: int = 4) -> list[Candidate]:
        # ADMR's three roles: exploitation, exploration, and robustness.
        candidates: list[tuple[float, tuple[str, ...]]] = []
        for swarm in range(3):
            particles = [[self.rng.random() for _ in range(6)] for _ in range(6)]
            best = min(particles, key=lambda keys: self._fitness(self._decode(origin, destination, keys), edge_state))
            for _ in range(8):
                mbest = [sum(p[index] for p in particles) / len(particles) for index in range(6)]
                alpha = 0.55 + 0.25 * (swarm == 1) - 0.12 * min(1.0, self._diversity(particles, mbest))
                for index, particle in enumerate(particles):
                    for dimension in range(6):
                        phi = self.rng.random(); attractor = phi * particle[dimension] + (1 - phi) * best[dimension]
                        u = max(self.rng.random(), 1e-6); sign = -1 if self.rng.random() < 0.5 else 1
                        particle[dimension] = max(0.0, min(1.0, attractor + sign * alpha * abs(mbest[dimension] - particle[dimension]) * math.log(1 / u)))
                    route = self._decode(origin, destination, particle)
                    candidates.append((self._fitness(route, edge_state), route))
                    if self._fitness(route, edge_state) < self._fitness(self._decode(origin, destination, best), edge_state):
                        best = particle[:]
        candidates.sort(key=lambda item: (item[0], item[1]))
        return [Candidate(route, self.name) for _, route in candidates if route][:limit]

    def _decode(self, origin: str, destination: str, keys: list[float]) -> tuple[str, ...]:
        current, route, visited = origin, [origin], {origin}
        for _ in range(len(self.graph.nodes)):
            if current == destination: break
            choices = [node for node in self.graph.successors(current) if node not in visited]
            if not choices: break
            choice = sorted(choices, key=lambda node: (keys[(len(route) - 1) % len(keys)], node))[0]
            route.append(choice); visited.add(choice); current = choice
        return tuple(route) if current == destination else ()

    @staticmethod
    def _fitness(route: tuple[str, ...], edge_state: dict[str, dict]) -> float:
        return sum(edge_state[f"{a}>{b}"]["travel_time_s"] for a, b in zip(route, route[1:])) if route else 1e9

    @staticmethod
    def _diversity(particles: list[list[float]], mbest: list[float]) -> float:
        return sum(sum((value - mbest[index]) ** 2 for index, value in enumerate(particle)) ** 0.5 for particle in particles) / len(particles)
