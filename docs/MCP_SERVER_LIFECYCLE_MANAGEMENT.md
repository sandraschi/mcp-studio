# MCP Server Lifecycle Management - 2025-12-02

## Vision

Transform MCP Studio into a **complete CRUD machine** for MCP servers, providing full lifecycle management from creation to deletion.

## Core Concept

MCP Studio becomes the **single source of truth** for MCP server management:
- **Create**: Scaffold new SOTA-compliant MCP servers
- **Read**: Analyze and inspect existing servers (✅ already implemented)
- **Update**: Add missing components to bring servers to SOTA
- **Delete**: Remove test/throwaway servers safely

## Architecture

### CRUD Operations

#### 1. **CREATE** - Server Scaffolding

**Goal**: Generate SOTA-compliant MCP server from scratch

**Features**:
- Interactive server creation wizard
- Template-based scaffolding
- SOTA compliance by default
- All required components included

**Scaffold Includes**:
```
new-mcp-server/
├── .github/
│   └── workflows/
│       └── ci.yml              # Ruff + pytest CI
├── docs/
│   ├── README.md               # Server documentation
│   ├── MCP_SERVER_STANDARDS.md # MCP standards reference
│   ├── MCPB_STANDARDS.md       # MCPB packaging guide
│   └── CLIENT_RULEBOOKS/       # Client-specific guides
│       ├── CLAUDE_DESKTOP.md
│       ├── CURSOR_IDE.md
│       ├── WINDSURF.md
│       └── CLINE.md
├── scripts/
│   ├── setup.py                # Development setup
│   └── test.sh                 # Test runner
├── src/
│   └── {package_name}/
│       ├── __init__.py
│       ├── mcp_server.py       # Main FastMCP server
│       └── tools/
│           ├── __init__.py
│           ├── help.py         # Help tool (SOTA required)
│           └── status.py       # Status tool (SOTA required)
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   └── test_tools.py
│   └── integration/
│       └── test_server.py
├── .gitignore
├── pyproject.toml              # With FastMCP 2.13.1, ruff, pytest
├── README.md
├── LICENSE
└── manifest.json               # DXT packaging
```

**Template Variables**:
- `{server_name}`: Kebab-case server name
- `{package_name}`: Snake_case package name
- `{description}`: Server description
- `{author}`: Author name
- `{license}`: License type (MIT, Apache-2.0, etc.)

#### 2. **READ** - Server Analysis (✅ Already Implemented)

**Current Capabilities**:
- Repository scanning
- SOTA compliance checking
- Detailed repository information
- Rule-based evaluation

**Enhancements Needed**:
- Better integration with CRUD operations
- Actionable recommendations linked to UPDATE operations

#### 3. **UPDATE** - Server Enhancement

**Goal**: Add missing components to bring servers to SOTA

**Update Operations**:
- **Add Help Tool**: Generate help tool if missing
- **Add Status Tool**: Generate status tool if missing
- **Add CI/CD**: Create GitHub Actions workflow
- **Add Tests**: Scaffold test directory structure
- **Add Ruff Config**: Add ruff configuration to pyproject.toml
- **Add DXT Packaging**: Create manifest.json
- **Add Documentation**: Create docs folder with standards
- **Upgrade FastMCP**: Update FastMCP version in dependencies
- **Add Portmanteau**: Refactor tools to portmanteau pattern (if >15 tools)

**Update Strategy**:
1. Analyze server using existing analyzer
2. Identify missing components
3. Generate missing files/components
4. Update existing files (pyproject.toml, etc.)
5. Verify changes don't break existing code

#### 4. **DELETE** - Server Removal

**Goal**: Safely remove test/throwaway servers

**Safety Features**:
- Confirmation prompts
- Backup before deletion
- Git repository detection (warn if not a throwaway)
- Dependency checking (warn if other servers depend on it)
- Dry-run mode

**Delete Operations**:
- Remove directory
- Clean up references in configs
- Remove from cache
- Update discovery lists

## Implementation Plan

### Phase 1: CREATE - Server Scaffolding

**New Tool**: `create_mcp_server`

**Parameters**:
- `server_name: str` - Kebab-case server name (e.g., "my-awesome-server")
- `description: str` - Server description
- `author: str` - Author name
- `license: str` - License type (default: "MIT")
- `target_path: str` - Where to create server (default: "D:/Dev/repos")
- `include_examples: bool` - Include example tools (default: True)
- `template: str` - Template type (default: "sota")

**Features**:
- Interactive wizard mode
- Template selection
- Git initialization
- Initial commit
- SOTA compliance verification

### Phase 2: UPDATE - Server Enhancement

**New Tool**: `update_mcp_server`

**Parameters**:
- `repo_path: str` - Path to repository
- `components: List[str]` - Components to add (or "all" for auto-detect)
- `dry_run: bool` - Preview changes without applying (default: True)

**Components**:
- `help_tool` - Add help tool
- `status_tool` - Add status tool
- `ci_cd` - Add CI/CD workflow
- `tests` - Add test structure
- `ruff` - Add ruff configuration
- `dxt` - Add DXT packaging
- `docs` - Add documentation folder
- `upgrade_fastmcp` - Upgrade FastMCP version
- `portmanteau` - Refactor to portmanteau (if needed)

**Auto-Detect Mode**:
- Analyze server
- Identify missing SOTA components
- Generate update plan
- Apply updates

### Phase 3: DELETE - Server Removal

**New Tool**: `delete_mcp_server`

**Parameters**:
- `repo_path: str` - Path to repository
- `force: bool` - Skip confirmation (default: False)
- `backup: bool` - Create backup before deletion (default: True)
- `dry_run: bool` - Preview deletion without applying (default: True)

**Safety Checks**:
- Git repository detection
- Dependency analysis
- Config file references
- Confirmation prompts

### Phase 4: Integration

**Enhanced Tools**:
- `analyze_runts()` - Link to UPDATE operations
- `get_repo_status()` - Show UPDATE suggestions
- `scan_repos_for_sota_compliance()` - Bulk UPDATE recommendations

## Template System

### SOTA Template Structure

**Base Template** (`templates/sota/`):
- FastMCP 2.13.1
- Help and status tools included
- CI/CD with ruff + pytest
- Test structure (unit + integration)
- Ruff configuration
- DXT packaging
- Complete documentation

**Minimal Template** (`templates/minimal/`):
- Basic FastMCP server
- Single example tool
- Minimal structure
- For quick prototypes

**Portmanteau Template** (`templates/portmanteau/`):
- Pre-configured portmanteau structure
- Multiple operation examples
- For servers with many tools

## Documentation Templates

### MCP Server Standards (`docs/MCP_SERVER_STANDARDS.md`)
- FastMCP 2.13+ requirements
- Tool documentation standards
- SOTA compliance checklist
- Best practices

### MCPB Standards (`docs/MCPB_STANDARDS.md`)
- MCPB packaging guide
- manifest.json structure
- Distribution guidelines

### Client Rulebooks

**Claude Desktop** (`docs/CLIENT_RULEBOOKS/CLAUDE_DESKTOP.md`):
- Configuration format
- Integration steps
- Troubleshooting

**Cursor IDE** (`docs/CLIENT_RULEBOOKS/CURSOR_IDE.md`):
- Cursor-specific setup
- MCP integration in Cursor
- Best practices

**Windsurf** (`docs/CLIENT_RULEBOOKS/WINDSURF.md`):
- Windsurf configuration
- Integration guide

**Cline** (`docs/CLIENT_RULEBOOKS/CLINE.md`):
- Cline-specific setup

## File Templates

### `mcp_server.py` Template
```python
"""Main MCP server module.

{description}
"""
from fastmcp import FastMCP

app = FastMCP("{server_name}")

@app.tool()
async def help(level: str = "basic", topic: str | None = None) -> str:
    """Get help information about this MCP server.
    
    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        topic: Optional topic to focus on
    
    Returns:
        Help text for the server
    """
    # Implementation here
    pass

@app.tool()
async def status(level: str = "basic", focus: str | None = None) -> str:
    """Get server status and diagnostics.
    
    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        focus: Optional focus area
    
    Returns:
        Status information
    """
    # Implementation here
    pass

if __name__ == "__main__":
    app.run()
```

### `pyproject.toml` Template
```toml
[project]
name = "{package_name}"
version = "0.1.0"
description = "{description}"
authors = [{name = "{author}"}]
requires-python = ">=3.11"
dependencies = [
    "fastmcp[all]>=2.13.1,<2.14.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = []

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
asyncio_mode = "auto"

[tool.coverage.run]
source = ["src"]
omit = ["tests/*", "*/__pycache__/*"]
```

### CI/CD Template (`.github/workflows/ci.yml`)
```yaml
name: CI

on:
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Lint with ruff
        run: ruff check .
      - name: Run tests
        run: pytest
```

## Integration with Existing Tools

### Enhanced `analyze_runts()`
- Add `suggest_updates: bool` parameter
- Return actionable UPDATE suggestions
- Link to `update_mcp_server()` tool

### Enhanced `get_repo_status()`
- Show "Update Available" badges
- Link to UPDATE operations
- Preview what would be added

## Benefits

### 1. **Complete Lifecycle Management**
- Create, read, update, delete - all in one place
- Consistent SOTA standards across all servers
- Automated compliance

### 2. **Developer Productivity**
- Quick server scaffolding
- Automated updates
- No manual configuration

### 3. **Ecosystem Quality**
- All servers start SOTA-compliant
- Easy to bring existing servers to SOTA
- Consistent structure and documentation

### 4. **AI Client Integration**
- Tools added by Claude/Cursor
- Scaffold maintained by MCP Studio
- Clear separation of concerns

## Future Enhancements

1. **Template Marketplace**
   - Community-contributed templates
   - Specialized templates (database, API, etc.)
   - Template versioning

2. **Migration Tools**
   - Upgrade from FastMCP 2.11 → 2.13
   - Migrate to portmanteau pattern
   - Bulk updates across multiple servers

3. **Server Registry**
   - Track all created servers
   - Version management
   - Dependency tracking

4. **Code Generation**
   - Generate tool stubs from descriptions
   - Auto-generate tests
   - Generate documentation

## Conclusion

This transforms MCP Studio from a **management tool** into a **complete development platform** for MCP servers. It ensures all servers meet SOTA standards from creation and provides tools to maintain compliance throughout their lifecycle.
