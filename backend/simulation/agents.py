import networkx as nx

from backend.simulation.schemas import NodeAgent


def create_agents(graph: nx.DiGraph) -> dict[str, NodeAgent]:
    return {
        node: NodeAgent(node_id=node, neighbors=tuple(sorted(graph.successors(node))))
        for node in sorted(graph.nodes)
    }
