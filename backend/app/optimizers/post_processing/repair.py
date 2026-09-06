from backend.vrptw.model import Problem, Route, Solution


class ConstraintRepair:
    """Repairs raw heuristic route assignments to ensure valid node coverage and structure."""

    def __init__(self, problem: Problem):
        self.problem = problem
        self.customer_ids = {c.id for c in problem.customers}

    def repair_solution(self, raw_solution: Solution) -> Solution:
        visited = set()
        cleaned_routes = []

        # Step 1: Remove duplicate visits across routes
        for route in raw_solution.routes:
            filtered_customers = []
            for customer_id in route.customers:
                if customer_id in self.customer_ids and customer_id not in visited:
                    visited.add(customer_id)
                    filtered_customers.append(customer_id)
            cleaned_routes.append(
                Route(vehicle_id=route.vehicle_id, customers=tuple(filtered_customers))
            )

        # Step 2: Assign unvisited customers to available vehicles via greedy insertion
        unvisited = self.customer_ids - visited
        if unvisited:
            cleaned_routes = self._insert_unvisited(cleaned_routes, list(unvisited))

        return Solution(routes=tuple(cleaned_routes))

    def _insert_unvisited(self, routes: list[Route], unvisited: list[int]) -> list[Route]:
        routes_dict = {r.vehicle_id: list(r.customers) for r in routes}
        vehicle_ids = [v.id for v in self.problem.vehicles]

        for customer_id in unvisited:
            assigned = False
            for v_id in vehicle_ids:
                if v_id not in routes_dict:
                    routes_dict[v_id] = []
                # Append unassigned customer to vehicle route
                routes_dict[v_id].append(customer_id)
                assigned = True
                break

            if not assigned:
                routes_dict[vehicle_ids[0]].append(customer_id)

        return [
            Route(vehicle_id=v_id, customers=tuple(custs))
            for v_id, custs in routes_dict.items()
        ]