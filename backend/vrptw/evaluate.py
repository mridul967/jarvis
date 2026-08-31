from collections import Counter
from dataclasses import dataclass

import numpy as np

from backend.vrptw.model import Customer, Problem, Route, Solution, Vehicle


@dataclass(frozen=True, order=True)
class Score:
    hard_violations: int
    coverage_errors: int
    vehicles: int
    lateness: float
    travel_time: float
    distance: float
    congestion: float = 0.0


@dataclass(frozen=True)
class RouteEvaluation:
    vehicle_id: int
    load: int
    distance: float
    travel_time: float
    lateness: float
    hard_violations: int


@dataclass(frozen=True)
class Evaluation:
    solution: Solution
    score: Score
    route_evaluations: tuple[RouteEvaluation, ...]

    @property
    def feasible(self) -> bool:
        return self.score.hard_violations == 0 and self.score.coverage_errors == 0

    @property
    def routes(self) -> tuple[tuple[int, ...], ...]:
        return tuple(route.customers for route in self.solution.routes)

    @property
    def distance(self) -> float:
        return self.score.distance

    @property
    def violations(self) -> int:
        return self.score.hard_violations + self.score.coverage_errors


def decode_solution(problem: Problem, keys: np.ndarray) -> Solution:
    if len(keys) != len(problem.customers):
        raise ValueError("Particle dimension does not match customer count")
    order = [problem.customers[index].id for index in np.argsort(keys, kind="stable")]
    routes: list[Route] = []
    current: list[int] = []
    vehicle_index = 0
    customers = {customer.id: customer for customer in problem.customers}

    for customer_id in order:
        while vehicle_index < len(problem.vehicles):
            vehicle = problem.vehicles[vehicle_index]
            candidate = Route(vehicle.id, tuple((*current, customer_id)))
            if not _evaluate_route(problem, vehicle, candidate, customers).hard_violations:
                break
            if current:
                routes.append(Route(vehicle.id, tuple(current)))
                current = []
            vehicle_index += 1
        current.append(customer_id)

    if current:
        vehicle_id = (
            problem.vehicles[vehicle_index].id
            if vehicle_index < len(problem.vehicles)
            else -(vehicle_index + 1)
        )
        routes.append(Route(vehicle_id, tuple(current)))
    return Solution(tuple(routes))


def decode(problem: Problem, keys: np.ndarray) -> Evaluation:
    return validate_solution(problem, decode_solution(problem, keys))


def objective(problem: Problem, keys: np.ndarray) -> Score:
    return decode(problem, keys).score


def validate_solution(problem: Problem, solution: Solution) -> Evaluation:
    customers = {customer.id: customer for customer in problem.customers}
    vehicles = {vehicle.id: vehicle for vehicle in problem.vehicles}
    visits = Counter(customer_id for route in solution.routes for customer_id in route.customers)
    missing = sum(customer_id not in visits for customer_id in customers)
    duplicates = sum(
        max(0, count - 1) for customer_id, count in visits.items() if customer_id in customers
    )
    unknown = sum(count for customer_id, count in visits.items() if customer_id not in customers)
    coverage_errors = missing + duplicates + unknown

    route_evaluations: list[RouteEvaluation] = []
    seen_vehicles: set[int] = set()
    extra_hard_violations = 0
    for route in solution.routes:
        vehicle = vehicles.get(route.vehicle_id)
        if vehicle is None or route.vehicle_id in seen_vehicles:
            extra_hard_violations += 1
        else:
            seen_vehicles.add(route.vehicle_id)
        route_evaluations.append(_evaluate_route(problem, vehicle, route, customers))

    hard_violations = extra_hard_violations + sum(
        route.hard_violations for route in route_evaluations
    )
    score = Score(
        hard_violations=hard_violations,
        coverage_errors=coverage_errors,
        vehicles=sum(bool(route.customers) for route in solution.routes),
        lateness=sum(route.lateness for route in route_evaluations),
        travel_time=sum(route.travel_time for route in route_evaluations),
        distance=sum(route.distance for route in route_evaluations),
    )
    return Evaluation(solution, score, tuple(route_evaluations))


def _evaluate_route(
    problem: Problem,
    vehicle: Vehicle | None,
    route: Route,
    customers: dict[int, Customer],
) -> RouteEvaluation:
    time = max(problem.depot.ready, vehicle.shift_start) if vehicle else problem.depot.ready
    previous: Customer = problem.depot
    distance = 0.0
    travel_time = 0.0
    lateness = 0.0
    load = 0
    hard_violations = 0

    for customer_id in route.customers:
        customer = customers.get(customer_id)
        if customer is None:
            continue
        leg = problem.distance(previous, customer)
        arrival = time + leg
        service_start = max(arrival, customer.ready)
        customer_lateness = max(0.0, service_start - customer.due)
        hard_violations += int(customer_lateness > 0)
        lateness += customer_lateness
        distance += leg
        travel_time += leg
        load += customer.demand
        time = service_start + customer.service
        previous = customer

    return_leg = problem.distance(previous, problem.depot)
    distance += return_leg
    travel_time += return_leg
    return_time = time + return_leg
    if vehicle:
        hard_violations += int(load > vehicle.capacity)
        latest_return = min(problem.depot.due, vehicle.shift_end)
        return_lateness = max(0.0, return_time - latest_return)
        hard_violations += int(return_lateness > 0)
        lateness += return_lateness

    return RouteEvaluation(
        vehicle_id=route.vehicle_id,
        load=load,
        distance=distance,
        travel_time=travel_time,
        lateness=lateness,
        hard_violations=hard_violations,
    )
