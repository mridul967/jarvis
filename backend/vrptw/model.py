from dataclasses import dataclass
from math import hypot


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
class Instance:
    name: str
    vehicle_count: int
    capacity: int
    depot: Customer
    customers: tuple[Customer, ...]

    def distance(self, a: Customer, b: Customer) -> float:
        return hypot(a.x - b.x, a.y - b.y)
