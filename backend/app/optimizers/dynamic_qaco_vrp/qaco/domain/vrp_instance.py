# qaco/domain/vrp_instance.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
import numpy as np
from qaco.domain.solution import Route, Solution

@dataclass
class DynamicVRP:
    """Capacitated multi-vehicle dynamic VRP instance with matrix traffic state."""
    cfg: Mapping[str, object]
    coords: np.ndarray = field(init=False); demand: np.ndarray = field(init=False)
    base: np.ndarray = field(init=False); weight: np.ndarray = field(init=False); previous: np.ndarray = field(init=False)
    tw_open: np.ndarray = field(init=False); tw_close: np.ndarray = field(init=False)
    changed_edges: set[tuple[int, int]] = field(default_factory=set, init=False)
    active_shocks: dict[tuple[int, int], int] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.active_shocks = {}
        rng = np.random.default_rng(int(self.cfg['seed']))
        n = int(self.cfg['n_customers']) + 1
        self.coords = rng.uniform(0, 1, (n, 2)); self.coords[0] = (0.5, 0.5)
        
        # 1. Base Euclidean distance matrix
        self.base = np.linalg.norm(self.coords[:, None] - self.coords[None, :], axis=2) + np.eye(n)
        
        # 2. Integrate CQM / QUBO penalty layer if present
        qubo_mat = self.cfg.get('qubo_matrix')
        if qubo_mat is not None and isinstance(qubo_mat, np.ndarray):
            lambda_weight = float(self.cfg.get('qubo_weight', 0.5))
            self.base += (qubo_mat * lambda_weight)

        np.fill_diagonal(self.base, 0.0)
        self.weight = self.base.copy()
        self.previous = self.weight.copy()
        
        self.demand = np.r_[0.0, rng.integers(1, 4, n - 1)].astype(float)
        self.tw_open = np.zeros(n); self.tw_close = np.full(n, np.inf)
        if bool(self.cfg['time_windows']): 
            self.tw_close[1:] = rng.uniform(3.0, 6.0, n - 1)
            
        self.phase = rng.uniform(0, 2*np.pi, (n, n))
        self.phase = (self.phase + self.phase.T) / 2

    def advance(self, iteration: int, dynamic: bool, prefer_edges=None):
        self.previous = self.weight.copy()
        n = len(self.weight)

        if not dynamic:
            self.weight = self.base.copy()
            self.changed_edges = set()
            delta = self.weight - self.previous
            volatility = float(np.linalg.norm(delta) / (np.linalg.norm(self.previous) + 1e-12))
            return volatility, delta

        factor = 1.0 + float(self.cfg['traffic_drift']) * np.sin(0.07 * iteration + self.phase)
        factor = (factor + factor.T) / 2.0

        if iteration in self.cfg['shock_iterations']:
            rng = np.random.default_rng(int(self.cfg['seed']) + iteration)
            duration = int(self.cfg.get('shock_duration', 20))
            fraction = float(self.cfg['shock_edge_fraction'])

            preferred = [tuple(sorted(e)) for e in (prefer_edges or set()) if e[0] != e[1]]

            if len(preferred) >= 2:
                m = max(2, int(len(preferred) * fraction))
                idx = rng.choice(len(preferred), size=min(m, len(preferred)), replace=False)
                chosen = [preferred[int(k)] for k in idx]
            else:
                all_pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
                m = max(2, int(len(all_pairs) * fraction))
                idx = rng.choice(len(all_pairs), size=m, replace=False)
                chosen = [all_pairs[int(k)] for k in idx]

            for e in chosen:
                self.active_shocks[e] = iteration + duration

        self.active_shocks = {e: exp for e, exp in self.active_shocks.items() if exp > iteration}
        self.changed_edges = set(self.active_shocks.keys())

        shock = np.zeros_like(self.base)
        for i, j in self.changed_edges:
            shock[i, j] = shock[j, i] = float(self.cfg['shock_strength'])

        self.weight = self.base * np.maximum(0.05, factor + shock)
        np.fill_diagonal(self.weight, 0.0)

        delta = self.weight - self.previous
        volatility = float(np.linalg.norm(delta) / (np.linalg.norm(self.previous) + 1e-12))
        return volatility, delta

    def feasible_route(self, route: Route) -> bool:
        if len(route) < 2 or route[0] != 0 or route[-1] != 0: return False
        if sum(self.demand[c] for c in route[1:-1]) > float(self.cfg['capacity']) + 1e-9: return False
        clock = 0.0
        for i, j in zip(route[:-1], route[1:]):
            clock += self.weight[i, j]
            if j and (clock < self.tw_open[j] or clock > self.tw_close[j]): return False
        return True

    def feasible(self, solution: Solution) -> bool:
        seen = [c for r in solution for c in r[1:-1]]
        return (len(solution) <= int(self.cfg['n_vehicles']) and sorted(seen) == list(range(1, len(self.demand)))
                and len(set(seen)) == len(seen) and all(self.feasible_route(r) for r in solution))

    def objective_parts(self, solution: Solution) -> dict[str, float]:
        distance = sum(self.base[i,j] for r in solution for i,j in zip(r[:-1], r[1:]))
        travel = sum(self.weight[i,j] for r in solution for i,j in zip(r[:-1], r[1:]))
        congestion = sum(max(self.weight[i,j] / max(self.base[i,j],1e-12) - 1, 0) * self.base[i,j]
                         for r in solution for i,j in zip(r[:-1], r[1:]))
        violations = 0 if self.feasible(solution) else 1
        value = (float(self.cfg['objective_distance'])*distance + float(self.cfg['objective_time'])*travel +
                 float(self.cfg['objective_congestion'])*congestion + float(self.cfg['objective_vehicles'])*len(solution) +
                 float(self.cfg['penalty'])*violations)
        return {'distance': float(distance), 'travel_time': float(travel), 'congestion': float(congestion),
                'vehicles': float(len(solution)), 'violations': float(violations), 'objective': float(value)}

    def affected_route_indices(self, solution: Solution) -> list[int]:
        return [k for k,r in enumerate(solution) if any(tuple(sorted((i,j))) in self.changed_edges for i,j in zip(r[:-1],r[1:]))]