# MCP Zoo Runt Analyzer

A standalone dashboard for analyzing MCP server quality across your repository collection.

## Quick Start

```powershell
cd D:\Dev\repos\mcp-studio
python runt_api.py
```

Dashboard: http://localhost:8888

## Features

### Dashboard
- Real-time scan progress with SSE streaming
- Collapsible log panel
- Filterable repo cards (Runts, Improvable, SOTA, Jumbos)
- Click-to-expand detail modal

### Detail Modal (Click any repo card)
- **Header**: Zoo emoji + repo name + status badge + path
- **Stats Row**: 6 boxes showing FastMCP version, Portmanteaus, Operations, Individual tools, CI/CD count, Zoo Class
- **Structure Badges**: ✓/✗ indicators for src/, tests/, scripts/, tools/, portmanteau
- **Issues Panel** (🚨): Red X markers for each detected problem
- **Recommendations Panel** (💡): Arrow markers with upgrade suggestions
- **README Preview**: Collapsible full README content
- **Tools Section**: 
  - 📦 Portmanteau tools with operation counts
  - 🔹 Individual tools
  - Each tool expandable to show docstring and file path

## Zoo Classification

| Animal | Emoji | Tool Count |
|--------|-------|------------|
| Jumbo | 🐘 | 20+ tools or specialized domain |
| Large | 🦁 | 10-19 tools |
| Medium | 🦊 | 5-9 tools |
| Small | 🐰 | 2-4 tools |
| Chipmunk | 🐿️ | 0-1 tools |

## Status Classification

| Status | Emoji | Meaning |
|--------|-------|---------|
| SOTA | ✅ | State of the art, no issues |
| Improvable | ⚠️ | Minor issues, still functional |
| Minor Runt | 🐣 | 1-2 issues |
| Runt | 🐛 | 3-4 issues |
| Critical | 💀 | 5+ issues |

## Analysis Criteria

### Runt Triggers (hard failures)
- FastMCP < 2.10.0 (ancient version)
- No `src/` AND no package directory
- No CI/CD workflows (for repos with 10+ tools)
- ALL tools use non-FastMCP registration (100% non-conforming)

### Improvable Triggers (warnings)
- FastMCP 2.10-2.11 (upgrade recommended)
- No `tests/` directory (for repos with 10+ tools)
- No `tools/` subdirectory (for repos with 20+ tools)
- Some non-FastMCP registration patterns
- No portmanteau pattern (for repos with 20+ tools)

### Recommendations Only (no status impact)
- Consider adding `scripts/`
- Consider adding `tests/` (for small repos)
- Fix N non-decorator registrations

## Tool Classification

### Portmanteau Tools
Tools in `*_tool.py`, `*_tools.py`, or `portmanteau/` directories.
These are consolidated tools that expose multiple operations via action parameters.

Example: `blender_mesh(action: Literal["create", "delete", "modify"], ...)`

### Portmanteau Operations
The individual operations within a portmanteau, counted from `Literal[...]` types.
These represent the actual capabilities exposed to Claude/clients.

### Individual Tools
Simple standalone tools like `help`, `status`, `health_check`.
These are fine to keep separate - they don't need portmanteau consolidation.

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard HTML |
| `GET /api/runts/` | Full scan with all repo data |
| `GET /api/repo/{name}` | Detailed single repo analysis |
| `GET /api/progress` | Current scan progress |
| `GET /api/progress/stream` | SSE stream for real-time progress |
| `GET /api/logs` | Collected scan logs |

## Performance

- Scans ~80 repos in < 1 second
- Skips: `node_modules`, `__pycache__`, `.git`, `venv`, `dist`, `build`
- Depth-limited to 4 levels for tool detection
- Async scanning with progress updates

## Example Output

```
🦁 MCP Zoo Runt Analyzer v2.2.0 starting...
🐘 Dashboard: http://localhost:8888
🦒 API: http://localhost:8888/api/runts/

17:21:40 | [1/81] Scanning advanced-memory-mcp...
17:21:40 |   🐘 ⚠️ v2.12.0 68(0)+0 [!tools/]
17:21:40 | [2/81] Scanning blender-mcp...
17:21:40 |   🐘 ✅ v2.12.0 50(82)+0 [✓]
...
17:21:41 | ✅ Scan complete in 0.6s - Found 51 MCP repos
17:21:41 |    🐛 Runts: 12 | ✅ SOTA: 21 | ⚠️ Improvable: 18
```

Format: `zoo status version portmanteau(ops)+individual [flags]`

