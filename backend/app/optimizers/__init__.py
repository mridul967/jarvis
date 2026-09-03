"""Optimization algorithms."""
"""Optimization algorithms and unified registry."""

from backend.app.optimizers.model import (
    CancelCheck,
    ConvergencePoint,
    EvaluationBudget,
    SolverParameters,
    SolverResult,
)
from backend.app.optimizers.registry import (
    SOLVERS,
    get_solver,
    solve_pso,
    solve_qpso,
    solve_sbm,
)

__all__ = [
    "SOLVERS",
    "get_solver",
    "solve_pso",
    "solve_qpso",
    "solve_sbm",
    "SolverParameters",
    "EvaluationBudget",
    "SolverResult",
    "ConvergencePoint",
    "CancelCheck",
]