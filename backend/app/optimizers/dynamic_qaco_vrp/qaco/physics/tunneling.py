from __future__ import annotations
import copy
import math
from typing import Mapping
import numpy as np

from qaco.domain.vrp_instance import DynamicVRP
from qaco.domain.solution import Solution, solution_key


class TunnelingOperator:
    """Feasibility-preserving nonlocal VRP basin-transition operator."""

    def __init__(self, p: DynamicVRP, rng: np.random.Generator):
        self.p = p
        self.rng = rng

    def propose(self, s: Solution, affected: list[int] | None = None) -> Solution:
        original = copy.deepcopy(s)
        base_obj = self.p.objective_parts(original)['objective']
        feasible_candidates: list[tuple[float, Solution]] = []

        for _ in range(25):
            z = copy.deepcopy(original)

            nonempty = [k for k, r in enumerate(z) if len(r) > 3]
            if affected:
                target = list(set(nonempty) & set(affected)) or nonempty
            else:
                target = nonempty

            if not target:
                return original

            op = int(self.rng.integers(4))

            if op == 0:
                # Large segment reversal.
                k = int(self.rng.choice(target))
                r = z[k]
                if len(r) > 4:
                    a = int(self.rng.integers(1, max(2, len(r) - 2)))
                    b = int(self.rng.integers(a + 1, len(r) - 1))
                    z[k] = r[:a] + r[a:b + 1][::-1] + r[b + 1:]

            elif op == 1:
                # Large segment relocation inside the same route.
                k = int(self.rng.choice(target))
                r = z[k]
                if len(r) > 5:
                    a = int(self.rng.integers(1, len(r) - 3))
                    b = min(len(r) - 1, a + int(self.rng.integers(1, 3)))
                    block = r[a:b]
                    del z[k][a:b]
                    pos = int(self.rng.integers(1, max(2, len(z[k]) - 1)))
                    z[k][pos:pos] = block

            elif op == 2 and len(z) > 1:
                # Cross-route node relocation with capacity check.
                x = int(self.rng.choice(target))
                others = [k for k in range(len(z)) if k != x]
                if others and len(z[x]) > 3:
                    y = int(self.rng.choice(others))
                    pos = int(self.rng.integers(1, len(z[x]) - 1))
                    node = z[x].pop(pos)

                    load_y = sum(self.p.demand[c] for c in z[y][1:-1]) + self.p.demand[node]
                    if load_y <= float(self.p.cfg['capacity']) + 1e-9:
                        z[y].insert(len(z[y]) - 1, node)
                    else:
                        z[x].insert(pos, node)

            else:
                # Swap customers between two routes.
                if len(z) > 1:
                    x, y = self.rng.choice(len(z), 2, replace=False)
                    x, y = int(x), int(y)
                    if len(z[x]) > 3 and len(z[y]) > 3:
                        px = int(self.rng.integers(1, len(z[x]) - 1))
                        py = int(self.rng.integers(1, len(z[y]) - 1))
                        z[x][px], z[y][py] = z[y][py], z[x][px]

            if self.p.feasible(z) and solution_key(z) != solution_key(original):
                obj = self.p.objective_parts(z)['objective']
                feasible_candidates.append((obj, z))

                # If we already found an improving nonlocal move, return it immediately.
                if obj < base_obj:
                    return z

        if feasible_candidates:
            feasible_candidates.sort(key=lambda item: item[0])
            return feasible_candidates[0][1]

        return original

    def tunnel_accept(self, current: float, new: float, iteration: int, total: int, stagnation: int,volatility: float,cfg: Mapping[str, object],rng: np.random.Generator) -> bool:
        """Accept improvements; otherwise cross only bounded relative barriers."""
        if new <= current:
            return True

        delta = (new - current) / max(abs(current), 1e-12)
        barrier_max = float(cfg.get('tunnel_barrier_max', 0.18))

        # Do not allow crossing huge barriers.
        if delta > barrier_max:
            return False

        temp = (float(cfg['tunnel_temperature'])* (0.30 + 0.70 * (1.0 - iteration / max(total, 1)))* (1.0 + min(stagnation / float(cfg['S_max']), 2.0) + 4.0 * volatility))

        exponent = min(delta / max(temp, 1e-12), 40.0)
        return bool(rng.random() < math.exp(-exponent))
