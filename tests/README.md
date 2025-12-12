# MCP Studio Test Suite

This directory contains tests for MCP Studio, organized by component.

## Test Structure

```
tests/
├── web_app/              # Web app tests (FastAPI, routes, services)
│   ├── test_api_health.py
│   ├── test_api_servers.py
│   ├── test_api_tools.py
│   ├── test_web_routes.py
│   ├── test_services.py
│   └── test_models.py
├── test_crud_tools.py    # MCP server CRUD operations
├── test_fastmcp.py       # FastMCP integration tests
├── test_imports.py       # Import validation
├── test_setup.py         # Setup/installation tests
├── test_working_sets.py  # Working sets functionality
└── simple_test.py        # Quick functionality test
```

## Running Tests

### All Tests
```bash
pytest
```

### Web App Tests Only
```bash
pytest tests/web_app/ -m web_app
```

### MCP Server Tests Only
```bash
pytest tests/ -m mcp_server
```

### With Coverage
```bash
pytest --cov=mcp_studio --cov-report=html
```

### Specific Test File
```bash
pytest tests/web_app/test_api_health.py
```

## Test Markers

- `@pytest.mark.web_app` - Web app component tests
- `@pytest.mark.mcp_server` - MCP server component tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.unit` - Unit tests

## Test Categories

### Web App Tests (`tests/web_app/`)
Tests for the FastAPI web application:
- API endpoints (health, servers, tools, clients)
- Web routes (dashboard, pages)
- Services (server_service, config_service)
- Data models validation
- WebSocket functionality (if applicable)

### MCP Server Tests
Tests for the MCP server component:
- CRUD operations for MCP servers
- FastMCP integration
- Tool execution
- Server discovery

## Writing New Tests

### Web App Test Example
```python
import pytest
from fastapi.testclient import TestClient
from tests.web_app.conftest import client

def test_my_endpoint(client: TestClient):
    response = client.get("/api/my-endpoint")
    assert response.status_code == 200
```

### MCP Server Test Example
```python
import pytest

@pytest.mark.mcp_server
@pytest.mark.asyncio
async def test_my_tool():
    result = await my_tool_function()
    assert result["success"] is True
```





