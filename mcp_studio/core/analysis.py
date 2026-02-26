import re
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set

logger = logging.getLogger(__name__)

# Skip these directories when scanning - MUST include all venv patterns
SKIP_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "dist",
    "build",
    "env",
    ".env",
    "eggs",
    ".eggs",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "lib",
    "bin",
    "lib64",  # Linux venv
}

# FastMCP version thresholds
FASTMCP_LATEST = "2.13.1"
FASTMCP_RUNT_THRESHOLD = "2.10.0"
FASTMCP_WARN_THRESHOLD = "2.12.0"


def fast_py_glob(directory: Path, max_depth: int = 3) -> List[Path]:
    """Fast python file glob with depth limit and skip dirs."""
    results = []

    # Pre-check: don't scan if directory itself is in a venv
    dir_str = str(directory).lower()
    if ".venv" in dir_str or "site-packages" in dir_str or "\\lib\\" in dir_str:
        return results

    def _walk(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                name_lower = item.name.lower()
                if item.is_dir():
                    # Skip venv, cache, and hidden dirs
                    if (
                        name_lower in SKIP_DIRS
                        or item.name.startswith(".")
                        or item.name.endswith(".egg-info")
                    ):
                        continue
                    _walk(item, depth + 1)
                elif (
                    item.suffix == ".py"
                    and "test" not in name_lower
                    and name_lower != "__init__.py"
                ):
                    # Skip backup/development files
                    if any(x in name_lower for x in ["_fixed", "_backup", "_old", "_dev", "_wip"]):
                        continue
                    results.append(item)
        except (PermissionError, OSError):
            pass

    _walk(directory, 0)
    return results


def analyze_repo(repo_path: Path) -> Optional[Dict[str, Any]]:
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
        "status_emoji": "✅",
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

    # Check for requirements.txt or pyproject.toml
    req_file = repo_path / "requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"

    fastmcp_version = None
    for config_file in [pyproject_file, req_file]:
        if config_file.exists():
            try:
                content = config_file.read_text(encoding="utf-8", errors="ignore")
                match = re.search(r"fastmcp[>=<~]+(\d+\.\d+\.?\d*)", content, re.IGNORECASE)
                if not match:
                    match = re.search(r"fastmcp.*?(\d+\.\d+\.?\d*)", content, re.IGNORECASE)
                if match:
                    fastmcp_version = match.group(1)
                    break
            except Exception:
                pass

    if not fastmcp_version:
        return None  # Not an MCP repo

    info["fastmcp_version"] = fastmcp_version

    # Count tools
    tool_pattern = re.compile(
        r"@(?:(?:app|mcp|self(?:\.(?:app|mcp))?(?:_server\.mcp)?|server)\.)?tool(?:\s*\(|(?=\s*(?:\r?\n|def\s)))",
        re.MULTILINE,
    )
    nonconforming_pattern = re.compile(
        r"def register_\w+_tool\s*\(|\.add_tool\s*\(|register_tool\s*\("
    )
    tool_count = 0

    pkg_name = repo_path.name.replace("-", "_")
    pkg_name_short = pkg_name.replace("_mcp", "").replace("mcp_", "")
    pkg_name_underscore = (
        pkg_name.replace("mcp", "_mcp")
        if "mcp" in pkg_name and "_mcp" not in pkg_name
        else pkg_name
    )

    tools_init_paths = [
        repo_path / "src" / pkg_name_underscore / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name_underscore / "tools" / "__init__.py",
        repo_path / "src" / pkg_name_short / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name_short / "tools" / "__init__.py",
        repo_path / "src" / pkg_name / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name / "tools" / "__init__.py",
        repo_path / pkg_name_underscore / "tools" / "__init__.py",
        repo_path / pkg_name_short / "tools" / "__init__.py",
        repo_path / pkg_name / "tools" / "__init__.py",
        repo_path / "tools" / "__init__.py",
    ]

    imported_modules = set()
    tools_dir = None
    for init_path in tools_init_paths:
        if init_path.exists():
            tools_dir = init_path.parent
            try:
                init_content = init_path.read_text(encoding="utf-8", errors="ignore")
                if "else:" in init_content:
                    else_block = init_content.split("else:")[-1]
                    imports = re.findall(r"from\s+\.(\w+)\s+import", else_block)
                else:
                    imports = re.findall(r"from\s+\.(\w+)\s+import", init_content)
                imported_modules.update(imports)
            except Exception:
                pass
            break

    search_dirs = []
    for pkg_dir_name in [pkg_name, pkg_name_short, pkg_name_underscore]:
        for base in [repo_path / "src", repo_path]:
            pkg_dir = base / pkg_dir_name
            if pkg_dir.exists() and pkg_dir.is_dir() and pkg_dir not in search_dirs:
                search_dirs.append(pkg_dir)

    if tools_dir and tools_dir.exists():
        is_child_of_existing = any(tools_dir.is_relative_to(d) for d in search_dirs)
        if not is_child_of_existing:
            search_dirs.append(tools_dir)

    if not search_dirs:
        src_dir = repo_path / "src"
        if src_dir.exists():
            search_dirs.append(src_dir)
        else:
            search_dirs.append(repo_path)

    pkg_init_files = []
    for pkg_base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name]:
        init_file = pkg_base / "__init__.py"
        if init_file.exists():
            pkg_init_files.append(init_file)
            break

    plugins_dir = None
    for base in [
        repo_path / "src" / pkg_name_underscore,
        repo_path / "src" / pkg_name,
        repo_path / pkg_name,
    ]:
        candidate = base / "plugins"
        if candidate.exists() and candidate.is_dir():
            plugins_dir = candidate
            break

    has_nonconforming = False
    nonconforming_count = 0
    portmanteau_tools = 0
    portmanteau_ops = 0
    individual_tools = 0

    literal_pattern = re.compile(r"Literal\[([^\]]+)\]")
    uses_portmanteau_pattern = False
    portmanteau_dir = None
    portmanteau_modules = set()
    if tools_dir:
        init_file = tools_dir / "__init__.py"
        if init_file.exists():
            init_text = init_file.read_text(encoding="utf-8", errors="ignore")
            has_register_tools = "def register_tools" in init_text
            has_portmanteau_imports = (
                "from .manage_" in init_text
                or "from .query_" in init_text
                or "from .analyze_" in init_text
            )
            uses_portmanteau_pattern = has_register_tools and has_portmanteau_imports
            if "PORTMANTEAU_MODULES" in init_text:
                import_match = re.findall(r"'(portmanteau_\w+|desktop_state)'", init_text)
                portmanteau_modules = set(import_match)
        candidate_portmanteau = tools_dir / "portmanteau"
        if candidate_portmanteau.exists() and candidate_portmanteau.is_dir():
            portmanteau_dir = candidate_portmanteau

    monolithic_server = None
    if not uses_portmanteau_pattern and not portmanteau_modules and not portmanteau_dir:
        for server_file in [
            "fastmcp_server.py",
            "mcp_server.py",
            "server.py",
            "main.py",
            "__main__.py",
        ]:
            for base_path in [
                repo_path / "src" / pkg_name_underscore,
                repo_path / "src" / pkg_name,
                repo_path / pkg_name,
                repo_path,
            ]:
                candidate = base_path / server_file
                if candidate.exists():
                    try:
                        server_content = candidate.read_text(encoding="utf-8", errors="ignore")
                        if tool_pattern.findall(server_content):
                            monolithic_server = candidate
                            break
                    except Exception:
                        pass
            if monolithic_server:
                break

    imported_tool_modules = set()
    for entry_file in ["mcp_main.py", "mcp_server_clean.py", "mcp_server.py"]:
        for base in [
            repo_path / "src" / pkg_name_underscore,
            repo_path / "src" / pkg_name,
            repo_path / pkg_name,
        ]:
            candidate = base / entry_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                    tool_imports = re.findall(r"import\s+\w+\.tools\.(\w+)\.(\w+)", content)
                    for pkg_name_imported, mod in tool_imports:
                        imported_tool_modules.add(f"{pkg_name_imported}/{mod}.py")
                except Exception:
                    pass

    if monolithic_server:
        search_dirs = []
        py_files_to_scan = [monolithic_server]
    elif imported_tool_modules:
        py_files_to_scan = None
    elif portmanteau_modules:
        py_files_to_scan = [
            tools_dir / f"{m}.py" for m in portmanteau_modules if (tools_dir / f"{m}.py").exists()
        ]
        search_dirs = []
    elif portmanteau_dir:
        has_tools = False
        for pf in portmanteau_dir.glob("*.py"):
            if pf.name != "__init__.py":
                try:
                    pf_content = pf.read_text(encoding="utf-8", errors="ignore")
                    if "@mcp.tool" in pf_content or "@app.tool" in pf_content:
                        has_tools = True
                        break
                except Exception:
                    pass
        if has_tools:
            search_dirs = [portmanteau_dir]
            if plugins_dir:
                portmanteau_names = {
                    p.stem.replace("_management", "")
                    for p in portmanteau_dir.glob("*_management.py")
                }
                for plugin_subdir in plugins_dir.iterdir():
                    if plugin_subdir.is_dir() and plugin_subdir.name not in portmanteau_names:
                        search_dirs.append(plugin_subdir)
            py_files_to_scan = None
        else:
            py_files_to_scan = None
    else:
        py_files_to_scan = None

    for search_dir in search_dirs if py_files_to_scan is None else [None]:
        if py_files_to_scan is None:
            py_files = fast_py_glob(search_dir, max_depth=4)
        else:
            py_files = py_files_to_scan

        for py_file in py_files:
            filename = py_file.stem.lower()
            if uses_portmanteau_pattern:
                is_portmanteau_entry = (
                    filename.startswith("manage_")
                    or filename.startswith("query_")
                    or filename.startswith("analyze_")
                    or filename.endswith("_portmanteau")
                    or filename in {"test_calibre_connection", "calibre_ocr_tool"}
                )
                if not is_portmanteau_entry:
                    continue
            elif imported_tool_modules:
                rel_path = f"{py_file.parent.name}/{py_file.name}"
                if rel_path not in imported_tool_modules:
                    continue
            elif imported_modules and tools_dir and py_file.is_relative_to(tools_dir):
                if (
                    py_file.stem not in imported_modules
                    and py_file.parent.name not in imported_modules
                ):
                    continue
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                matches = tool_pattern.findall(content)
                file_tools = len(matches)
                path_str = str(py_file).lower()
                if (
                    "portmanteau" in path_str
                    or path_str.endswith("_tool.py")
                    or path_str.endswith("_tools.py")
                ):
                    portmanteau_tools += file_tools
                    for lit_match in literal_pattern.findall(content):
                        ops = len(re.findall(r'["\'][^"\']+["\']', lit_match))
                        if ops > 1:
                            portmanteau_ops += ops
                else:
                    individual_tools += file_tools
                tool_count += file_tools
                nc_matches = nonconforming_pattern.findall(content)
                if nc_matches:
                    has_nonconforming = True
                    nonconforming_count += len(nc_matches)
            except Exception:
                pass

    for init_file in pkg_init_files:
        try:
            content = init_file.read_text(encoding="utf-8", errors="ignore")
            matches = tool_pattern.findall(content)
            tool_count += len(matches)
            individual_tools += len(matches)
        except Exception:
            pass

    info["tool_count"] = tool_count
    info["tools"] = tool_count
    info["portmanteau_tools"] = portmanteau_tools
    info["portmanteau_ops"] = portmanteau_ops
    info["individual_tools"] = individual_tools
    info["has_portmanteau"] = portmanteau_tools > 0
    info["has_nonconforming_registration"] = has_nonconforming
    info["nonconforming_count"] = nonconforming_count

    has_server_tools = False
    has_tools_dir_tools = False
    for base in [
        repo_path / "src" / pkg_name_underscore,
        repo_path / "src" / pkg_name,
        repo_path / pkg_name,
    ]:
        for server_file in ["server.py", "mcp_server.py", "fastmcp_server.py"]:
            candidate = base / server_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                    if tool_pattern.search(content):
                        has_server_tools = True
                        break
                except Exception:
                    pass
        if has_server_tools:
            break

    if tools_dir and tools_dir.exists():
        for py_file in tools_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if tool_pattern.search(content):
                        has_tools_dir_tools = True
                        break
                except Exception:
                    pass

    if has_server_tools and has_tools_dir_tools:
        info["runt_reasons"].append(
            "Tools split between server.py and tools/ (incomplete refactor)"
        )
        info["issues"].append("Split tools (server.py + tools/)")
        info["recommendations"].append("Move all tools to tools/ directory, keep server.py clean")

    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.exists():
        info["has_ci"] = True
        info["has_cicd"] = True
        info["ci_workflows"] = len(list(workflows_dir.glob("*.yml")))
        info["cicd_count"] = info["ci_workflows"]

    has_src = (repo_path / "src").exists()
    has_tests = (repo_path / "tests").exists()
    has_scripts = (repo_path / "scripts").exists()
    tools_paths = [
        repo_path / "src" / pkg_name_underscore / "tools",
        repo_path / "src" / pkg_name / "tools",
        repo_path / pkg_name_underscore / "tools",
        repo_path / pkg_name / "tools",
        repo_path / "tools",
    ]
    has_tools_dir = any(p.exists() and p.is_dir() for p in tools_paths)
    info["has_src"] = has_src
    info["has_tests"] = has_tests
    info["has_scripts"] = has_scripts
    info["has_tools_dir"] = has_tools_dir

    try:
        version_parts = [int(x) for x in fastmcp_version.split(".")[:2]]
        runt_parts = [int(x) for x in FASTMCP_RUNT_THRESHOLD.split(".")[:2]]
        warn_parts = [int(x) for x in FASTMCP_WARN_THRESHOLD.split(".")[:2]]
        if version_parts < runt_parts:
            info["is_runt"] = True
            info["runt_reasons"].append(f"FastMCP {fastmcp_version} is ancient")
            info["issues"].append(f"FastMCP {fastmcp_version} is ancient")
            info["recommendations"].append(f"Upgrade to FastMCP {FASTMCP_LATEST}")
        elif version_parts < warn_parts:
            info["recommendations"].append(f"Upgrade FastMCP {fastmcp_version} → {FASTMCP_LATEST}")
    except Exception:
        pass

    if portmanteau_tools == 0 and tool_count > 20:
        info["runt_reasons"].append(f"{tool_count} tools, no portmanteau pattern")
        info["issues"].append(f"{tool_count} tools, no portmanteau pattern")
        info["recommendations"].append("Consider consolidating to portmanteau tools")

    if not info["has_ci"]:
        if tool_count >= 10:
            info["is_runt"] = True
            info["runt_reasons"].append("No CI/CD workflows")
            info["issues"].append("No CI/CD workflows")
        info["recommendations"].append("Add CI workflow")

    if not has_src:
        info["runt_reasons"].append("No src/ directory")
        info["issues"].append("No src/ directory")
        info["recommendations"].append("Use proper src/ layout")
    if not has_tests and tool_count >= 10:
        info["runt_reasons"].append("No tests/ directory")
        info["issues"].append("No tests/ directory")
        info["recommendations"].append("Add tests/ with pytest")

    server_files = []
    for server_name in [
        "server.py",
        "fastmcp_server.py",
        "mcp_server.py",
        "simple_mcp_server.py",
        "mcp_compliant_server.py",
    ]:
        for base in [
            repo_path / "src" / pkg_name_underscore,
            repo_path / "src" / pkg_name,
            repo_path / pkg_name,
        ]:
            if (base / server_name).exists():
                server_files.append(server_name)
                break
    if len(server_files) > 1:
        info["runt_reasons"].append(f"Multiple server files: {', '.join(server_files)}")
        info["issues"].append(f"Multiple server files ({len(server_files)})")
        info["recommendations"].append("Keep only the main server file, delete obsolete ones")

    has_mcpb = (repo_path / "manifest.json").exists()
    has_dxt = (
        (repo_path / "dxt").exists() or (repo_path / "dxt").is_dir()
        if (repo_path / "dxt").exists()
        else False
    )
    info["has_mcpb"] = has_mcpb
    info["has_dxt"] = has_dxt
    if not has_mcpb and tool_count >= 5:
        info["runt_reasons"].append("No MCPB packaging (manifest.json)")
        info["issues"].append("No MCPB packaging")
        info["recommendations"].append("Add manifest.json for MCPB distribution")
    if has_dxt and not has_mcpb:
        info["runt_reasons"].append("Uses deprecated DXT instead of MCPB")
        info["issues"].append("DXT without MCPB")
        info["recommendations"].append("Migrate from DXT to MCPB (manifest.json)")

    has_readme = any(
        (repo_path / f).exists() for f in ["README.md", "README.rst", "README.txt", "README"]
    )
    if not has_readme:
        info["runt_reasons"].append("No README")
        info["issues"].append("No README")
        info["recommendations"].append("Add README.md with usage instructions")

    has_license = any(
        (repo_path / f).exists() for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    )
    if not has_license:
        info["runt_reasons"].append("No LICENSE file")
        info["issues"].append("No LICENSE")
        info["recommendations"].append("Add LICENSE file (MIT recommended)")

    has_cursorrules = (repo_path / ".cursorrules").exists()
    if not has_cursorrules:
        info["runt_reasons"].append("No .cursorrules")
        info["issues"].append("No .cursorrules")
        info["recommendations"].append("Add .cursorrules for Cursor AI context")

    has_git = (repo_path / ".git").exists()
    if not has_git:
        info["runt_reasons"].append("No git repository")
        info["issues"].append("No .git")
        info["recommendations"].append("Initialize git: git init")
    else:
        git_config = repo_path / ".git" / "config"
        has_remote = False
        if git_config.exists():
            try:
                config_content = git_config.read_text(encoding="utf-8", errors="ignore")
                has_remote = '[remote "origin"]' in config_content or "[remote " in config_content
            except Exception:
                pass
        if not has_remote:
            info["runt_reasons"].append("No git remote configured")
            info["issues"].append("No git remote")
            info["recommendations"].append("Add remote: git remote add origin <url>")

    has_setup_py = (repo_path / "setup.py").exists()
    has_pyproject = (repo_path / "pyproject.toml").exists()
    if has_setup_py and not has_pyproject:
        info["runt_reasons"].append("Uses setup.py without pyproject.toml")
        info["issues"].append("Old packaging (setup.py)")
        info["recommendations"].append("Migrate to pyproject.toml")

    print_count = 0
    if monolithic_server:
        try:
            server_content = monolithic_server.read_text(encoding="utf-8", errors="ignore")
            import re as re_module

            prints = re_module.findall(r"(?<!\w)print\s*\(", server_content)
            stderr_prints = re_module.findall(r"print\s*\([^)]*file\s*=", server_content)
            console_prints = re_module.findall(r"console\.print\s*\(", server_content)
            print_count = len(prints) - len(stderr_prints) - len(console_prints)
        except Exception:
            pass
    if print_count > 3:
        info["runt_reasons"].append(f"{print_count} print() calls in server (use logging)")
        info["issues"].append(f"{print_count} print() statements")
        info["recommendations"].append("Replace print() with logging or print(file=sys.stderr)")

    server_lines = 0
    if monolithic_server:
        try:
            server_lines = len(
                monolithic_server.read_text(encoding="utf-8", errors="ignore").splitlines()
            )
        except Exception:
            pass
    if server_lines > 1000:
        info["runt_reasons"].append(f"Monolithic server.py ({server_lines} lines)")
        info["issues"].append(f"Server file too large ({server_lines} lines)")
        info["recommendations"].append("Split server.py into modules (tools/, handlers/)")

    has_mcp_server = False
    has_fastapi_server = False
    has_health_endpoint = False
    dual_search_dirs = [
        repo_path / "src" / pkg_name,
        repo_path / "src" / pkg_name_short,
        repo_path / "src" / pkg_name_underscore,
        repo_path / pkg_name,
        repo_path / pkg_name_short,
        repo_path,
    ]
    src_dir = repo_path / "src"
    if src_dir.exists():
        for subdir in src_dir.iterdir():
            if (
                subdir.is_dir()
                and not subdir.name.startswith(".")
                and not subdir.name.startswith("_")
            ):
                dual_search_dirs.append(subdir)
    mcp_server_files = ["mcp_server.py", "fastmcp_server.py"]
    for mcp_file in mcp_server_files:
        for ds_dir in dual_search_dirs:
            if ds_dir.exists() and (ds_dir / mcp_file).exists():
                has_mcp_server = True
                break
    fastapi_files = ["main.py", "server.py", "app.py"]
    for fa_file in fastapi_files:
        for ds_dir in dual_search_dirs:
            if ds_dir.exists():
                fp = ds_dir / fa_file
                if fp.exists():
                    try:
                        content = fp.read_text(encoding="utf-8", errors="ignore")
                        if "FastAPI" in content or "fastapi" in content:
                            has_fastapi_server = True
                            if (
                                "/health" in content
                                or '@app.get("/health")' in content
                                or "health" in content.lower()
                            ):
                                has_health_endpoint = True
                            break
                    except Exception:
                        pass
    info["has_dual_interface"] = has_mcp_server and has_fastapi_server
    info["has_http_interface"] = has_fastapi_server
    info["has_health_endpoint"] = has_health_endpoint
    if has_mcp_server and has_fastapi_server:
        if has_health_endpoint:
            info["features"].append("Dual interface (stdio + HTTP)")
        else:
            info["runt_reasons"].append("HTTP interface missing /health endpoint")
            info["issues"].append("No /health endpoint")
            info["recommendations"].append("Add @app.get('/health') endpoint to FastAPI server")
    elif has_fastapi_server and not has_mcp_server and tool_count == 0:
        info["runt_reasons"].append("REST API only, no MCP tools")
        info["issues"].append("No MCP interface")
        info["recommendations"].append("Add mcp_server.py with @mcp.tool decorators")

    if has_nonconforming:
        if tool_count == 0 and nonconforming_count > 10:
            info["is_runt"] = True
            info["runt_reasons"].append(f"All tools non-FastMCP ({nonconforming_count}x)")
            info["issues"].append(f"All tools non-FastMCP ({nonconforming_count}x)")
        info["recommendations"].append("Use @app.tool decorators")

    proper_docstrings = 0
    if tool_count > 0:
        docstring_pattern = re.compile(
            r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool(?:\(\))?\s*\n\s*(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
            re.MULTILINE,
        )
        for ds_dir in dual_search_dirs:
            if ds_dir.exists():
                for py_file in ds_dir.rglob("*.py"):
                    if any(skip in str(py_file) for skip in SKIP_DIRS):
                        continue
                    try:
                        content = py_file.read_text(encoding="utf-8", errors="ignore")
                        proper_docstrings += len(docstring_pattern.findall(content))
                    except Exception:
                        pass
    info["has_proper_docstrings"] = proper_docstrings > 0 and proper_docstrings >= tool_count * 0.5
    if tool_count >= 3 and not info["has_proper_docstrings"]:
        info["runt_reasons"].append("Missing proper docstrings (Args/Returns)")
        info["issues"].append("Poor docstrings")
        info["recommendations"].append(
            "Add multiline docstrings with Args, Returns, Examples sections"
        )
    elif info["has_proper_docstrings"]:
        info["features"].append("Good docstrings")

    prompts_dir = repo_path / "assets" / "prompts"
    has_prompts = prompts_dir.exists() and any(prompts_dir.glob("*.md"))
    mcpb_prompts = repo_path / "mcpb" / "assets" / "prompts"
    has_mcpb_prompts = mcpb_prompts.exists() and any(mcpb_prompts.glob("*.md"))
    info["has_prompt_templates"] = has_prompts or has_mcpb_prompts
    if has_prompts or has_mcpb_prompts:
        prompt_count = len(list(prompts_dir.glob("*.md"))) if has_prompts else 0
        prompt_count += len(list(mcpb_prompts.glob("*.md"))) if has_mcpb_prompts else 0
        info["features"].append(f"Prompt templates ({prompt_count})")

    has_type_hints = False
    for ds_dir in dual_search_dirs:
        if ds_dir.exists():
            for py_file in ds_dir.rglob("*.py"):
                if any(skip in str(py_file) for skip in SKIP_DIRS):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r"def \w+\([^)]*:\s*\w+|-> \w+|\[[\w\[\], ]+\]", content):
                        has_type_hints = True
                        break
                except Exception:
                    pass
            if has_type_hints:
                break
    info["has_type_hints"] = has_type_hints
    if has_type_hints:
        info["features"].append("Type hints")

    has_logging = False
    for ds_dir in dual_search_dirs:
        if ds_dir.exists():
            for py_file in ds_dir.rglob("*.py"):
                if any(skip in str(py_file) for skip in SKIP_DIRS):
                    continue
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if "import logging" in content or "from logging" in content:
                        has_logging = True
                        break
                except Exception:
                    pass
            if has_logging:
                break
    info["has_logging"] = has_logging
    if has_logging:
        info["features"].append("Proper logging")

    tests_dir = repo_path / "tests"
    test_count = 0
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
        test_count = len(test_files)
    info["test_count"] = test_count
    if test_count >= 3:
        info["features"].append(f"Test suite ({test_count} files)")
    elif test_count == 0 and tool_count >= 5:
        info["recommendations"].append("Add tests/ directory with test files")

    if info["is_runt"]:
        info["status_color"] = "red"
        info["status"] = "runt"
        info["status_emoji"] = "🐛"
        info["status_label"] = "Runt"
    elif len(info["runt_reasons"]) > 0:
        info["status_emoji"] = "⚠️"
        info["status_color"] = "yellow"
        info["status_label"] = "Improvable"
        info["status"] = "improvable"
    else:
        info["status"] = "sota"
        info["status_emoji"] = "✅"
        info["status_label"] = "SOTA"
        info["status_color"] = "green"

    if tool_count >= 20:
        info["zoo_class"] = "jumbo"
        info["zoo_emoji"] = "🐘"
    elif tool_count >= 10:
        info["zoo_class"] = "large"
        info["zoo_emoji"] = "🦁"
    elif tool_count >= 5:
        info["zoo_class"] = "medium"
        info["zoo_emoji"] = "🦊"
    elif tool_count >= 2:
        info["zoo_class"] = "small"
        info["zoo_emoji"] = "🐰"
    else:
        info["zoo_class"] = "chipmunk"
        info["zoo_emoji"] = "🐿️"

    return info


def scan_repos(repos_dir: Path, progress_callback=None, log_func=None) -> List[Dict[str, Any]]:
    """Scan all repositories for MCP servers."""
    results = []

    def _log(msg):
        if log_func:
            log_func(msg)
        logger.info(msg)

    if not repos_dir.exists():
        return results

    dirs = [d for d in repos_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]

    if progress_callback:
        progress_callback(
            {
                "total": len(dirs),
                "status": "scanning",
                "done": 0,
                "mcp_repos_found": 0,
                "errors": 0,
                "skipped": 0,
                "activity": f"🔍 Starting scan of {len(dirs)} directories...",
            }
        )

    for i, repo_path in enumerate(dirs):
        if progress_callback:
            progress_callback({"current": repo_path.name, "done": i})

        try:
            info = analyze_repo(repo_path)
            if info:
                results.append(info)
                if progress_callback:
                    progress_callback(
                        {
                            "mcp_repos_found_inc": 1,
                            "activity": f"  {info['zoo_emoji']} {info['status_emoji']} {info['name']} v{info['fastmcp_version'] or '?'} ({info['tools']} tools)",
                        }
                    )
                _log(f"Found MCP repo: {info['name']}")
            else:
                if progress_callback:
                    progress_callback({"skipped_inc": 1})
        except Exception as e:
            if progress_callback:
                progress_callback(
                    {"errors_inc": 1, "activity": f"  ❌ {repo_path.name}: {str(e)[:50]}"}
                )
            logger.error(f"Error analyzing {repo_path.name}: {e}", exc_info=True)
            _log(f"Error analyzing {repo_path.name}: {e}")

    if progress_callback:
        progress_callback(
            {"status": "complete", "activity": f"✅ Scan complete: {len(results)} MCP repos found"}
        )

    return results
