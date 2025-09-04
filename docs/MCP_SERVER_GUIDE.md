# MCP Server Development Guide

## Table of Contents
1. [Introduction to MCP](#introduction-to-mcp)
2. [MCP Architecture](#mcp-architecture)
3. [Setting Up Your Development Environment](#setting-up-your-development-environment)
4. [Creating a Basic MCP Server](#creating-a-basic-mcp-server)
5. [Tool Development](#tool-development)
6. [Testing and Debugging](#testing-and-debugging)
7. [Packaging and Distribution](#packaging-and-distribution)
8. [Best Practices](#best-practices)
9. [Advanced Topics](#advanced-topics)

## Introduction to MCP

MCP (Model Control Protocol) is an open protocol for interacting with AI models and tools. It provides a standardized way to:

- **Discover** available AI models and tools
- **Execute** operations in a consistent manner
- **Stream** results in real-time
- **Manage** AI resources efficiently

MCP Studio is built on top of FastMCP 2.11, which provides a high-performance, async-first implementation of the MCP protocol.

## MCP Architecture

### Core Components

1. **MCP Server**: Manages tools and handles client connections
2. **Tools**: Individual units of functionality (e.g., text generation, image processing)
3. **Transports**: Communication channels (HTTP, WebSockets, stdio)
4. **Schema**: Type definitions and validation for tool inputs/outputs

### Communication Flow

```
Client <-> Transport Layer <-> MCP Server <-> Tools
```

## Setting Up Your Development Environment

### Prerequisites

- Python 3.10+
- Node.js 18+ (for UI development)
- Docker (optional, for containerization)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourorg/mcp-studio.git
   cd mcp-studio
   ```

2. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e .[dev]
   ```

4. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

## Creating a Basic MCP Server

### Project Structure

```
my_mcp_server/
├── pyproject.toml
├── my_mcp_server/
│   ├── __init__.py
│   ├── server.py
│   └── tools/
│       ├── __init__.py
│       └── example_tool.py
└── tests/
    └── test_example_tool.py
```

### Example Server Implementation

```python
# my_mcp_server/server.py
from fastmcp import FastMCP, Tool
from fastapi import FastAPI
import uvicorn

app = FastAPI()
mcp = FastMCP(app)

@mcp.tool()
async def greet(name: str) -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Running the Server

```bash
python -m my_mcp_server.server
```

## Tool Development

### Tool Structure

```python
from fastmcp import Tool, Parameter
from pydantic import BaseModel

class ToolInput(BaseModel):
    text: str = Parameter(..., description="Input text to process")
    max_length: int = Parameter(100, ge=1, le=1000, description="Maximum output length")

@Tool(
    name="text_processor",
    description="Processes text with advanced NLP",
    input_model=ToolInput
)
async def process_text(input: ToolInput) -> str:
    """Process the input text and return the result."""
    # Your tool logic here
    return input.text[:input.max_length]
```

### Tool Registration

Tools can be registered in two ways:

1. **Decorator-based** (shown above)
2. **Programmatic registration**:
   ```python
   mcp.register_tool(process_text)
   ```

## Testing and Debugging

### Unit Testing

```python
# tests/test_example_tool.py
def test_greet():
    from my_mcp_server.tools.example_tool import greet
    assert await greet("World") == "Hello, World!"
```

### Integration Testing

```python
# tests/test_server.py
from fastapi.testclient import TestClient
from my_mcp_server.server import app

def test_greet_endpoint():
    client = TestClient(app)
    response = client.post("/tools/greet", json={"name": "World"})
    assert response.status_code == 200
    assert response.json() == {"result": "Hello, World!"}
```

### Debugging

1. Enable debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Use the MCP Studio debugger for step-through debugging

## Packaging and Distribution

### Creating a DXT Package

1. Create a `pyproject.toml`:
   ```toml
   [build-system]
   requires = ["setuptools>=42"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "my-mcp-tools"
   version = "0.1.0"
   description = "My custom MCP tools"
   
   [tool.fastmcp]
   entry_point = "my_mcp_tools:app"
   ```

2. Build the package:
   ```bash
   python -m build
   ```

3. Install locally:
   ```bash
   pip install dist/my-mcp-tools-0.1.0.tar.gz
   ```

## Best Practices

### Tool Design

1. **Idempotency**: Make tools idempotent when possible
2. **Stateless**: Keep tools stateless for better scalability
3. **Validation**: Validate all inputs using Pydantic models
4. **Error Handling**: Provide meaningful error messages
5. **Documentation**: Document all tools with examples

### Performance

1. Use async/await for I/O operations
2. Implement streaming for large outputs
3. Cache expensive computations
4. Use connection pooling for external services

### Security

1. Validate all inputs
2. Use HTTPS for production
3. Implement authentication and authorization
4. Sanitize outputs to prevent XSS

## Advanced Topics

### Custom Transports

```python
from fastmcp.transports import BaseTransport

class CustomTransport(BaseTransport):
    async def start(self):
        # Initialize transport
        pass
        
    async def send(self, message: dict):
        # Send message to client
        pass
        
    async def stop(self):
        # Cleanup resources
        pass
```

### Authentication

```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate token and return user
    user = validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user

@mcp.tool()
async def secure_tool(user: User = Depends(get_current_user)):
    return {"message": f"Hello, {user.username}"}
```

### Metrics and Monitoring

```python
from prometheus_client import Counter, generate_latest
from fastapi import Response

REQUEST_COUNT = Counter('mcp_requests_total', 'Total number of requests')

@mcp.tool()
async def monitored_tool():
    REQUEST_COUNT.inc()
    return {"status": "ok"}

@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest())
```

## Next Steps

1. Explore the [MCP Specification](https://github.com/model-control-protocol/spec)
2. Check out the [Example Tools](examples/) directory
3. Join the [MCP Community](https://community.mcprotocol.org)
4. Contribute to the project on [GitHub](https://github.com/yourorg/mcp-studio)

## Support

For help and support:
- [Documentation](https://docs.mcprotocol.org)
- [GitHub Issues](https://github.com/yourorg/mcp-studio/issues)
- [Community Forum](https://community.mcprotocol.org)
- Email: support@mcprotocol.org
