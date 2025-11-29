# Changelog

## [1.1.0] - 2025-11-29 - AI Assistant with Tools

### Added
- **🤖 AI Assistant Tab** - Chat with Ollama for intelligent MCP analysis
- **Ollama model dropdown** - Auto-detects loaded models with sizes
- **File reading** - AI can read any file in `D:/Dev/repos`
- **Directory browsing** - AI can list folder contents
- **Web search** - DuckDuckGo integration (no API key needed)
- **Repo context** - Include full repo list in AI context

### AI Assistant Features
- 🛠️ AI Tools panel: file path input, web search input, repo list toggle
- ⚡ Quick prompts: Analyze runts, Suggest portmanteaus, Review naming, etc.
- 📋 Context sidebar: Shows repo count, tool count, SOTA/runt stats
- ⚙️ Model selector: Dropdown with all Ollama models + refresh button
- Real-time thinking indicators with tool usage display

### API Endpoints
- `GET /api/ai/read-file?path=` - Read files from repos directory
- `GET /api/ai/search-web?query=` - DuckDuckGo web search
- `GET /api/ai/list-repos` - List all repos with type detection
- `GET /api/ollama/models` - List loaded Ollama models
- `POST /api/ai/chat` - Chat with context (file, web, repos)

## [1.0.0] - 2025-11-29 - MCP Studio Dashboard

### Added
- **Unified MCP Studio Dashboard** (`studio_dashboard.py`) - Mission Control for the MCP Zoo
- Auto-discovers servers from Claude Desktop, Cursor, Windsurf, Cline configs
- Static analysis of all MCP repos with runt/SOTA classification
- Beautiful dark theme with glass morphism UI
- Tabbed interface: Overview, MCP Clients, Repositories, Tools, Console, AI Assistant
- Live activity log with real-time updates
- Stats dashboard: Clients, Repos, Tools, SOTA count
- Repository health breakdown: SOTA/Improvable/Runts
- Zoo classification with animal emojis (🐘 Jumbo → 🐿️ Chipmunk)

### Dashboard Features
- 📊 Overview: Stats + client discovery + repo health
- 🔌 MCP Clients: All discovered server configs with connect buttons
- 📦 Repositories: Filterable repo grid with detail modals
- 🔧 Tools: Tool explorer with live connection support
- 💻 Console: Tool execution console with parameter input
- 🤖 AI Assistant: Ollama-powered chat with file/web access

## [0.2.1] - 2025-11-29 - Detail Modal Redesign

### Improved
- **Redesigned detail modal** with comprehensive repo analysis:
  - 6-stat header row: FastMCP version, Portmanteaus, Operations, Individual tools, CI/CD, Zoo Class
  - Structure badge row: src/, tests/, scripts/, tools/, portmanteau presence indicators
  - Side-by-side Issues (🚨) and Recommendations (💡) panels
  - Collapsible README preview with full content
  - Organized tool list: Portmanteau section (📦) with operations, Individual section (🔹)
  - Each tool shows name, file path, and expandable docstring
- Better visual hierarchy with color-coded status badges
- Improved contrast and readability

## [0.2.0] - 2025-11-29 - MCP Zoo Runt Analyzer

### Added
- **MCP Zoo Runt Analyzer** (`runt_api.py`) - Standalone dashboard for analyzing MCP server quality
- Real-time progress reporting with SSE streaming
- Log collection and display in dashboard
- Detailed repo analysis modal with:
  - README preview
  - Tool list with docstrings (collapsible)
  - Portmanteau vs Individual tool classification
  - Operations count within portmanteaus
- Zoo classification system: 🐘 Jumbo, 🦁 Large, 🦊 Medium, 🐰 Small, 🐿️ Chipmunk
- Status classification: ✅ SOTA, ⚠️ Improvable, 🐛 Runt, 💀 Critical

### Analysis Criteria
- FastMCP version check (< 2.10 = runt, 2.10-2.11 = improvable)
- Project structure validation: `src/`, `tests/`, `scripts/`, `tools/`
- CI/CD workflow presence
- Tool registration pattern detection (decorator vs non-conforming)
- Portmanteau pattern adoption for large tool counts

### Technical
- Fast directory scanning with skip-dirs optimization
- Depth-limited file globbing for performance
- Async API with progress updates
- Tailwind CSS dashboard UI

## [0.1.0] - 2025-08-08 - Initial Release

### Added
- Initial project setup with FastAPI and FastMCP 2.11 integration
- Basic server management UI
- Stdio transport implementation
- CI/CD pipeline with GitHub Actions
- Automated release process
- Development tooling and pre-commit hooks
