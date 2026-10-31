"""
Health probe service evaluating live dependencies without false claims.
"""

import socket
import sys
from urllib.parse import urlparse
from typing import Any, Dict

from backend.app.core.config import settings
from backend.app.db.session import check_database_health
from backend.app.schemas.health import BasicHealthResponse, DetailedHealthResponse


def _check_tcp_port(url_str: str, default_port: int, timeout_seconds: float = 0.5) -> Dict[str, Any]:
    """Probes whether a network host:port responds to a TCP connection handshake."""
    try:
        parsed = urlparse(url_str)
        host = parsed.hostname or "localhost"
        port = parsed.port or default_port
        
        with socket.create_connection((host, port), timeout=timeout_seconds):
            return {
                "status": "healthy",
                "connected": True,
                "endpoint": f"{host}:{port}",
            }
    except Exception as exc:
        return {
            "status": "unreachable",
            "connected": False,
            "detail": f"Connection probe failed: {exc.__class__.__name__}",
        }


def check_redis_health() -> Dict[str, Any]:
    """Tests whether Redis server is reachable at configured URL."""
    return _check_tcp_port(settings.REDIS_URL, default_port=6379)


def check_storage_health() -> Dict[str, Any]:
    """Tests whether S3/MinIO object store is reachable at configured URL."""
    return _check_tcp_port(settings.S3_ENDPOINT_URL, default_port=9000)


def get_basic_health() -> BasicHealthResponse:
    """Returns baseline API availability."""
    return BasicHealthResponse(
        status="healthy",
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
    )


def get_detailed_health() -> DetailedHealthResponse:
    """Probes live dependencies and returns structured diagnosis."""
    db_health = check_database_health()
    redis_health = check_redis_health()
    storage_health = check_storage_health()

    # Overall system health evaluation
    dependencies = {
        "database": db_health,
        "redis": redis_health,
        "object_storage": storage_health,
    }

    # If database is healthy, the backend core is healthy; if optional infrastructure is down in dev, status is degraded
    if db_health.get("connected"):
        overall_status = "healthy" if (redis_health.get("connected") and storage_health.get("connected")) else "degraded"
    else:
        overall_status = "unhealthy"

    system_info = {
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
    }

    return DetailedHealthResponse(
        status=overall_status,
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        dependencies=dependencies,
        system=system_info,
    )

