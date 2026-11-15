from fastapi import APIRouter

from app.api.v1 import ai, analytics, ranking, research
from app.api.v1 import datasets, system

api_router = APIRouter()
api_router.include_router(system.router)
api_router.include_router(datasets.router)
api_router.include_router(research.router)
api_router.include_router(analytics.router)
api_router.include_router(ranking.router)
api_router.include_router(ai.router)
