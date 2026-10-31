"""
API v1 Router aggregation for Veritas.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health
from backend.app.api.v1.endpoints import image
from backend.app.api.v1.endpoints import video

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(image.router)
api_v1_router.include_router(video.router)
