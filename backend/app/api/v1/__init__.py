"""
API v1 Router aggregation for Veritas.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health, assets, image

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(assets.router)
api_v1_router.include_router(image.router)
