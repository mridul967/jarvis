"""Service-safe ports of the optimizers defined in ``research/*.ipynb``.

Notebook plotting, installs, and full experiment loops intentionally stay out of
this module. Every variant below shares the production VRPTW decoder and
validator so comparisons cannot quietly use different constraint rules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from itertools import pairwise
from math import exp, pi
from time import perf_counter
from typing import Protocol

import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

from backend.optimizers.model import ConvergencePoint, EvaluationBudget, SolverParameters
from backend.optimizers.swarm import optimize
from backend.vrptw.evaluate import Evaluation, Score, decode_solution, validate_solution
from backend.vrptw.model import Problem, Route, Solution


class Costs(Protocol):
    def distance(self, origin: int, destination: int) -> float: ...

    def travel_time(
        self, origin: int, destination: int, departure: float, flow: float = 0.0
    ) -> float: ...

    def base_travel_time(self, origin: int, destination: int) -> float: ...


@dataclass(frozen=True)
class AlgorithmSpec:
    id: str
    name: str
    family: str
    quantum_inspired: bool
    mechanisms: tuple[str, ...]
    notebook: str


@dataclass(frozen=True)
class PortfolioResult:
    algorithm: str
    evaluation: Evaluation
    convergence: tuple[ConvergencePoint, ...]
    evaluations: int
    runtime_ms: float
    diagnostics: dict[str, float | int | str | bool] = field(default_factory=dict)


ALGORITHMS: dict[str, AlgorithmSpec] = {
    "nearest_neighbor": AlgorithmSpec(
        "nearest_neighbor",
        "Nearest-Neighbour Baseline",
        "constructive",
        False,
        ("greedy nearest feasible customer",),
        "standard_qpso_vrp_benchmark",
    ),
    "random_keys": AlgorithmSpec(
        "random_keys",
        "Random-Keys Baseline",
        "sampling",
        False,
        ("uniform random permutation", "best-of-budget"),
        "standard_qpso_vrp_benchmark",
    ),
    "ortools": AlgorithmSpec(
        "ortools",
        "Google OR-Tools VRPTW",
        "constraint_programming",
        False,
        ("capacity dimension", "time windows", "guided local search"),
        "GAT_SA_ADMR_QPSO_on_synthetic_dataset_across_Google_OR_tools",
    ),
    "dynamic_ors": AlgorithmSpec(
        "dynamic_ors",
        "OR-Tools (Dynamic ORS)",
        "constraint_programming",
        False,
        ("capacity dimension", "time windows", "guided local search", "dynamic distance matrix"),
        "or_tools.py",
    ),
    "pso": AlgorithmSpec(
        "pso",
        "Classical PSO",
        "particle_swarm",
        False,
        ("velocity update", "personal/global best"),
        "standard_qpso_vrp_benchmark",
    ),
    "qpso": AlgorithmSpec(
        "qpso",
        "Standard QPSO",
        "quantum_particle_swarm",
        True,
        ("mean-best attractor", "delta potential well", "Born-style sampling"),
        "standard_qpso_vrp_benchmark",
    ),
    "qrg_qpso": AlgorithmSpec(
        "qrg_qpso",
        "QRG-QPSO + SA-VND",
        "quantum_particle_swarm",
        True,
        ("rotation gate", "sin² Born collapse", "simulated annealing", "VND"),
        "GAT_QPSO_GRQ",
    ),
    "admr_qpso": AlgorithmSpec(
        "admr_qpso",
        "GAT ADMR-QPSO",
        "quantum_particle_swarm",
        True,
        ("multi-swarm", "adaptive diversity", "GAT prior", "SA-VND"),
        "GAT_SA_ADMR_QPSO_on_synthetic_dataset_across_Google_OR_tools",
    ),
    "aco": AlgorithmSpec(
        "aco",
        "Classical ACO",
        "ant_colony",
        False,
        ("pheromone", "distance heuristic", "evaporation"),
        "QACO_Version 2.2",
    ),
    "aco_local_search": AlgorithmSpec(
        "aco_local_search",
        "ACO + Local Search",
        "ant_colony",
        False,
        ("pheromone", "2-opt/relocate/swap"),
        "QACO_Version 2.2",
    ),
    "qaco_rotation": AlgorithmSpec(
        "qaco_rotation",
        "Rotation-Amplitude QACO",
        "quantum_ant_colony",
        True,
        ("qubit-inspired amplitude", "rotation update", "Born probability"),
        "QACO_version 1.0 (Research Paper)",
    ),
    "qaco_interference": AlgorithmSpec(
        "qaco_interference",
        "QACO + Interference",
        "quantum_ant_colony",
        True,
        ("complex amplitudes", "constructive/destructive cross term"),
        "QACO_Version 2.2",
    ),
    "qaco_tunneling": AlgorithmSpec(
        "qaco_tunneling",
        "QACO + Tunnelling",
        "quantum_ant_colony",
        True,
        ("non-local proposal", "bounded barrier acceptance"),
        "QACO_Version 2.2",
    ),
    "qaco_adaptive": AlgorithmSpec(
        "qaco_adaptive",
        "Adaptive QACO",
        "quantum_ant_colony",
        True,
        ("interference", "tunnelling", "adaptive exploration pressure"),
        "QACO_Version 2.2",
    ),
    "qaco_full": AlgorithmSpec(
        "qaco_full",
        "Full QACO + Local Search",
        "quantum_ant_colony",
        True,
        ("interference", "tunnelling", "adaptive control", "local search"),
        "QACO_Version 2.2",
    ),
    "classical_fusion": AlgorithmSpec(
        "classical_fusion",
        "Classical Fusion Control",
        "ant_colony",
        False,
        ("additive traffic/history fusion", "adaptive control", "local search"),
        "QACO_Version 2.2",
    ),
    "dynamic_qaco": AlgorithmSpec(
        "dynamic_qaco",
        "Dynamic Full QACO",
        "quantum_ant_colony",
        True,
        ("persistent shock", "mid-run re-evaluation", "interference", "tunnelling"),
        "QACO_Version 2.2",
    ),
}


_ANT_FLAGS = {
    "aco": {},
    "aco_local_search": {"local_search": True},
    "qaco_rotation": {"rotation": True},
    "qaco_interference": {"interference": True},
    "qaco_tunneling": {"tunnelling": True},
    "qaco_adaptive": {"interference": True, "tunnelling": True, "adaptive": True},
    "qaco_full": {
        "interference": True,
        "tunnelling": True,
        "adaptive": True,
        "local_search": True,
    },
    "classical_fusion": {"classical_fusion": True, "adaptive": True, "local_search": True},
    "dynamic_qaco": {
        "interference": True,
        "tunnelling": True,
        "adaptive": True,
        "local_search": True,
        "dynamic": True,
    },
}


def solve_research(
    problem: Problem,
    costs: Costs,
    algorithm: str,
    parameters: SolverParameters,
    seed: int,
    gat_prior: dict[tuple[int, int], float] | None = None,
    base_costs: Costs | None = None,
) -> PortfolioResult:
    if algorithm not in ALGORITHMS:
        raise ValueError(f"Unknown research algorithm: {algorithm}")
    if algorithm in {"nearest_neighbor", "random_keys"}:
        return _baseline(problem, costs, algorithm, parameters, seed)
    if algorithm == "ortools":
        return _ortools(problem, costs, parameters)
    if algorithm in {"pso", "qpso"}:
        return _standard_swarm(problem, costs, algorithm, parameters, seed, gat_prior)
    if algorithm in {"qrg_qpso", "admr_qpso"}:
        return _quantum_swarm(problem, costs, algorithm, parameters, seed, gat_prior)
    return _ant_colony(
        problem,
        costs,
        algorithm,
        parameters,
        seed,
        gat_prior,
        base_costs or costs,
    )


def _evaluate(problem: Problem, costs: Costs, keys: np.ndarray) -> Evaluation:
    return validate_solution(problem, decode_solution(problem, keys), costs)


def _baseline(
    problem: Problem,
    costs: Costs,
    algorithm: str,
    parameters: SolverParameters,
    seed: int,
) -> PortfolioResult:
    started = perf_counter()
    rng = np.random.default_rng(seed)
    customer_ids = [customer.id for customer in problem.customers]
    candidates: list[np.ndarray] = []
    if algorithm == "nearest_neighbor":
        remaining = set(customer_ids)
        current = problem.depot.id
        order = []
        while remaining:
            current = min(remaining, key=lambda node: costs.travel_time(current, node, 0))
            order.append(current)
            remaining.remove(current)
        candidates.append(_keys_for_order(problem, order))
    else:
        count = parameters.population_size * max(parameters.iterations, 1)
        candidates.extend(rng.random(len(customer_ids)) for _ in range(count))
    evaluations = [_evaluate(problem, costs, keys) for keys in candidates]
    best = min(evaluations, key=lambda item: item.score)
    convergence: list[ConvergencePoint] = []
    incumbent = evaluations[0]
    for index, evaluation in enumerate(evaluations, 1):
        if evaluation.score < incumbent.score:
            incumbent = evaluation
        convergence.append(ConvergencePoint(index, incumbent.score))
    return PortfolioResult(
        algorithm,
        best,
        tuple(convergence),
        len(evaluations),
        round((perf_counter() - started) * 1_000, 2),
        {"deterministic": algorithm == "nearest_neighbor"},
    )


def _ortools(
    problem: Problem,
    costs: Costs,
    parameters: SolverParameters,
) -> PortfolioResult:
    """Small deterministic OR-Tools control ported from the comparison notebook."""
    started = perf_counter()
    nodes = [problem.depot, *problem.customers]
    manager = pywrapcp.RoutingIndexManager(len(nodes), len(problem.vehicles), 0)
    routing = pywrapcp.RoutingModel(manager)

    def transit(from_index: int, to_index: int) -> int:
        origin = nodes[manager.IndexToNode(from_index)]
        destination = nodes[manager.IndexToNode(to_index)]
        return round((costs.travel_time(origin.id, destination.id, 0) + origin.service) * 100)

    transit_index = routing.RegisterTransitCallback(transit)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_index)
    demand_index = routing.RegisterUnaryTransitCallback(
        lambda index: nodes[manager.IndexToNode(index)].demand
    )
    routing.AddDimensionWithVehicleCapacity(
        demand_index,
        0,
        [vehicle.capacity for vehicle in problem.vehicles],
        True,
        "Capacity",
    )
    routing.AddDimension(transit_index, 60_000, 60_000, False, "Time")
    time_dimension = routing.GetDimensionOrDie("Time")
    for node_index, node in enumerate(nodes):
        index = manager.NodeToIndex(node_index)
        time_dimension.CumulVar(index).SetRange(round(node.ready * 100), round(node.due * 100))
    for vehicle_index, vehicle in enumerate(problem.vehicles):
        time_dimension.CumulVar(routing.Start(vehicle_index)).SetRange(
            round(vehicle.shift_start * 100), round(vehicle.shift_end * 100)
        )
        time_dimension.CumulVar(routing.End(vehicle_index)).SetRange(
            round(vehicle.shift_start * 100), round(vehicle.shift_end * 100)
        )

    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search.time_limit.FromMilliseconds(min(1_000, max(100, parameters.iterations * 20)))
    assignment = routing.SolveWithParameters(search)
    if assignment is None:
        raise RuntimeError("OR-Tools found no feasible VRPTW assignment")
    routes = []
    for vehicle_index, vehicle in enumerate(problem.vehicles):
        index = routing.Start(vehicle_index)
        customers = []
        while not routing.IsEnd(index):
            node = manager.IndexToNode(index)
            if node:
                customers.append(nodes[node].id)
            index = assignment.Value(routing.NextVar(index))
        if customers:
            routes.append(Route(vehicle.id, tuple(customers)))
    evaluation = validate_solution(problem, Solution(tuple(routes)), costs)
    return PortfolioResult(
        "ortools",
        evaluation,
        (ConvergencePoint(1, evaluation.score),),
        1,
        round((perf_counter() - started) * 1_000, 2),
        {"status": "feasible" if evaluation.feasible else "invalid"},
    )


def _keys_for_order(problem: Problem, order: list[int]) -> np.ndarray:
    positions = np.zeros(len(problem.customers), dtype=float)
    index = {customer.id: i for i, customer in enumerate(problem.customers)}
    for rank, customer_id in enumerate(order):
        positions[index[customer_id]] = (rank + 1) / (len(order) + 1)
    return positions


def _gat_positions(
    problem: Problem,
    prior: dict[tuple[int, int], float] | None,
    count: int,
    rng: np.random.Generator,
) -> np.ndarray | None:
    if not prior or count <= 0:
        return None
    rows = []
    customers = [customer.id for customer in problem.customers]
    for _ in range(count):
        remaining = set(customers)
        current = problem.depot.id
        order = []
        while remaining:
            choices = sorted(remaining)
            weights = np.asarray([max(prior.get((current, item), 1e-4), 1e-4) for item in choices])
            weights /= weights.sum()
            current = int(rng.choice(choices, p=weights))
            order.append(current)
            remaining.remove(current)
        rows.append(_keys_for_order(problem, order))
    return np.asarray(rows)


def _standard_swarm(
    problem: Problem,
    costs: Costs,
    algorithm: str,
    parameters: SolverParameters,
    seed: int,
    gat_prior: dict[tuple[int, int], float] | None,
) -> PortfolioResult:
    started = perf_counter()
    rng = np.random.default_rng(seed)
    seeds = _gat_positions(problem, gat_prior, max(1, parameters.population_size // 4), rng)
    budget = EvaluationBudget(parameters.population_size * (parameters.iterations + 1))
    result = optimize(
        objective=lambda keys: _evaluate(problem, costs, keys).score,
        dimension=len(problem.customers),
        algorithm=algorithm,
        population_size=parameters.population_size,
        iterations=parameters.iterations,
        seed=seed,
        budget=budget,
        initial_positions=seeds,
    )
    return PortfolioResult(
        algorithm,
        _evaluate(problem, costs, result.best_position),
        result.convergence,
        result.evaluations,
        round((perf_counter() - started) * 1_000, 2),
        {"gat_seeded_particles": 0 if seeds is None else len(seeds)},
    )


def _energy(score: Score) -> float:
    return (
        score.hard_violations * 1e9
        + score.coverage_errors * 1e8
        + score.vehicles * 1e6
        + score.lateness * 1e4
        + score.travel_time * 100
        + score.distance
        + score.congestion
    )


def _anneal(
    problem: Problem,
    costs: Costs,
    keys: np.ndarray,
    rng: np.random.Generator,
    moves: int = 12,
) -> tuple[np.ndarray, Evaluation, int]:
    current = keys.copy()
    current_eval = _evaluate(problem, costs, current)
    best, best_eval = current.copy(), current_eval
    temperature = max(1.0, _energy(current_eval.score) * 0.01)
    evaluations = 1
    for _ in range(moves):
        candidate = current.copy()
        i, j = sorted(rng.choice(len(candidate), 2, replace=False))
        if rng.random() < 0.5:
            candidate[i : j + 1] = candidate[i : j + 1][::-1]
        else:
            candidate[i], candidate[j] = candidate[j], candidate[i]
        candidate_eval = _evaluate(problem, costs, candidate)
        evaluations += 1
        delta = _energy(candidate_eval.score) - _energy(current_eval.score)
        if delta <= 0 or rng.random() < exp(-min(delta / max(temperature, 1e-9), 40)):
            current, current_eval = candidate, candidate_eval
        if candidate_eval.score < best_eval.score:
            best, best_eval = candidate.copy(), candidate_eval
        temperature *= 0.88
    return best, best_eval, evaluations


def _quantum_swarm(
    problem: Problem,
    costs: Costs,
    algorithm: str,
    parameters: SolverParameters,
    seed: int,
    gat_prior: dict[tuple[int, int], float] | None,
) -> PortfolioResult:
    started = perf_counter()
    rng = np.random.default_rng(seed)
    population, dimension = parameters.population_size, len(problem.customers)
    theta = rng.uniform(0, pi / 2, (population, dimension))
    positions = np.sin(theta) ** 2
    seeds = _gat_positions(problem, gat_prior, max(1, population // 3), rng)
    if seeds is not None:
        positions[: len(seeds)] = seeds
        theta[: len(seeds)] = np.arcsin(np.sqrt(np.clip(seeds, 0, 1)))
    pbest_theta = theta.copy()
    pbest_eval = [_evaluate(problem, costs, item) for item in positions]
    evaluations = population
    best_index = min(range(population), key=lambda i: pbest_eval[i].score)
    gbest_theta = pbest_theta[best_index].copy()
    gbest_eval = pbest_eval[best_index]
    convergence = [ConvergencePoint(evaluations, gbest_eval.score)]

    for _iteration in range(parameters.iterations):
        if algorithm == "qrg_qpso":
            r1, r2 = rng.random(theta.shape), rng.random(theta.shape)
            theta = np.mod(
                theta + 0.8 * r1 * (pbest_theta - theta) + 1.2 * r2 * (gbest_theta - theta),
                pi / 2,
            )
            positions = np.sin(theta) ** 2
        else:
            groups = np.array_split(np.arange(population), 3)
            for group_number, indices in enumerate(groups):
                mbest = np.mean(np.sin(pbest_theta[indices]) ** 2, axis=0)
                diversity = float(np.mean(np.linalg.norm(positions[indices] - mbest, axis=1)))
                alpha = (0.5 + 0.5 * exp(-diversity / 0.2)) * (1.2 if group_number == 1 else 1)
                phi = rng.random((len(indices), dimension))
                attractor = phi * (np.sin(pbest_theta[indices]) ** 2) + (1 - phi) * (
                    np.sin(gbest_theta) ** 2
                )
                u = rng.uniform(np.finfo(float).eps, 1, (len(indices), dimension))
                sign = np.where(rng.random((len(indices), dimension)) < 0.5, -1.0, 1.0)
                positions[indices] = np.clip(
                    attractor + sign * alpha * np.abs(mbest - positions[indices]) * np.log(1 / u),
                    0,
                    1,
                )
                theta[indices] = np.arcsin(np.sqrt(positions[indices]))

        current = [_evaluate(problem, costs, item) for item in positions]
        evaluations += population
        elite = min(range(population), key=lambda i: current[i].score)
        if algorithm == "admr_qpso" or current[elite].score <= gbest_eval.score:
            refined, refined_eval, used = _anneal(problem, costs, positions[elite], rng, moves=6)
            evaluations += used
            if refined_eval.score < current[elite].score:
                positions[elite] = refined
                theta[elite] = np.arcsin(np.sqrt(np.clip(refined, 0, 1)))
                current[elite] = refined_eval
        for index, evaluation in enumerate(current):
            if evaluation.score < pbest_eval[index].score:
                pbest_eval[index] = evaluation
                pbest_theta[index] = theta[index].copy()
            if evaluation.score < gbest_eval.score:
                gbest_eval = evaluation
                gbest_theta = theta[index].copy()
        convergence.append(ConvergencePoint(evaluations, gbest_eval.score))

    return PortfolioResult(
        algorithm,
        gbest_eval,
        tuple(convergence),
        evaluations,
        round((perf_counter() - started) * 1_000, 2),
        {
            "gat_seeded_particles": 0 if seeds is None else len(seeds),
            "swarms": 3 if algorithm == "admr_qpso" else 1,
        },
    )


def _construct_ant(
    problem: Problem,
    costs: Costs,
    pheromone: np.ndarray,
    angles: np.ndarray,
    rng: np.random.Generator,
    flags: dict[str, bool],
    gat_prior: dict[tuple[int, int], float] | None,
    base_costs: Costs,
    candidate_k: int,
    traffic_weight: float,
) -> tuple[Solution, float]:
    """Notebook probability-amplitude construction with canonical constraints."""
    node_ids = [problem.depot.id, *(customer.id for customer in problem.customers)]
    index = {node_id: i for i, node_id in enumerate(node_ids)}
    customer_by_id = {customer.id: customer for customer in problem.customers}
    remaining = set(customer_by_id)
    routes: list[Route] = []
    cross_total = 0.0

    for vehicle in problem.vehicles:
        if not remaining:
            break
        route: list[int] = []
        current = problem.depot.id
        load = 0
        clock = max(problem.depot.ready, vehicle.shift_start)
        while remaining:
            feasible = []
            for customer_id in remaining:
                customer = customer_by_id[customer_id]
                arrival = clock + costs.travel_time(current, customer_id, clock)
                if load + customer.demand <= vehicle.capacity and arrival <= customer.due:
                    feasible.append(customer_id)
            if not feasible:
                break
            feasible.sort(key=lambda node: costs.travel_time(current, node, clock))
            feasible = feasible[:candidate_k]
            current_index = index[current]
            candidate_indices = np.asarray([index[node] for node in feasible], dtype=int)
            travel = np.asarray(
                [max(costs.travel_time(current, node, clock), 1e-9) for node in feasible]
            )
            history = pheromone[current_index, candidate_indices] * (1 / travel) ** 2.5
            history /= max(float(history.max()), 1e-12)

            if flags.get("rotation"):
                history *= np.sin(angles[current_index, candidate_indices]) ** 2
            if gat_prior:
                history *= np.asarray(
                    [0.25 + max(gat_prior.get((current, node), 0.0), 0.0) for node in feasible]
                )

            base = np.asarray(
                [max(base_costs.travel_time(current, node, clock), 1e-9) for node in feasible]
            )
            signed_traffic = np.clip(base / travel - 1, -0.95, 2.0)
            if flags.get("interference"):
                phase = np.minimum(
                    pi * np.clip(-signed_traffic, 0, 1),
                    0.85 * pi,
                )
                history_amplitude = np.sqrt(np.maximum(history, 0)).astype(complex)
                traffic_amplitude = (
                    traffic_weight
                    * np.sqrt(np.clip(np.abs(signed_traffic), 0, 1))
                    * np.exp(1j * phase)
                )
                cross = 2 * np.real(np.conj(history_amplitude) * traffic_amplitude)
                cross_total += float(cross.sum())
                weights = np.abs(history_amplitude + traffic_amplitude) ** 2
            elif flags.get("classical_fusion"):
                weights = np.maximum(history + traffic_weight * signed_traffic, 1e-10)
            else:
                weights = np.maximum(history, 1e-10)
            probabilities = weights / weights.sum()
            chosen = int(rng.choice(feasible, p=probabilities))
            customer = customer_by_id[chosen]
            clock = (
                max(clock + costs.travel_time(current, chosen, clock), customer.ready)
                + customer.service
            )
            load += customer.demand
            route.append(chosen)
            remaining.remove(chosen)
            current = chosen
        if route:
            routes.append(Route(vehicle.id, tuple(route)))

    # Deterministic repair keeps missing-customer failures visible only when the
    # declared fleet is genuinely too small.
    for customer_id in sorted(remaining):
        for vehicle in problem.vehicles[len(routes) :]:
            customer = customer_by_id[customer_id]
            if customer.demand <= vehicle.capacity:
                routes.append(Route(vehicle.id, (customer_id,)))
                remaining.remove(customer_id)
                break
    return Solution(tuple(routes)), cross_total


def _solution_keys(problem: Problem, solution: Solution) -> np.ndarray:
    order = [customer for route in solution.routes for customer in route.customers]
    missing = [customer.id for customer in problem.customers if customer.id not in order]
    return _keys_for_order(problem, [*order, *missing])


def _tunnel(
    problem: Problem,
    costs: Costs,
    solution: Solution,
    rng: np.random.Generator,
    iteration: int,
    iterations: int,
    stagnation: int,
) -> tuple[Solution, Evaluation, bool]:
    keys = _solution_keys(problem, solution)
    current_eval = validate_solution(problem, solution, costs)
    candidate = keys.copy()
    if len(candidate) > 3:
        a = int(rng.integers(0, len(candidate) - 2))
        b = int(rng.integers(a + 2, len(candidate) + 1))
        candidate[a:b] = candidate[a:b][::-1]
    candidate_solution = decode_solution(problem, candidate)
    candidate_eval = validate_solution(problem, candidate_solution, costs)
    old, new = _energy(current_eval.score), _energy(candidate_eval.score)
    if new <= old:
        return candidate_solution, candidate_eval, True
    relative_barrier = (new - old) / max(abs(old), 1e-12)
    if relative_barrier > 0.18:
        return solution, current_eval, False
    temperature = (
        0.18 * (0.3 + 0.7 * (1 - iteration / max(iterations, 1))) * (1 + min(stagnation / 14, 2))
    )
    accepted = rng.random() < exp(-min(relative_barrier / max(temperature, 1e-12), 40))
    return (
        (candidate_solution, candidate_eval, True) if accepted else (solution, current_eval, False)
    )


def _ant_colony(
    problem: Problem,
    costs: Costs,
    algorithm: str,
    parameters: SolverParameters,
    seed: int,
    gat_prior: dict[tuple[int, int], float] | None,
    base_costs: Costs,
) -> PortfolioResult:
    started = perf_counter()
    rng = np.random.default_rng(seed)
    flags = _ANT_FLAGS[algorithm]
    size = len(problem.customers) + 1
    pheromone = np.ones((size, size), dtype=float)
    np.fill_diagonal(pheromone, 0)
    angles = np.full((size, size), pi / 4, dtype=float)
    np.fill_diagonal(angles, 0)
    best_solution: Solution | None = None
    best_evaluation: Evaluation | None = None
    convergence: list[ConvergencePoint] = []
    evaluations = 0
    stagnation = 0
    tunnel_attempts = tunnel_accepts = 0
    cross_total = 0.0
    shock_iteration = max(1, int(parameters.iterations * 0.4))
    active_costs = base_costs if flags.get("dynamic") else costs

    for iteration in range(parameters.iterations):
        if flags.get("dynamic") and iteration == shock_iteration:
            active_costs = costs
            if best_solution is not None:
                best_evaluation = validate_solution(problem, best_solution, active_costs)
                evaluations += 1
        pressure = min(stagnation / 14, 1.0) if flags.get("adaptive") else 0.0
        candidate_k = min(size - 1, 8 + round(4 * pressure))
        traffic_weight = 0.45 * (1 + 1.4 * pressure)
        rho = min(0.45, 0.18 + 0.22 * pressure)
        population: list[tuple[Solution, Evaluation]] = []

        for _ in range(parameters.population_size):
            solution, cross = _construct_ant(
                problem,
                active_costs,
                pheromone,
                angles,
                rng,
                flags,
                gat_prior,
                base_costs,
                candidate_k,
                traffic_weight,
            )
            evaluation = validate_solution(problem, solution, active_costs)
            evaluations += 1
            cross_total += cross
            population.append((solution, evaluation))

        population.sort(key=lambda pair: pair[1].score)
        candidate_solution, candidate_evaluation = population[0]
        if flags.get("local_search"):
            refined, refined_evaluation, used = _anneal(
                problem,
                active_costs,
                _solution_keys(problem, candidate_solution),
                rng,
                moves=6,
            )
            evaluations += used
            if refined_evaluation.score < candidate_evaluation.score:
                candidate_solution = decode_solution(problem, refined)
                candidate_evaluation = refined_evaluation

        if best_evaluation is None or candidate_evaluation.score < best_evaluation.score:
            best_solution, best_evaluation = candidate_solution, candidate_evaluation
            stagnation = 0
        else:
            stagnation += 1

        if flags.get("tunnelling") and best_solution is not None and stagnation >= 4:
            tunnel_attempts += 1
            tunneled, tunnel_eval, accepted = _tunnel(
                problem,
                active_costs,
                best_solution,
                rng,
                iteration,
                parameters.iterations,
                stagnation,
            )
            evaluations += 1
            if accepted:
                tunnel_accepts += 1
                best_solution, best_evaluation = tunneled, tunnel_eval

        pheromone *= 1 - rho
        node_index = {problem.depot.id: 0} | {
            customer.id: i + 1 for i, customer in enumerate(problem.customers)
        }
        for solution, evaluation in population[: max(1, len(population) // 4)]:
            deposit = 12 / max(_energy(evaluation.score), 1e-9)
            for route in solution.routes:
                path = [problem.depot.id, *route.customers, problem.depot.id]
                for origin, destination in pairwise(path):
                    pheromone[node_index[origin], node_index[destination]] += deposit
        pheromone = np.maximum(pheromone, 1e-9)

        if flags.get("rotation") and best_solution is not None:
            selected = set()
            for route in best_solution.routes:
                path = [problem.depot.id, *route.customers, problem.depot.id]
                selected.update(pairwise(path))
            for origin, destination in selected:
                angles[node_index[origin], node_index[destination]] = np.clip(
                    angles[node_index[origin], node_index[destination]] + pi / 90,
                    0,
                    pi / 2,
                )

        if best_evaluation is not None:
            convergence.append(ConvergencePoint(evaluations, best_evaluation.score))

    if best_solution is None or best_evaluation is None:
        raise RuntimeError("Ant colony produced no candidate")
    final_evaluation = validate_solution(problem, best_solution, costs)
    return PortfolioResult(
        algorithm,
        final_evaluation,
        tuple(convergence),
        evaluations,
        round((perf_counter() - started) * 1_000, 2),
        {
            "gat_prior_edges": len(gat_prior or {}),
            "interference_cross_term": round(cross_total, 6),
            "tunnel_attempts": tunnel_attempts,
            "tunnel_accepts": tunnel_accepts,
            "shock_iteration": shock_iteration if flags.get("dynamic") else -1,
        },
    )
