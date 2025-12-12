# MCP Server Tools Improvements

**Date:** 2025-12-02  
**Status:** ✅ **COMPLETED**

## Summary

Fixed several issues with MCP Studio server tools:
1. Added `set_discovery_path` tool with path parameter
2. Fixed hardcoded `D:/Dev/repos` defaults to use environment/config
3. Reduced terminal spam by adjusting logging levels and adding delays
4. Improved discovery path configuration

## Changes Made

### 1. Added `set_discovery_path` Tool

**File:** `src/mcp_studio/mcp_server.py`

Added new MCP tool to set discovery paths:

```python
@app.tool()
async def set_discovery_path(path: str) -> Dict[str, Any]:
    """Set the MCP server discovery path.
    
    Args:
        path: The new discovery path to set (can be absolute or relative)
    
    Returns:
        Dictionary with success status, path, and previous paths
    """
```

**Features:**
- Accepts path parameter (required)
- Resolves relative paths to absolute
- Validates path existence
- Updates settings and global DISCOVERY_PATHS
- Returns previous paths for reference

**Usage:**
```python
result = await set_discovery_path("D:/Dev/repos")
result = await set_discovery_path("./mcp-servers")
```

### 2. Fixed Hardcoded Default Paths

**Problem:** Multiple tools had hardcoded `D:/Dev/repos` default paths.

**Solution:** Created `get_default_repos_path()` function that:
- Checks `REPOS_DIR`, `REPOS_PATH`, or `MCP_REPOS_DIR` environment variables
- Falls back to platform-specific defaults:
  - Windows: `%USERPROFILE%\Dev\repos`, `D:\Dev\repos`, `C:\Dev\repos`
  - Linux/Mac: `~/dev/repos`, `~/repos`, `/opt/repos`
- Returns first existing path, or creates default if none exist

**Files Updated:**
- `src/mcp_studio/app/core/config.py` - Added `get_default_repos_path()` and `DEFAULT_REPOS_PATH`
- `src/mcp_studio/mcp_server.py` - Updated all tools to use `DEFAULT_REPOS_PATH`
- `src/mcp_studio/tools/runt_analyzer.py` - Updated to use default path

**Tools Fixed:**
- `analyze_repo_sota_status()` - `scan_path` parameter
- `create_mcp_server()` - `target_path` parameter
- `scan_repos_for_sota_compliance()` - `scan_path` parameter
- `analyze_runts()` - `scan_path` parameter

### 3. Reduced Terminal Spam

**Changes:**
- Changed verbose `logger.info()` calls to `logger.debug()` in:
  - `server_scaffold.py`: Frontend generation, git init, server creation
- Added small delays to file scanning loops:
  - `runt_analyzer.py`: 100ms delay between repos
  - `server.py`: 50ms delay between servers
- Updated config.py to use logger instead of print for warnings

**Impact:**
- Less verbose output during normal operations
- Reduced CPU usage during large scans
- Better user experience with less terminal noise

### 4. Improved Discovery Path Configuration

**File:** `src/mcp_studio/app/core/config.py`

**Enhancements:**
- Checks `MCP_DISCOVERY_PATHS` and `DISCOVERY_PATHS` environment variables
- Adds `REPOS_DIR` to discovery paths if set
- Better error handling with logging instead of print
- Validates paths before adding to list

## Environment Variables

The following environment variables are now supported:

- `REPOS_DIR` / `REPOS_PATH` / `MCP_REPOS_DIR`: Default repos directory
- `MCP_DISCOVERY_PATHS` / `DISCOVERY_PATHS`: Comma-separated discovery paths

## Migration Guide

**Before:**
```python
# Hardcoded paths
result = await analyze_repo_sota_status("mcp-studio", "D:/Dev/repos")
result = await create_mcp_server("my-server", "Description", target_path="D:/Dev/repos")
```

**After:**
```python
# Uses environment/config defaults
result = await analyze_repo_sota_status("mcp-studio")  # Uses REPOS_DIR or default
result = await create_mcp_server("my-server", "Description")  # Uses REPOS_DIR or default

# Or set discovery path first
await set_discovery_path("D:/Dev/repos")
result = await analyze_repo_sota_status("mcp-studio")
```

## Testing

To test the changes:

1. **Test set_discovery_path:**
   ```python
   result = await set_discovery_path("D:/Dev/repos")
   assert result["success"] == True
   assert "D:/Dev/repos" in result["current_paths"]
   ```

2. **Test default path:**
   ```python
   # Without REPOS_DIR set, should use platform default
   result = await analyze_repo_sota_status("mcp-studio")
   # Should work with default path
   ```

3. **Test reduced spam:**
   - Run discovery scan and verify less verbose output
   - Check that debug-level messages don't appear in normal operation

## Related Files

- `src/mcp_studio/mcp_server.py` - Main MCP server with tools
- `src/mcp_studio/app/core/config.py` - Configuration management
- `src/mcp_studio/tools/runt_analyzer.py` - Repository analysis
- `src/mcp_studio/tools/server.py` - Server discovery
- `src/mcp_studio/tools/server_scaffold.py` - Server creation

## Notes

- All changes are backward compatible
- Existing code using hardcoded paths will continue to work
- New code should use environment variables or `set_discovery_path` tool
- Discovery paths are now more flexible and configurable


