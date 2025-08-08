# MCP Studio Quickstart

This guide will help you get started with MCP Studio in just a few minutes.

## Prerequisites

- Python 3.10 or later
- pip (Python package manager)
- Git (optional)

## Installation

1. **Install MCP Studio**
   ```bash
   pip install mcp-studio
   ```

2. **Verify Installation**
   ```bash
   mcp-studio --version
   ```

## First Steps

1. **Start MCP Studio**
   ```bash
   mcp-studio start
   ```

2. **Access the Web Interface**
   Open your browser and go to: http://localhost:8000

3. **Connect to an MCP Server**
   - Click "Add Server"
   - Enter the server details
   - Click "Connect"

## Basic Usage

### List Available Tools
```bash
mcp-studio tools list
```

### Execute a Tool
```bash
mcp-studio tools execute text_generator --prompt "Hello, world!" --max_length 50
```

### View Execution History
```bash
mcp-studio executions list
```

## Next Steps

- Explore the [User Guide](user-guide/)
- Check out [API Reference](api/reference.md)
- Join our [Community Discussions](community/discussions.md)

## Need Help?

- Check the [FAQ](faq.md)
- Search the [Discussions](https://github.com/sandraschi/mcp-studio/discussions)
- Open an [Issue](https://github.com/sandraschi/mcp-studio/issues)
