from backend.simulation.schemas import Shock


def demo_shocks() -> tuple[Shock, ...]:
    return (
        Shock(
            shock_id="arterial-incident-0845",
            start_s=300.0,
            end_s=660.0,
            affected_edges=("j-02>j-03", "j-03>j-02"),
            capacity_multiplier=0.25,
            travel_time_multiplier=3.2,
            type="incident",
        ),
        Shock(
            shock_id="morning-peak",
            start_s=0.0,
            end_s=900.0,
            affected_edges=(),
            capacity_multiplier=0.82,
            travel_time_multiplier=1.15,
            type="peak",
        ),
    )


def active_shocks(shocks: tuple[Shock, ...], timestamp_s: float) -> list[Shock]:
    return [shock for shock in shocks if shock.start_s <= timestamp_s < shock.end_s]
