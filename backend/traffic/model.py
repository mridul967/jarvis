from dataclasses import dataclass, field
from itertools import pairwise
from math import isfinite
from typing import Literal

from backend.vrptw.evaluate import Evaluation

TrafficSource = Literal["simulated", "historical_replay", "live"]


@dataclass(frozen=True)
class ArcMultiplier:
    origin: int
    destination: int
    start: float
    end: float
    multiplier: float

    def __post_init__(self) -> None:
        if self.origin < 0 or self.destination < 0:
            raise ValueError("Traffic arc node ids must be non-negative")
        if not all(isfinite(value) for value in (self.start, self.end, self.multiplier)):
            raise ValueError("Exogenous interval values must be finite")
        if self.start >= self.end or self.multiplier <= 0:
            raise ValueError("Exogenous intervals require start < end and multiplier > 0")


@dataclass(frozen=True)
class ExogenousTraffic:
    source_type: TrafficSource
    timezone: str
    horizon_start: float
    horizon_end: float
    intervals: tuple[ArcMultiplier, ...]
    source: str
    generator_seed: int | None = None
    generator_parameters: dict[str, int | float | str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.source_type not in {"simulated", "historical_replay", "live"}:
            raise ValueError("Invalid exogenous traffic source type")
        if not self.timezone.strip() or not self.source.strip():
            raise ValueError("Exogenous traffic requires timezone and source")
        if not isfinite(self.horizon_start) or not isfinite(self.horizon_end):
            raise ValueError("Traffic horizon must be finite")
        if self.horizon_start >= self.horizon_end or not self.intervals:
            raise ValueError("Traffic requires a non-empty positive horizon")
        if any(
            isinstance(value, int | float) and not isfinite(value)
            for value in self.generator_parameters.values()
        ):
            raise ValueError("Generator parameters must be finite")
        grouped: dict[tuple[int, int], list[ArcMultiplier]] = {}
        for interval in self.intervals:
            if interval.start < self.horizon_start or interval.end > self.horizon_end:
                raise ValueError("Traffic interval lies outside the declared horizon")
            grouped.setdefault((interval.origin, interval.destination), []).append(interval)
        for intervals in grouped.values():
            ordered = sorted(intervals, key=lambda interval: interval.start)
            if ordered[0].start != self.horizon_start or ordered[-1].end != self.horizon_end:
                raise ValueError("Every declared traffic arc must cover the full horizon")
            if any(left.end != right.start for left, right in pairwise(ordered)):
                raise ValueError("Traffic intervals must be contiguous and non-overlapping")


@dataclass(frozen=True)
class ArcCongestion:
    origin: int
    destination: int
    capacity: float
    alpha: float
    beta: float

    def __post_init__(self) -> None:
        if self.origin < 0 or self.destination < 0:
            raise ValueError("Congestion arc node ids must be non-negative")
        if not all(isfinite(value) for value in (self.capacity, self.alpha, self.beta)):
            raise ValueError("Congestion parameters must be finite")
        if self.capacity <= 0 or self.alpha < 0 or self.beta <= 0:
            raise ValueError("Congestion requires capacity > 0, alpha >= 0, and beta > 0")


@dataclass(frozen=True)
class EndogenousTraffic:
    arcs: tuple[ArcCongestion, ...]
    flow_unit: str
    interval_seconds: float
    assignment_rule: Literal["simultaneous_vehicle_count"]
    tolerance: float
    max_rounds: int

    def __post_init__(self) -> None:
        if not self.arcs or not self.flow_unit.strip():
            raise ValueError("Endogenous traffic requires arc parameters and a flow unit")
        if not isfinite(self.interval_seconds) or not isfinite(self.tolerance):
            raise ValueError("Congestion interval and tolerance must be finite")
        if self.interval_seconds <= 0 or self.tolerance < 0 or self.max_rounds <= 0:
            raise ValueError("Invalid congestion interval, tolerance, or maximum rounds")
        if self.assignment_rule != "simultaneous_vehicle_count":
            raise ValueError("Unsupported congestion assignment rule")
        pairs = [(arc.origin, arc.destination) for arc in self.arcs]
        if len(pairs) != len(set(pairs)):
            raise ValueError("Congestion arc parameters must be unique")


@dataclass(frozen=True)
class AssignmentResult:
    evaluation: Evaluation
    flows: dict[tuple[int, int, int], float]
    rounds: int
    residual: float
    converged: bool
