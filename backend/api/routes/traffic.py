import json
from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from backend.api.schemas import (
    TrafficScenarioDetailResponse,
    TrafficScenarioRequest,
    TrafficScenarioResponse,
    TrafficScenarioValidationResponse,
)
from backend.app.core.artifacts import sha256
from backend.traffic.model import (
    ArcCongestion,
    ArcMultiplier,
    EndogenousTraffic,
    ExogenousTraffic,
)
from backend.traffic.service import (
    create_scenario,
    get_scenario,
    list_scenarios,
    scenario_content,
    scenario_payload,
)

router = APIRouter(prefix="/traffic/scenarios", tags=["traffic scenarios"])


@router.post("/validate", response_model=TrafficScenarioValidationResponse)
def validate(payload: TrafficScenarioRequest) -> TrafficScenarioValidationResponse:
    try:
        content, mode = scenario_content(payload.name, *_models(payload))
    except ValueError as error:
        return TrafficScenarioValidationResponse(valid=False, errors=[str(error)])
    encoded = json.dumps(
        content,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return TrafficScenarioValidationResponse(
        valid=True,
        errors=[],
        mode=mode,
        content_sha256=sha256(encoded),
    )


@router.post("", response_model=TrafficScenarioResponse, status_code=201)
def create(payload: TrafficScenarioRequest) -> dict:
    try:
        return asdict(create_scenario(payload.name, *_models(payload)))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@router.get("", response_model=list[TrafficScenarioResponse])
def scenarios(limit: Annotated[int, Query(ge=1, le=500)] = 100) -> list[dict]:
    return [asdict(scenario) for scenario in list_scenarios(limit)]


@router.get("/{scenario_id}", response_model=TrafficScenarioDetailResponse)
def scenario(scenario_id: str) -> dict:
    found = get_scenario(scenario_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Traffic scenario not found")
    return asdict(found) | {"content": scenario_payload(scenario_id)}


def _models(
    payload: TrafficScenarioRequest,
) -> tuple[ExogenousTraffic | None, EndogenousTraffic | None]:
    exogenous = None
    if payload.exogenous:
        values = payload.exogenous.model_dump(exclude={"intervals"})
        exogenous = ExogenousTraffic(
            **values,
            intervals=tuple(
                ArcMultiplier(**item.model_dump()) for item in payload.exogenous.intervals
            ),
        )
    endogenous = None
    if payload.endogenous:
        values = payload.endogenous.model_dump(exclude={"arcs"})
        endogenous = EndogenousTraffic(
            **values,
            arcs=tuple(ArcCongestion(**item.model_dump()) for item in payload.endogenous.arcs),
        )
    return exogenous, endogenous
