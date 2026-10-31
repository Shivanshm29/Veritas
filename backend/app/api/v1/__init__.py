"""
API v1 Router aggregation for Veritas.
"""

from fastapi import APIRouter
from backend.app.api.v1.endpoints import health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)

