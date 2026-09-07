"""
POST /api/v1/gat/infer  — run GAT inference (one or both heads)
POST /api/v1/gat/reload — hot-reload checkpoints from disk
GET  /api/v1/gat/status — report checkpoint presence + trained flag
"""

from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.gat import inference as gat

router = APIRouter(prefix="/gat", tags=["gat"])


# ---- Request / Response schemas -----------------------------------------

class GATInferRequest(BaseModel):
    """
    Graph data + inference mode.

    node_features: [[lat, lon, degree], ...]  one row per node
    edge_index:    [[src, dst], ...]           one pair per directed edge
    edge_features: [[length, speed_limit, lanes], ...]  one row per edge
    mode:          which head to run
    top_k:         for search_space, outgoing edges to keep per source node
    """

    node_features: list[list[float]] = Field(..., min_length=1)
    edge_index: list[list[int]] = Field(..., min_length=1)
    edge_features: list[list[float]] = Field(..., min_length=1)
    mode: Literal["search_space", "edge_weight", "both"] = "both"
    top_k: int = Field(8, ge=1, le=64)


class GATInferResponse(BaseModel):
    mode: str
    edge_scores: list[float] | None = None
    reduced_search_space: dict[str, list] | None = None
    search_space_trained: bool | None = None
    predicted_weights: list[float] | None = None
    edge_weight_trained: bool | None = None


# ---- Endpoints ----------------------------------------------------------

@router.post("/infer", response_model=GATInferResponse)
def infer(req: GATInferRequest) -> GATInferResponse:
    """Run GAT forward pass. Returns edge probability scores and/or predicted
    edge weights depending on `mode`. `*_trained=False` means the model is
    running with random-init weights — upload a checkpoint and call /reload."""
    n_edges = len(req.edge_index)
    if len(req.edge_features) != n_edges:
        raise HTTPException(
            status_code=422,
            detail=f"edge_features length {len(req.edge_features)} != edge_index length {n_edges}",
        )
    try:
        result = gat.infer(
            node_features=req.node_features,
            edge_index=req.edge_index,
            edge_features=req.edge_features,
            mode=req.mode,
            top_k=req.top_k,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return GATInferResponse(mode=req.mode, **result)


@router.post("/reload")
def reload() -> dict:
    """Hot-reload checkpoints from disk. Call after dropping new .pt files
    into data/artifacts/gat_checkpoints/."""
    return gat.reload_checkpoints()


@router.get("/status")
def status() -> dict:
    """Returns checkpoint presence and whether each model has trained weights."""
    return gat.reload_checkpoints()
