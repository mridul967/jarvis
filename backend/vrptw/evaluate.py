from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

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
class Traversal:
    vehicle_id: int
    origin: int
    destination: int
    departure: float
    arrival: float


class TravelCosts(Protocol):
    def distance(self, origin: int, destination: int) -> float: ...

    def travel_time(
        self, origin: int, destination: int, departure: float, flow: float = 0.0
    ) -> float: ...

    def base_travel_time(self, origin: int, destination: int) -> float: ...


FlowResolver = Callable[[int, int, float], float]


@dataclass(frozen=True)
class Evaluation:
    solution: Solution
    score: Score
    route_evaluations: tuple[RouteEvaluation, ...]
    traversals: tuple[Traversal, ...] = ()

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


def validate_solution(
    problem: Problem,
    solution: Solution,
    costs: TravelCosts | None = None,
    flow_for: FlowResolver | None = None,
) -> Evaluation:
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
    traversals: list[Traversal] = []
    seen_vehicles: set[int] = set()
    extra_hard_violations = 0
    for route in solution.routes:
        vehicle = vehicles.get(route.vehicle_id)
        if vehicle is None or route.vehicle_id in seen_vehicles:
            extra_hard_violations += 1
        else:
            seen_vehicles.add(route.vehicle_id)
        route_evaluation, route_traversals = _trace_route(
            problem, vehicle, route, customers, costs, flow_for
        )
        route_evaluations.append(route_evaluation)
        traversals.extend(route_traversals)

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
        congestion=sum(
            max(
                0.0,
                (traversal.arrival - traversal.departure)
                - costs.base_travel_time(traversal.origin, traversal.destination),
            )
            for traversal in traversals
        )
        if costs
        else 0.0,
    )
    return Evaluation(solution, score, tuple(route_evaluations), tuple(traversals))


def _evaluate_route(
    problem: Problem,
    vehicle: Vehicle | None,
    route: Route,
    customers: dict[int, Customer],
) -> RouteEvaluation:
    return _trace_route(problem, vehicle, route, customers, None, None)[0]


def _trace_route(
    problem: Problem,
    vehicle: Vehicle | None,
    route: Route,
    customers: dict[int, Customer],
    costs: TravelCosts | None,
    flow_for: FlowResolver | None,
) -> tuple[RouteEvaluation, tuple[Traversal, ...]]:
    time = max(problem.depot.ready, vehicle.shift_start) if vehicle else problem.depot.ready
    previous: Customer = problem.depot
    distance = 0.0
    travel_time = 0.0
    lateness = 0.0
    load = 0
    hard_violations = 0
    traversals: list[Traversal] = []
    served = False

    for customer_id in route.customers:
        customer = customers.get(customer_id)
        if customer is None:
            continue
        served = True
        departure = time
        flow = flow_for(previous.id, customer.id, departure) if flow_for else 0.0
        leg_time = (
            costs.travel_time(previous.id, customer.id, departure, flow)
            if costs
            else problem.distance(previous, customer)
        )
        leg_distance = (
            costs.distance(previous.id, customer.id)
            if costs
            else problem.distance(previous, customer)
        )
        arrival = departure + leg_time
        service_start = max(arrival, customer.ready)
        customer_lateness = max(0.0, service_start - customer.due)
        hard_violations += int(customer_lateness > 0)
        lateness += customer_lateness
        distance += leg_distance
        travel_time += leg_time
        load += customer.demand
        time = service_start + customer.service
        traversals.append(Traversal(route.vehicle_id, previous.id, customer.id, departure, arrival))
        previous = customer

    if not served:
        return RouteEvaluation(route.vehicle_id, 0, 0.0, 0.0, 0.0, hard_violations), ()

    departure = time
    flow = flow_for(previous.id, problem.depot.id, departure) if flow_for else 0.0
    return_time_value = (
        costs.travel_time(previous.id, problem.depot.id, departure, flow)
        if costs
        else problem.distance(previous, problem.depot)
    )
    return_distance = (
        costs.distance(previous.id, problem.depot.id)
        if costs
        else problem.distance(previous, problem.depot)
    )
    distance += return_distance
    travel_time += return_time_value
    return_time = departure + return_time_value
    traversals.append(
        Traversal(route.vehicle_id, previous.id, problem.depot.id, departure, return_time)
    )
    if vehicle:
        hard_violations += int(load > vehicle.capacity)
        latest_return = min(problem.depot.due, vehicle.shift_end)
        return_lateness = max(0.0, return_time - latest_return)
        hard_violations += int(return_lateness > 0)
        lateness += return_lateness

    return (
        RouteEvaluation(
            vehicle_id=route.vehicle_id,
            load=load,
            distance=distance,
            travel_time=travel_time,
            lateness=lateness,
            hard_violations=hard_violations,
        ),
        tuple(traversals),
    )
