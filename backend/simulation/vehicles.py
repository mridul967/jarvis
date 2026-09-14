from backend.simulation.schemas import VehicleState


def edge_id(vehicle: VehicleState) -> str:
    if vehicle.current_node == vehicle.destination_node:
        return "arrived"
    return vehicle.current_edge
