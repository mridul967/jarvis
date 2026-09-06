# qaco/physics/qubo_converter.py
from __future__ import annotations
import numpy as np

def extract_edge_bias_from_qubo(Q: np.ndarray | dict, n_nodes: int) -> np.ndarray:
    """
    Transforms a quadratic matrix or dict Q (from CQM formulation) into 
    an (n_nodes x n_nodes) spatial penalty matrix usable by DynamicVRP.
    
    Args:
        Q: Binary quadratic model dictionary or numpy matrix.
        n_nodes: Number of nodes in VRP (depot + customers).
        
    Returns:
        np.ndarray: Symmetric (n_nodes, n_nodes) edge penalty matrix.
    """
    bias = np.zeros((n_nodes, n_nodes))
    
    if isinstance(Q, dict):
        for (u, v), val in Q.items():
            # If variables map directly to node pairs
            if isinstance(u, tuple) and isinstance(v, tuple):
                i, j = u[0], v[0]
                if i < n_nodes and j < n_nodes and i != j:
                    bias[i, j] += val
                    bias[j, i] += val
    elif isinstance(Q, np.ndarray):
        # Direct dimension mapping or slice aggregation
        if Q.shape == (n_nodes, n_nodes):
            bias = (Q + Q.T) / 2.0
            
    # Normalize bias matrix
    max_val = np.max(np.abs(bias))
    if max_val > 0:
        bias = bias / max_val
        
    return bias