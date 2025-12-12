# MCP Studio Architecture - 2025-12-02

## Overview

MCP Studio is a comprehensive MCP server management platform with dual architecture:
1. **Web Dashboard**: FastAPI-based web interface
2. **MCP Server**: FastMCP 2.13.1 server providing tools to other MCP clients

## System Architecture

```
┌─────────────────┐    stdio     ┌──────────────────┐    HTTP/WS    ┌─────────────────┐
│  Claude Desktop │ ←----------→ │   MCP Studio     │ ←----------→ │   Web Browser   │
│  (MCP Client)   │   JSON-RPC   │   (MCP Server)   │   REST API    │   (Frontend UI) │
└─────────────────┘              └──────────────────┘               └─────────────────┘
```

## Core Components

### 1. MCP Server (`mcp_server.py`)

**FastMCP 2.13.1 Server** providing 15 tools:

**Server Discovery & Management:**
**Client Management:**
- `discover_clients` - Discover all MCP clients and their configured servers
- `get_client_config` - Get configuration for a specific MCP client
- `set_client_config` - Set or update configuration for a specific MCP client

**Server Discovery:**
- `discover_mcp_servers` - Find MCP servers
- `get_server_info` - Get server details
- `list_server_tools` - List available tools
- `execute_remote_tool` - Execute tools on remote servers
- `test_server_connection` - Test connectivity

**Server Lifecycle (CRUD):**
- `create_mcp_server` - Scaffold new SOTA servers
- `update_mcp_server` - Add missing SOTA components
- `delete_mcp_server` - Safely remove servers

**SOTA Analysis:**
- `scan_repos_for_sota_compliance` - Bulk repository scanning
- `analyze_repo_sota_status` - Single repository analysis

**System:**
- `help` - Multi-level help system
- `status` - System status and diagnostics

### 2. Repository Analysis System

#### Rule-Based Analyzer (`runt_analyzer_rules.py`)
- **Declarative Rule System**: Rules defined as dataclasses
- **Categories**: VERSION, TOOLS, STRUCTURE, QUALITY, TESTING, CI_CD, DOCUMENTATION
- **Severity Levels**: CRITICAL, WARNING, INFO
- **Dynamic Scoring**: Conditional score deductions
- **Extensible**: Easy to add new rules

#### Repository Detail Collector (`repo_detail_collector.py`)
- **Comprehensive Data Collection**: 9 categories of information
- **AI-Friendly Format**: Structured JSON for AI consumption
- **Complete Coverage**: Metadata, structure, dependencies, tools, config, quality, docs, testing, CI/CD

#### Scan Cache (`scan_cache.py`)
- **File-Based Persistence**: JSON cache in `~/.mcp-studio/scan-cache/`
- **TTL-Based Expiration**: Configurable cache time-to-live
- **Smart Invalidation**: File modification time checking
- **Cache Management**: Clear, statistics, manual control

#### Markdown Formatter (`scan_formatter.py`)
- **Human-Readable Output**: Formatted markdown reports
- **Structured Sections**: Summary, runts, SOTA repos
- **Emoji Indicators**: Visual status representation

### 3. Server Lifecycle Management

#### Server Scaffold (`server_scaffold.py`)
- **SOTA-Compliant Generation**: All new servers meet standards
- **Complete Structure**: Full project scaffold
- **Template System**: Reusable templates
- **Git Integration**: Optional git initialization

#### Server Updater (`server_updater.py`)
- **Auto-Detection**: Identifies missing components
- **Targeted Updates**: Add specific components
- **Dry-Run Mode**: Preview changes
- **Non-Destructive**: Only adds, doesn't modify

#### Server Deleter (`server_deleter.py`)
- **Safety Checks**: Git repo, uncommitted changes, remote detection
- **Backup Option**: Create backup before deletion
- **Dry-Run Mode**: Preview deletion
- **Force Mode**: Skip safety checks when needed

## Data Flow

### Repository Scanning Flow
```
User Request
    ↓
Check Cache (if enabled)
    ↓
[Cache Hit] → Return Cached Result
    ↓
[Cache Miss] → Scan Repository
    ↓
Collect Details (metadata, structure, dependencies, tools, etc.)
    ↓
Evaluate Rules (rule-based system)
    ↓
Calculate SOTA Score
    ↓
Cache Result (if enabled)
    ↓
Format Output (JSON or Markdown)
    ↓
Return Result
```

### Server Creation Flow
```
User Request (create_mcp_server)
    ↓
Validate Parameters
    ↓
Create Directory Structure
    ↓
Generate Files:
  - mcp_server.py (with help/status tools)
  - pyproject.toml
  - README.md
  - .gitignore
  - CI/CD workflow
  - manifest.json
  - Test structure
  - Documentation
  - Scripts
    ↓
Initialize Git (if requested)
    ↓
Return Creation Status
```

### Server Update Flow
```
User Request (update_mcp_server)
    ↓
Analyze Repository (get_repo_status)
    ↓
Identify Missing Components
    ↓
[Auto-Detect Mode] → Find all missing components
    ↓
[Specific Components] → Use provided list
    ↓
[Dry-Run] → Preview changes
    ↓
[Apply] → Add missing components
    ↓
Return Update Status
```

## Persistence Layer

### Cache System
- **Location**: `~/.mcp-studio/scan-cache/`
- **Format**: JSON files
- **Keys**: MD5 hash of scan path or repo path
- **TTL**: Configurable (default: 1 hour)
- **Invalidation**: Time-based, file modification, manual

### Database (Future)
- SQLite database for cache (like preprompt_db)
- Better query capabilities
- Indexed lookups
- Cache analytics

## Template System

### SOTA Template
- FastMCP 2.13.1
- Help and status tools
- CI/CD workflow
- Test structure
- Documentation
- DXT packaging

### File Templates
- `mcp_server.py` - Main server file
- `pyproject.toml` - Project configuration
- `README.md` - Project documentation
- `.github/workflows/ci.yml` - CI/CD workflow
- `manifest.json` - DXT packaging
- Documentation files (standards, rulebooks)

## Integration Points

### MCP Protocol
- Stdio transport
- JSON-RPC messages
- Tool execution
- Server discovery

### Web Interface
- FastAPI REST API
- WebSocket for real-time updates
- Static file serving
- Template rendering

### File System
- Repository scanning
- File reading/writing
- Git operations
- Cache management

## Security & Safety

### Server Deletion
- Git repository detection
- Uncommitted changes check
- Remote repository warning
- Backup before deletion
- Force mode for override

### Server Updates
- Dry-run mode by default
- Non-destructive operations
- Backup recommendations
- Validation before applying

### Cache
- File-based (no network)
- User-specific directory
- TTL-based expiration
- Manual clearing

## Performance Considerations

### Caching Strategy
- Cache scan results (1 hour TTL)
- Cache repo status (1 hour TTL)
- File modification time checking
- Configurable TTL

### Scanning Optimization
- Skip common directories (node_modules, .git, etc.)
- Depth-limited scanning
- Parallel processing (future)
- Incremental updates (future)

## Extension Points

### Rule System
- Add new rules to `SOTA_RULES` list
- Define rule categories
- Set severity levels
- Configure scoring

### Templates
- Add new template types
- Customize file generation
- Add template variables
- Template versioning

### Update Operations
- Add new component types
- Custom update logic
- Integration with other tools
- Batch operations

## Future Enhancements

1. **Database Persistence**
   - SQLite for cache
   - Better query capabilities
   - Analytics and reporting

2. **Incremental Updates**
   - Only scan changed repos
   - Merge cache with fresh data
   - Partial invalidation

3. **Template Marketplace**
   - Community templates
   - Specialized templates
   - Template versioning

4. **Migration Tools**
   - Bulk upgrades
   - Version migrations
   - Pattern refactoring
