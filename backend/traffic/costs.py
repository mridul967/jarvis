from collections import Counter
from dataclasses import dataclass, field
from math import isfinite

from backend.networks.snapshots import CostSnapshot
from backend.traffic.model import (
    AssignmentResult,
    EndogenousTraffic,
    ExogenousTraffic,
)
from backend.vrptw.evaluate import Evaluation, validate_solution
from backend.vrptw.model import Problem, Solution


class UnreachableArcError(ValueError):
    pass


class MissingTrafficDataError(ValueError):
    pass


@dataclass(frozen=True)
class Costs:
    snapshot: CostSnapshot
    exogenous: ExogenousTraffic | None = None
    endogenous: EndogenousTraffic | None = None
    _index: dict[int, int] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "_index",
            {node_id: index for index, node_id in enumerate(self.snapshot.node_ids)},
        )

    def reachable(self, origin: int, destination: int) -> bool:
        row, column = self._indices(origin, destination)
        return (
            self.snapshot.distances[row][column] is not None
            and self.snapshot.durations[row][column] is not None
        )

    def distance(self, origin: int, destination: int) -> float:
        row, column = self._indices(origin, destination)
        value = self.snapshot.distances[row][column]
        if value is None:
            raise UnreachableArcError(f"Unreachable arc: {origin} -> {destination}")
        return value

    def travel_time(
        self,
        origin: int,
        destination: int,
        departure: float,
        flow: float = 0.0,
    ) -> float:
        if not isfinite(flow) or flow < 0:
            raise ValueError("Flow must be non-negative")
        row, column = self._indices(origin, destination)
        base = self.snapshot.durations[row][column]
        if base is None:
            raise UnreachableArcError(f"Unreachable arc: {origin} -> {destination}")
        travel_time = base
        if self.exogenous:
            travel_time *= _multiplier(self.exogenous, origin, destination, departure)
        if self.endogenous:
            arc = next(
                (
                    arc
                    for arc in self.endogenous.arcs
                    if arc.origin == origin and arc.destination == destination
                ),
                None,
            )
            if arc is None:
                raise MissingTrafficDataError(
                    f"Missing congestion parameters for arc: {origin} -> {destination}"
                )
            travel_time *= 1 + arc.alpha * (flow / arc.capacity) ** arc.beta
        return travel_time

    def base_travel_time(self, origin: int, destination: int) -> float:
        row, column = self._indices(origin, destination)
        value = self.snapshot.durations[row][column]
        if value is None:
            raise UnreachableArcError(f"Unreachable arc: {origin} -> {destination}")
        return value

    def _indices(self, origin: int, destination: int) -> tuple[int, int]:
        try:
            return self._index[origin], self._index[destination]
        except KeyError as error:
            raise ValueError(f"Unknown cost node: {error.args[0]}") from error


def evaluate_solution(
    problem: Problem,
    solution: Solution,
    costs: Costs,
    flows: dict[tuple[int, int, int], float] | None = None,
) -> Evaluation:
    active_flows = flows or {}
    return validate_solution(
        problem,
        solution,
        costs,
        lambda origin, destination, departure: _flow(
            active_flows, costs.endogenous, origin, destination, departure
        ),
    )


def assign_congestion(problem: Problem, solution: Solution, costs: Costs) -> AssignmentResult:
    if costs.endogenous is None:
        raise ValueError("Closed-loop assignment requires endogenous traffic")
    flows: dict[tuple[int, int, int], float] = {}
    residual = 0.0
    evaluation = evaluate_solution(problem, solution, costs, flows)
    for round_number in range(1, costs.endogenous.max_rounds + 1):
        proposed = Counter(
            (
                traversal.origin,
                traversal.destination,
                _bucket(traversal.departure, costs.endogenous.interval_seconds),
            )
            for traversal in evaluation.traversals
        )
        keys = flows.keys() | proposed.keys()
        residual = max(
            (abs(flows.get(key, 0.0) - proposed.get(key, 0.0)) for key in keys), default=0.0
        )
        flows = {key: float(value) for key, value in proposed.items()}
        evaluation = evaluate_solution(problem, solution, costs, flows)
        if residual <= costs.endogenous.tolerance:
            return AssignmentResult(evaluation, flows, round_number, residual, True)
    return AssignmentResult(evaluation, flows, costs.endogenous.max_rounds, residual, False)


def _multiplier(
    traffic: ExogenousTraffic,
    origin: int,
    destination: int,
    departure: float,
) -> float:
    if not traffic.horizon_start <= departure < traffic.horizon_end:
        raise MissingTrafficDataError(f"Departure {departure} is outside the traffic horizon")
    interval = next(
        (
            interval
            for interval in traffic.intervals
            if interval.origin == origin
            and interval.destination == destination
            and interval.start <= departure < interval.end
        ),
        None,
    )
    if interval is None:
        raise MissingTrafficDataError(
            f"Missing exogenous multiplier for arc {origin} -> {destination} at {departure}"
        )
    return interval.multiplier


def _flow(
    flows: dict[tuple[int, int, int], float],
    traffic: EndogenousTraffic | None,
    origin: int,
    destination: int,
    departure: float,
) -> float:
    if traffic is None:
        return 0.0
    return flows.get((origin, destination, _bucket(departure, traffic.interval_seconds)), 0.0)


def _bucket(departure: float, interval_seconds: float) -> int:
    return int(departure // interval_seconds)
