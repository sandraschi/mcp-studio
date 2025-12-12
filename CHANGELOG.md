# Changelog

## [2.2.0] - 2025-12-02 - Complete MCP Server Lifecycle Management (CRUD)

### Added
- **🏗️ CREATE: Server Scaffolding** - Generate new SOTA-compliant MCP servers from scratch
- **📝 UPDATE: Server Enhancement** - Add missing SOTA components to existing servers
- **🗑️ DELETE: Server Removal** - Safely delete test/throwaway servers with safety checks
- **📚 Complete Documentation Templates** - MCP standards, MCPB standards, client rulebooks
- **🔧 Full Project Scaffold** - Git, CI/CD, tests, scripts, docs folder structure

### Server Scaffolding Features
- **SOTA-Compliant by Default**: All new servers meet FastMCP 2.13.1 standards
- **Complete Structure**: src/, tests/, docs/, scripts/, .github/workflows/
- **Help & Status Tools**: Pre-generated SOTA-required tools
- **CI/CD Ready**: GitHub Actions workflow with ruff + pytest
- **DXT Packaging**: manifest.json included
- **Documentation**: Complete docs folder with standards and client rulebooks
- **Git Integration**: Optional git initialization with initial commit

### Server Update Features
- **Auto-Detect Missing Components**: Analyzes server and identifies gaps
- **Targeted Updates**: Add specific components (help_tool, status_tool, ci_cd, tests, etc.)
- **Dry-Run Mode**: Preview changes before applying
- **Non-Destructive**: Only adds missing components, doesn't modify existing code

### Server Deletion Features
- **Safety Checks**: Git repo detection, uncommitted changes, remote repository checks
- **Backup Option**: Create backup before deletion
- **Dry-Run Mode**: Preview deletion without applying
- **Force Mode**: Skip safety checks when needed

### Documentation Templates
- **MCP Server Standards**: FastMCP 2.13+ requirements and best practices
- **MCPB Standards**: Packaging and distribution guidelines
- **Client Rulebooks**: Integration guides for Claude Desktop, Cursor IDE, Windsurf, Cline

### Technical Improvements
- **New Modules**: `server_scaffold.py`, `server_updater.py`, `server_deleter.py`
- **Template System**: Reusable templates for server generation
- **Integration**: CRUD tools integrated into MCP server
- **Help Updates**: Help tool now lists all 12 tools including CRUD operations

## [2.1.0] - 2025-12-02 - Enhanced Runt Analyzer & Persistence

### Added
- **📊 Rule-Based SOTA Analyzer** - Declarative rule system replacing hardcoded criteria
- **💾 Scan Result Caching** - File-based persistence to avoid re-scanning on every request
- **📝 Markdown Report Format** - Human-readable markdown output for scan results
- **🔍 Comprehensive Repo Details** - Structured JSON with full repository information for AI consumption
- **⚙️ Cache Management** - Configurable TTL, cache clearing, and statistics

### Runt Analyzer Improvements
- **Rule-Based Architecture**: Declarative rule definitions with categories (VERSION, TOOLS, STRUCTURE, QUALITY, TESTING, CI_CD, DOCUMENTATION)
- **Severity Levels**: CRITICAL, WARNING, INFO for rule violations
- **Dynamic Scoring**: Conditional score deductions based on context
- **Extensible Rules**: Easy to add new rules without touching evaluation logic
- **Repository Detail Collector**: Comprehensive metadata, structure, dependencies, tools, configuration, code quality, documentation, testing, and CI/CD information

### Persistence & Caching
- **File-Based Cache**: JSON cache in `~/.mcp-studio/scan-cache/`
- **TTL-Based Expiration**: Configurable cache time-to-live (default: 1 hour)
- **Smart Invalidation**: File modification time checking for automatic cache refresh
- **Cache Statistics**: Track cache size, age, and performance

### Markdown Formatting
- **Human-Readable Reports**: Formatted markdown with emojis and structure
- **Scan Summaries**: Complete scan results in markdown format
- **Repo Status Reports**: Detailed single-repo analysis in markdown
- **Format Parameter**: `format="json"` or `format="markdown"` for both tools

### Technical Improvements
- **New Modules**: `runt_analyzer_rules.py`, `repo_detail_collector.py`, `scan_cache.py`, `scan_formatter.py`
- **Backward Compatible**: All existing functionality preserved
- **Performance**: Significant speedup for repeated scans via caching
- **AI-Friendly**: Structured JSON output enables AI to answer questions without re-analysis

### API Enhancements
- `analyze_runts()`: Added `format`, `use_cache`, `cache_ttl` parameters
- `get_repo_status()`: Added `format`, `use_cache`, `cache_ttl` parameters
- Cache management functions: `clear_cache()`, `get_cache_stats()`

## [2.0.0] - 2025-12-04 - Preprompt Management System

### Added
- **🎭 Preprompt Management** - Dynamic AI personality system with SQLite storage
- **🤖 AI Refine Generator** - Type concept → AI generates elaborate preprompt in 60 seconds
- **📁 Import from .md** - Upload markdown files as preprompts
- **💾 SQLite Database** - Persistent storage with full CRUD operations
- **🎨 Dynamic Dropdown** - Load unlimited personalities without code changes
- **🏴‍☠️ Creative Personalities** - 7 preprompts including AI-generated "Coin Collector" and "Long John Silver, Pirate"

### Preprompt Features
- AI-assisted generation using local Ollama LLM (14g model tested)
- Auto-emoji detection from concept keywords
- Personality-aware welcome messages on connection
- Markdown import with auto-title extraction
- Soft delete (preserves history)
- Tag system for categorization
- Source tracking (builtin/imported/ai_generated/user)

### API Endpoints Added
- `GET /api/ai/preprompts` - List all preprompts
- `POST /api/preprompts/add` - Add new preprompt
- `POST /api/preprompts/import` - Import from markdown
- `POST /api/preprompts/ai-refine` - AI-generate preprompt (🌟 star feature!)
- `GET /api/preprompts/{id}` - Get specific preprompt
- `PUT /api/preprompts/{id}` - Update preprompt
- `DELETE /api/preprompts/{id}` - Delete preprompt
- `POST /api/preprompts/seed` - Seed builtin preprompts

### Technical Improvements
- Fixed hardcoded port (now reads from .env)
- CORS configured for Tailscale access (`allow_origins=["*"]`)
- Database module with comprehensive error handling
- Simplified imports (preprompt_db.py in root)
- Personality-specific AI responses and greetings

### Demo Value
- **60-second personality generation** - Perfect for live demos
- **Infinite scalability** - No code changes needed for new personalities
- **User-generated content** - Community sharing potential
- **Professional UI** - Clean, integrated design

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
