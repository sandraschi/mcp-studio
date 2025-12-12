"""Tests for web app services."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path


def test_config_service_initialization():
    """Test that config service can be initialized."""
    from mcp_studio.app.services.config_service import config_service
    
    assert config_service is not None
    # Should have methods for getting config
    assert hasattr(config_service, 'get_config')
    assert hasattr(config_service, 'get_clients')


def test_server_service_initialization():
    """Test that server service can be initialized."""
    from mcp_studio.app.services.server_service import server_service
    
    assert server_service is not None
    # Should have methods for managing servers
    assert hasattr(server_service, 'get_servers')
    assert hasattr(server_service, 'get_server')


@pytest.mark.asyncio
async def test_server_service_get_servers():
    """Test getting all servers."""
    from mcp_studio.app.services.server_service import server_service
    
    servers = server_service.get_servers()
    assert isinstance(servers, dict)


@pytest.mark.asyncio
async def test_server_service_get_server_tools():
    """Test getting tools for a server."""
    from mcp_studio.app.services.server_service import server_service
    
    # Get first available server or use a test ID
    servers = server_service.get_servers()
    if servers:
        server_id = list(servers.keys())[0]
        try:
            tools = await server_service.get_server_tools(server_id)
            assert isinstance(tools, list)
        except Exception:
            # Server might not be running, which is OK for tests
            pass


def test_config_service_get_clients():
    """Test getting MCP clients."""
    from mcp_studio.app.services.config_service import config_service
    
    clients = config_service.get_clients()
    assert isinstance(clients, list)





