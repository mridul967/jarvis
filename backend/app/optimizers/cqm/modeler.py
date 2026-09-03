import dimod
from backend.vrptw.model import Problem


class VRPTWCQMModeler:
    """Translates a canonical VRPTW Problem into a Constrained Quadratic Model (CQM)."""

    def __init__(self, problem: Problem):
        self.problem = problem
        self.cqm = dimod.ConstrainedQuadraticModel()
        self.x = {}
        self.nodes = [problem.depot] + list(problem.customers)
        self.vehicles = problem.vehicles

    def build_model(self) -> dimod.ConstrainedQuadraticModel:
        self._define_variables()
        self._set_objective()
        self._add_constraints()
        return self.cqm

    def _define_variables(self) -> None:
        for k in self.vehicles:
            for i in self.nodes:
                for j in self.nodes:
                    if i.id != j.id:
                        name = f"x_{i.id}_{j.id}_{k.id}"
                        self.x[(i.id, j.id, k.id)] = dimod.Binary(name)

    def _set_objective(self) -> None:
        objective = sum(
            self.problem.distance(i, j) * self.x[(i.id, j.id, k.id)]
            for k in self.vehicles
            for i in self.nodes
            for j in self.nodes
            if i.id != j.id
        )
        self.cqm.set_objective(objective)

    def _add_constraints(self) -> None:
        # 1. Customer Visitation Constraint (Exactly once per customer)
        for customer in self.problem.customers:
            self.cqm.add_constraint(
                sum(
                    self.x[(i.id, customer.id, k.id)]
                    for k in self.vehicles
                    for i in self.nodes
                    if i.id != customer.id
                )
                == 1,
                label=f"visit_once_{customer.id}",
            )

        # 2. Flow Conservation Constraint
        for k in self.vehicles:
            for h in self.nodes:
                inflow = sum(
                    self.x[(i.id, h.id, k.id)] for i in self.nodes if i.id != h.id
                )
                outflow = sum(
                    self.x[(h.id, j.id, k.id)] for j in self.nodes if j.id != h.id
                )
                self.cqm.add_constraint(
                    inflow - outflow == 0, label=f"flow_{h.id}_{k.id}"
                )

        # 3. Capacity & MTZ Subtour Elimination Constraint
        for k in self.vehicles:
            q = {
                i.id: dimod.Integer(
                    f"q_{i.id}_{k.id}", lower_bound=0, upper_bound=k.capacity
                )
                for i in self.nodes
            }
            for i in self.problem.customers:
                for j in self.problem.customers:
                    if i.id != j.id:
                        self.cqm.add_constraint(
                            q[j.id] - q[i.id] - j.demand + k.capacity * (1 - self.x[(i.id, j.id, k.id)]) >= 0,
                            label=f"mtz_{i.id}_{j.id}_{k.id}",
                        )