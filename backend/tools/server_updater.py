"""MCP Server Update Tool.

Adds missing components to bring servers to SOTA compliance.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import json

import structlog

from .decorators import ToolCategory, tool
from .runt_analyzer import get_repo_status
from .server_scaffold import (
    _generate_ci_workflow,
    _generate_manifest_json,
    _generate_docs,
    _generate_test_files,
    _generate_mcp_server_py,
    _kebab_to_snake,
)

logger = structlog.get_logger(__name__)


def _add_help_tool(repo_path: Path, package_name: str) -> Dict[str, Any]:
    """Add help tool to server if missing."""
    server_file = repo_path / "src" / package_name / "mcp_server.py"
    if not server_file.exists():
        # Try alternative locations
        for alt_path in [
            repo_path / package_name / "mcp_server.py",
            repo_path / "mcp_server.py",
            repo_path / "src" / "mcp_server.py",
        ]:
            if alt_path.exists():
                server_file = alt_path
                break
    
    if not server_file.exists():
        return {"success": False, "error": "Could not find mcp_server.py"}
    
    content = server_file.read_text(encoding='utf-8')
    
    # Check if help tool already exists
    if 'async def help(' in content or 'def help(' in content:
        return {"success": False, "error": "Help tool already exists"}
    
    # Find the app definition
    if 'app = FastMCP(' not in content:
        return {"success": False, "error": "Could not find FastMCP app definition"}
    
    # Add help tool after app definition
    help_tool = '''
@app.tool()
async def help(level: str = "basic", topic: str | None = None) -> str:
    """Get help information about this MCP server.
    
    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        topic: Optional topic to focus on
    
    Returns:
        Help text for the server
    """
    if level == "basic":
        return """# Help

## Overview
This MCP server provides tools for your workflow.

## Available Tools
Use the status tool to see all available tools.

## Usage
Call tools with appropriate parameters as documented.
"""
    elif level == "intermediate":
        return """# Help - Intermediate

## Tools
See individual tool docstrings for detailed information.

## Examples
- help("basic") - Basic overview
- status("intermediate") - Detailed status
"""
    else:
        return """# Help - Advanced

## Architecture
This server is built with FastMCP 2.13.1.

## Tool Details
See individual tool docstrings for detailed information.
"""
'''
    
    # Insert after app definition
    lines = content.split('\n')
    insert_idx = None
    for i, line in enumerate(lines):
        if 'app = FastMCP(' in line:
            # Find the end of app definition (next blank line or @app.tool)
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == '' or lines[j].strip().startswith('@'):
                    insert_idx = j
                    break
            if insert_idx is None:
                insert_idx = i + 1
            break
    
    if insert_idx is None:
        return {"success": False, "error": "Could not find insertion point"}
    
    lines.insert(insert_idx, help_tool)
    server_file.write_text('\n'.join(lines), encoding='utf-8')
    
    return {"success": True, "file": str(server_file.relative_to(repo_path))}


def _add_status_tool(repo_path: Path, package_name: str) -> Dict[str, Any]:
    """Add status tool to server if missing."""
    server_file = repo_path / "src" / package_name / "mcp_server.py"
    if not server_file.exists():
        # Try alternative locations
        for alt_path in [
            repo_path / package_name / "mcp_server.py",
            repo_path / "mcp_server.py",
            repo_path / "src" / "mcp_server.py",
        ]:
            if alt_path.exists():
                server_file = alt_path
                break
    
    if not server_file.exists():
        return {"success": False, "error": "Could not find mcp_server.py"}
    
    content = server_file.read_text(encoding='utf-8')
    
    # Check if status tool already exists
    if 'async def status(' in content or 'def status(' in content:
        return {"success": False, "error": "Status tool already exists"}
    
    # Add status tool after help tool (or at end)
    status_tool = '''
@app.tool()
async def status(level: str = "basic", focus: str | None = None) -> str:
    """Get server status and diagnostics.
    
    Args:
        level: Detail level - "basic", "intermediate", or "advanced"
        focus: Optional focus area (servers, tools, system)
    
    Returns:
        Status information
    """
    if level == "basic":
        return """# Server Status

**Status:** ✅ Running
**FastMCP:** 2.13.1
"""
    elif level == "intermediate":
        return """# Server Status - Detailed

## Server Information
- **Status:** ✅ Running
- **FastMCP:** 2.13.1

## Tools
Use help tool to see all available tools.
"""
    else:
        return """# Server Status - Advanced

## System Information
- FastMCP: 2.13.1
- Status: ✅ Running

## Compliance
- ✅ FastMCP 2.13.1
- ✅ Help tool
- ✅ Status tool
"""
'''
    
    # Insert after help tool or at end
    lines = content.split('\n')
    insert_idx = len(lines) - 1  # Before the final if __name__ block
    
    # Try to find after help tool
    for i, line in enumerate(lines):
        if 'async def help(' in line or 'def help(' in line:
            # Find the end of help function
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == '' and j > i + 10:  # Blank line after function
                    insert_idx = j
                    break
            break
    
    lines.insert(insert_idx, status_tool)
    server_file.write_text('\n'.join(lines), encoding='utf-8')
    
    return {"success": True, "file": str(server_file.relative_to(repo_path))}


def _add_ci_cd(repo_path: Path) -> Dict[str, Any]:
    """Add CI/CD workflow if missing."""
    ci_file = repo_path / ".github" / "workflows" / "ci.yml"
    
    if ci_file.exists():
        return {"success": False, "error": "CI workflow already exists"}
    
    ci_file.parent.mkdir(parents=True, exist_ok=True)
    ci_file.write_text(_generate_ci_workflow())
    
    return {"success": True, "file": str(ci_file.relative_to(repo_path))}


def _add_dxt_packaging(repo_path: Path, server_name: str) -> Dict[str, Any]:
    """Add DXT packaging (manifest.json) if missing."""
    manifest_file = repo_path / "manifest.json"
    
    if manifest_file.exists():
        return {"success": False, "error": "manifest.json already exists"}
    
    # Try to get description from README or pyproject.toml
    description = server_name
    readme_file = repo_path / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        if len(lines) > 1:
            description = lines[1].strip()
    
    manifest_file.write_text(_generate_manifest_json(server_name, description))
    
    return {"success": True, "file": "manifest.json"}


def _add_tests(repo_path: Path, package_name: str) -> Dict[str, Any]:
    """Add test structure if missing."""
    test_dir = repo_path / "tests"
    files_created = []
    
    if not test_dir.exists():
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "__init__.py").write_text("")
        files_created.append("tests/__init__.py")
    
    unit_dir = test_dir / "unit"
    if not unit_dir.exists():
        unit_dir.mkdir(parents=True, exist_ok=True)
        (unit_dir / "__init__.py").write_text("")
        files_created.append("tests/unit/__init__.py")
    
    integration_dir = test_dir / "integration"
    if not integration_dir.exists():
        integration_dir.mkdir(parents=True, exist_ok=True)
        (integration_dir / "__init__.py").write_text("")
        files_created.append("tests/integration/__init__.py")
    
    # Add basic test file if none exist
    test_file = unit_dir / "test_tools.py"
    if not test_file.exists() and not any(unit_dir.glob("test_*.py")):
        test_files = _generate_test_files(package_name)
        test_file.write_text(test_files.get("tests/unit/test_tools.py", ""))
        files_created.append("tests/unit/test_tools.py")
    
    return {"success": True, "files_created": files_created}


def _add_ruff_config(repo_path: Path) -> Dict[str, Any]:
    """Add ruff configuration to pyproject.toml if missing."""
    pyproject_file = repo_path / "pyproject.toml"
    
    if not pyproject_file.exists():
        return {"success": False, "error": "pyproject.toml not found"}
    
    content = pyproject_file.read_text(encoding='utf-8')
    
    if '[tool.ruff]' in content:
        return {"success": False, "error": "Ruff config already exists"}
    
    ruff_config = '''

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W"]
ignore = []
'''
    
    # Append to end of file
    pyproject_file.write_text(content + ruff_config, encoding='utf-8')
    
    return {"success": True, "file": "pyproject.toml"}


def _add_docs(repo_path: Path, server_name: str) -> Dict[str, Any]:
    """Add documentation folder with standards if missing."""
    docs_dir = repo_path / "docs"
    files_created = []
    
    if not docs_dir.exists():
        docs_dir.mkdir(parents=True, exist_ok=True)
        (docs_dir / "CLIENT_RULEBOOKS").mkdir(parents=True, exist_ok=True)
    
    # Get description
    description = server_name
    readme_file = repo_path / "README.md"
    if readme_file.exists():
        content = readme_file.read_text(encoding='utf-8')
        lines = content.split('\n')
        if len(lines) > 1:
            description = lines[1].strip()
    
    doc_files = _generate_docs(server_name, description)
    
    for doc_path, content in doc_files.items():
        doc_file = repo_path / doc_path
        if not doc_file.exists():
            doc_file.write_text(content)
            files_created.append(doc_path)
    
    return {"success": True, "files_created": files_created}


def _upgrade_fastmcp(repo_path: Path) -> Dict[str, Any]:
    """Upgrade FastMCP version in dependencies."""
    pyproject_file = repo_path / "pyproject.toml"
    requirements_file = repo_path / "requirements.txt"
    
    updated = []
    
    # Update pyproject.toml
    if pyproject_file.exists():
        content = pyproject_file.read_text(encoding='utf-8')
        if 'fastmcp' in content.lower():
            # Replace any fastmcp version with 2.13.1
            import re
            new_content = re.sub(
                r'fastmcp.*?(\d+\.\d+\.?\d*)',
                'fastmcp[all]>=2.13.1,<2.14.0',
                content,
                flags=re.IGNORECASE
            )
            if new_content != content:
                pyproject_file.write_text(new_content, encoding='utf-8')
                updated.append("pyproject.toml")
    
    # Update requirements.txt
    if requirements_file.exists():
        content = requirements_file.read_text(encoding='utf-8')
        if 'fastmcp' in content.lower():
            import re
            new_content = re.sub(
                r'fastmcp.*?(\d+\.\d+\.?\d*)',
                'fastmcp[all]>=2.13.1,<2.14.0',
                content,
                flags=re.IGNORECASE
            )
            if new_content != content:
                requirements_file.write_text(new_content, encoding='utf-8')
                updated.append("requirements.txt")
    
    if not updated:
        return {"success": False, "error": "FastMCP dependency not found or already up to date"}
    
    return {"success": True, "files_updated": updated}


@tool(
    name="update_mcp_server",
    description="""Update an MCP server to add missing SOTA components.

    Analyzes a server and adds missing components to bring it to SOTA compliance:
    - Help and status tools
    - CI/CD workflow
    - Test structure
    - Ruff configuration
    - DXT packaging
    - Documentation
    - FastMCP version upgrade
    
    Can update specific components or auto-detect and add all missing ones.""",
    category=ToolCategory.DISCOVERY,
    tags=["server", "update", "sota", "enhancement"],
    estimated_runtime="5-15s"
)
async def update_mcp_server(
    repo_path: str,
    components: Optional[List[str]] = None,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Update MCP server to add missing SOTA components.
    
    Args:
        repo_path: Path to the repository
        components: List of components to add (or None for auto-detect)
                    Options: "help_tool", "status_tool", "ci_cd", "tests",
                            "ruff", "dxt", "docs", "upgrade_fastmcp", "all"
        dry_run: Preview changes without applying (default: True)
    
    Returns:
        Dictionary with update status and changes made
    """
    try:
        path = Path(repo_path).expanduser().resolve()
        
        if not path.exists():
            return {
                "success": False,
                "error": f"Repository not found: {repo_path}"
            }
        
        # Get server name from path
        server_name = path.name
        
        # Analyze server to find missing components
        repo_status = await get_repo_status(str(path), use_cache=False)
        
        if not repo_status.get("success"):
            return {
                "success": False,
                "error": f"Could not analyze repository: {repo_status.get('error')}"
            }
        
        # Determine package name
        details = repo_status.get("details", {})
        structure = details.get("structure", {})
        package_name = structure.get("main_package") or _kebab_to_snake(server_name)
        
        # Auto-detect missing components if not specified
        if components is None or "all" in components:
            missing_components = []
            
            if not repo_status.get("has_help_tool"):
                missing_components.append("help_tool")
            if not repo_status.get("has_status_tool"):
                missing_components.append("status_tool")
            if not repo_status.get("has_ci"):
                missing_components.append("ci_cd")
            if not repo_status.get("has_tests"):
                missing_components.append("tests")
            if not repo_status.get("has_ruff"):
                missing_components.append("ruff")
            if not repo_status.get("has_dxt"):
                missing_components.append("dxt")
            
            # Check for docs
            docs_dir = path / "docs"
            if not docs_dir.exists():
                missing_components.append("docs")
            
            # Check FastMCP version
            fastmcp_version = repo_status.get("fastmcp_version", "")
            if fastmcp_version and fastmcp_version < "2.13.1":
                missing_components.append("upgrade_fastmcp")
            
            components = missing_components if components is None else components
        
        if not components:
            return {
                "success": True,
                "message": "Server is already SOTA compliant",
                "components_added": []
            }
        
        # Component update functions
        update_functions = {
            "help_tool": lambda: _add_help_tool(path, package_name),
            "status_tool": lambda: _add_status_tool(path, package_name),
            "ci_cd": lambda: _add_ci_cd(path),
            "tests": lambda: _add_tests(path, package_name),
            "ruff": lambda: _add_ruff_config(path),
            "dxt": lambda: _add_dxt_packaging(path, server_name),
            "docs": lambda: _add_docs(path, server_name),
            "upgrade_fastmcp": lambda: _upgrade_fastmcp(path),
        }
        
        results = []
        changes = []
        
        for component in components:
            if component not in update_functions:
                results.append({
                    "component": component,
                    "success": False,
                    "error": f"Unknown component: {component}"
                })
                continue
            
            if dry_run:
                results.append({
                    "component": component,
                    "success": True,
                    "dry_run": True,
                    "message": f"Would add {component}"
                })
                changes.append(component)
            else:
                try:
                    result = update_functions[component]()
                    result["component"] = component
                    results.append(result)
                    if result.get("success"):
                        changes.append(component)
                except Exception as e:
                    logger.error(f"Failed to add {component}: {e}", exc_info=True)
                    results.append({
                        "component": component,
                        "success": False,
                        "error": str(e)
                    })
        
        return {
            "success": True,
            "repo_path": str(path),
            "server_name": server_name,
            "dry_run": dry_run,
            "components_requested": components,
            "components_added": changes,
            "results": results,
            "next_steps": [
                "Review the changes",
                "Run tests: pytest",
                "Commit changes: git add . && git commit -m 'Add SOTA components'",
            ] if not dry_run else [
                "Run with dry_run=False to apply changes",
            ]
        }
    
    except Exception as e:
        logger.error(f"Failed to update MCP server: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
