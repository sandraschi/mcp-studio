# MCP Studio Dashboard

Mission Control for your MCP Zoo - a unified dashboard for managing, analyzing, and interacting with Model Context Protocol servers.

## Quick Start

```powershell
cd D:\Dev\repos\mcp-studio
python studio_dashboard.py
```

Dashboard: http://localhost:8888

## Features

### 📊 Overview Tab
- **Stats Cards**: Total clients, repos, tools, SOTA count
- **MCP Clients Discovery**: Auto-discovers servers from Claude Desktop, Cursor, Windsurf, Cline configs
- **Repository Health**: Pie chart breakdown of SOTA/Improvable/Runts

### 🔌 MCP Clients Tab
- Lists all discovered MCP server configurations
- Shows server name, command, and config source
- Connect buttons to establish live stdio connections

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

### AI Assistant
- `GET /api/ollama/models` - List Ollama models
- `GET /api/ai/read-file?path=` - Read file from repos
- `GET /api/ai/search-web?query=` - Web search
- `GET /api/ai/list-repos` - List repos with metadata
- `POST /api/ai/chat` - Chat with Ollama (supports file/web/repo context)

## Requirements

- Python 3.10+
- FastAPI, uvicorn, httpx
- Ollama running locally (for AI Assistant)
- MCP repos in `D:/Dev/repos`

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    MCP Studio Dashboard                      │
├──────────┬──────────┬──────────┬──────────┬─────────────────┤
│ Overview │ Clients  │  Repos   │  Tools   │  AI Assistant   │
├──────────┴──────────┴──────────┴──────────┴─────────────────┤
│                      FastAPI Backend                         │
├─────────────────┬───────────────────┬───────────────────────┤
│  Client Zoo     │  Repo Analyzer    │  Ollama Integration   │
│  (config scan)  │  (static check)   │  (chat + web + file)  │
├─────────────────┼───────────────────┼───────────────────────┤
│ Claude/Cursor/  │  D:/Dev/repos/*   │  localhost:11434      │
│ Windsurf/Cline  │  (45+ MCP repos)  │  (local LLMs)         │
└─────────────────┴───────────────────┴───────────────────────┘
```

## Version History

See [CHANGELOG.md](../CHANGELOG.md) for full version history.

- **v1.1.0** - AI Assistant with file/web/repo context
- **v1.0.0** - Unified dashboard with 6 tabs
- **v0.2.x** - Runt analyzer improvements
- **v0.1.0** - Initial release

