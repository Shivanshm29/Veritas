"""
Pytest configuration and fixtures for Veritas Backend Tests.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Ensure test database is in-memory
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"

from backend.app.main import create_app


@pytest.fixture(scope="session")
def app():
    """Provides a fresh FastAPI test application."""
    return create_app()


@pytest.fixture(scope="session")
def client(app):
    """Provides a synchronous HTTP test client."""
    with TestClient(app) as test_client:
        yield test_client

