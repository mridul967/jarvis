# qaco/physics/interference.py
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping, Sequence
import numpy as np

from qaco.domain.vrp_instance import DynamicVRP

@dataclass
class QuantumAmplitudeState:
    """Pheromone memory and last traffic relation for all possible VRP transitions."""
    n: int
    initial: float = 1.0
    pheromone: np.ndarray = field(init=False)

    def __post_init__(self) -> None:
        self.pheromone = np.full((self.n, self.n), self.initial)
        np.fill_diagonal(self.pheromone, 0)


class InterferenceEngine:
    """Build/measure historical and traffic amplitudes; retain every cross term."""

    def __init__(self, problem: DynamicVRP, state: QuantumAmplitudeState, cfg: Mapping[str, object]) -> None:
        self.problem, self.state, self.cfg, self.log = problem, state, cfg, []

    def scores(
        self,
        i: int,
        candidates: Sequence[int],
        delta: np.ndarray
    ):
        """Return (history, signed_traffic_signal, phase).

        Correct limit behavior: if current weights equal base weights and
        delta == 0, the traffic signal is 0 for every candidate, so the
        traffic amplitude vanishes and interference reduces to classical
        history-based sampling.
        """
        c = np.asarray(candidates, int)
        current = np.maximum(self.problem.weight[i, c], 1e-12)
        base = np.maximum(self.problem.base[i, c], 1e-12)
        change = delta[i, c] / base

        static_eta = (1.0 / base) ** float(self.cfg['beta'])
        history_raw = (self.state.pheromone[i, c] ** float(self.cfg['alpha'])) * static_eta
        history = history_raw / (np.max(history_raw) + 1e-12)

        # Signed traffic signal:
        #  > 0  edge is faster than base (improving)  -> constructive
        #  < 0  edge is congested / worsening         -> destructive
        ratio_signal = np.clip(base / current - 1.0, -0.95, 2.0)
        change_signal = np.clip(-change, -0.95, 2.0)
        signed = 0.7 * ratio_signal + 0.3 * change_signal

        badness = np.clip(-signed, 0.0, 1.0)
        phase = np.minimum(
            np.pi * badness,
            float(self.cfg.get('phase_max_fraction', 0.9)) * np.pi
        )

        return history, signed, phase

    def probabilities(self, i, candidates, delta, traffic_weight,
                      interference_on, classical_control, iteration):
        h, s, phase = self.scores(i, candidates, delta)
        mag = np.clip(np.abs(s), 0.0, 1.0)   # how strongly traffic "speaks"

        wh = float(self.cfg['history_weight'])
        wt = float(traffic_weight)

        if interference_on:
            ah = wh * np.sqrt(np.maximum(h, 0.0)).astype(complex)
            at = wt * np.sqrt(mag) * np.exp(1j * phase)
            cross = 2.0 * np.real(np.conj(ah) * at)
            scores = np.abs(ah + at) ** 2 + 1e-10
        elif classical_control:
            cross = np.zeros_like(h)
            scores = np.maximum(wh * h + wt * np.clip(s, -1.0, 1.0), 1e-10)
        else:
            cross = np.zeros_like(h)
            scores = h + 1e-10

        prob = scores / scores.sum()

        for j, x, p, ph in zip(candidates, cross, prob, phase):
            self.log.append({
                'iteration': iteration, 'i': i, 'j': int(j),
                'cross_term': float(x), 'probability': float(p),
                'phase': float(ph)
            })
        return prob


def interference_demo() -> None:
    """Demonstrate fixed constructive and destructive cases with the exact cross term."""
    import matplotlib.pyplot as plt  # Localized import to avoid unresolved dependencies

    ah = np.array([1 + 0j, 1 + 0j])
    at = np.array([1 + 0j, np.exp(1j * np.pi)])
    cross = 2 * np.real(np.conj(ah) * at)
    assert cross[0] > 0 and cross[1] < 0
    plt.bar(['agreement / constructive', 'traffic conflict / destructive'], cross, color=['tab:green', 'tab:red'])
    plt.ylabel(r'$2 Re(\bar a_h a_t)$')
    plt.title('Explicit interference cross-term control')
    plt.show()