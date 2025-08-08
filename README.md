# MCP Studio

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.11-FF6F00.svg)](https://github.com/yourorg/fastmcp)

A comprehensive UI for managing MCP (Model Control Protocol) servers, built with FastMCP 2.11 and FastAPI.

## The MCP Story

MCP (Model Control Protocol) is an open protocol for interacting with AI models and tools. It provides a standardized way to:

- **Discover** available AI models and tools
- **Execute** operations in a consistent manner
- **Stream** results in real-time
- **Manage** AI resources efficiently

MCP Studio is built on top of FastMCP 2.11, which provides a high-performance, async-first implementation of the MCP protocol, combined with FastAPI for the web interface.

## FastMCP 2.11 and 2.10 Features

### FastMCP 2.11 Improvements

- **Performance**: Optimized for high-throughput, low-latency operations
- **Async-First**: Built on Python's asyncio for efficient I/O handling
- **Type Safety**: Full type annotations and validation with Pydantic
- **Extensible**: Easy to add new transports and protocols
- **Compatibility**: Backward compatible with existing MCP implementations

### FastMCP 2.10 Key Features

- **Structured Output**: Standardized JSON-based output format for consistent parsing and processing
- **Elicitation**: Built-in support for interactive prompts and user input collection
- **DXT Packaging**: Seamless distribution and deployment of MCP tools and configurations

### DXT Packaging

MCP Studio leverages FastMCP's DXT packaging system for

- **Tool Distribution**: Bundle and distribute MCP tools as self-contained packages
- **Dependency Management**: Automatic handling of Python dependencies
- **Versioning**: Clear version control for tools and their requirements
- **Deployment**: One-command deployment of tools to MCP servers

## FastAPI Integration

MCP Studio leverages FastAPI to provide:

- **Automatic API Documentation**: Interactive API docs with Swagger UI and ReDoc
- **Dependency Injection**: Clean architecture with dependency injection
- **WebSocket Support**: Real-time updates and streaming
- **Background Tasks**: Efficient handling of long-running operations
- **Security**: Built-in security features and middleware

## Features

- **Dashboard**: Overview of all registered MCP servers
- **Stdio Transport**: Robust stdio-based communication with MCP clients, including process management and error handling
- **Tool Explorer**: Browse and search available tools across MCP servers
- **Schema Visualization**: Interactive visualization of tool schemas
- **Test Console**: Directly test MCP tools from the UI
- **Local Development**: Integration with local MCP server development
- **Structured Logging**: Comprehensive logging with structured data
- **DXT Packaging**: Seamless tool distribution and deployment
- **FastSPI Integration**: High-performance communication

## Stdio Transport

MCP Studio includes a robust stdio transport implementation for seamless communication with MCP clients. This transport is ideal for local development and production deployments where direct process management is required.

### Key Features

- **Bidirectional Communication**: Full-duplex communication over stdio streams
- **Process Management**: Automatic process lifecycle management
- **Reconnection Logic**: Automatic reconnection with exponential backoff
- **Error Handling**: Comprehensive error handling and recovery
- **Logging**: Detailed logging of all communications
- **Platform Support**: Works on Windows, macOS, and Linux

### Basic Usage

```python
from mcp_studio.app.core.stdio import StdioTransport
import asyncio

async def main():
    # Create a new stdio transport
    transport = StdioTransport(
        command="python -m your_mcp_client",
        cwd="/path/to/client",
        env={"ENV_VAR": "value"}
    )
    
    # Start the transport
    await transport.start()
    
    try:
        # Send a message to the client
        response = await transport.send_message({
            "jsonrpc": "2.0",
            "method": "get_tools",
            "params": {},
            "id": 1
        })
        print(f"Response: {response}")
        
    finally:
        # Clean up
        await transport.stop()

# Run the example
asyncio.run(main())
```

### Configuration Options

| Parameter     | Type            | Description                                        | Default     |
|---------------|-----------------|----------------------------------------------------|-------------|
| `command`     | str or List[str]| Command to execute                                 | Required    |
| `cwd`         | str             | Working directory for the process                  | Current dir |
| `env`         | Dict[str, str]  | Environment variables                              | `None`      |
| `auto_reconnect`| bool           | Enable/disable automatic reconnection              | `True`      |
| `max_retries` | int             | Maximum reconnection attempts                      | `5`         |
| `retry_delay` | float           | Initial delay between reconnection attempts (sec)  | `1.0`       |
| `log_level`   | str             | Logging level (debug, info, warning, error)        | `"info"`    |

### Error Handling

The stdio transport includes comprehensive error handling:

- `TransportError`: Base class for all transport-related errors
- `ProcessError`: Raised when the client process fails to start or crashes
- `TimeoutError`: Raised when a request times out
- `ConnectionError`: Raised when the connection to the client is lost

### Advanced Usage: Custom Message Handling

```python
class CustomStdioTransport(StdioTransport):
    async def handle_message(self, message: dict):
        # Process incoming messages here
        if message.get("method") == "notification":
            print(f"Received notification: {message}")
        else:
            # Default message handling
            await super().handle_message(message)

    async def on_connect(self):
        print("Connected to MCP client")
        # Perform any initialization here

    async def on_disconnect(self):
        print("Disconnected from MCP client")
        # Perform any cleanup here
```

### Logging

Enable debug logging to see detailed communication:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Troubleshooting

### Common Issues

1. **Connection Timeouts**
   - Verify the MCP client is running and accessible
   - Check firewall settings if connecting to a remote host
   - Increase timeout settings if needed

2. **Process Failures**
   - Check the client logs for errors
   - Verify all dependencies are installed
   - Ensure the command path is correct

3. **Permission Issues**
   - Ensure the process has necessary permissions
   - Check file system permissions for the working directory

4. **Debugging**

   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

## Prerequisites

- Python 3.10+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```powershell
   git clone https://github.com/yourusername/mcp-studio.git
   cd mcp-studio
   ```

2. Create and activate a virtual environment (recommended):
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```powershell
   pip install -e ".[dev]"
   ```

## Usage

### Starting MCP Studio

```powershell
# Start the MCP Studio server
python -m mcp_studio
```

### Development

Run the development server with hot-reload:

```powershell
uvicorn mcp_studio.main:app --reload
```

### Testing

Run the test suite:

```powershell
pytest
```

## Project Structure

```
mcp-studio/
├── src/
│   └── mcp_studio/
│       ├── app/
│       │   ├── api/           # FastAPI routes
│       │   ├── core/          # Core application logic
│       │   ├── models/        # Pydantic models
│       │   ├── services/      # Business logic
│       │   └── utils/         # Utility functions
│       ├── static/            # Static files (JS, CSS, images)
│       ├── templates/         # HTML templates
│       ├── __init__.py
│       └── main.py           # Application entry point
├── tests/                     # Test files
├── .env.example              # Example environment variables
├── pyproject.toml            # Project metadata and dependencies
└── README.md                 # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Your Name - [@your_twitter](https://twitter.com/your_twitter) - your.email@example.com

Project Link: [https://github.com/yourusername/mcp-studio](https://github.com/yourusername/mcp-studio)
