# qaco/solver/runner.py
from __future__ import annotations
import copy
import time
from typing import Mapping, Sequence
import numpy as np

from config import FLAGS
from qaco.domain.vrp_instance import DynamicVRP
from qaco.domain.solution import Solution, solution_key, edge_set
from qaco.physics.interference import QuantumAmplitudeState, InterferenceEngine
from qaco.physics.tunneling import TunnelingOperator
from qaco.solver.local_search import LocalSearch
from qaco.solver.controller import AdaptiveController
from qaco.utils.metrics import solution_diversity, entropy

class DynamicQACO:
    """Unified, reproducible ACO/QACO dynamic-VRP engine."""
    def __init__(self,cfg:Mapping[str,object],flags:Mapping[str,bool]):
        self.cfg={**cfg}; self.flags={**FLAGS,**flags}; self.p=DynamicVRP(self.cfg); self.rng=np.random.default_rng(int(self.cfg['seed']))
        self.state=QuantumAmplitudeState(len(self.p.demand)); self.interference=InterferenceEngine(self.p,self.state,self.cfg); self.local=LocalSearch(self.p); self.tunneler=TunnelingOperator(self.p,self.rng); self.controller=AdaptiveController(self.cfg)
    def _build(self,delta:np.ndarray, controls:Mapping[str,float], customers:Sequence[int]|None=None, fixed:Solution|None=None)->Solution:
        """Construct feasible multi-route VRP solution, applying candidate filtering before sampling."""
        remaining=set(range(1,len(self.p.demand))) if customers is None else set(customers); routes=copy.deepcopy(fixed) if fixed else []
        used_load=[sum(self.p.demand[c] for c in r[1:-1]) for r in routes]
        while remaining and len(routes)<int(self.cfg['n_vehicles']):
            route=[0]; load=0.; clock=0.
            while remaining:
                feasible=[j for j in remaining if load+self.p.demand[j]<=float(self.cfg['capacity']) and clock+self.p.weight[route[-1],j]<=self.p.tw_close[j]]
                if not feasible:break
                i=route[-1]; feasible=sorted(feasible,key=lambda j:self.p.weight[i,j])[:int(controls['candidate_k'])]
                prob=self.interference.probabilities(i,feasible,delta,controls['traffic_weight'],self.flags['interference_on'],self.flags['classical_fusion_control'],self.iteration)
                j=int(self.rng.choice(feasible,p=prob)); route.append(j); remaining.remove(j); load+=self.p.demand[j]; clock+=self.p.weight[i,j]
            route.append(0)
            if len(route)>2:routes.append(route)
            else:break
        # Deterministic repair: insert any leftover customer at best feasible position.
        for j in list(remaining):
            placed=False
            for r in routes:
                for pos in range(1,len(r)):
                    z=copy.deepcopy(routes); z[routes.index(r)].insert(pos,j)
                    if self.p.feasible(z): routes=z; placed=True; break
                if placed:break
            if not placed and len(routes)<int(self.cfg['n_vehicles']) and self.p.demand[j]<=float(self.cfg['capacity']): routes.append([0,j,0]); placed=True
            if placed: remaining.remove(j)
        return routes
    def partial_reconstruct(self,s:Solution,delta:np.ndarray,controls:Mapping[str,float])->tuple[Solution,int,int]:
        """Freeze unaffected routes; reconstruct customer portions from shock-affected routes only."""
        affected=self.p.affected_route_indices(s)
        if not affected:return s,0,0
        frozen=[r for k,r in enumerate(s) if k not in affected]; pool=[c for k in affected for c in s[k][1:-1]]
        started=time.perf_counter(); rebuilt=self._build(delta,controls,pool,frozen); elapsed=int((time.perf_counter()-started)*1000)
        return rebuilt,len(affected),elapsed
    def run(self) -> tuple[list[dict[str, float]], list[dict[str, float]]]:
        records = []
        unique = set()

        best = None
        bestv = float('inf')
        current = None

        stagnation = 0
        ls_fail = 0

        tunnel_proposals = 0
        tunnel_feasible = 0
        tunnel_accepted = 0
        tunnel_improved = 0

        last_diversity = 0.0
        last_reconstruct = -999

        start = time.perf_counter()

        for self.iteration in range(int(self.cfg['iterations'])):
            # Preferentially shock edges used by current incumbent so dynamic effect is visible.
            prefer_edges = edge_set(current) if current is not None else None
            vol, delta = self.p.advance(self.iteration, bool(self.flags['dynamic_on']), prefer_edges)

                        # Validation helper: if a shock iteration occurs but the incumbent
            # is not affected, force some shocked edges to belong to the incumbent.
            if (
                bool(self.flags['dynamic_on'])
                and self.iteration in self.p.cfg['shock_iterations']
                and current is not None
            ):
                if len(self.p.affected_route_indices(current)) == 0:
                    current_edges = list(edge_set(current))

                    if len(current_edges) >= 2:
                        rng_shock = np.random.default_rng(
                            int(self.cfg['seed']) + self.iteration + 777
                        )

                        m = max(
                            2,
                            int(len(current_edges) * float(self.cfg.get('shock_edge_fraction', 0.25)))
                        )

                        chosen_idx = rng_shock.choice(
                            len(current_edges),
                            size=min(m, len(current_edges)),
                            replace=False
                        )

                        chosen_edges = [
                            tuple(sorted(current_edges[int(k)]))
                            for k in chosen_idx
                        ]

                        duration = int(self.cfg.get('shock_duration', 30))

                        for e in chosen_edges:
                            self.p.active_shocks[e] = self.iteration + duration

                        self.p.changed_edges = set(self.p.active_shocks.keys())

                        # Apply shock to weights immediately.
                        shock = np.zeros_like(self.p.base)
                        for ii, jj in self.p.changed_edges:
                            shock[ii, jj] = shock[jj, ii] = float(self.cfg['shock_strength'])

                        factor = self.p.weight / np.maximum(self.p.base, 1e-12)

                        self.p.previous = self.p.weight.copy()
                        self.p.weight = self.p.base * np.maximum(0.05, factor + shock)
                        np.fill_diagonal(self.p.weight, 0.0)

                        delta = self.p.weight - self.p.previous
                        vol = float(
                            np.linalg.norm(delta)
                            / (np.linalg.norm(self.p.previous) + 1e-12)
                        )

            ctl = self.controller.controls(stagnation,last_diversity,vol,ls_fail,bool(self.flags['adaptive_on']))

            pop = [self._build(delta, ctl)for _ in range(int(self.cfg['num_ants']))]

            raw_vals = [self.p.objective_parts(s)['objective'] for s in pop]
            pre_local_best = float(min(raw_vals)) if raw_vals else float('inf')

            if self.flags['local_search_on']:
                # Improve only the best quarter of the population.
                # This prevents deterministic local search from erasing all construction diversity.
                idxs = np.argsort(raw_vals)[:max(1, len(pop) // 4)]
                failures = []

                for ix in idxs:
                    pop[int(ix)], f = self.local.improve(pop[int(ix)], int(ctl['ls_budget']))
                    failures.append(f)

                ls_fail = int(np.mean(failures)) if failures else 0

            vals = [self.p.objective_parts(s)['objective'] for s in pop]
            candidate = pop[int(np.argmin(vals))]
            cv = min(vals)

            if current is None or cv < self.p.objective_parts(current)['objective']:
                current = copy.deepcopy(candidate)

            affected_idx = self.p.affected_route_indices(current) if current is not None else []
            affected = len(affected_idx)
            rebuild_ms = 0

            if bool(self.flags.get('partial_reconstruct_on', False)) and affected_idx:
                cooldown = int(self.cfg.get('reconstruct_cooldown', 3))
                should_rebuild = (vol > float(self.cfg['volatility_reconstruct_threshold'])or (self.iteration - last_reconstruct) >= cooldown)

                if should_rebuild:
                    current, affected_count, rebuild_ms = self.partial_reconstruct(current, delta, ctl)
                    affected = affected_count
                    last_reconstruct = self.iteration

                    if self.flags['local_search_on']:
                        current, _ = self.local.improve(current, max(1, int(ctl['ls_budget'])))

            want_tunnel = (self.flags['tunneling_on']and current is not None and (stagnation >= int(self.cfg['S_max'])or (affected > 0 and stagnation >= max(1, int(self.cfg['S_max']) // 3))))

            if want_tunnel and self.rng.random() < float(ctl['tunnel_p']):
                tunnel_proposals += 1

                proposal = self.tunneler.propose(current,self.p.affected_route_indices(current))

                old = self.p.objective_parts(current)['objective']
                new = self.p.objective_parts(proposal)['objective']

                if solution_key(proposal) != solution_key(current):
                    tunnel_feasible += 1

                    if self.tunneler.tunnel_accept(old,new,self.iteration,int(self.cfg['iterations']),stagnation,vol,self.cfg,self.rng):
                        current = proposal
                        tunnel_accepted += 1

                        if new < old:
                            tunnel_improved += 1

            value = self.p.objective_parts(current)['objective']

            if value < bestv - 1e-9:
                best = copy.deepcopy(current)
                bestv = value
                stagnation = 0
            else:
                stagnation += 1

            adaptive_evaporate(self.state,pop,self.p,float(ctl['rho']),float(self.cfg['deposit']))

            unique.update(solution_key(s) for s in pop)

            pop_diversity = solution_diversity(pop)
            last_diversity = pop_diversity

            parts = self.p.objective_parts(current)

            records.append({
                **parts,
                'iteration': self.iteration,
                'runtime_s': time.perf_counter() - start,
                'pre_local_best': pre_local_best,
                'volatility': vol,
                'diversity': pop_diversity,
                'edge_diversity': len(set().union(*[edge_set(x) for x in pop])) if pop else 0,
                'entropy': entropy(self.state.pheromone),
                'unique_solutions': len(unique),
                'stagnation': stagnation,
                'traffic_weight': float(ctl['traffic_weight']),
                'tunnel_p': float(ctl['tunnel_p']),
                'tunneling_events': tunnel_proposals,
                'tunnel_feasible': tunnel_feasible,
                'successful_tunnels': tunnel_accepted,
                'improving_tunnels': tunnel_improved,
                'affected_routes': affected,
                'reconstructed_customers': sum(
                    len(current[k]) - 2
                    for k in self.p.affected_route_indices(current)
                ) if affected else 0,
                'reconstruction_ms': rebuild_ms,
            })

        return records, self.interference.log

def adaptive_evaporate(state: QuantumAmplitudeState, population: Sequence[Solution], problem: DynamicVRP, rho: float, deposit: float) -> None:
    """Classical pheromone learning; its dynamic evaporation is distinct from amplitude interference."""
    state.pheromone *= (1-rho)
    for s in population:
        q=deposit/max(problem.objective_parts(s)['objective'],1e-9)
        for r in s:
            for i,j in zip(r[:-1],r[1:]): state.pheromone[i,j]+=q; state.pheromone[j,i]+=q
    state.pheromone=np.maximum(state.pheromone,1e-9)