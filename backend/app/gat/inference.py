"""
GAT inference service.

Loads SearchSpaceGAT + EdgeWeightGAT checkpoints from disk.
Falls back to random-init weights (untrained) when no checkpoint exists,
and sets `trained=False` in the response so callers can detect this.

ponytail: module-level singletons — single process, no concurrency needed.
Upgrade path: wrap in a proper model registry if multi-model versioning is added.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import torch

from backend.app.gat.models import EdgeWeightGAT, SearchSpaceGAT

# Default feature dimensions match the spec self-check and the Colab notebook.
_NODE_FEAT_DIM = 3  # lat, lon, degree
_EDGE_FEAT_DIM = 3  # length, speed_limit, lanes

_SS_CKPT = Path("data/artifacts/gat_checkpoints/search_space_gat.pt")
_EW_CKPT = Path("data/artifacts/gat_checkpoints/edge_weight_gat.pt")


@dataclass
class _ModelState:
    model: SearchSpaceGAT | EdgeWeightGAT
    trained: bool


def _load(model_cls, ckpt_path: Path, **kwargs) -> _ModelState:
    """Instantiate model; load checkpoint if it exists."""
    model = model_cls(**kwargs)
    if ckpt_path.exists():
        state = torch.load(ckpt_path, map_location="cpu", weights_only=True)
        model.load_state_dict(state)
        return _ModelState(model=model, trained=True)
    return _ModelState(model=model, trained=False)


# Module-level singletons — loaded once on first import.
_ss: _ModelState | None = None
_ew: _ModelState | None = None


def _get_ss() -> _ModelState:
    global _ss
    if _ss is None:
        _ss = _load(
            SearchSpaceGAT,
            _SS_CKPT,
            node_feat_dim=_NODE_FEAT_DIM,
            edge_feat_dim=_EDGE_FEAT_DIM,
        )
    return _ss


def _get_ew() -> _ModelState:
    global _ew
    if _ew is None:
        _ew = _load(
            EdgeWeightGAT,
            _EW_CKPT,
            node_feat_dim=_NODE_FEAT_DIM,
            edge_feat_dim=_EDGE_FEAT_DIM,
        )
    return _ew


def reload_checkpoints() -> dict[str, bool]:
    """Force reload from disk — call after uploading new .pt files."""
    global _ss, _ew
    _ss = None
    _ew = None
    return {
        "search_space_trained": _get_ss().trained,
        "edge_weight_trained": _get_ew().trained,
    }


def infer(
    node_features: list[list[float]],
    edge_index: list[list[int]],
    edge_features: list[list[float]],
    mode: Literal["search_space", "edge_weight", "both"],
    top_k: int = 8,
) -> dict:
    """
    Run GAT inference.

    Args:
        node_features: [[lat, lon, degree], ...] — one row per node
        edge_index:    [[src, dst], ...] — one pair per directed edge
        edge_features: [[length, speed_limit, lanes], ...] — one row per edge
        mode:          which head(s) to run
        top_k:         for search_space, per-source top-k edges to return

    Returns dict with keys depending on mode:
        search_space  -> edge_scores, reduced_search_space, search_space_trained
        edge_weight   -> predicted_weights, edge_weight_trained
        both          -> all of the above
    """
    x = torch.tensor(node_features, dtype=torch.float32)
    ei = torch.tensor(edge_index, dtype=torch.long).t().contiguous()  # shape [2, E]
    ea = torch.tensor(edge_features, dtype=torch.float32)

    result: dict = {}

    if mode in ("search_space", "both"):
        state = _get_ss()
        state.model.eval()
        reduced, scores = state.model.reduced_search_space(x, ei, ea, top_k=top_k)
        result["edge_scores"] = scores.tolist()
        # Convert int keys to str for JSON serialisation
        result["reduced_search_space"] = {
            str(u): [(dst, sc, idx) for dst, sc, idx in edges] for u, edges in reduced.items()
        }
        result["search_space_trained"] = state.trained
        result["search_space_confidence"] = 1.0 if state.trained else 0.0

    if mode in ("edge_weight", "both"):
        state = _get_ew()
        state.model.eval()
        with torch.no_grad():
            weights = state.model(x, ei, ea)
        result["predicted_weights"] = weights.tolist()
        result["edge_weight_trained"] = state.trained
        result["edge_weight_confidence"] = 1.0 if state.trained else 0.0

    return result
