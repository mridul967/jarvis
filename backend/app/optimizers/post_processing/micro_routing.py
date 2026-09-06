from backend.vrptw.model import Customer, Problem, Route, Solution


class MicroRouter:
    """Applies deterministic 2-opt local search polishing to macro-clustered routes."""

    def __init__(self, problem: Problem):
        self.problem = problem
        self.cust_map: dict[int, Customer] = {c.id: c for c in problem.customers}
        self.cust_map[0] = problem.depot

    def optimize_solution(self, solution: Solution) -> Solution:
        polished_routes = []
        for route in solution.routes:
            if len(route.customers) <= 2:
                polished_routes.append(route)
            else:
                optimized_custs = self._two_opt(list(route.customers))
                polished_routes.append(
                    Route(
                        vehicle_id=route.vehicle_id, customers=tuple(optimized_custs)
                    )
                )

        return Solution(routes=tuple(polished_routes))

    def _two_opt(self, route: list[int]) -> list[int]:
        best = route
        improved = True
        while improved:
            improved = False
            for i in range(len(best) - 1):
                for j in range(i + 1, len(best)):
                    if j - i == 1:
                        continue
                    new_route = best[:i] + best[i:j][::-1] + best[j:]
                    if self._route_distance(new_route) < self._route_distance(best):
                        best = new_route
                        improved = True
                        break
                if improved:
                    break
        return best

    def _route_distance(self, route: list[int]) -> float:
        if not route:
            return 0.0
        dist = self.problem.distance(self.cust_map[0], self.cust_map[route[0]])
        for idx in range(len(route) - 1):
            dist += self.problem.distance(
                self.cust_map[route[idx]], self.cust_map[route[idx + 1]]
            )
        dist += self.problem.distance(self.cust_map[route[-1]], self.cust_map[0])
        return dist