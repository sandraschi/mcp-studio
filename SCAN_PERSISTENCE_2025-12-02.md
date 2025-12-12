# Scan Persistence & Markdown Formatting - 2025-12-02

## Summary

Added file-based persistence (caching) for repository scan results and markdown formatting support to avoid re-scanning repositories on every request and provide human-readable output.

## Problem

**Before:**
- Full scan of `D:/Dev/repos` takes significant time
- No caching - every request re-scans all repos
- Results only in JSON format
- No way to get human-readable reports

## Solution

**After:**
- File-based caching system with TTL
- Cache invalidation based on file modification times
- Markdown formatting for human-readable reports
- Configurable cache behavior

## New Modules

### 1. `scan_cache.py` - File-Based Caching

**Features:**
- JSON file-based cache in `~/.mcp-studio/scan-cache/`
- TTL-based expiration (default: 1 hour)
- File modification time checking for invalidation
- Separate caching for bulk scans and individual repos
- Cache statistics and management

**Cache Structure:**
```
~/.mcp-studio/scan-cache/
  ├── scan_{hash}.json      # Bulk scan results
  └── repo_{hash}.json      # Individual repo results
```

**Functions:**
- `get_cached_scan()` - Get cached bulk scan result
- `cache_scan_result()` - Cache bulk scan result
- `get_cached_repo_status()` - Get cached repo status
- `cache_repo_status()` - Cache repo status
- `clear_cache()` - Clear cache entries
- `get_cache_stats()` - Get cache statistics

**Cache Invalidation:**
- Time-based: TTL expiration (default 1 hour)
- File-based: Repository modification time check
- Manual: `clear_cache()` function

### 2. `scan_formatter.py` - Markdown Formatting

**Features:**
- Human-readable markdown output
- Formatted scan summaries
- Detailed repo status reports
- Emoji indicators for status
- Structured sections

**Functions:**
- `format_scan_result_markdown()` - Format bulk scan results
- `format_repo_status_markdown()` - Format single repo status

## Integration

### Updated Tools

#### `analyze_runts()`

**New Parameters:**
- `format: str = "json"` - Output format: "json" or "markdown"
- `use_cache: bool = True` - Whether to use cached results
- `cache_ttl: int = 3600` - Cache time-to-live in seconds

**Behavior:**
1. Check cache if `use_cache=True`
2. If cache hit and valid, return cached result
3. Otherwise, perform scan
4. Cache result if `use_cache=True`
5. Format output based on `format` parameter

**Example:**
```python
# JSON output (default)
result = await analyze_runts("D:/Dev/repos", format="json")

# Markdown output
markdown = await analyze_runts("D:/Dev/repos", format="markdown")

# Force fresh scan (no cache)
result = await analyze_runts("D:/Dev/repos", use_cache=False)
```

#### `get_repo_status()`

**New Parameters:**
- `format: str = "json"` - Output format: "json" or "markdown"
- `use_cache: bool = True` - Whether to use cached results
- `cache_ttl: int = 3600` - Cache time-to-live in seconds

**Behavior:**
1. Check cache if `use_cache=True`
2. If cache hit and valid, return cached result
3. Otherwise, analyze repo
4. Cache result if `use_cache=True`
5. Format output based on `format` parameter

## Cache Details

### Cache Key Generation
- Bulk scans: MD5 hash of `{scan_path}:{max_depth}`
- Individual repos: MD5 hash of `{repo_path}`

### Cache File Format
```json
{
  "scan_path": "D:/Dev/repos",
  "max_depth": 1,
  "cache_timestamp": 1701234567.89,
  "result": {
    "success": true,
    "summary": {...},
    "runts": [...],
    "sota_repos": [...]
  }
}
```

### Cache Validation
1. **TTL Check**: `current_time - cache_timestamp < ttl`
2. **Path Existence**: Verify scan path/repo still exists
3. **Modification Time**: For repos, check if modified since cache

## Markdown Output

### Scan Results Format

```markdown
# MCP Repository Scan Results

## Summary
- **Total MCP Repos:** 15
- **Runts:** 3
- **SOTA:** 12
- **Scan Path:** `D:/Dev/repos`
- **Scan Time:** 2025-12-02 14:30:00

## 🐛 Runts (Need Upgrades)

### 🐛 repo-name
**Status:** Runt
**SOTA Score:** 65/100
**FastMCP Version:** 2.11.0
**Tool Count:** 8

**Issues:**
- FastMCP 2.11.0 < 2.12.0
- No help tool
- No status tool

**Recommendations:**
- Upgrade to FastMCP 2.13.1
- Add help() tool for discoverability
- Add status() tool for diagnostics

---

## ✅ SOTA Repositories

### ✅ sota-repo
**Status:** SOTA
**SOTA Score:** 100/100
...
```

### Repo Status Format

```markdown
# Repository Name

## Status Overview
**Status:** ✅ SOTA
**SOTA Score:** 100/100
**Upgrade Priority:** N/A
**Path:** `D:/Dev/repos/repo-name`

## Basic Information
- **FastMCP Version:** 2.13.1
- **Tool Count:** 15
- **Has Portmanteau:** Yes
- **Zoo Class:** large 🦁

## Detailed Information

### Metadata
**Description:** ...
**Author:** ...
**Version:** 1.0.0
**License:** MIT

### Dependencies
- **FastMCP:** 2.13.1
- **Total Dependencies:** 12
- **Python Packages:** fastmcp, pydantic, ...

### Tools
- **Total Tools:** 15
- **Has Help Tool:** Yes
- **Has Status Tool:** Yes

**Tool List:**
- `help` (fastmcp)
- `status` (fastmcp)
- ...
```

## Benefits

### 1. **Performance**
- Avoid re-scanning on every request
- Fast cache lookups (< 10ms)
- Significant time savings for large scans

### 2. **Flexibility**
- Configurable cache behavior
- TTL-based expiration
- Manual cache clearing

### 3. **Human-Readable Output**
- Markdown format for reports
- Easy to read and share
- Formatted with emojis and structure

### 4. **Smart Invalidation**
- Automatic invalidation on file changes
- TTL-based expiration
- Manual cache management

## Usage Examples

### Basic Usage (with cache)
```python
# Uses cache if available
result = await analyze_runts("D:/Dev/repos")
```

### Markdown Output
```python
# Get human-readable markdown report
markdown = await analyze_runts("D:/Dev/repos", format="markdown")
print(markdown)
```

### Force Fresh Scan
```python
# Bypass cache
result = await analyze_runts("D:/Dev/repos", use_cache=False)
```

### Custom Cache TTL
```python
# Use 30-minute cache
result = await analyze_runts("D:/Dev/repos", cache_ttl=1800)
```

### Cache Management
```python
from mcp_studio.tools.scan_cache import clear_cache, get_cache_stats

# Clear all cache
clear_cache()

# Clear specific scan cache
clear_cache(scan_path="D:/Dev/repos")

# Get cache statistics
stats = get_cache_stats()
# {
#   "cache_dir": "~/.mcp-studio/scan-cache",
#   "total_files": 15,
#   "total_size": 1024000,
#   "oldest_cache": 1701234567.89,
#   "newest_cache": 1701237890.12
# }
```

## Files Modified

1. **NEW:** `src/mcp_studio/tools/scan_cache.py`
   - File-based caching system
   - Cache management functions
   - ~200 lines

2. **NEW:** `src/mcp_studio/tools/scan_formatter.py`
   - Markdown formatting
   - Human-readable reports
   - ~250 lines

3. **UPDATED:** `src/mcp_studio/tools/runt_analyzer.py`
   - Integrated caching
   - Added format parameter
   - Added cache parameters

## Future Enhancements

1. **Database Persistence**
   - SQLite database for cache (like preprompt_db)
   - Better query capabilities
   - Indexed lookups

2. **Incremental Updates**
   - Only re-scan changed repos
   - Merge cache with fresh data
   - Partial cache invalidation

3. **Cache Analytics**
   - Track cache hit rates
   - Monitor cache performance
   - Optimize cache strategy

4. **Export Formats**
   - PDF export
   - HTML export
   - CSV export for bulk analysis

## Conclusion

The scan persistence system provides:
- ✅ Fast cached results
- ✅ Configurable cache behavior
- ✅ Human-readable markdown output
- ✅ Smart cache invalidation
- ✅ Easy cache management

This significantly improves performance for large scans while providing flexible output formats for both programmatic and human consumption.
