from dataclasses import dataclass
from math import hypot, isfinite


@dataclass(frozen=True)
class Customer:
    id: int
    x: float
    y: float
    demand: int
    ready: float
    due: float
    service: float


@dataclass(frozen=True)
class Vehicle:
    id: int
    capacity: int
    shift_start: float
    shift_end: float
    start_node: int = 0
    end_node: int = 0
    fixed_cost: float = 0.0


@dataclass(frozen=True)
class Route:
    vehicle_id: int
    customers: tuple[int, ...]


@dataclass(frozen=True)
class Solution:
    routes: tuple[Route, ...]


@dataclass(frozen=True)
class Problem:
    name: str
    depot: Customer
    customers: tuple[Customer, ...]
    vehicles: tuple[Vehicle, ...]

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Problem name is required")
        if self.depot.id != 0:
            raise ValueError("Depot id must be 0")
        if self.depot.demand != 0:
            raise ValueError("Depot demand must be 0")
        if not self.vehicles:
            raise ValueError("At least one vehicle is required")

        customer_ids = [customer.id for customer in self.customers]
        if any(customer_id <= 0 for customer_id in customer_ids):
            raise ValueError("Customer ids must be positive")
        if len(customer_ids) != len(set(customer_ids)):
            raise ValueError("Customer ids must be unique")
        if len({vehicle.id for vehicle in self.vehicles}) != len(self.vehicles):
            raise ValueError("Vehicle ids must be unique")
        if any(vehicle.id < 0 for vehicle in self.vehicles):
            raise ValueError("Vehicle ids must be non-negative")

        for node in (self.depot, *self.customers):
            if not all(
                isfinite(value) for value in (node.x, node.y, node.ready, node.due, node.service)
            ):
                raise ValueError("Node values must be finite")
            if node.demand < 0 or node.service < 0:
                raise ValueError("Demand and service time must be non-negative")
            if node.ready > node.due:
                raise ValueError("Ready time must not exceed due time")
        for vehicle in self.vehicles:
            if not all(
                isfinite(value)
                for value in (vehicle.shift_start, vehicle.shift_end, vehicle.fixed_cost)
            ):
                raise ValueError("Vehicle values must be finite")
            if vehicle.capacity <= 0:
                raise ValueError("Vehicle capacity must be positive")
            if vehicle.fixed_cost < 0:
                raise ValueError("Vehicle fixed cost must be non-negative")
            if vehicle.shift_start > vehicle.shift_end:
                raise ValueError("Vehicle shift start must not exceed shift end")
            if vehicle.start_node != self.depot.id or vehicle.end_node != self.depot.id:
                raise ValueError("Phase 1 supports a single shared depot")

    def distance(self, a: Customer, b: Customer) -> float:
        return hypot(a.x - b.x, a.y - b.y)


# ponytail: compatibility alias; remove when external callers use Problem.
Instance = Problem
