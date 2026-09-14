import networkx as nx

from backend.simulation.schemas import AgentMessage, NodeAgent


def create_agents(graph: nx.DiGraph) -> dict[str, NodeAgent]:
    return {
        node: NodeAgent(node_id=node, neighbors=tuple(sorted(graph.successors(node))))
        for node in sorted(graph.nodes)
    }


def neighbor_messages(sender: NodeAgent, tick: int, active_shocks: list[str]) -> list[AgentMessage]:
    return [
        AgentMessage(sender.node_id, recipient, tick, sender.queue_length, sender.occupancy, sender.predicted_pressure, tuple(active_shocks))
        for recipient in sender.neighbors
    ]
