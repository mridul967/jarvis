# qaco/utils/metrics.py
from __future__ import annotations
from typing import Sequence
import numpy as np
from qaco.domain.solution import Solution, edge_set

def solution_diversity(pop: Sequence[Solution]) -> float:
    """Mean Jaccard edge distance across a population."""
    if len(pop) < 2:
        return 0.0
    vals = []
    for a in range(len(pop)):
        for b in range(a):
            x, y = edge_set(pop[a]), edge_set(pop[b])
            vals.append(1 - len(x & y) / max(1, len(x | y)))
    return float(np.mean(vals))

def entropy(tau: np.ndarray) -> float:
    p = tau / (tau.sum(axis=1, keepdims=True) + 1e-12)
    return float(np.mean(-np.sum(p * np.log(p + 1e-12), axis=1) / np.log(len(tau))))