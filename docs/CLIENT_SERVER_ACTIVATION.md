# Client Server Activation Feature - 2025-12-02

## Overview

Feature for activating sets of servers for each detected MCP client (Claude Desktop, Cursor, Windsurf, Antigravity, Zed). This extends the working sets functionality to support all MCP clients, not just Claude Desktop.

## Current State

### What Exists
- ✅ **MCP Client Zoo** (`mcp_client_zoo.py`) - Scans all MCP clients and their configs
- ✅ **Working Sets Manager** (`working_sets/manager.py`) - Manages server sets, but **hardcoded to Claude Desktop only**
- ✅ **Client Metadata** (`mcp_client_metadata.py`) - Database of all known MCP clients
- ✅ **Client API** (`app/api/clients.py`) - REST API for client information
- ✅ **Working Sets API** (`src/api/working_sets.py`) - REST API for working sets (Claude Desktop only)

### What's Missing
- ❌ **Multi-Client Support** - Working sets manager only supports Claude Desktop
- ❌ **Client Detail Pages** - No UI page for each client showing server activation
- ❌ **Client-Specific Config Management** - Can't manage configs for Cursor, Windsurf, etc.
- ❌ **Antigravity Support** - Not in client zoo yet

## Architecture

### Current Working Sets (Claude Desktop Only)

```
WorkingSetManager
├── config_path: "C:/Users/sandr/AppData/Roaming/Claude/claude_desktop_config.json"
├── backup_dir: "C:/Users/sandr/AppData/Roaming/Claude/backup"
└── templates_dir: "templates"
```

**Limitation**: Hardcoded to Claude Desktop config path.

### Proposed Multi-Client Architecture

```
ClientWorkingSetManager
├── client_configs: {
│   "claude-desktop": {
│       "config_path": "...",
│       "backup_dir": "...",
│       "manager": WorkingSetManager(...)
│   },
│   "cursor-ide": {
│       "config_path": "...",
│       "backup_dir": "...",
│       "manager": WorkingSetManager(...)
│   },
│   ...
│ }
└── get_manager(client_id) -> WorkingSetManager
```

## Implementation Plan

### Phase 1: Extend Working Sets Manager

**File**: `src/working_sets/manager.py`

**Changes**:
1. Make `WorkingSetManager` client-agnostic
2. Accept client_id and config_path as parameters
3. Use `MCPClientZoo` to get client config paths
4. Support all clients: Claude Desktop, Cursor, Windsurf, Antigravity, Zed

### Phase 2: Add Antigravity to Client Zoo

**File**: `src/mcp_studio/app/services/mcp_client_zoo.py`

**Changes**:
1. Add `parse_antigravity_ide()` method
2. Add to `scan_all_clients()` parser list
3. Add to client metadata database

### Phase 3: Create Client Detail API

**File**: `src/mcp_studio/app/api/clients.py` (extend)

**New Endpoints**:
- `GET /api/v1/clients/{client_id}/servers` - Get servers for client
- `GET /api/v1/clients/{client_id}/working-sets` - Get working sets for client
- `POST /api/v1/clients/{client_id}/working-sets/{set_id}/activate` - Activate working set
- `GET /api/v1/clients/{client_id}/config` - Get current config
- `POST /api/v1/clients/{client_id}/config` - Update config

### Phase 4: Create Client Detail UI

**File**: `src/mcp_studio/templates/clients/detail.html` (NEW)

**Features**:
- Client information (name, description, homepage, etc.)
- Detected servers list
- Working sets selector
- Activate/switch working set button
- Preview changes before applying
- Backup management
- Current active servers display

### Phase 5: Update Client List UI

**File**: `src/mcp_studio/templates/clients/list.html` (NEW)

**Features**:
- List all detected MCP clients
- Show which clients have configs
- Link to client detail page
- Quick stats (server count, active working set)

## Client Config Paths

### Claude Desktop
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`
- Linux/Mac: `~/.config/Claude/claude_desktop_config.json`

### Cursor IDE
- Windows: `%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
- Windows Alt: `%APPDATA%\Cursor\mcp_settings.json`
- Linux: `~/.cursor/mcp_settings.json`

### Windsurf IDE
- Windows: `%APPDATA%\Windsurf\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json`
- Windows Alt: `%APPDATA%\Windsurf\mcp_settings.json`
- Linux: `~/.config/Windsurf/mcp_settings.json`

### Antigravity IDE
- Windows: `%APPDATA%\Antigravity\mcp_config.json`
- Windows Alt: `%APPDATA%\GitKraken\Antigravity\mcp_config.json`
- Linux: `~/.config/antigravity/mcp_config.json`
- Mac: `~/Library/Application Support/Antigravity/mcp_config.json`

### Zed Editor
- Linux: `~/.config/zed/mcp.json`
- Windows: `%APPDATA%\Zed\mcp.json`
- Mac: `~/Library/Application Support/Zed/mcp.json`

## API Design

### Client Working Sets Endpoints

```python
# Get working sets for a client
GET /api/v1/clients/{client_id}/working-sets
Response: {
    "client_id": "claude-desktop",
    "working_sets": [...],
    "current_working_set": "development"
}

# Activate working set for a client
POST /api/v1/clients/{client_id}/working-sets/{set_id}/activate
Body: {
    "create_backup": true
}
Response: {
    "success": true,
    "client_id": "claude-desktop",
    "working_set_id": "development",
    "backup_created": "backup_20251202_143022.json"
}

# Preview working set changes
GET /api/v1/clients/{client_id}/working-sets/{set_id}/preview
Response: {
    "current_servers": ["server1", "server2"],
    "new_servers": ["server1", "server3"],
    "added_servers": ["server3"],
    "removed_servers": ["server2"]
}
```

## UI Design

### Client Detail Page

```
┌─────────────────────────────────────────┐
│  ← Back to Clients                      │
│                                         │
│  🖥️ Claude Desktop                     │
│  Official Anthropic Claude desktop app  │
│  Status: ✅ Active                      │
│                                         │
│  [Overview] [Servers] [Working Sets]   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Current Active Servers (3)      │   │
│  │ • advanced-memory-mcp           │   │
│  │ • mcp-studio                    │   │
│  │ • docker-mcp                    │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ Working Sets                    │   │
│  │                                 │   │
│  │ [🛠️ Development] [Active]      │   │
│  │  3 servers                      │   │
│  │  [Activate] [Preview]           │   │
│  │                                 │   │
│  │ [🎨 Media & Creative]          │   │
│  │  5 servers                      │   │
│  │  [Activate] [Preview]           │   │
│  │                                 │   │
│  │ [📞 Communication]              │   │
│  │  4 servers                      │   │
│  │  [Activate] [Preview]           │   │
│  └─────────────────────────────────┘   │
│                                         │
│  [Create Backup] [Restore Backup]      │
└─────────────────────────────────────────┘
```

## Next Steps

1. **Extend WorkingSetManager** to support multiple clients
2. **Add Antigravity** to client zoo
3. **Create client detail API endpoints**
4. **Create client detail UI template**
5. **Update client list to show working sets**
6. **Test with all clients**

## Status

**Current**: Working sets only work for Claude Desktop  
**Target**: Working sets work for all MCP clients  
**Priority**: High - Core feature for multi-client support
