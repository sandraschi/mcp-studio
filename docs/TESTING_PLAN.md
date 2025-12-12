# MCP Studio Testing Plan - 2025-12-02

## Overview

Comprehensive testing plan for MCP Studio CRUD tools and recent enhancements.

## Test Categories

### 1. Pre-Commit Hooks ✅
- [x] **Ruff Linting** - Verify ruff check passes
- [x] **Ruff Formatting** - Verify ruff format works
- [x] **Mypy Type Checking** - Verify type checking works
- [x] **Basic Hooks** - trailing-whitespace, end-of-file-fixer, etc.

**Status**: ✅ All hooks passing

### 2. CRUD Tools Testing

#### 2.1 CREATE - `create_mcp_server`

**Test Cases**:
- [ ] **Basic Server Creation**
  - Create server without frontend
  - Verify all SOTA components generated
  - Check file structure matches template
  
- [ ] **Server with Frontend**
  - Create server with `include_frontend=True`
  - Verify PowerShell script execution
  - Check frontend directory created
  - Verify integration between server and frontend

- [ ] **Git Initialization**
  - Create server with `init_git=True`
  - Verify `.git` directory exists
  - Check initial commit created

- [ ] **Error Handling**
  - Invalid server name
  - Path already exists
  - Missing dependencies
  - PowerShell script failure

**Test Command**:
```python
# Basic test
await create_mcp_server(
    server_name="test-server",
    description="Test MCP server",
    author="Test Author",
    target_path="D:/Dev/repos/test-servers",
    include_frontend=False,
    init_git=False
)

# With frontend
await create_mcp_server(
    server_name="test-server-frontend",
    description="Test server with frontend",
    author="Test Author",
    target_path="D:/Dev/repos/test-servers",
    include_frontend=True,
    frontend_type="fullstack",
    init_git=True
)
```

#### 2.2 UPDATE - `update_mcp_server`

**Test Cases**:
- [ ] **Auto-Detect Missing Components**
  - Analyze existing server
  - Identify missing SOTA components
  - Apply updates in dry-run mode
  - Apply updates for real

- [ ] **Specific Component Updates**
  - Add help tool only
  - Add status tool only
  - Add CI/CD workflow
  - Add tests structure
  - Add documentation

- [ ] **Error Handling**
  - Non-existent repository
  - Invalid repository structure
  - Permission errors
  - Component already exists

**Test Command**:
```python
# Dry-run test
await update_mcp_server(
    repo_path="D:/Dev/repos/test-server",
    components=None,  # Auto-detect
    dry_run=True
)

# Specific component
await update_mcp_server(
    repo_path="D:/Dev/repos/test-server",
    components=["help_tool", "status_tool"],
    dry_run=False
)
```

#### 2.3 DELETE - `delete_mcp_server`

**Test Cases**:
- [ ] **Safety Checks**
  - Git repository detection
  - Uncommitted changes warning
  - Remote repository warning
  - Standard repos directory check

- [ ] **Dry-Run Mode**
  - Preview deletion without applying
  - Show all warnings and checks

- [ ] **Backup Creation**
  - Create backup before deletion
  - Verify backup directory exists
  - Check backup contents

- [ ] **Force Mode**
  - Skip safety checks
  - Delete with force=True
  - Verify deletion

- [ ] **Error Handling**
  - Non-existent repository
  - Permission errors
  - Cache clearing failures

**Test Command**:
```python
# Dry-run test
await delete_mcp_server(
    repo_path="D:/Dev/repos/test-server",
    force=False,
    backup=True,
    dry_run=True
)

# Actual deletion (CAREFUL!)
await delete_mcp_server(
    repo_path="D:/Dev/repos/test-server",
    force=False,
    backup=True,
    dry_run=False
)
```

### 3. Frontend Integration Testing

**Test Cases**:
- [ ] **PowerShell Script Execution**
  - Verify script path exists
  - Check script execution
  - Verify timeout handling
  - Check error handling

- [ ] **Frontend Generation**
  - Verify frontend directory created
  - Check React app structure
  - Verify MCP client integration
  - Check Docker setup

- [ ] **Integration Points**
  - Server API endpoints
  - Frontend API calls
  - WebSocket connections
  - MCP client configuration

### 4. SOTA Analysis Tools

**Test Cases**:
- [ ] **Repository Scanning**
  - Scan single repository
  - Scan directory of repositories
  - Verify cache usage
  - Check markdown format output

- [ ] **Cache Management**
  - Cache creation
  - Cache expiration
  - Cache invalidation
  - Cache statistics

### 5. Integration Testing

**Test Cases**:
- [ ] **End-to-End Workflow**
  1. Create new server
  2. Update server with missing components
  3. Scan server for SOTA compliance
  4. Delete test server

- [ ] **MCP Server Integration**
  - Verify tools exposed correctly
  - Test tool execution via MCP protocol
  - Check error handling
  - Verify response formats

## Test Execution Plan

### Phase 1: Unit Tests (Current)
- Pre-commit hooks ✅
- Basic tool structure verification

### Phase 2: Integration Tests (Next)
- CRUD tool execution
- Frontend integration
- SOTA analysis

### Phase 3: End-to-End Tests (Future)
- Complete workflows
- MCP protocol integration
- Error scenarios

## Test Data

### Test Servers Directory
```
D:/Dev/repos/test-servers/
├── test-server-basic/
├── test-server-frontend/
├── test-server-update/
└── test-server-delete/
```

### Cleanup
After testing, clean up test servers:
```python
# Cleanup test servers
test_servers = [
    "D:/Dev/repos/test-servers/test-server-basic",
    "D:/Dev/repos/test-servers/test-server-frontend",
    "D:/Dev/repos/test-servers/test-server-update",
]

for server in test_servers:
    await delete_mcp_server(
        repo_path=server,
        force=True,
        backup=False,
        dry_run=False
    )
```

## Success Criteria

- ✅ All pre-commit hooks pass
- ✅ CRUD tools execute without errors
- ✅ Generated servers are SOTA-compliant
- ✅ Frontend integration works
- ✅ Safety checks prevent accidental deletion
- ✅ Error handling is robust
- ✅ Documentation is accurate

## Next Steps

1. Execute basic CRUD tool tests
2. Test frontend integration
3. Verify SOTA compliance of generated servers
4. Document any issues found
5. Create automated test suite
