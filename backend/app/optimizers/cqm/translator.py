from collections.abc import Callable
import dimod
import numpy as np


class BranchingTranslator:
    """Takes a CQM and branches it into a QUBO matrix or a continuous penalty function."""

    def __init__(self, cqm: dimod.ConstrainedQuadraticModel):
        self.cqm = cqm

    def to_qubo(self, penalty_multiplier: float = 1000.0) -> tuple[np.ndarray, dict[str, int]]:
        """
        Path 2: QUBO Matrix Translator (For SBM Engine).
        Converts CQM constraints into an upper-triangular QUBO matrix.
        """
        bqm, _ = dimod.cqm_to_bqm(self.cqm, lagrange_multiplier=penalty_multiplier)
        
        # dimod's bqm.to_qubo() returns (qubo_dict, offset)
        qubo_dict, _ = bqm.to_qubo()

        num_vars = len(bqm.variables)
        var_to_idx = {var: i for i, var in enumerate(bqm.variables)}

        Q = np.zeros((num_vars, num_vars), dtype=np.float64)

        # Map qubo_dict keys (tuple of var names) to matrix indices
        for (u, v), bias in qubo_dict.items():
            i, j = var_to_idx[u], var_to_idx[v]
            if i > j:
                i, j = j, i
            Q[i, j] += bias

        return Q, var_to_idx

    def to_penalty_function(
        self, penalty_multiplier: float = 1000.0
    ) -> tuple[Callable[[dict], float], list]:
        """
        Path 1: Continuous/Discrete Penalty Translator (For QPSO & QACO Engines).
        Generates a penalized fitness function where hard constraints become cost multipliers.
        """
        bqm, _ = dimod.cqm_to_bqm(self.cqm, lagrange_multiplier=penalty_multiplier)
        variables = list(bqm.variables)

        def evaluate_penalty(sample: dict) -> float:
            return bqm.energy(sample)

        return evaluate_penalty, variables