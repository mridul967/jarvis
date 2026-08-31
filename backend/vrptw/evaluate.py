from dataclasses import dataclass

import numpy as np

from backend.vrptw.model import Customer, Instance


@dataclass(frozen=True)
class Evaluation:
    routes: tuple[tuple[int, ...], ...]
    distance: float
    violations: int

    @property
    def feasible(self) -> bool:
        return self.violations == 0


def decode(instance: Instance, keys: np.ndarray) -> Evaluation:
    if len(keys) != len(instance.customers):
        raise ValueError("Particle dimension does not match customer count")
    order = [instance.customers[index] for index in np.argsort(keys, kind="stable")]
    routes: list[tuple[int, ...]] = []
    current: list[Customer] = []

    for customer in order:
        if current and not _route_feasible(instance, [*current, customer]):
            routes.append(tuple(item.id for item in current))
            current = []
        current.append(customer)
    if current:
        routes.append(tuple(item.id for item in current))

    by_id = {customer.id: customer for customer in instance.customers}
    distance = sum(_route_distance(instance, [by_id[item] for item in route]) for route in routes)
    violations = max(0, len(routes) - instance.vehicle_count)
    violations += sum(
        not _route_feasible(instance, [by_id[item] for item in route]) for route in routes
    )
    return Evaluation(tuple(routes), round(distance, 3), int(violations))


def objective(instance: Instance, keys: np.ndarray) -> float:
    result = decode(instance, keys)
    # A violation must dominate every plausible distance improvement.
    return result.distance + result.violations * 1_000_000


def _route_feasible(instance: Instance, route: list[Customer]) -> bool:
    if sum(customer.demand for customer in route) > instance.capacity:
        return False
    time = 0.0
    previous = instance.depot
    for customer in route:
        arrival = time + instance.distance(previous, customer)
        if arrival > customer.due:
            return False
        time = max(arrival, customer.ready) + customer.service
        previous = customer
    return time + instance.distance(previous, instance.depot) <= instance.depot.due


def _route_distance(instance: Instance, route: list[Customer]) -> float:
    previous = instance.depot
    distance = 0.0
    for customer in route:
        distance += instance.distance(previous, customer)
        previous = customer
    return distance + instance.distance(previous, instance.depot)
