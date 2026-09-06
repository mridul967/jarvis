# config.py
from __future__ import annotations

CFG: dict[str, object] = {
    'seed': 17,
    'n_customers': 18,
    'n_vehicles': 5,
    'capacity': 12.0,

    'num_ants': 14,
    'iterations': 160,

    'candidate_k': 8,
    'candidate_k_min': 4,
    'candidate_k_max': 14,

    'alpha': 1.0,
    'beta': 2.5,

    'rho': 0.18,
    'rho_min': 0.10,
    'rho_max': 0.45,
    'deposit': 12.0,

    'history_weight': 1.0,
    'traffic_weight': 0.45,
    'positive_change_sensitivity': 3.0,

    'traffic_drift': 0.22,
    'shock_strength': 4.0,
    'shock_iterations': (40, 85, 130),
    'shock_edge_fraction': 0.25,
    'shock_duration': 40,

    'volatility_reconstruct_threshold': 0.02,
    'reconstruct_cooldown': 3,

    'S_max': 14,
    'tunnel_temperature': 0.18,
    'tunnel_barrier_max': 0.18,

    'objective_distance': 0.25,
    'objective_time': 1.0,
    'objective_congestion': 1.75,
    'objective_vehicles': 0.10,
    'penalty': 10_000.0,

    'local_search_moves': 2,
    'time_windows': False,

    'phase_congestion_scale': 1.0,
    'phase_worsening_scale': 0.35,
    'phase_max_fraction': 0.85,
    'interference_baseline': 0.15,

    # --- CQM / QUBO Specific Extensions ---
    'qubo_matrix': None,      # Set to an (N, N) ndarray when CQM layer is active
    'qubo_weight': 0.5,       # Blending factor for QUBO penalty vs Euclidean base distance
}

FLAGS = {
    'interference_on': False,
    'tunneling_on': False,
    'local_search_on': False,
    'adaptive_on': False,
    'dynamic_on': False,
    'classical_fusion_control': False,
    'partial_reconstruct_on': False,
}