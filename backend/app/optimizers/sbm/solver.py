from time import perf_counter
import simulated_bifurcation as sb
import torch

from backend.app.optimizers.cqm.modeler import VRPTWCQMModeler
from backend.app.optimizers.cqm.translator import BranchingTranslator
from backend.app.optimizers.model import (
    CancelCheck,
    ConvergencePoint,
    EvaluationBudget,
    SolverParameters,
    SolverResult,
)
from backend.app.optimizers.post_processing.micro_routing import MicroRouter
from backend.app.optimizers.post_processing.repair import ConstraintRepair
from backend.vrptw.evaluate import validate_solution
from backend.vrptw.model import Problem, Route, Solution


def solve_sbm(
    problem: Problem,
    parameters: SolverParameters,
    seed: int,
    budget: EvaluationBudget,
    warm_start: Solution | None = None,
    should_cancel: CancelCheck | None = None,
) -> SolverResult:
    if warm_start is not None:
        raise ValueError("Warm starts are not implemented for SBM in Phase 1")

    started = perf_counter()

    # Step 1: CQM Abstraction Tier
    modeler = VRPTWCQMModeler(problem)
    cqm = modeler.build_model()

    # Step 2: Branching Translator Tier (QUBO Path)
    translator = BranchingTranslator(cqm)
    qubo_matrix, var_to_idx = translator.to_qubo()
    idx_to_var = {v: k for k, v in var_to_idx.items()}

    # Step 3: Hybrid Optimization Tier (SBM Quantum Physics Engine)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    Q_tensor = torch.tensor(qubo_matrix, dtype=torch.float32, device=device)

    # Clean native call to Simulated Bifurcation Engine with explicitly required 'domain'
    best_state, _ = sb.minimize(
        Q_tensor,
        domain="binary",
        agents=parameters.population_size,
        max_steps=parameters.iterations,
    )

    # Convert PyTorch tensor to 1D NumPy array
    if isinstance(best_state, torch.Tensor):
        binary_solution = best_state.cpu().numpy().flatten()
    else:
        binary_solution = best_state.flatten()

    raw_solution = _decode_binary_state(binary_solution, idx_to_var, problem)

    # Step 4: Post-Processing & Hybrid Refinement Tier
    repair_engine = ConstraintRepair(problem)
    repaired_solution = repair_engine.repair_solution(raw_solution)

    micro_router = MicroRouter(problem)
    final_solution = micro_router.optimize_solution(repaired_solution)

    # Step 5: Authoritative External Validation Check
    evaluation = validate_solution(problem, final_solution)
    runtime_ms = round((perf_counter() - started) * 1_000, 2)

    return SolverResult(
        algorithm="sbm",
        algorithm_version="1.0.0",
        parameters=parameters,
        seed=seed,
        budget=budget,
        evaluation=evaluation,
        convergence=(ConvergencePoint(evaluations=1, score=evaluation.score),),
        evaluations=1,
        runtime_ms=runtime_ms,
        cancelled=False,
    )


def _decode_binary_state(
    binary_solution: list[float] | torch.Tensor,
    idx_to_var: dict[int, str],
    problem: Problem,
) -> Solution:
    active_edges = []
    for idx, val in enumerate(binary_solution):
        if val == 1.0 or val == 1:
            raw_var = idx_to_var.get(idx)
            if raw_var is not None: 
                var_str = str(raw_var[0]) if isinstance(raw_var, tuple)  else str(raw_var)

                if var_str.startswith("x_"):
                     parts = var_str.split("_")
                     u, v, k = int(parts[1]), int(parts[2]), int(parts[3])
                     active_edges.append((u, v, k))
               

    routes_out = []
    for vehicle in problem.vehicles:
        v_edges = [(u, v) for u, v, k in active_edges if k == vehicle.id]
        route_nodes = []
        current_node = 0
        while v_edges:
            next_step = next((v for u, v in v_edges if u == current_node), None)
            if next_step is None or next_step == 0:
                break
            route_nodes.append(next_step)
            v_edges = [(u, v) for u, v in v_edges if u != current_node]
            current_node = next_step

        routes_out.append(Route(vehicle_id=vehicle.id, customers=tuple(route_nodes)))

    return Solution(routes=tuple(routes_out))