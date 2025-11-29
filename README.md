# MCP Studio

[![FastMCP 2.13.1](https://img.shields.io/badge/FastMCP-2.13.1-green.svg)](https://github.com/jlowin/fastmcp)
[![CI](https://img.shields.io/github/actions/workflow/status/sandraschi/mcp-studio/ci.yml?label=CI)](https://github.com/sandraschi/mcp-studio/actions)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)

🎯 **Mission Control for the MCP Zoo** 🦁🐘🦒 - A comprehensive web-based management platform for MCP (Model Context Protocol) servers, built with FastMCP 2.13.1 and FastAPI.

## 🆕 **What's New (v2.0.0)**

### 🔍 **Runt Analyzer** - SOTA Compliance Dashboard
Scan `D:/Dev/repos` and instantly identify which MCP repos need work:
- 🔴 **Red** = Critical runts (FastMCP outdated, no CI, no tests)
- 🟠 **Orange** = Needs improvement (warnings, minor issues)
- 🟢 **Green** = SOTA compliant (all checks pass)

**Checks performed:**
- FastMCP version (2.12+ required)
- Portmanteau refactor (if >15 tools)
- CI/CD workflow presence
- Ruff linting configuration
- Test harness (unit/integration, pytest, coverage)
- Help & status tools
- DXT packaging
- Proper docstrings
- Logging vs print statements
- Error handling quality

### 🎛️ **Tool Groups** - Smart Activate/Deactivate
Like Cursor's MCP activation, but with predefined workflow groups:

| Group | Servers | Use Case |
|-------|---------|----------|
| 🎵 Audio Production | virtualdj, reaper, ableton | DJ & DAW workflows |
| 🎬 Video Production | davinci-resolve, premiere | Video editing |
| 🏠 Smart Home | tapo, hue, ring, nest | Home automation |
| 📺 Media | plex, jellyfin, spotify | Media libraries |
| 📚 Knowledge | advanced-memory, obsidian | Note-taking |
| 💻 Development | github, gitlab, docker | Coding |
| 🚇 Transit | vienna-transit, weather | Location services |
| 💬 Communication | gmail, calendar, slack | Productivity |
| 🌐 Web | browser, puppeteer | Web automation |

**Context Budget:** When LLM is added, only active group tools load into context!

### 🧪 **Smoke Test** - No-LLM Server Testing
Bare minimum connectivity test for all MCP servers:
1. Spawn via stdio
2. Initialize connection
3. List available tools
4. Call help/status tool
5. Verify non-empty response

**No LLM required** - just validates servers are alive!

## 🚀 **What is MCP Studio?**

MCP Studio is the **central hub** for managing your entire MCP infrastructure. It provides both a **beautiful web interface** and a **powerful MCP server**, making it the ultimate tool for developers and users working with AI tools and MCP servers.

### **Dual Architecture** 🏗️

```
┌─────────────────┐    stdio     ┌──────────────────┐    HTTP/WS    ┌─────────────────┐
│  Claude Desktop │ ←----------→ │   MCP Studio     │ ←----------→ │   Web Browser   │
│  (MCP Client)   │   JSON-RPC   │   (MCP Server)   │   REST API    │   (Frontend UI) │
└─────────────────┘              └──────────────────┘               └─────────────────┘
```

## ✨ **Key Features**

### **🎯 Working Sets Switcher** (New!)
One-click switching between focused MCP server configurations for different workflows:

- **🛠️ Development Work**: GitHub, Docker, Playwright, coding tools (10 servers)
- **🎨 Media & Creative**: Blender, Immich, Plex, creative tools (10 servers)
- **📞 Communication**: Microsoft 365, productivity tools (9 servers)
- **🤖 Automation**: VirtualBox, PyWinAuto, system automation (10 servers)
- **🎮 Entertainment**: Media consumption, personal tools (8 servers)

**Safety Features:**
- ✅ Automatic backups before every switch
- ✅ Preview mode showing exact changes
- ✅ Config validation and compatibility checks
- ✅ One-click restoration from any backup

### **📊 MCP Server Management**
- **Server Discovery**: Automatically discovers and lists all available MCP servers
- **Health Monitoring**: Real-time status, performance metrics, and health checks
- **Tool Explorer**: Browse, search, and categorize tools across all servers
- **Schema Visualization**: Interactive display of tool schemas and parameters
- **Test Console**: Live testing interface for MCP tools with parameter forms

### **⚡ FastMCP 2.13.1 Integration**
- **High-Performance**: Optimized for low-latency, high-throughput operations
- **Stdio Transport**: Robust bidirectional communication over stdin/stdout
- **Type Safety**: Full Pydantic validation for all tool parameters
- **Async-First**: Built on Python asyncio for efficient I/O handling
- **MCPB Packaging**: Seamless tool distribution and deployment
- **250+ Tools**: No context limit since no LLM - connect everything!

### **🎨 Modern Web Interface**
- **Real-time Updates**: WebSocket-based live updates
- **Mobile Responsive**: Works perfectly on all screen sizes
- **Beautiful UI**: Modern design with Tailwind CSS
- **Interactive Components**: Drag-and-drop, modals, and smooth animations

## 🎯 **Use Cases**

### **For Developers** 👨‍💻
- **MCP Server Development**: Test and debug MCP servers during development
- **Tool Discovery**: Explore available tools across multiple MCP servers
- **Integration Testing**: Validate MCP integrations before deployment
- **Performance Monitoring**: Track MCP server performance and health

### **For End Users** 👤
- **Workflow Optimization**: Switch between focused tool sets for different tasks
- **Tool Management**: Organize and access AI tools through intuitive interface
- **System Administration**: Monitor and manage MCP infrastructure
- **Configuration Management**: Safely manage complex MCP configurations

## 📦 **Installation**

### **Prerequisites**
- Python 3.10+
- Node.js 18+ (for some MCP servers)
- Git

### **Quick Start**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sandraschi/mcp-studio.git
   cd mcp-studio
   ```

2. **Install with uv (recommended):**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create virtual environment and install
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e ".[dev]"
   ```

3. **Or install with pip:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

## 🚀 **Usage**

### **Web Interface Mode** (Recommended)
Start the full web interface with management dashboard:

```bash
# Start MCP Studio web interface
python -m mcp_studio

# Or with custom settings
python -m mcp_studio --host 0.0.0.0 --port 8080
```

Then open http://localhost:8000 in your browser.

### **MCP Server Mode**
Run as a standalone MCP server for integration with Claude Desktop:

```bash
# Run as MCP server
python -m mcp_studio --mode mcp

# With custom configuration
python -m mcp_studio --mode mcp --name "My MCP Studio" --minimal
```

### **Claude Desktop Integration**
Add to your Claude Desktop configuration (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "mcp-studio": {
      "command": "python",
      "args": ["-m", "mcp_studio", "--mode", "mcp"],
      "cwd": "/path/to/mcp-studio"
    }
  }
}
```

## 🔧 **Working Sets Configuration**

### **Using Working Sets**
1. Open MCP Studio web interface
2. Navigate to "Working Sets" section
3. Click on any working set card to preview changes
4. Click "Activate" to switch your Claude Desktop configuration
5. Restart Claude Desktop to apply changes

### **Custom Working Sets**
Create your own working set templates by adding JSON files to the `templates/` directory:

```json
{
  "name": "My Custom Set",
  "id": "custom_set",
  "description": "Custom tools for my specific workflow",
  "icon": "🎯",
  "category": "Custom",
  "servers": [
    {
      "name": "basic-memory",
      "required": true,
      "description": "Essential note-taking"
    },
    {
      "name": "github",
      "required": false,
      "description": "Version control"
    }
  ]
}
```

## 🏗️ **Project Structure**

```
mcp-studio/
├── src/
│   └── mcp_studio/
│       ├── app/                    # FastAPI web application
│       │   ├── api/               # API routes and endpoints
│       │   ├── core/              # Core application logic
│       │   ├── models/            # Pydantic data models
│       │   └── services/          # Business logic services
│       ├── components/            # React UI components
│       │   └── WorkingSetSwitcher.tsx
│       ├── working_sets/          # Working sets management
│       │   └── manager.py         # Working set manager
│       ├── api/                   # Working sets API
│       │   └── working_sets.py    # FastAPI endpoints
│       ├── static/               # Static web assets
│       ├── templates/            # HTML templates
│       └── main.py              # Application entry point
├── templates/                    # Working set definitions
│   ├── dev_work.json            # Development working set
│   ├── media_work.json          # Media/creative working set
│   ├── communication.json       # Communication working set
│   ├── automation.json          # Automation working set
│   └── entertainment.json       # Entertainment working set
├── tests/                       # Test files
├── simple_test.py              # Quick functionality test
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

## 🧪 **Testing**

### **Quick Test**
```bash
# Test core functionality
python simple_test.py
```

### **Full Test Suite**
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp_studio

# Run specific test category
pytest tests/test_working_sets.py
```

### **Manual Testing**
1. **Test Working Sets**: Use the web interface to switch between working sets
2. **Test MCP Server**: Connect from Claude Desktop and verify tools work
3. **Test API**: Use the interactive API docs at `/api/docs`

## 🔒 **Security & Safety**

### **Working Sets Safety**
- **Automatic Backups**: Every configuration change creates a timestamped backup
- **Preview Mode**: See exactly what will change before applying
- **Validation**: Compatibility checks before switching
- **Recovery**: Restore from any backup with one click

### **MCP Security**
- **Stdio Transport**: Secure local communication
- **Input Validation**: Full Pydantic validation on all inputs
- **Error Handling**: Comprehensive error handling and recovery
- **Audit Logging**: Detailed logs of all operations

## 🛠️ **Development**

### **Development Mode**
```bash
# Start with hot reload
uvicorn mcp_studio.main:app --reload

# Or using the development server
python -m mcp_studio --experimental --deprecated
```

### **Building New Tools**
```python
from fastmcp import FastMCP

mcp = FastMCP("My Tool Server")

@mcp.tool
def my_tool(param: str) -> str:
    """My custom tool description."""
    return f"Result: {param}"

if __name__ == "__main__":
    mcp.run()
```

### **Adding to Working Sets**
1. Create your MCP server
2. Add it to your Claude Desktop config
3. Update working set templates in `templates/`
4. The working sets will automatically include your new server

## 📚 **Documentation**

- **API Documentation**: Available at `/api/docs` when running
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io)
- **FastMCP**: [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- **FastAPI**: [FastAPI Documentation](https://fastapi.tiangolo.com)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Setup**
```bash
# Clone your fork
git clone https://github.com/yourusername/mcp-studio.git
cd mcp-studio

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 🎉 **What Makes MCP Studio Special**

### **🎯 Mission Control for MCP**
MCP Studio is the **first comprehensive management platform** for the MCP Zoo. It bridges the gap between raw MCP servers and user-friendly interfaces. (Not a flea circus - these are proper beasts! 🦁)

### **⚡ Performance First**
Built on **FastMCP 2.13.1** and **FastAPI**, providing enterprise-grade performance with developer-friendly APIs.

### **🔧 Workflow Optimization**
The **Working Sets** feature revolutionizes how users interact with AI tools by providing **context-aware tool selection**.

### **🚀 Future-Ready**
Designed for the rapidly evolving AI landscape with support for **DXT packaging**, **authentication**, and **enterprise deployment**.

## 📄 **License**

Distributed under the MIT License. See `LICENSE` for more information.

## 🙏 **Acknowledgments**

- **FastMCP** by Jonathan Lowin - The foundation that makes this possible
- **FastAPI** by Sebastián Ramirez - Excellent web framework
- **Anthropic** - For the Model Context Protocol specification
- **The MCP Zoo** 🦁🐘🦒 - For building amazing tools and servers

---

**MCP Studio** - Your mission control for the MCP Zoo! 🦁🐘🦒🚀