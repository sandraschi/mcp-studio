import asyncio
import json
import logging
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

# Prometheus client
try:
    from prometheus_client import Counter, Histogram, Gauge
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Dummy classes to prevent errors
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def observe(self, value): pass
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, value): pass
        def inc(self): pass
        def dec(self): pass

from ..core.config import settings
from ..core.logging_utils import get_logger

logger = get_logger(__name__)

# Prometheus metrics for repo scanning
if PROMETHEUS_AVAILABLE:
    SCAN_DURATION = Histogram(
        'mcp_scan_duration_seconds',
        'Duration of repository scan operations',
        ['operation'],
        buckets=[1, 5, 10, 30, 60, 120, 300]
    )

    SCAN_REPOS_FOUND = Counter(
        'mcp_scan_repos_found_total',
        'Total number of MCP repositories found'
    )

    SCAN_REPOS_SKIPPED = Counter(
        'mcp_scan_repos_skipped_total',
        'Total number of repositories skipped'
    )

    SCAN_ERRORS = Counter(
        'mcp_scan_errors_total',
        'Total number of scan errors'
    )


class RepoScannerService:
    """Service for scanning repositories to detect MCP servers and fullstack features."""

    def __init__(self):
        self.scan_progress = {
            "status": "idle",
            "total": 0,
            "current": "",
            "done": 0,
            "mcp_repos_found": 0,
            "skipped": 0,
            "errors": 0,
            "activity_log": [],
        }
        self.last_scan_results: List[Dict[str, Any]] = []

    def get_progress(self) -> Dict[str, Any]:
        """Get current scan progress."""
        progress = self.scan_progress.copy()
        # Include recent errors if available
        if hasattr(self, 'recent_errors') and self.recent_errors:
            progress['recent_errors'] = self.recent_errors[-3:]  # Last 3 errors
        return progress

    def get_results(self) -> List[Dict[str, Any]]:
        """Get results of the last scan."""
        return self.last_scan_results

    def log_scan(self, message: str, is_error: bool = False):
        """Log a message to the scan activity log and actual logs."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"{timestamp} | {message}"

        # Initialize log if needed (redundant given __init__ but safe)
        if "activity_log" not in self.scan_progress:
            self.scan_progress["activity_log"] = []

        self.scan_progress["activity_log"].append(formatted_msg)

        # Keep only last 50 entries
        if len(self.scan_progress["activity_log"]) > 50:
            self.scan_progress["activity_log"] = self.scan_progress["activity_log"][-50:]

        # Also log to actual logger so it appears in logger modal and Loki
        if is_error:
            self.scan_progress["errors"] += 1
            logger.error(f"[SCAN] {message}")
        else:
            logger.info(f"[SCAN] {message}")

    def scan_repos(self, scan_path: Optional[Path] = None) -> List[Dict[str, Any]]:
        """Scan all repositories for MCP servers."""
        results = []
        try:
            repos_dir = scan_path or Path(settings.REPOS_PATH)
            self.log_scan(f"Using repos directory: {repos_dir}")

            if not repos_dir.exists():
                self.log_scan(f"ERROR: Repos directory not found: {repos_dir}", is_error=True)
                logger.error(f"Repos directory not found: {repos_dir}")
                return results

            dirs = [d for d in repos_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
            self.log_scan(f"Found {len(dirs)} directories to scan")

            self.scan_progress["total"] = len(dirs)
            self.scan_progress["status"] = "scanning"
            self.scan_progress["mcp_repos_found"] = 0
            self.scan_progress["errors"] = 0
            self.scan_progress["skipped"] = 0
            self.scan_progress["activity_log"] = []

            # Add initial activity
            self.log_scan(f"Starting scan of {len(dirs)} directories in {repos_dir}...")

            # Set scan timeout (10 minutes)
            scan_start_time = datetime.now()
            max_scan_time = 600  # 10 minutes

            for i, repo_path in enumerate(dirs):
                # Check for timeout
                elapsed = (datetime.now() - scan_start_time).total_seconds()
                if elapsed > max_scan_time:
                    self.log_scan(f"Scan timeout reached ({max_scan_time}s). Stopping scan.", is_error=True)
                    break
                self.scan_progress["current"] = repo_path.name
                self.scan_progress["done"] = i + 1

                try:
                    self.log_scan(f"Analyzing {repo_path.name}...")

                    # Add timeout for individual repo analysis (30 seconds)
                    import asyncio
                    import concurrent.futures

                    def analyze_with_timeout():
                        return self.analyze_repo(repo_path)

                    # Run analysis with timeout
                    try:
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(analyze_with_timeout)
                            info = future.result(timeout=30.0)  # 30 second timeout per repo
                    except concurrent.futures.TimeoutError:
                        raise Exception(f"Analysis timeout for {repo_path.name}")

                    # analyze_repo returns None if not MCP repo
                    if info:
                        results.append(info)
                        mcp_count = self.scan_progress["mcp_repos_found"] + 1
                        self.scan_progress["mcp_repos_found"] = mcp_count

                        # Update Prometheus metrics
                        if PROMETHEUS_AVAILABLE:
                            SCAN_REPOS_FOUND.inc()

                        self.log_scan(
                            f"  [FOUND] {info['zoo_emoji']} {info['name']} v{info['fastmcp_version'] or '?'} ({info['tools']} tools)"
                        )
                    else:
                        skipped = self.scan_progress["skipped"] + 1
                        self.scan_progress["skipped"] = skipped

                        # Update Prometheus metrics
                        if PROMETHEUS_AVAILABLE:
                            SCAN_REPOS_SKIPPED.inc()

                        self.log_scan(f"  [SKIP] {repo_path.name} (not MCP/fullstack repo)")
                except Exception as e:
                    error_msg = f"[ERROR] {repo_path.name}: {str(e)}"
                    self.log_scan(error_msg, is_error=True)
                    logger.error(f"Error analyzing {repo_path.name}: {e}", exc_info=True)

                    # Increment error count but continue scanning
                    self.scan_progress["errors"] += 1

                    # Add error to activity log
                    error_entry = {
                        "repo": repo_path.name,
                        "error": str(e),
                        "timestamp": datetime.now().isoformat()
                    }

                    # Store last few errors for debugging
                    if not hasattr(self, 'recent_errors'):
                        self.recent_errors = []
                    self.recent_errors.append(error_entry)
                    if len(self.recent_errors) > 5:
                        self.recent_errors = self.recent_errors[-5:]

                    # Continue scanning other repos instead of failing completely

            # Final summary
            self.scan_progress["status"] = "complete"
            summary = f"[COMPLETE] Scan complete: {len(results)} MCP repos found, {self.scan_progress['skipped']} skipped, {self.scan_progress['errors']} errors"
            self.log_scan(summary)
            logger.info(summary)

            self.last_scan_results = results
            return results

        except Exception as e:
            error_msg = f"CRITICAL FAILURE: {str(e)}"
            self.log_scan(error_msg, is_error=True)
            logger.error(f"Critical scanner failure: {e}", exc_info=True)
            self.scan_progress["status"] = "failed"
            return []

    def analyze_repo(self, repo_path: Path) -> Optional[Dict[str, Any]]:
        """Analyze a single MCP repository."""
        info = {
            "name": repo_path.name,
            "path": str(repo_path),
            "fastmcp_version": None,
            "tool_count": 0,
            "tools": 0,  # Alias for compatibility
            "has_portmanteau": False,
            "has_ci": False,
            "has_cicd": False,  # Alias
            "ci_workflows": 0,
            "cicd_count": 0,  # Alias
            "is_runt": False,
            "runt_reasons": [],
            "issues": [],  # Alias
            "recommendations": [],
            "status_emoji": "OK",
            "status_color": "green",
            "status_label": "SOTA",
            "status": "sota",
            "zoo_class": "unknown",
            "zoo_emoji": "🦔",
            "portmanteau_tools": 0,
            "portmanteau_ops": 0,
            "individual_tools": 0,
            "has_src": False,
            "has_tests": False,
            "has_scripts": False,
            "has_tools_dir": False,
            "has_mcpb": False,
            "has_dxt": False,
            "has_dual_interface": False,
            "has_http_interface": False,
            "has_health_endpoint": False,
            "has_proper_docstrings": False,
            "has_prompt_templates": False,
            "has_type_hints": False,
            "has_logging": False,
            "test_count": 0,
            "features": [],
        }

        # Detect Fullstack Features
        try:
            fs_features = self.detect_fullstack_features(repo_path)
            info.update(fs_features)
        except Exception as e:
            self.log_scan(
                f"Error detecting stack features for {repo_path.name}: {e}", is_error=True
            )
            # Continue with defaults

        # Check for requirements.txt or pyproject.toml
        req_file = repo_path / "requirements.txt"
        pyproject_file = repo_path / "pyproject.toml"

        fastmcp_version = None
        # Prefer pyproject.toml (more authoritative) over requirements.txt
        for config_file in [pyproject_file, req_file]:
            if config_file.exists():
                try:
                    content = config_file.read_text(encoding="utf-8", errors="ignore")
                    # Relaxed detection: if fastmcp is present, it's an MCP repo
                    if "fastmcp" in content.lower():
                        # Try to extract version if possible
                        match = re.search(r"fastmcp[>=<~]+(\d+\.\d+\.?\d*)", content, re.IGNORECASE)
                        if not match:
                            match = re.search(r"fastmcp.*?(\d+\.\d+\.?\d*)", content, re.IGNORECASE)

                        fastmcp_version = match.group(1) if match else "unknown"
                        break
                except Exception:
                    pass

        # Accepts if it's either an MCP repo OR a Fullstack repo
        if not fastmcp_version and not info.get("is_fullstack"):
            return None  # Not an MCP or Fullstack repo

        info["fastmcp_version"] = fastmcp_version

        # Count tools logic (simplified for now to avoid huge regex blocks, can restore if needed)
        # Using a simpler heuristic for tools count based on file size/content for speed in this migration
        # Restoring the regex logic is safer for accuracy

        tool_pattern = re.compile(
            r"@(?:(?:app|mcp|self(?:\.(?:app|mcp))?(?:_server\.mcp)?|server)\.)?tool(?:\s*\(|(?=\s*(?:\r?\n|def\s)))",
            re.MULTILINE,
        )

        # Simple walk to count tools
        tool_count = 0
        try:
            for root, _, files in os.walk(repo_path):
                if "node_modules" in root or ".git" in root or ".venv" in root:
                    continue
                for file in files:
                    if file.endswith(".py"):
                        try:
                            content = (Path(root) / file).read_text(
                                encoding="utf-8", errors="ignore"
                            )
                            tool_count += len(tool_pattern.findall(content))
                        except:
                            pass
        except Exception:
            pass

        info["tool_count"] = tool_count
        info["tools"] = tool_count

        # Zoo classification
        if tool_count >= 20:
            info["zoo_class"] = "jumbo"
            info["zoo_emoji"] = "ELEPHANT"
        elif tool_count >= 10:
            info["zoo_class"] = "large"
            info["zoo_emoji"] = "LION"
        elif tool_count >= 5:
            info["zoo_class"] = "medium"
            info["zoo_emoji"] = "FOX"
        elif tool_count >= 2:
            info["zoo_class"] = "small"
            info["zoo_emoji"] = "RABBIT"
        else:
            info["zoo_class"] = "chipmunk"
            info["zoo_emoji"] = "CHIPMUNK"

        return info

    def detect_fullstack_features(self, repo_path: Path) -> Dict[str, Any]:
        """Detect fullstack capabilities (frontend, backend, infra, docs)."""
        features = {
            "is_fullstack": False,
            "frontend": [],
            "backend": [],
            "infrastructure": [],
            "docs": [],
            "git": {"exists": False, "dirty": False, "branch": "unknown"},
            "runtime": {"running": False, "container_id": None},
        }

        # --- Frontend Detection ---
        package_json = repo_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                    if "react" in deps:
                        features["frontend"].append("React")
                    if "vue" in deps:
                        features["frontend"].append("Vue")
                    if "svelte" in deps:
                        features["frontend"].append("Svelte")
                    if "angular" in deps:
                        features["frontend"].append("Angular")
                    if "next" in deps:
                        features["frontend"].append("Next.js")
                    if "vite" in deps:
                        features["frontend"].append("Vite")
                    if "tailwindcss" in deps:
                        features["frontend"].append("Tailwind")
                    if "typescript" in deps:
                        features["frontend"].append("TypeScript")
            except:
                pass

        # Simple file checks
        if list(repo_path.glob("*.html")):
            features["frontend"].append("HTML")
        if list(repo_path.glob("*.css")):
            features["frontend"].append("CSS")

        # --- Backend Detection ---
        # Python
        req_txt = repo_path / "requirements.txt"
        py_toml = repo_path / "pyproject.toml"
        if req_txt.exists() or py_toml.exists():
            features["backend"].append("Python")
            # Read content to be more specific
            content = ""
            if req_txt.exists():
                content += req_txt.read_text(errors="ignore")
            if py_toml.exists():
                content += py_toml.read_text(errors="ignore")

            if "fastapi" in content:
                features["backend"].append("FastAPI")
            if "flask" in content:
                features["backend"].append("Flask")
            if "django" in content:
                features["backend"].append("Django")

        # Node Backend (Express/Nest)
        if package_json.exists():
            try:
                with open(package_json, "r", encoding="utf-8") as f:
                    pkg = json.load(f)
                    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                    if "express" in deps:
                        features["backend"].append("Express")
                    if "nestjs" in deps:
                        features["backend"].append("NestJS")
            except:
                pass

        # --- Infrastructure ---
        if (repo_path / "docker-compose.yml").exists() or (
            repo_path / "docker-compose.yaml"
        ).exists():
            features["infrastructure"].append("Docker Compose")
        if (repo_path / "Dockerfile").exists():
            features["infrastructure"].append("Dockerfile")

        # --- Docs ---
        if (repo_path / "README.md").exists():
            features["docs"].append("README")
        if (repo_path / "docs").exists():
            features["docs"].append("docs/")

        # --- Git Status ---
        git_dir = repo_path / ".git"
        if git_dir.exists():
            features["git"]["exists"] = True
            try:
                # Check branch
                branch = subprocess.check_output(
                    ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                    cwd=repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL,
                ).strip()
                features["git"]["branch"] = branch

                # Check dirty
                status = subprocess.check_output(
                    ["git", "status", "--porcelain"],
                    cwd=repo_path,
                    text=True,
                    stderr=subprocess.DEVNULL,
                )
                features["git"]["dirty"] = bool(status.strip())
            except:
                pass

        # --- Runtime (Docker) ---
        repo_name = repo_path.name.lower()
        try:
            output = subprocess.check_output(
                ["docker", "ps", "--format", "{{.ID}}|{{.Names}}"],
                text=True,
                stderr=subprocess.DEVNULL,
            )
            for line in output.strip().splitlines():
                if "|" in line:
                    cid, name = line.split("|", 1)
                    if repo_name in name.lower() or name.lower() in repo_name:
                        features["runtime"]["running"] = True
                        features["runtime"]["container_id"] = cid
                        features["runtime"]["name"] = name
                        break
        except:
            pass

        # Decision
        has_frontend = len(features["frontend"]) > 0
        has_backend = len(features["backend"]) > 0
        has_docker = "Docker Compose" in features["infrastructure"]

        if (
            (has_frontend and has_backend)
            or (has_frontend and has_docker)
            or (has_backend and has_docker)
        ):
            features["is_fullstack"] = True
        elif (repo_path / "package.json").exists() and (repo_path / "requirements.txt").exists():
            features["is_fullstack"] = True

        return features


# Global instance
repo_scanner = RepoScannerService()
