from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any
import uuid

from backend.simulation.engine import SimulationEngine

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="simulation")


@dataclass
class SimulationJob:
    job_id: str
    future: Future[Any]


_jobs: dict[str, SimulationJob] = {}


def submit(seed: int, vehicle_count: int, ticks: int) -> SimulationJob:
    job_id = f"simjob-{uuid.uuid4().hex[:10]}"
    job = SimulationJob(job_id, _executor.submit(SimulationEngine(seed, vehicle_count, ticks).run))
    _jobs[job_id] = job
    return job


def status(job_id: str) -> dict:
    job = _jobs.get(job_id)
    if job is None:
        raise KeyError(job_id)
    if not job.future.done():
        return {"job_id": job_id, "status": "running"}
    result = job.future.result()
    return {"job_id": job_id, "status": "completed", "run_id": result["run_id"]}
