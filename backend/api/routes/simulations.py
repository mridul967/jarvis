from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.simulation.engine import SimulationEngine
from backend.simulation import jobs

router = APIRouter(prefix="/simulations", tags=["simulations"])
_runs: dict[str, dict] = {}


class SimulationCreateRequest(BaseModel):
    seed: int = Field(42, ge=0, le=2_147_483_647)
    vehicle_count: int = Field(16, ge=1, le=50)
    ticks: int = Field(30, ge=1, le=60)


class OSMImportRequest(BaseModel):
    place: str = Field("Koramangala, Bengaluru, India", min_length=3, max_length=200)


@router.post("", status_code=201)
def create_simulation(payload: SimulationCreateRequest) -> dict:
    result = SimulationEngine(payload.seed, payload.vehicle_count, payload.ticks).run()
    _runs[result["run_id"]] = result
    return result


@router.post("/imports/osm", status_code=201)
def import_osm(payload: OSMImportRequest) -> dict:
    from backend.simulation.osm import import_district

    return import_district(payload.place)


@router.post("/jobs", status_code=202)
def create_simulation_job(payload: SimulationCreateRequest) -> dict:
    job = jobs.submit(payload.seed, payload.vehicle_count, payload.ticks)
    return {"job_id": job.job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def simulation_job(job_id: str) -> dict:
    try:
        return jobs.status(job_id)
    except KeyError as error:
        raise HTTPException(status_code=404, detail="Simulation job not found") from error


@router.get("/{run_id}")
def simulation(run_id: str) -> dict:
    result = _runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation run not found in this API process")
    return result


@router.get("/{run_id}/events")
def events(run_id: str, limit: Annotated[int, Query(ge=1, le=5000)] = 5000) -> list[dict]:
    result = _runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation run not found in this API process")
    return result["events"][:limit]


@router.post("/{run_id}/neo4j")
def export_to_neo4j(run_id: str) -> dict:
    result = _runs.get(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Simulation run not found in this API process")
    try:
        from backend.simulation.neo4j_export import export_audit

        return {"run_id": run_id, "events_exported": export_audit(Path(result["audit_path"]), run_id)}
    except ValueError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


def _summary(result: dict) -> dict:
    return {
        "run_id": result["run_id"],
        "scenario_id": result["scenario_id"],
        "seed": result["seed"],
        "frame_count": len(result["frames"]),
        "vehicle_count": len(result["frames"][0]["vehicles"]) if result["frames"] else 0,
        "audit_path": result["audit_path"],
    }
