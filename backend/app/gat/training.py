"""Small supervised trainer for deterministic rollout targets."""

from pathlib import Path

import torch
from torch_geometric.data import Data

from backend.app.gat.models import EdgeWeightGAT, SearchSpaceGAT, train_gat
from backend.simulation.engine import SimulationEngine


def train_edge_weights(epochs: int = 20, runs: int = 3, checkpoint: Path = Path("data/artifacts/gat_checkpoints/edge_weight_gat.pt")) -> dict[str, float | str]:
    samples: list[Data] = []
    for seed in range(42, 42 + runs):
        replay = SimulationEngine(seed=seed, vehicle_count=16, ticks=30).run()
        graph = replay["graph"]
        index = {node["id"]: number for number, node in enumerate(graph["nodes"])}
        x = torch.tensor([[node["latitude"], node["longitude"], sum(edge["source"] == node["id"] for edge in graph["edges"])] for node in graph["nodes"]], dtype=torch.float32)
        edge_index = torch.tensor([[index[edge["source"]] for edge in graph["edges"]], [index[edge["target"]] for edge in graph["edges"]]], dtype=torch.long)
        static = {edge["id"]: edge for edge in graph["edges"]}
        for frame, future in zip(replay["frames"], replay["frames"][1:]):
            current = {edge["edge_id"]: edge for edge in frame["edges"]}; target = {edge["edge_id"]: edge for edge in future["edges"]}
            attrs = [[static[edge_id]["length_m"], 40.0, current[edge_id]["capacity"] / 900.0] for edge_id in static]
            costs = [target[edge_id]["travel_time_s"] for edge_id in static]
            cutoff = sorted(costs)[len(costs) // 2]
            samples.append(Data(x=x, edge_index=edge_index, edge_attr=torch.tensor(attrs, dtype=torch.float32), edge_target=torch.tensor(costs, dtype=torch.float32), edge_label=torch.tensor([cost <= cutoff for cost in costs], dtype=torch.float32)))
    model = EdgeWeightGAT(node_feat_dim=3, edge_feat_dim=3)
    train_gat(model, samples, "edge_target", torch.nn.HuberLoss(), epochs=epochs)
    checkpoint.parent.mkdir(parents=True, exist_ok=True); torch.save(model.state_dict(), checkpoint)
    search = SearchSpaceGAT(node_feat_dim=3, edge_feat_dim=3)
    train_gat(search, samples, "edge_label", torch.nn.BCELoss(), epochs=epochs)
    search_checkpoint = checkpoint.with_name("search_space_gat.pt"); torch.save(search.state_dict(), search_checkpoint)
    return {"checkpoint": str(checkpoint), "search_checkpoint": str(search_checkpoint), "samples": float(len(samples)), "epochs": float(epochs)}
