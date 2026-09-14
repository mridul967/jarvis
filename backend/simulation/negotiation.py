from dataclasses import dataclass


@dataclass(frozen=True)
class RouteOffer:
    sender: str
    recipient: str
    vehicle_id: str
    route: tuple[str, ...]
    predicted_arrival_s: float
    predicted_queue: float
    predicted_energy: float
    spillback_risk: float

    @property
    def utility(self) -> tuple[float, ...]:
        return (self.predicted_arrival_s, self.predicted_queue, self.spillback_risk, self.predicted_energy)


def pareto_front(offers: list[RouteOffer]) -> list[RouteOffer]:
    result = []
    for offer in offers:
        dominated = any(
            other != offer
            and all(a <= b for a, b in zip(other.utility, offer.utility))
            and any(a < b for a, b in zip(other.utility, offer.utility))
            for other in offers
        )
        if not dominated:
            result.append(offer)
    return result


def choose_offer(offers: list[RouteOffer]) -> RouteOffer:
    if not offers:
        raise ValueError("At least one route offer is required")
    return sorted(offers, key=lambda item: (item.predicted_arrival_s, item.predicted_queue, item.spillback_risk, item.predicted_energy, item.route))[0]
