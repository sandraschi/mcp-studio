"""Pytest fixtures for web app tests."""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pathlib import Path
import sys
import os

# Add src to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set environment variables for testing
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "WARNING")  # Reduce log noise in tests

from mcp_studio.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    # TestClient automatically handles lifespan events
    return TestClient(app, follow_redirects=False)


@pytest_asyncio.fixture
async def async_client():
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mock_server_service(monkeypatch):
    """Mock server service for testing."""
    from unittest.mock import AsyncMock, MagicMock

    mock_service = MagicMock()
    mock_service.get_servers = AsyncMock(return_value={})
    mock_service.get_server = AsyncMock(return_value=None)
    mock_service.get_server_tools = AsyncMock(return_value=[])
    mock_service.start_server = AsyncMock(return_value={"success": True, "message": "Server started"})
    mock_service.stop_server = AsyncMock(return_value={"success": True, "message": "Server stopped"})
    mock_service.execute_tool = AsyncMock(return_value={"success": True, "result": "Tool executed"})

    # Mock the server_service import in the modules that use it
    monkeypatch.setattr("mcp_studio.app.api.endpoints.mcp_servers.server_service", mock_service)

    return mock_service


@pytest.fixture
def mock_config_service(monkeypatch):
    """Mock config service for testing."""
    from unittest.mock import AsyncMock, MagicMock
    
    mock_service = MagicMock()
    mock_service.get_config = AsyncMock(return_value={})
    mock_service.get_clients = AsyncMock(return_value=[])
    
    # Monkeypatch the config_service instance
    from mcp_studio.app.services import config_service
    monkeypatch.setattr("mcp_studio.app.services.config_service.config_service", mock_service)
    
    return mock_service





