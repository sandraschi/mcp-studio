# MCP Studio Dashboard

Mission Control for your MCP Zoo - a unified dashboard for managing, analyzing, and interacting with Model Context Protocol servers.

## 🏗️ **Architecture Overview**

The dashboard follows a **modular architecture** for maintainability and performance:

### **📁 File Structure**
```
src/mcp_studio/
├── templates/
│   └── dashboard.html          # Main HTML template (~400 lines)
├── static/
│   ├── css/
│   │   └── dashboard.css       # Custom styles (~110 lines)
│   └── js/
│       ├── utils.js            # Docstring formatting utilities (~180 lines)
│       ├── tabs.js             # Tab switching functionality (~30 lines)
│       ├── clients.js          # MCP client management (~200 lines)
│       ├── repos.js            # Repository scanning (~300 lines)
│       ├── tools.js            # Tool exploration (~150 lines)
│       ├── console.js          # Command execution (~80 lines)
│       └── main.js             # Dashboard coordination (~150 lines)
```

### **🎯 Benefits of Modular Design**
- **Maintainability**: Each module has a single responsibility
- **Readability**: No more scrolling through 3600-line files
- **Debugging**: Issues isolated to specific modules
- **Performance**: Better caching with separate files
- **Development**: Easier to modify individual features

### **🔄 Migration from Monolithic**
- **Before**: Single `dashboard_old.html` (3,601 lines)
- **After**: 8 modular files totaling ~1,600 lines
- **Performance**: Reduced load times, better caching
- **Maintenance**: 87% reduction in file complexity

## Quick Start

```powershell
cd D:\Dev\repos\mcp-studio
python run_dev.py
```

Dashboard: http://localhost:8331

## 🧩 **Modular JavaScript Architecture**

The dashboard JavaScript is organized into focused modules:

### **Core Modules**
- **`utils.js`** - Docstring formatting, text processing, HTML escaping
- **`tabs.js`** - Navigation between dashboard sections
- **`main.js`** - Initialization and coordination of all modules

### **Feature Modules**
- **`clients.js`** - MCP client discovery and management
- **`repos.js`** - Repository scanning and analysis
- **`tools.js`** - Tool exploration and execution
- **`console.js`** - Command-line interface

### **🎨 Styling**
- **`dashboard.css`** - Custom CSS with Tailwind integration
- **Tailwind CDN** - Utility-first CSS framework
- **Toastify** - Notification system

### **📡 API Integration**
All modules communicate with the FastAPI backend via REST endpoints:
- `/api/v1/clients` - Client management
- `/api/v1/clients/{client_id}/tools` - Tool discovery and enablement
- `/api/v1/clients/{client_id}/tools/{tool_name}/toggle` - Enable/disable individual tools
- `/api/v1/repos` - Repository operations
- `/api/v1/tools` - Tool execution

## Features

### 📊 Overview Tab
- **Stats Cards**: Total clients, repos, tools, SOTA count
- **MCP Clients Discovery**: Auto-discovers servers from Claude Desktop, Cursor, Windsurf, Cline configs
- **Repository Health**: Pie chart breakdown of SOTA/Improvable/Runts

### 🔌 MCP Clients Tab
- Lists all discovered MCP server configurations
- Shows server name, command, and config source
- Connect buttons to establish live stdio connections
- **Working Sets**: Purpose-built server configurations for specific use cases:
  - **Media Consumption**: Calibre, Plex, Immich for content management
  - **Robotics & 3D**: Robotics MCP, Avatar, Unity3D, OSC, Blender, VRChat
  - **Development**: Full development environment with testing tools
  - **Automation**: CI/CD, monitoring, and system automation
  - **Communication**: Office tools, email, and productivity apps
- **One-click activation** with automatic backup/restore

### 📦 Repositories Tab
- Grid of all MCP repos in `D:/Dev/repos`
- Filter by status: All, SOTA, Improvable, Runt
- Click any card for detailed analysis modal
- Zoo classification: 🐘 Jumbo → 🐿️ Chipmunk

### 🔧 Tools Tab
- Repository selector dropdown
- Shows static analysis: FastMCP version, tool counts
- Live connection support for real-time tool discovery
- Displays tool schemas and docstrings
- **🟢 Tool Enablement**: Enable/disable individual tools per MCP client
- **📊 Status Indicators**: Visual badges showing enabled/disabled state
- **🔄 Interactive Toggles**: Click to enable/disable tools with immediate feedback

### 💻 Console Tab
- Execute MCP tools directly without an LLM
- Select connected server → select tool → enter JSON params
- View execution results with success/error styling

### 🤖 AI Assistant Tab
- Chat interface powered by Ollama
- **Model Selector**: Dropdown of all loaded Ollama models with sizes
- **AI Tools**:
  - 📁 Include repo list in context
  - 📄 Read any file from `D:/Dev/repos`
  - 🌐 Web search via DuckDuckGo
- **Quick Prompts**: Pre-built analysis prompts
- **Context Sidebar**: Repo stats, SOTA/runt counts

## AI Assistant Capabilities

### File Reading
Enter a path like `advanced-memory-mcp/src/server.py` to include file contents in the AI context.

### Directory Browsing
Enter a folder path like `database-operations-mcp/src` to list its contents.

### Web Search
Enter a search query to fetch results from DuckDuckGo and include them in context.

### Example Prompts
- "Analyze my MCP zoo and identify runts that need improvement"
- "Read `mcp-studio/studio_dashboard.py` and suggest refactoring"
- "What's new in FastMCP 2.x?" (with web search)
- "Compare the tool patterns in `advanced-memory-mcp` vs `database-operations-mcp`"

## API Endpoints

### Discovery & Analysis
- `GET /api/clients` - List discovered MCP clients
- `GET /api/repos` - Analyze all MCP repositories
- `GET /api/repos/{name}` - Get specific repo details
- `GET /api/progress` - Get scan progress
- `GET /api/logs` - Get recent log messages

### Live Connections
- `POST /api/repos/{name}/connect` - Connect to repo's MCP server
- `POST /api/servers/{client}/{id}/connect` - Connect via client config
- `GET /api/connections` - List active connections
- `GET /api/connections/{id}/tools` - List tools for connection
- `POST /api/connections/{id}/tools/{name}/execute` - Execute tool

### Tool Management
- `GET /api/v1/clients/{client_id}/tools` - Get all tools for a client with enablement status
- `POST /api/v1/clients/{client_id}/tools/{tool_name}/toggle` - Enable/disable individual tools

### AI Assistant
- `GET /api/ollama/models` - List Ollama models
- `GET /api/ai/read-file?path=` - Read file from repos
- `GET /api/ai/search-web?query=` - Web search
- `GET /api/ai/list-repos` - List repos with metadata
- `POST /api/ai/chat` - Chat with Ollama (supports file/web/repo context)

## Requirements

- Python 3.10+
- FastAPI, uvicorn, httpx
- MCP repos in `D:/Dev/repos`

## 🔧 **Development**

### **Frontend Development**
- **HTML**: Modular template in `src/mcp_studio/templates/dashboard.html`
- **CSS**: Custom styles in `src/mcp_studio/static/css/dashboard.css`
- **JavaScript**: ES6 modules in `src/mcp_studio/static/js/`
- **Hot Reload**: Changes automatically reflected via FastAPI static files

### **Backend Integration**
- **FastAPI Routes**: `src/mcp_studio/app/api/web.py`
- **Static Files**: Served from `src/mcp_studio/static/`
- **Templates**: Jinja2 templates in `src/mcp_studio/templates/`

### **Modular Benefits**
- **Single Responsibility**: Each JS module handles one feature
- **Easy Testing**: Isolated functionality testing
- **Performance**: Separate file caching
- **Maintainability**: Clear separation of concerns

## Architecture

### **🏗️ Frontend Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Studio Dashboard                      │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Overview │ Clients  │  Repos   │  Tools   │    Console      │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                    Modular JavaScript                       │
├─────┬──────┬─────┬─────┬─────┬──────┬──────┬─────────────────┤
│main │utils │tabs │repos│tools│console│clients│  dashboard.css │
│.js  │.js   │.js  │.js  │.js  │.js    │.js    │  + tailwind    │
└─────┴──────┴─────┴─────┴─────┴──────┴──────┴─────────────────┘
```

### **⚙️ Backend Architecture**
```
┌─────────────────────────────────────────────────────────────┐
│                   FastAPI Backend                           │
├─────────────────┬───────────────────┬───────────────────────┤
│  Client Zoo     │  Repo Analyzer    │  Tool Execution       │
│  (config scan)  │  (static check)   │  (runtime tools)      │
├─────────────────┼───────────────────┼───────────────────────┤
│ Claude/Cursor/  │  D:/Dev/repos/*   │  MCP Server Runtime   │
│ Windsurf/Cline  │  (45+ MCP repos)  │  (stdio connections)  │
└─────────────────┴───────────────────┴───────────────────────┘
```

### **📦 File Organization**
```
src/mcp_studio/
├── app/
│   └── api/
│       └── web.py              # FastAPI web routes
├── static/
│   ├── css/
│   │   └── dashboard.css       # Custom styling
│   └── js/
│       ├── main.js             # App initialization
│       ├── utils.js            # Utilities
│       ├── tabs.js             # Navigation
│       ├── repos.js            # Repository features
│       ├── tools.js            # Tool features
│       ├── console.js          # Console features
│       └── clients.js          # Client features
└── templates/
    └── dashboard.html          # Main HTML template
```

## 🎯 **Development Notes**

### **🏗️ Dashboard Refactoring (December 2025)**
**Challenge**: Monolithic 3,601-line `dashboard_old.html` file became unmaintainable.

**Solution**: Modular architecture with separate concerns:
- **HTML**: Clean template with proper includes (~400 lines)
- **CSS**: Extracted to `dashboard.css` (~110 lines)
- **JavaScript**: 7 focused modules (~1,600 lines total)

**Benefits Achieved**:
- ✅ **87% complexity reduction** (3,601 → 400 lines)
- ✅ **Single responsibility** per module
- ✅ **Better caching** with separate files
- ✅ **Easier debugging** and maintenance
- ✅ **Performance improvements** via modular loading

**Migration Process**:
1. Created directory structure for modules
2. Extracted CSS to separate file
3. Split JavaScript into logical modules
4. Updated FastAPI routes to serve new structure
5. Verified all functionality preserved

### **🔧 Technical Implementation**
- **Frontend**: Vanilla JavaScript with ES6 modules
- **Backend**: FastAPI with Jinja2 templates
- **Styling**: Tailwind CSS + custom CSS
- **Architecture**: Modular, maintainable, performant

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for full version history.

- **v1.4.0** - Enhanced working sets with purpose-built configurations (Media, Robotics, Dev, etc.)
- **v1.3.0** - Tool enablement/disablement with visual status indicators
- **v1.2.0** - Dashboard modular refactoring (87% complexity reduction)
- **v1.1.0** - AI Assistant with file/web/repo context
- **v1.0.0** - Unified dashboard with 5 tabs
- **v0.2.x** - Runt analyzer improvements
- **v0.1.0** - Initial release

