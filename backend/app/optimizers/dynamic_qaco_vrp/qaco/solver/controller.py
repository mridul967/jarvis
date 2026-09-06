from __future__ import annotations
from dataclasses import dataclass
from typing import Mapping
import numpy as np

@dataclass
class AdaptiveController:
    """Maps observed search state into bounded exploration/exploitation controls."""
    cfg: Mapping[str, object]

    def controls(
        self,
        stagnation: int,
        diversity: float,
        volatility: float,
        ls_fail: int,
        adaptive: bool
    ) -> dict[str, float]:
        stag = stagnation / max(float(self.cfg['S_max']), 1.0)

        if adaptive:
            pressure = np.clip(
                0.45 * stag +
                0.25 * (1.0 - diversity) +
                3.0 * volatility +
                0.12 * ls_fail,
                0.0,
                1.0
            )
        else:
            # Even without full adaptation, tunneling should respond to stagnation.
            pressure = np.clip(stag, 0.0, 1.0)

        traffic_weight = float(self.cfg['traffic_weight'])
        candidate_k = int(self.cfg['candidate_k'])
        rho = float(self.cfg['rho'])
        ls_budget = int(self.cfg['local_search_moves'])

        if adaptive:
            traffic_weight = float(np.clip(
                traffic_weight * (1.0 + 1.4 * pressure),
                0.25,
                1.75
            ))

            candidate_k = int(np.clip(
                int(self.cfg['candidate_k']) + round(4.0 * pressure),
                int(self.cfg['candidate_k_min']),
                int(self.cfg['candidate_k_max'])
            ))

            rho = float(np.clip(
                rho + 0.22 * pressure,
                float(self.cfg['rho_min']),
                float(self.cfg['rho_max'])
            ))

            ls_budget = int(np.clip(
                int(self.cfg['local_search_moves']) + round(4.0 * (1.0 - pressure)),
                1,
                8
            ))

        tunnel_p = float(np.clip(0.12 + 0.60 * pressure, 0.12, 0.80))

        return {
            'traffic_weight': traffic_weight,
            'candidate_k': candidate_k,
            'rho': rho,
            'ls_budget': ls_budget,
            'tunnel_p': tunnel_p,
        }