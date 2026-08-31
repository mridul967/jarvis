"""
Quantum Particle Swarm Optimization (QPSO) for Vehicle Routing
Integrated with PyTorch Geometric (GAT) and OSMnx for Real-World Search Space Reduction.
"""

import osmnx as ox
import networkx as nx
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
import time

# Set device (Will use GPU if you have CUDA installed in your local environment, otherwise CPU)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"--- INITIALIZING ON DEVICE: {device} ---")

# =====================================================================
# BLOCK 1: GRAPH NEURAL NETWORK ARCHITECTURE
# =====================================================================
class EdgePruningGAT(torch.nn.Module):
    def __init__(self, in_channels, hidden_channels):
        super().__init__()
        # GAT layer learns the spatial relationship between connected intersections
        self.conv1 = GATConv(in_channels, hidden_channels, heads=1)
        # Linear layer scores the edge based on combined node data
        self.edge_mlp = torch.nn.Linear(hidden_channels * 2, 1)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        src, dst = edge_index
        edge_features = torch.cat([x[src], x[dst]], dim=1)
        # Output probability (0.0 to 1.0) of edge optimality
        return torch.sigmoid(self.edge_mlp(edge_features)).squeeze()

# =====================================================================
# BLOCK 2: REAL MAP EXTRACTION & TENSOR CONVERSION
# =====================================================================
print("\n[1/4] Downloading real street network...")
# Using a 500-meter radius around a central point to ensure the PoC runs quickly on local CPUs
center_point = (28.6415, 77.3708) # Coordinates in Indirapuram, Ghaziabad
G_osm = ox.graph_from_point(center_point, dist=800, network_type='drive')
G = ox.get_undirected(G_osm)

nodes = list(G.nodes(data=True))
num_nodes = len(nodes)
node_mapping = {node_id: i for i, (node_id, _) in enumerate(nodes)}
reverse_node_mapping = {i: node_id for i, (node_id, _) in enumerate(nodes)}

coords = torch.tensor([[data['x'], data['y']] for _, data in nodes], dtype=torch.float32, device=device)

edges = list(G.edges(data=True))
src_list = []
dst_list = []

# Initialize distance matrix with heavy penalties for unconnected roads
dist_matrix = torch.full((num_nodes, num_nodes), 99999.0, device=device) 
dist_matrix.fill_diagonal_(0.0)

for u, v, data in edges:
    idx_u = node_mapping[u]
    idx_v = node_mapping[v]
    src_list.append(idx_u)
    dst_list.append(idx_v)
    
    # OSMnx provides actual physical road length
    road_length = data.get('length', 99999.0) 
    dist_matrix[idx_u, idx_v] = road_length
    dist_matrix[idx_v, idx_u] = road_length

edge_index = torch.tensor([src_list, dst_list], dtype=torch.long, device=device)

print(f"      Total Intersections (Nodes): {num_nodes}")
print(f"      Total Roads (Edges): {len(src_list)}")

# =====================================================================
# BLOCK 3: GAT GRAPH PRUNING (SEARCH SPACE REDUCTION)
# =====================================================================
print("\n[2/4] Executing GAT for predictive edge pruning...")

gat_model = EdgePruningGAT(in_channels=2, hidden_channels=8).to(device)
with torch.no_grad():
    edge_probs = gat_model(coords, edge_index)

# Threshold: Keep only the top 50% most probable edges for the QPSO search space
threshold = torch.quantile(edge_probs, 0.50) 
valid_edges_mask = edge_probs >= threshold

# Build the Pruned Adjacency Matrix (1 = allowed road, 0 = GAT pruned road)
pruned_adj_matrix = torch.zeros((num_nodes, num_nodes), device=device)
src_t, dst_t = edge_index[0], edge_index[1]
pruned_adj_matrix[src_t[valid_edges_mask], dst_t[valid_edges_mask]] = 1

print(f"      Original Edges: {len(src_list)}")
print(f"      Pruned Edges: {len(src_list) - valid_edges_mask.sum().item()}")
print(f"      Edges remaining for QPSO: {valid_edges_mask.sum().item()}")

# =====================================================================
# BLOCK 4: THE QPSO ALGORITHM
# =====================================================================
def evaluate_fitness_vectorized(X):
    """Decodes QPSO vectors using SPV and calculates total route distance."""
    routes = torch.argsort(X, dim=-1) 
    
    srcs = routes[:, :-1]
    dsts = routes[:, 1:]
    
    step_distances = dist_matrix[srcs, dsts]
    step_validity = pruned_adj_matrix[srcs, dsts]
    
    # Apply constraint: If the road isn't valid, apply massive penalty
    penalized_distances = torch.where(
        step_validity == 1, 
        step_distances, 
        torch.tensor(99999.0, device=device)
    )
    
    return penalized_distances.sum(dim=1)

print("\n[3/4] Initializing Quantum Swarm...")
num_particles = 300
iterations = 100
alpha = 0.75 # Contraction-expansion coefficient

# Initialize continuous particle positions
X = torch.rand((num_particles, num_nodes), device=device)
pbest = X.clone()
pbest_fitness = evaluate_fitness_vectorized(pbest)

global_best_idx = torch.argmin(pbest_fitness)
gbest = pbest[global_best_idx].clone()
gbest_fitness = pbest_fitness[global_best_idx].item()

print("\n[4/4] Running QPSO Optimization Loop...")
start_time = time.time()

for i in range(iterations):
    mbest = torch.mean(pbest, dim=0, keepdim=True)
    
    phi = torch.rand_like(X)
    P = phi * pbest + (1 - phi) * gbest.unsqueeze(0)
    
    u = torch.rand_like(X)
    ln_inv_u = torch.log(1.0 / u)
    sign = torch.sign(torch.rand_like(X) - 0.5)
    
    # QPSO Hardware-accelerated update equation
    X = P + sign * alpha * torch.abs(mbest - X) * ln_inv_u
    
    # Evaluate
    current_fitness = evaluate_fitness_vectorized(X)
    
    # Update Personal Bests
    better_mask = current_fitness < pbest_fitness
    pbest[better_mask] = X[better_mask]
    pbest_fitness[better_mask] = current_fitness[better_mask]
    
    # Update Global Best
    min_idx = torch.argmin(pbest_fitness)
    if pbest_fitness[min_idx] < gbest_fitness:
        gbest = pbest[min_idx].clone()
        gbest_fitness = pbest_fitness[min_idx].item()
        
    if (i + 1) % 20 == 0:
        print(f"      Iteration {i+1:3d} | Best Route Penalty Cost: {gbest_fitness:.2f}")

end_time = time.time()

# =====================================================================
# FINAL OUTPUT
# =====================================================================
best_route_indices = torch.argsort(gbest).tolist()
best_route_osm_ids = [reverse_node_mapping[idx] for idx in best_route_indices]

print(f"\n--- OPTIMIZATION COMPLETE in {end_time - start_time:.2f} seconds ---")
print(f"Optimal Node Visitation Sequence (First 10 OSM Node IDs):")
print(best_route_osm_ids[:10])