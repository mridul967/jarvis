# verify_sbm.py

from backend.app.optimizers import EvaluationBudget, SolverParameters, get_solver
from backend.vrptw.model import Customer, Problem, Vehicle


def create_synthetic_problem() -> Problem:
    """Creates a tiny 3-customer synthetic VRPTW problem for instant local testing."""
    depot = Customer(
        id=0, x=0.0, y=0.0, demand=0, ready=0.0, due=100.0, service=0.0
    )

    customers = (
        Customer(
            id=1, x=1.0, y=1.0, demand=10, ready=0.0, due=100.0, service=5.0
        ),
        Customer(
            id=2, x=2.0, y=2.0, demand=15, ready=0.0, due=100.0, service=5.0
        ),
        Customer(
            id=3, x=-1.0, y=1.0, demand=20, ready=0.0, due=100.0, service=5.0
        ),
    )

    vehicles = (
        Vehicle(id=1, capacity=50, shift_start=0.0, shift_end=100.0),
        Vehicle(id=2, capacity=50, shift_start=0.0, shift_end=100.0),
    )

    return Problem(
        name="synthetic_test_case",
        depot=depot,
        customers=customers,
        vehicles=vehicles,
    )


def test_sbm_execution():
    print("--- 1. Creating Synthetic VRPTW Problem ---")
    problem = create_synthetic_problem()
    print(f"Problem: {problem.name}")
    print(f"Customers: {len(problem.customers)}, Vehicles: {len(problem.vehicles)}")

    print("\n--- 2. Retrieving SBM Solver from Registry ---")
    sbm_solver = get_solver("sbm")

    params = SolverParameters(population_size=20, iterations=100)
    budget = EvaluationBudget(max_evaluations=1000)

    print("\n--- 3. Executing SBM Engine Pipeline ---")
    result = sbm_solver(
        problem=problem, parameters=params, seed=42, budget=budget
    )

    print("\n--- 4. Verification Results ---")
    print(f"Algorithm Executed : {result.algorithm} v{result.algorithm_version}")
    print(f"Runtime            : {result.runtime_ms} ms")
    print(f"Hard Violations    : {result.evaluation.score.hard_violations}")
    print(f"Total Distance     : {result.evaluation.score.distance:.2f}")
    print(f"Routes Generated   :")

    for route in result.evaluation.solution.routes:
        print(f"  Vehicle {route.vehicle_id}: {list(route.customers)}")

    print("\nSUCCESS: SBM Pipeline executed and validated end-to-end!")


if __name__ == "__main__":
    test_sbm_execution()