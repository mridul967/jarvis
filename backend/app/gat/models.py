"""
GAT models for the QRoute traffic-routing pipeline.

Two independent heads on one shared GAT encoder:
  - SearchSpaceGAT: P(edge belongs to a good route), per directed edge.
    Consumed however the caller wants -- e.g. QPSO restricts its SPV
    permutation-decode to each node's top-k scoring edges, or QACO seeds
    its pheromone/amplitude matrix from these scores. This model has no
    notion of QPSO's position update or QACO's rotation-gate equations;
    it only outputs a probability distribution over the search space.
  - EdgeWeightGAT: predicted edge cost (e.g. congestion-adjusted travel
    time), used to populate a NetworkX DiGraph's weights instead of a
    hand-written formula. Same shape as Google Maps' GNN-based ETA model
    (GNN over the road graph -> per-segment travel time).

Requires: torch, torch_geometric, networkx.
"""

import networkx as nx
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv
from torch_geometric.utils import from_networkx


# --------------------------------------------------------------------------
# Shared encoder
# --------------------------------------------------------------------------

class GATEncoder(nn.Module):
    """Attention-based node encoder shared by both heads below."""

    def __init__(self, node_feat_dim, edge_feat_dim, hidden_dim=64, heads=4, layers=2, dropout=0.1):
        super().__init__()
        self.convs = nn.ModuleList()
        in_dim = node_feat_dim
        for _ in range(layers):
            self.convs.append(
                GATv2Conv(in_dim, hidden_dim, heads=heads, edge_dim=edge_feat_dim, dropout=dropout)
            )
            in_dim = hidden_dim * heads
        self.out_dim = in_dim

    def forward(self, x, edge_index, edge_attr):
        h = x
        for conv in self.convs:
            h = F.elu(conv(h, edge_index, edge_attr))
        return h

    @staticmethod
    def edge_repr(h, edge_index, edge_attr):
        src, dst = edge_index
        return torch.cat([h[src], h[dst], edge_attr], dim=-1)


# --------------------------------------------------------------------------
# Head 1: search-space reduction for QPSO / QACO
# --------------------------------------------------------------------------

class SearchSpaceGAT(nn.Module):
    def __init__(self, node_feat_dim, edge_feat_dim, hidden_dim=64, heads=4, layers=2):
        super().__init__()
        self.encoder = GATEncoder(node_feat_dim, edge_feat_dim, hidden_dim, heads, layers)
        self.head = nn.Sequential(
            nn.Linear(self.encoder.out_dim * 2 + edge_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
        )

    def forward(self, x, edge_index, edge_attr):
        h = self.encoder(x, edge_index, edge_attr)
        e = self.encoder.edge_repr(h, edge_index, edge_attr)
        return torch.sigmoid(self.head(e).squeeze(-1))

    @torch.no_grad()
    def reduced_search_space(self, x, edge_index, edge_attr, top_k=8):
        """Per source node, the top_k highest-scoring outgoing edges --
        the reduced candidate set QPSO/QACO restrict themselves to
        instead of the full adjacency. Returns (dict, raw_scores)."""
        scores = self(x, edge_index, edge_attr)
        src, dst = edge_index
        per_node = {}
        for i in range(edge_index.size(1)):
            per_node.setdefault(src[i].item(), []).append((dst[i].item(), scores[i].item(), i))
        reduced = {u: sorted(lst, key=lambda t: -t[1])[:top_k] for u, lst in per_node.items()}
        return reduced, scores


# --------------------------------------------------------------------------
# Head 2: edge-weight prediction for the NetworkX directed graph
# --------------------------------------------------------------------------

class EdgeWeightGAT(nn.Module):
    def __init__(self, node_feat_dim, edge_feat_dim, hidden_dim=64, heads=4, layers=2):
        super().__init__()
        self.encoder = GATEncoder(node_feat_dim, edge_feat_dim, hidden_dim, heads, layers)
        self.head = nn.Sequential(
            nn.Linear(self.encoder.out_dim * 2 + edge_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Softplus(),  # edge cost must be positive
        )

    def forward(self, x, edge_index, edge_attr):
        h = self.encoder(x, edge_index, edge_attr)
        e = self.encoder.edge_repr(h, edge_index, edge_attr)
        return self.head(e).squeeze(-1)


# --------------------------------------------------------------------------
# Training -- one generic loop, both heads are plain supervised learning
# (no QPSO/QACO/RL signal involved either way)
# --------------------------------------------------------------------------

def train_gat(model, data_list, label_attr, loss_fn, epochs=50, lr=1e-3, device="cpu"):
    """
    data_list: list of torch_geometric.data.Data, each carrying
      .x, .edge_index, .edge_attr, and the label named by `label_attr`:
        - SearchSpaceGAT: 'edge_label' (float 0/1, 1 = edge appears in a
          known-good route from an offline OR-Tools/Dijkstra/converged-
          QPSO solve on that instance)
        - EdgeWeightGAT:  'edge_target' (observed real-world edge cost,
          e.g. SUMO-simulated travel time or aggregated GPS traversal time)
    """
    model.to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=1e-5)
    model.train()
    for epoch in range(epochs):
        total = 0.0
        for data in data_list:
            data = data.to(device)
            opt.zero_grad()
            pred = model(data.x, data.edge_index, data.edge_attr)
            target = getattr(data, label_attr).float()
            loss = loss_fn(pred, target)
            loss.backward()
            opt.step()
            total += loss.item()
        if epoch % 10 == 0:
            print(f"epoch {epoch:3d}  loss {total / len(data_list):.4f}")
    return model


# --------------------------------------------------------------------------
# NetworkX bridge
# --------------------------------------------------------------------------

def networkx_to_pyg(nx_graph, node_feature_keys, edge_feature_keys):
    """Thin wrapper -- from_networkx already does the conversion, no
    reason to hand-roll it. Returns (Data, edge_list) where edge_list
    is in the same column order as data.edge_index."""
    data = from_networkx(nx_graph, group_node_attrs=node_feature_keys, group_edge_attrs=edge_feature_keys)
    edge_list = list(nx_graph.edges())
    return data, edge_list


def build_weighted_digraph(base_graph, model, x, edge_index, edge_attr, edge_list):
    """Runs a trained EdgeWeightGAT and writes predicted weights onto a
    copy of base_graph -- same weighted DiGraph artifact QPSO/QACO/
    OR-Tools/Dijkstra already consume, just with learned weights."""
    model.eval()
    with torch.no_grad():
        weights = model(x, edge_index, edge_attr).cpu().numpy()
    G = base_graph.copy()
    for (u, v), w in zip(edge_list, weights):
        G[u][v]["weight"] = float(w)
        G[u][v]["gat_predicted"] = True
    return G


# --------------------------------------------------------------------------
# Runnable self-check: builds a tiny synthetic road graph and exercises
# both models end to end. Not a benchmark -- just proof the shapes line up.
# --------------------------------------------------------------------------

if __name__ == "__main__":
    torch.manual_seed(0)

    NODE_FEATS = ["lat", "lon", "degree"]
    EDGE_FEATS = ["length", "speed_limit", "lanes"]

    G = nx.DiGraph()
    for n in range(6):
        G.add_node(n, lat=float(n), lon=float(n) * 0.5, degree=2.0)
    edges = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (0, 2), (2, 5), (1, 4)]
    for u, v in edges:
        G.add_edge(u, v, length=float(abs(u - v)), speed_limit=40.0, lanes=2.0)

    data, edge_list = networkx_to_pyg(G, NODE_FEATS, EDGE_FEATS)
    data.x = data.x.float()
    data.edge_attr = data.edge_attr.float()

    # fabricated labels/targets, just to exercise the training loop
    data.edge_label = torch.randint(0, 2, (data.edge_index.size(1),)).float()
    data.edge_target = torch.rand(data.edge_index.size(1)) * 10.0

    ss_model = SearchSpaceGAT(node_feat_dim=len(NODE_FEATS), edge_feat_dim=len(EDGE_FEATS))
    train_gat(ss_model, [data], "edge_label", nn.BCELoss(), epochs=5)
    reduced, scores = ss_model.reduced_search_space(data.x, data.edge_index, data.edge_attr, top_k=2)
    print("reduced search space (node -> top edges):", reduced)

    w_model = EdgeWeightGAT(node_feat_dim=len(NODE_FEATS), edge_feat_dim=len(EDGE_FEATS))
    train_gat(w_model, [data], "edge_target", nn.HuberLoss(), epochs=5)
    G_weighted = build_weighted_digraph(G, w_model, data.x, data.edge_index, data.edge_attr, edge_list)
    print("predicted weights:", nx.get_edge_attributes(G_weighted, "weight"))

    print("OK -- both models run end to end on the toy graph.")
