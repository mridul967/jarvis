from fastapi import APIRouter

from backend.api.routes.experiments import router as experiments_router
from backend.api.routes.instances import router as instances_router
from backend.api.routes.runs import router as runs_router

api_router = APIRouter()
api_router.include_router(instances_router)
api_router.include_router(experiments_router)
api_router.include_router(runs_router)
