from fastapi import APIRouter

from backend.api.routes.datasets import router as datasets_router
from backend.api.routes.experiments import router as experiments_router
from backend.api.routes.instances import router as instances_router
from backend.api.routes.runs import router as runs_router
from backend.api.routes.snapshots import router as snapshots_router
from backend.api.routes.gat import router as gat_router
from backend.api.routes.traffic import router as traffic_router
from backend.api.routes.simulations import router as simulations_router

api_router = APIRouter()
api_router.include_router(datasets_router)
api_router.include_router(instances_router)
api_router.include_router(experiments_router)
api_router.include_router(runs_router)
api_router.include_router(snapshots_router)
api_router.include_router(traffic_router)
api_router.include_router(gat_router)
api_router.include_router(simulations_router)
