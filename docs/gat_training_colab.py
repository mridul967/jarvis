"""
QRoute GAT Training — Google Colab Script
=========================================

Run in Colab (GPU runtime recommended). At the end, download the two
.pt checkpoint files and drop them into:
  data/artifacts/gat_checkpoints/
Then call POST /api/v1/gat/reload to hot-load them.

Usage:
  1. Upload this file to Colab, or paste directly into a code cell.
  2. Runtime > Change runtime type > GPU (T4 is fine).
  3. Run all cells.
  4. Download search_space_gat.pt and edge_weight_gat.pt from /content/.
  5. Place in data/artifacts/gat_checkpoints/ and call /api/v1/gat/reload.
"""

# ---- Install deps (Colab only) ------------------------------------------
# !pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
# !pip install torch_geometric -q
# !pip install networkx -q

import torch
import torch.nn as nn
import torch.nn.functional as F
import networkx as nx
from torch_geometric.nn import GATv2Conv
from torch_geometric.utils import from_networkx
from torch_geometric.data import Data

device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")


# ---- Model definitions (copy of backend/app/gat/models.py) --------------

class GATEncoder(nn.Module):
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


class EdgeWeightGAT(nn.Module):
    def __init__(self, node_feat_dim, edge_feat_dim, hidden_dim=64, heads=4, layers=2):
        super().__init__()
        self.encoder = GATEncoder(node_feat_dim, edge_feat_dim, hidden_dim, heads, layers)
        self.head = nn.Sequential(
            nn.Linear(self.encoder.out_dim * 2 + edge_feat_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 1),
            nn.Softplus(),
        )

    def forward(self, x, edge_index, edge_attr):
        h = self.encoder(x, edge_index, edge_attr)
        e = self.encoder.edge_repr(h, edge_index, edge_attr)
        return self.head(e).squeeze(-1)


# ---- Feature dimensions --------------------------------------------------
# Must match the defaults in backend/app/gat/inference.py.
# Node features: [lat, lon, degree]
# Edge features: [length, speed_limit, lanes]
NODE_FEAT_DIM = 3
EDGE_FEAT_DIM = 3


# ---- Synthetic dataset ---------------------------------------------------
# Replace this section with your real data loader once SUMO labels exist.
# Each Data object represents one graph instance.

def make_synthetic_instance(seed: int) -> Data:
    """
    Build one synthetic 6-node directed graph with random labels.
    Positive class (edge_label=1): edges that appear in a random 'good route'.

    Replace with:
      - OR-Tools solutions on real/SUMO instances for SearchSpaceGAT labels
      - SUMO-simulated traversal times for EdgeWeightGAT targets
    """
    torch.manual_seed(seed)
    G = nx.DiGraph()
    for n in range(6):
        G.add_node(n, lat=float(n) * 0.01 + torch.rand(1).item() * 0.001,
                   lon=float(n) * 0.005 + torch.rand(1).item() * 0.001,
                   degree=float(G.degree(n)) + 2.0)
    edges = [(0,1),(1,2),(2,3),(3,4),(4,5),(0,2),(2,5),(1,4)]
    for u, v in edges:
        G.add_edge(u, v,
                   length=float(abs(u-v)) + torch.rand(1).item(),
                   speed_limit=40.0,
                   lanes=2.0)

    data, _ = networkx_to_pyg(G, ["lat", "lon", "degree"], ["length", "speed_limit", "lanes"])
    data.x = data.x.float()
    data.edge_attr = data.edge_attr.float()

    # Fake labels — replace with real solver output
    good_route_edges = {0, 1, 6}  # indices into edge_index
    n_edges = data.edge_index.size(1)
    data.edge_label = torch.zeros(n_edges)
    for idx in good_route_edges:
        if idx < n_edges:
            data.edge_label[idx] = 1.0

    # Fake traversal times (seconds) — replace with SUMO output
    data.edge_target = torch.rand(n_edges) * 30.0 + 5.0

    return data


def networkx_to_pyg(nx_graph, node_feature_keys, edge_feature_keys):
    from torch_geometric.utils import from_networkx
    data = from_networkx(nx_graph, group_node_attrs=node_feature_keys, group_edge_attrs=edge_feature_keys)
    return data, list(nx_graph.edges())


# ---- Training loop -------------------------------------------------------

def train(model, data_list, label_attr, loss_fn, epochs=100, lr=1e-3):
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
        if epoch % 20 == 0:
            print(f"  epoch {epoch:4d}  avg_loss={total/len(data_list):.5f}")
    return model


# ---- Main ----------------------------------------------------------------

DATASET_SIZE = 50  # increase to 500-1000 once you have real SUMO data
print(f"Generating {DATASET_SIZE} synthetic instances...")
dataset = [make_synthetic_instance(seed=i) for i in range(DATASET_SIZE)]

# Split 80/20 by instance (not by edge — that would leak)
split = int(0.8 * DATASET_SIZE)
train_data, val_data = dataset[:split], dataset[split:]

# ---- Train SearchSpaceGAT -----------------------------------------------
print("\n[1/2] Training SearchSpaceGAT (edge probability head)...")
# ponytail: pos_weight handles class imbalance — edges in good routes are rare.
pos_weight = torch.tensor([5.0], device=device)
ss_model = SearchSpaceGAT(NODE_FEAT_DIM, EDGE_FEAT_DIM)
train(ss_model, train_data, "edge_label", nn.BCEWithLogitsLoss(pos_weight=pos_weight), epochs=100)

# Quick val pass
ss_model.eval()
val_losses = []
with torch.no_grad():
    for d in val_data:
        d = d.to(device)
        pred = ss_model(d.x, d.edge_index, d.edge_attr)
        loss = nn.BCELoss()(pred, d.edge_label.float().to(device))
        val_losses.append(loss.item())
print(f"  val BCE loss: {sum(val_losses)/len(val_losses):.5f}")

torch.save(ss_model.state_dict(), "/content/search_space_gat.pt")
print("  Saved: /content/search_space_gat.pt")

# ---- Train EdgeWeightGAT ------------------------------------------------
print("\n[2/2] Training EdgeWeightGAT (edge cost regression head)...")
ew_model = EdgeWeightGAT(NODE_FEAT_DIM, EDGE_FEAT_DIM)
train(ew_model, train_data, "edge_target", nn.HuberLoss(), epochs=100)

ew_model.eval()
val_losses = []
with torch.no_grad():
    for d in val_data:
        d = d.to(device)
        pred = ew_model(d.x, d.edge_index, d.edge_attr)
        loss = nn.HuberLoss()(pred, d.edge_target.float().to(device))
        val_losses.append(loss.item())
print(f"  val Huber loss: {sum(val_losses)/len(val_losses):.5f}")

torch.save(ew_model.state_dict(), "/content/edge_weight_gat.pt")
print("  Saved: /content/edge_weight_gat.pt")

print("""
Done. Download the two .pt files from /content/ (left panel → Files).
Place them in:  data/artifacts/gat_checkpoints/
Then call:      POST /api/v1/gat/reload
""")
