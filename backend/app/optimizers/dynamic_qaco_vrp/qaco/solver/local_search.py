from __future__ import annotations
import copy
from qaco.domain.vrp_instance import DynamicVRP
from qaco.domain.solution import Solution

class LocalSearch:
    """Bounded first-improvement feasible VRP local search."""
    def __init__(self, p: DynamicVRP): self.p=p
    def improve(self, s: Solution, budget: int) -> tuple[Solution,int]:
        current=copy.deepcopy(s); failures=0
        for _ in range(budget):
            before=self.p.objective_parts(current)['objective']; best=copy.deepcopy(current); bestv=before
            # 2-opt, relocate, and swap inside every route.
            for rix,r in enumerate(current):
                for a in range(1,len(r)-2):
                    for b in range(a+1,len(r)-1):
                        z=copy.deepcopy(current); z[rix]=r[:a]+list(reversed(r[a:b+1]))+r[b+1:]
                        if self.p.feasible(z) and self.p.objective_parts(z)['objective']<bestv: best,bestv=z,self.p.objective_parts(z)['objective']
                for a in range(1,len(r)-1):
                    for b in range(1,len(r)-1):
                        if a==b: continue
                        z=copy.deepcopy(current); node=z[rix].pop(a); z[rix].insert(b,node)
                        if self.p.feasible(z) and self.p.objective_parts(z)['objective']<bestv: best,bestv=z,self.p.objective_parts(z)['objective']
                for a in range(1,len(r)-1):
                    for b in range(a+1,len(r)-1):
                        z=copy.deepcopy(current); z[rix][a],z[rix][b]=z[rix][b],z[rix][a]
                        if self.p.feasible(z) and self.p.objective_parts(z)['objective']<bestv: best,bestv=z,self.p.objective_parts(z)['objective']
            # Cross-route relocate.
            for x in range(len(current)):
                for y in range(len(current)):
                    if x==y: continue
                    for a in range(1,len(current[x])-1):
                        z=copy.deepcopy(current); node=z[x].pop(a); z[y].insert(-1,node); z=[r for r in z if len(r)>2]
                        if self.p.feasible(z) and self.p.objective_parts(z)['objective']<bestv: best,bestv=z,self.p.objective_parts(z)['objective']
            if bestv >= before-1e-12: failures += 1; break
            current=best
        return current, failures