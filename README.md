# MCP Studio

**By FlowEngineer sandraschi**

[![Beta](https://img.shields.io/badge/Status-Beta-orange.svg)](README.md#-beta-status)
[![FastMCP 2.13.1](https://img.shields.io/badge/FastMCP-2.13.1-green.svg)](https://github.com/jlowin/fastmcp)
[![CI](https://img.shields.io/badge/CI-Passing-brightgreen.svg)](https://github.com/sandraschi/mcp-studio/actions)
[![Dual Architecture](https://img.shields.io/badge/Architecture-Dual-orange.svg)](README.md#-what-is-mcp-studio)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com/)

 **Mission Control for the MCP Zoo** 

>  **Beta Software**: MCP Studio is currently in **beta**. Features may be incomplete, APIs may change, and there may be bugs. Use at your own risk. See [Beta Status](#-beta-status) below for details.

**Dual-Architecture Platform**: A **web-based management dashboard** (FastAPI frontend) and an **MCP server** (FastMCP 2.13.1) for managing MCP servers.

** This repository contains:**
- **Web Dashboard**: FastAPI-based interface for MCP server management (work in progress)
- **MCP Server**: FastMCP 2.13.1 server providing tools to other MCP clients (Claude Desktop, etc.)
- **Dual Purpose**: Can be used as a web app OR as an MCP server, or both simultaneously

##  **Beta Status**

MCP Studio is currently in **beta**. This means:

-  Core functionality is working but may have bugs
-  Features may be incomplete or change without notice
-  APIs and configuration formats may change in future versions
-  Some edge cases may not be handled properly
-  Documentation may be incomplete or outdated
-  UI/UX is still being refined

**Before using in production:**
- Test thoroughly in your environment
- Keep backups of your MCP configurations
- Report issues on GitHub
- Expect breaking changes in future releases

##  **What's New (v0.3.0-beta)**

###  **Enhanced Working Sets** - MAJOR UPDATE!
Purpose-built MCP server configurations for specific workflows:

#### ** Media Consumption Set**
- **Calibre MCP** - Ebook library management
- **Plex MCP** - Media streaming server
- **Immich MCP** - Photo collection browsing

#### ** Robotics & 3D Development Set**
- **Robotics MCP** - Robot control and monitoring
- **Avatar MCP** - 3D avatar management
- **Unity3D MCP** - Unity game engine integration
- **OSC MCP** - Real-time communication protocol
- **Blender MCP** - 3D modeling and animation
- **VRChat MCP** - VR world creation

#### **Key Features:**
- **One-click activation** with automatic backup/restore
- **6 specialized working sets** for different use cases
- **Visual status indicators** for current active set
- **Preview functionality** before switching

###  **Client Configuration Management** - NEW!
Three powerful tools for managing MCP client configurations:
- **`discover_clients`** - Discover all MCP clients (Claude Desktop, Cursor IDE, Windsurf, etc.) and their configured servers
- **`get_client_config`** - Read configuration for any MCP client
- **`set_client_config`** - Update client configurations with automatic backup support

 for managing multiple MCP clients and their server configurations from a single interface.

##  **Previous Updates (v0.2.1-beta)**

###  **Enhanced Runt Analyzer** - Rule-Based SOTA Analysis
- ** Rule-Based System**: Declarative rule definitions replacing hardcoded criteria
- ** Smart Caching**: File-based persistence to avoid re-scanning (default: 1 hour TTL)
- ** Markdown Reports**: Human-readable markdown output for scan results
- ** Detailed Output**: Structured JSON with repo information for analysis
- ** Cache Management**: Configurable TTL, cache clearing, and statistics

###  **Runt Analyzer** - SOTA Compliance Dashboard
Scan `D:/Dev/repos` and instantly identify which MCP repos need work:
-  **Red** = Critical runts (FastMCP outdated, no CI, no tests)
-  **Orange** = Needs improvement (warnings, minor issues)
-  **Green** = SOTA compliant (all checks pass)

**Checks performed:**
- FastMCP version (2.12+ required)
- Portmanteau refactor (if >15 tools)
- CI/CD workflow presence
- Ruff linting configuration
- Test harness (unit/integration, pytest, coverage)
- Help & status tools
- Packaging & Distribution
- Proper docstrings
- Logging vs print statements
- Error handling quality

###  **Tool Groups** - Smart Activate/Deactivate
Like Cursor's MCP activation, but with predefined workflow groups:

| Group | Servers | Use Case |
|-------|---------|----------|
|  Audio Production | virtualdj, reaper, ableton | DJ & DAW workflows |
|  Video Production | davinci-resolve, premiere | Video editing |
|  Smart Home | tapo, hue, ring, nest | Home automation |
|  Media | plex, jellyfin, spotify | Media libraries |
|  Knowledge | advanced-memory, obsidian | Note-taking |
|  Development | github, gitlab, docker | Coding |
|  Transit | vienna-transit, weather | Location services |
|  Communication | gmail, calendar, slack | Productivity |
|  Web | browser, puppeteer | Web automation |

**Context Budget:** When LLM is added, only active group tools load into context!

###  **Smoke Test** - No-LLM Server Testing
Bare minimum connectivity test for all MCP servers:
1. Spawn via stdio
2. Initialize connection
3. List available tools
4. Call help/status tool
5. Verify non-empty response

**No LLM required** - just validates servers are alive!

###  **Preprompt Management** - AI Personality System (NEW!)
Create infinite AI assistant personalities with dynamic storage and AI-assisted generation:

**Features:**
-  **SQLite Storage**: Persistent preprompt library with metadata
-  **AI Refine**: Type "coin collector"  AI generates elaborate personality in 60 seconds
-  **Import .md Files**: Upload markdown files as preprompts
-  **Dynamic Dropdown**: Load unlimited personalities without code changes
-  **Creative Personalities**: Pirate, Butterfly, Zen Master, Aussie Coder, and more!

**Demo Workflow:**
```
User types: "coin collector"
       
Clicks: " AI Refine"
       
14g LLM generates: "You are a numismatic enthusiast helping with MCP servers!
                    You see code patterns like rare coins..."
       
Auto-saves with:  emoji
       
Appears in dropdown immediately!
```

** for demos** - generate new personalities on-the-fly!

##  **What is MCP Studio?**

MCP Studio is the **central hub** for managing your entire MCP infrastructure. It's a **dual-architecture platform** that provides both:

1. ** Web Dashboard** (FastAPI + React): Visual interface for browsing, testing, and managing MCP servers
2. ** MCP Server** (FastMCP 2.13.1): Provides 12 powerful tools to other MCP clients like Claude Desktop

**Use it as:**
- A standalone web application for MCP server management
- An MCP server integrated into Claude Desktop or other MCP clients
- Both simultaneously (web UI + MCP server tools)

### **Dual Architecture** 

```
    stdio         HTTP/WS    
  Claude Desktop  ----------    MCP Studio      ----------    Web Browser   
  (MCP Client)      JSON-RPC      (MCP Server)      REST API       (Frontend UI) 
                             
```

##  **Key Features**

### ** Working Sets Switcher** (New!)
One-click switching between focused MCP server configurations for different workflows:

- ** Development Work**: GitHub, Docker, Playwright, coding tools (10 servers)
- ** Media & Creative**: Blender, Immich, Plex, creative tools (10 servers)
- ** Communication**: Microsoft 365, productivity tools (9 servers)
- ** Automation**: VirtualBox, PyWinAuto, system automation (10 servers)
- ** Entertainment**: Media consumption, personal tools (8 servers)

**Safety Features:**
-  Automatic backups before every switch
-  Preview mode showing exact changes
-  Config validation and compatibility checks
-  One-click restoration from any backup

### ** MCP Server Management**
- **Server Discovery**: Automatically discovers and lists all available MCP servers
- **Health Monitoring**: Real-time status, performance metrics, and health checks
- **Tool Explorer**: Browse, search, and categorize tools across all servers
- **Schema Visualization**: Interactive display of tool schemas and parameters
- **Test Console**: Live testing interface for MCP tools with parameter forms

### ** FastMCP 2.13.1 Integration**
- **Stdio Transport**: Bidirectional communication over stdin/stdout
- **Type Safety**: Pydantic validation for tool parameters
- **Async-First**: Built on Python asyncio
- **MCPB Packaging**: Tool distribution support
- **MCP Studio Tools**: Server lifecycle management tools
- **Tool Discovery**: Connect to multiple MCP servers

### ** Server Lifecycle Management**
- **Create**: Generate SOTA-compliant servers with all required components
- **Read**: Repository analysis and scanning
- **Update**: Add missing SOTA components automatically
- **Delete**: Safe removal with backup and safety checks

### ** Web Interface** (Beta)
- **Real-time Updates**: WebSocket support (experimental)
- **Responsive Design**: Basic mobile support
- **UI**: Template-based interface with Tailwind CSS
- **Interactive Components**: Basic forms and navigation

##  Packaging & Distribution

This repository is SOTA 2026 compliant and uses the officially validated `@anthropic-ai/mcpb` workflow for distribution.

### Pack Extension
To generate a `.mcpb` distribution bundle with complete source code and automated build exclusions:
```bash
# SOTA 2026 standard pack command
mcpb pack . dist/mcp-studio.mcpb
```

##  **Use Cases**

### **For Developers** 
- **MCP Server Development**: Test and debug MCP servers during development
- **Tool Discovery**: Explore available tools across multiple MCP servers
- **Integration Testing**: Validate MCP integrations before deployment
- **Performance Monitoring**: Track MCP server performance and health

### **For End Users** 
- **Workflow Optimization**: Switch between focused tool sets for different tasks
- **Tool Management**: Organize and access AI tools through intuitive interface
- **System Administration**: Monitor and manage MCP infrastructure
- **Configuration Management**: Safely manage complex MCP configurations

##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx mcp-studio
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "mcp-studio": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/mcp-studio", "run", "mcp-studio"]
  }
}
```
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

##  **Usage**

### **Docker Deployment** (Beta - Use with Caution)

Containerize the web dashboard for easy deployment:

```bash
# Set your repos directory (Windows example)
$env:REPOS_DIR = "D:/Dev/repos"

# Build and run with Docker Compose
docker compose up -d

# Access dashboard at http://localhost:8001
```

**See [Docker Deployment Guide](DOCKER.md) for details:**
- Volume mounts for repos directory (full read-write access required)
- Ollama integration options (host, container, or network)
- Windows/Linux/Mac specific configuration
- Troubleshooting guide

**Important**: Only the web dashboard is containerized. MCP server mode should NEVER be containerized.

**Beta Note**: Docker deployment is experimental. Test thoroughly before using in production.

### **Web Interface Mode** (Native)

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

##  **Working Sets Configuration**

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
  "icon": "",
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

##  **Project Structure**

```
mcp-studio/
 src/
    mcp_studio/
        app/                    # FastAPI web application
           api/               # API routes and endpoints
           core/              # Core application logic
           models/            # Pydantic data models
           services/          # Business logic services
        components/            # React UI components
           WorkingSetSwitcher.tsx
        working_sets/          # Working sets management
           manager.py         # Working set manager
        api/                   # Working sets API
           working_sets.py    # FastAPI endpoints
        static/               # Static web assets
        templates/            # HTML templates
        main.py              # Application entry point
 templates/                    # Working set definitions
    dev_work.json            # Development working set
    media_work.json          # Media/creative working set
    communication.json       # Communication working set
    automation.json          # Automation working set
    entertainment.json       # Entertainment working set
 tests/                       # Test files
 simple_test.py              # Quick functionality test
 pyproject.toml              # Project metadata
 README.md                   # This file
```

##  **Testing**

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

##  **Security & Safety**

### **Working Sets Safety**
- **Automatic Backups**: Every configuration change creates a timestamped backup
- **Preview Mode**: See exactly what will change before applying
- **Validation**: Compatibility checks before switching
- **Recovery**: Restore from any backup with one click

### **MCP Security**
- **Stdio Transport**: Secure local communication
- **Input Validation**: Full Pydantic validation on all inputs
- **Error Handling**: Error handling and recovery
- **Audit Logging**: Detailed logs of all operations

##  **Development**

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

##  **Documentation**

- **API Documentation**: Available at `/api/docs` when running
- **MCP Protocol**: [Model Context Protocol Specification](https://modelcontextprotocol.io)
- **FastMCP**: [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- **FastAPI**: [FastAPI Documentation](https://fastapi.tiangolo.com)

##  **Contributing**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/-feature`)
3. Commit your changes (`git commit -m 'Add  feature'`)
4. Push to the branch (`git push origin feature/-feature`)
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

##  **What Makes MCP Studio Different**

### ** Management Tool for MCP**
MCP Studio aims to be a useful management tool for the MCP ecosystem. It provides a web interface and MCP server tools to help organize and manage MCP servers. 

### ** Built on Solid Foundations**
Built on **FastMCP 2.13.1** and **FastAPI** for reliable performance and developer-friendly APIs.

### ** Workflow Optimization**
The **Working Sets** feature helps organize MCP servers into focused configurations for different workflows.

### ** Future-Ready**
Designed for the rapidly evolving AI landscape with support for **MCPB packaging**, **authentication**, and **enterprise deployment**.

##  **License**

Distributed under the MIT License. See `LICENSE` for more information.

##  **Acknowledgments**

- **FastMCP** by Jonathan Lowin - The foundation that makes this possible
- **FastAPI** by Sebastin Ramirez - Excellent web framework
- **Anthropic** - For the Model Context Protocol specification
- **The MCP Zoo**  - For building  tools and servers

---

**MCP Studio** - Your mission control for the MCP Zoo! 
