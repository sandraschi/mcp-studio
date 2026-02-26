import re
from pathlib import Path


def cleanup_studio_dashboard():
    source_file = Path("studio_dashboard.py")

    with open(source_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Add new imports
    old_import = "from fastapi.templating import Jinja2Templates  # type: ignore[import-untyped]"
    new_imports = (
        old_import
        + "\nfrom mcp_studio.core.discovery import discover_mcp_clients\nfrom mcp_studio.core.analysis import analyze_repo, scan_repos, fast_py_glob, SKIP_DIRS, FASTMCP_LATEST, FASTMCP_RUNT_THRESHOLD, FASTMCP_WARN_THRESHOLD"
    )
    content = content.replace(old_import, new_imports)

    # 2. discover_mcp_clients replacement
    content = re.sub(
        r"def discover_mcp_clients\(\) -> Dict\[str, List\[Dict\]\]:.*?return results",
        "def discover_mcp_clients():\n    return discover_mcp_clients_modular(log_func=log)",
        content,
        flags=re.DOTALL,
    )
    # Actually I should rename the import to avoid conflict
    content = content.replace(
        "from mcp_studio.core.discovery import discover_mcp_clients",
        "from mcp_studio.core.discovery import discover_mcp_clients as discover_mcp_clients_modular",
    )

    # 3. fast_py_glob replacement
    content = re.sub(
        r"def fast_py_glob\(directory: Path, max_depth: int = 3\) -> List\[Path\]:.*?return results",
        "def fast_py_glob_wrapper(directory: Path, max_depth: int = 3):\n    return fast_py_glob(directory, max_depth)",
        content,
        flags=re.DOTALL,
    )

    # 4. analyze_repo replacement
    content = re.sub(
        r"def analyze_repo\(repo_path: Path\) -> Optional\[Dict\[str, Any\]\]:.*?return info",
        "def analyze_repo(repo_path: Path):\n    return analyze_repo_modular(repo_path)",
        content,
        flags=re.DOTALL,
    )
    content = content.replace(
        "from mcp_studio.core.analysis import analyze_repo",
        "from mcp_studio.core.analysis import analyze_repo as analyze_repo_modular",
    )

    # 5. scan_repos replacement
    scan_repos_wrapper = """
def scan_repos():
    \"\"\"Scan all repositories using the modular scanner.\"\"\"
    def progress_callback(update):
        if "total" in update: state["scan_progress"]["total"] = update["total"]
        if "status" in update: state["scan_progress"]["status"] = update["status"]
        if "current" in update: state["scan_progress"]["current"] = update["current"]
        if "done" in update: state["scan_progress"]["done"] = update["done"]
        if "mcp_repos_found_inc" in update: state["scan_progress"]["mcp_repos_found"] += update["mcp_repos_found_inc"]
        if "errors_inc" in update: state["scan_progress"]["errors"] += update["errors_inc"]
        if "skipped_inc" in update: state["scan_progress"]["skipped"] += update["skipped_inc"]
        if "activity" in update:
            state["scan_progress"]["activity_log"].append(update["activity"])
            if len(state["scan_progress"]["activity_log"]) > 20:
                state["scan_progress"]["activity_log"].pop(0)

    return scan_repos_modular(REPOS_DIR, progress_callback=progress_callback, log_func=log)
"""
    content = re.sub(
        r"def scan_repos\(\) -> List\[Dict\[str, Any\]\]:.*?return results",
        scan_repos_wrapper,
        content,
        flags=re.DOTALL,
    )
    content = content.replace(
        "from mcp_studio.core.analysis import scan_repos",
        "from mcp_studio.core.analysis import scan_repos as scan_repos_modular",
    )

    # 6. Remove constants (using broader matches)
    content = re.sub(
        r"SKIP_DIRS = \{.*?\}", "# SKIP_DIRS moved to core.analysis", content, flags=re.DOTALL
    )
    content = re.sub(
        r'FASTMCP_LATEST = ".*?".*?FASTMCP_WARN_THRESHOLD = ".*?"',
        "# FASTMCP thresholds moved to core.analysis",
        content,
        flags=re.DOTALL,
    )

    with open(source_file, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully cleaned up studio_dashboard.py")


if __name__ == "__main__":
    cleanup_studio_dashboard()
