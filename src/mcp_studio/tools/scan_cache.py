"""Cache management for repository scan results.

Provides file-based persistence for scan results to avoid re-scanning
repositories on every request. Uses JSON files with timestamp-based
invalidation.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib
import structlog

logger = structlog.get_logger(__name__)

# Cache directory (relative to user's home or temp)
CACHE_DIR = Path.home() / ".mcp-studio" / "scan-cache"
CACHE_TTL = 3600  # 1 hour default TTL


def _get_cache_key(scan_path: str, max_depth: int = 1) -> str:
    """Generate cache key for scan path."""
    key = f"{scan_path}:{max_depth}"
    return hashlib.md5(key.encode()).hexdigest()


def _get_repo_cache_key(repo_path: str) -> str:
    """Generate cache key for single repo."""
    return hashlib.md5(repo_path.encode()).hexdigest()


def get_cached_scan(scan_path: str, max_depth: int = 1, ttl: int = CACHE_TTL) -> Optional[Dict[str, Any]]:
    """Get cached scan result if still valid.
    
    Args:
        scan_path: Path that was scanned
        max_depth: Scan depth used
        ttl: Time-to-live in seconds (default: 1 hour)
    
    Returns:
        Cached result if valid, None otherwise
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_key = _get_cache_key(scan_path, max_depth)
    cache_file = CACHE_DIR / f"scan_{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        # Check if cache is still valid
        cache_time = cached.get("cache_timestamp", 0)
        if time.time() - cache_time > ttl:
            logger.debug(f"Cache expired for {scan_path}")
            return None
        
        # Check if scan path still exists and hasn't changed
        scan_path_obj = Path(scan_path).expanduser().resolve()
        if not scan_path_obj.exists():
            return None
        
        logger.debug(f"Using cached scan result for {scan_path}")
        return cached.get("result")
    
    except Exception as e:
        logger.warning(f"Failed to read cache: {e}")
        return None


def cache_scan_result(scan_path: str, max_depth: int, result: Dict[str, Any]) -> None:
    """Cache scan result.
    
    Args:
        scan_path: Path that was scanned
        max_depth: Scan depth used
        result: Scan result to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_key = _get_cache_key(scan_path, max_depth)
    cache_file = CACHE_DIR / f"scan_{cache_key}.json"
    
    try:
        cache_data = {
            "scan_path": scan_path,
            "max_depth": max_depth,
            "cache_timestamp": time.time(),
            "result": result,
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.debug(f"Cached scan result for {scan_path}")
    
    except Exception as e:
        logger.warning(f"Failed to cache scan result: {e}")


def get_cached_repo_status(repo_path: str, ttl: int = CACHE_TTL) -> Optional[Dict[str, Any]]:
    """Get cached repo status if still valid.
    
    Args:
        repo_path: Path to repository
        ttl: Time-to-live in seconds (default: 1 hour)
    
    Returns:
        Cached result if valid, None otherwise
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_key = _get_repo_cache_key(repo_path)
    cache_file = CACHE_DIR / f"repo_{cache_key}.json"
    
    if not cache_file.exists():
        return None
    
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            cached = json.load(f)
        
        # Check if cache is still valid
        cache_time = cached.get("cache_timestamp", 0)
        if time.time() - cache_time > ttl:
            logger.debug(f"Cache expired for {repo_path}")
            return None
        
        # Check if repo still exists
        repo_path_obj = Path(repo_path).expanduser().resolve()
        if not repo_path_obj.exists():
            return None
        
        # Check if repo has been modified (simple check - could be enhanced)
        repo_mtime = repo_path_obj.stat().st_mtime
        if repo_mtime > cache_time:
            logger.debug(f"Repo modified, cache invalid for {repo_path}")
            return None
        
        logger.debug(f"Using cached repo status for {repo_path}")
        return cached.get("result")
    
    except Exception as e:
        logger.warning(f"Failed to read repo cache: {e}")
        return None


def cache_repo_status(repo_path: str, result: Dict[str, Any]) -> None:
    """Cache repo status result.
    
    Args:
        repo_path: Path to repository
        result: Repo status result to cache
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    cache_key = _get_repo_cache_key(repo_path)
    cache_file = CACHE_DIR / f"repo_{cache_key}.json"
    
    try:
        cache_data = {
            "repo_path": repo_path,
            "cache_timestamp": time.time(),
            "result": result,
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
        
        logger.debug(f"Cached repo status for {repo_path}")
    
    except Exception as e:
        logger.warning(f"Failed to cache repo status: {e}")


def clear_cache(scan_path: Optional[str] = None, repo_path: Optional[str] = None) -> int:
    """Clear cache entries.
    
    Args:
        scan_path: Clear cache for specific scan path (None = all scans)
        repo_path: Clear cache for specific repo (None = all repos)
    
    Returns:
        Number of cache files deleted
    """
    if not CACHE_DIR.exists():
        return 0
    
    deleted = 0
    
    if scan_path:
        cache_key = _get_cache_key(scan_path)
        cache_file = CACHE_DIR / f"scan_{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()
            deleted += 1
    elif repo_path:
        cache_key = _get_repo_cache_key(repo_path)
        cache_file = CACHE_DIR / f"repo_{cache_key}.json"
        if cache_file.exists():
            cache_file.unlink()
            deleted += 1
    else:
        # Clear all
        for cache_file in CACHE_DIR.glob("*.json"):
            cache_file.unlink()
            deleted += 1
    
    logger.info(f"Cleared {deleted} cache entries")
    return deleted


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics.
    
    Returns:
        Dictionary with cache statistics
    """
    if not CACHE_DIR.exists():
        return {
            "cache_dir": str(CACHE_DIR),
            "total_files": 0,
            "total_size": 0,
            "oldest_cache": None,
            "newest_cache": None,
        }
    
    cache_files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in cache_files)
    
    cache_times = []
    for cache_file in cache_files:
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                cache_times.append(cached.get("cache_timestamp", 0))
        except Exception:
            pass
    
    return {
        "cache_dir": str(CACHE_DIR),
        "total_files": len(cache_files),
        "total_size": total_size,
        "oldest_cache": min(cache_times) if cache_times else None,
        "newest_cache": max(cache_times) if cache_times else None,
    }
