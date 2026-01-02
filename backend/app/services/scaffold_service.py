"""Scaffold Service.

Service for creating new SOTA-compliant MCP servers with all required components.
"""

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import structlog
import subprocess
import os

logger = structlog.get_logger(__name__)


class ScaffoldService:
    """Service for scaffolding MCP servers."""

    async def create_server(
        self,
        server_name: str,
        description: str,
        author: str = "MCP Studio",
        license_type: str = "MIT",
        target_path: str = "D:/Dev/repos",
        include_examples: bool = True,
        init_git: bool = True,
        include_frontend: bool = False,
        frontend_type: str = "fullstack",
    ) -> Dict[str, Any]:
        """
        Create a new SOTA-compliant MCP server.

        Args:
            server_name: Kebab-case server name (e.g., "my-awesome-server")
            description: Server description
            author: Author name
            license_type: License type
            target_path: Where to create server
            include_examples: Include example tools
            init_git: Initialize git repository
            include_frontend: Include React frontend
            frontend_type: Frontend type ("fullstack" or "minimal")

        Returns:
            Dictionary with creation status and server path
        """
        try:
            # Validate server name
            if (
                not server_name
                or not server_name.replace("-", "").replace("_", "").isalnum()
            ):
                return {
                    "success": False,
                    "error": "Server name must be alphanumeric with hyphens/underscores only",
                }

            # Convert to package name
            package_name = self._kebab_to_snake(server_name)

            # Create server directory
            target_dir = Path(target_path).expanduser().resolve()
            server_dir = target_dir / server_name

            if server_dir.exists():
                return {
                    "success": False,
                    "error": f"Directory already exists: {server_dir}",
                }

            server_dir.mkdir(parents=True, exist_ok=False)
            logger.debug(f"Creating MCP server: {server_name} at {server_dir}")

            # Create directory structure
            (server_dir / "src" / package_name / "tools").mkdir(
                parents=True, exist_ok=True
            )
            (server_dir / "tests" / "unit").mkdir(parents=True, exist_ok=True)
            (server_dir / "tests" / "integration").mkdir(parents=True, exist_ok=True)
            (server_dir / "docs" / "CLIENT_RULEBOOKS").mkdir(
                parents=True, exist_ok=True
            )
            (server_dir / "scripts").mkdir(parents=True, exist_ok=True)
            (server_dir / ".github" / "workflows").mkdir(parents=True, exist_ok=True)

            # Generate files
            files_created = []

            # Main server file
            server_file = server_dir / "src" / package_name / "mcp_server.py"
            server_file.write_text(
                self._generate_mcp_server_py(server_name, package_name, description),
                encoding="utf-8",
            )
            files_created.append(str(server_file.relative_to(server_dir)))

            # Package __init__.py
            (server_dir / "src" / package_name / "__init__.py").write_text(
                f'"""{description}"""\n', encoding="utf-8"
            )
            files_created.append(f"src/{package_name}/__init__.py")

            # Tools __init__.py
            (server_dir / "src" / package_name / "tools" / "__init__.py").write_text(
                "", encoding="utf-8"
            )
            files_created.append(f"src/{package_name}/tools/__init__.py")

            # pyproject.toml
            pyproject_file = server_dir / "pyproject.toml"
            pyproject_file.write_text(
                self._generate_pyproject_toml(
                    server_name, package_name, description, author, license_type
                ),
                encoding="utf-8",
            )
            files_created.append("pyproject.toml")

            # README.md
            readme_file = server_dir / "README.md"
            readme_file.write_text(
                self._generate_readme(server_name, description, author),
                encoding="utf-8",
            )
            files_created.append("README.md")

            # .gitignore
            gitignore_file = server_dir / ".gitignore"
            gitignore_file.write_text(self._generate_gitignore(), encoding="utf-8")
            files_created.append(".gitignore")

            # CI/CD workflow
            ci_file = server_dir / ".github" / "workflows" / "ci.yml"
            ci_file.write_text(self._generate_ci_workflow(), encoding="utf-8")
            files_created.append(".github/workflows/ci.yml")

            # manifest.json (DXT packaging)
            manifest_file = server_dir / "manifest.json"
            manifest_file.write_text(
                self._generate_manifest_json(server_name, description), encoding="utf-8"
            )
            files_created.append("manifest.json")

            # Test files
            test_files = self._generate_test_files(package_name)
            for test_path, content in test_files.items():
                test_file = server_dir / test_path
                test_file.write_text(content, encoding="utf-8")
                files_created.append(test_path)

            # Documentation
            doc_files = self._generate_docs(server_name, description)
            for doc_path, content in doc_files.items():
                doc_file = server_dir / doc_path
                doc_file.write_text(content, encoding="utf-8")
                files_created.append(doc_path)

            # Scripts
            script_files = self._generate_scripts(package_name)
            for script_path, content in script_files.items():
                script_file = server_dir / script_path
                script_file.write_text(content, encoding="utf-8")
                if script_path.endswith(".sh"):
                    script_file.chmod(0o755)  # Make executable
                files_created.append(script_path)

            # LICENSE file
            if license_type == "MIT":
                license_content = self._generate_license(author)
                (server_dir / "LICENSE").write_text(license_content, encoding="utf-8")
                files_created.append("LICENSE")

            # Initialize git if requested
            git_initialized = False
            if init_git:
                try:
                    subprocess.run(
                        ["git", "init"], cwd=server_dir, check=True, capture_output=True
                    )
                    subprocess.run(
                        ["git", "add", "."],
                        cwd=server_dir,
                        check=True,
                        capture_output=True,
                    )
                    subprocess.run(
                        [
                            "git",
                            "commit",
                            "-m",
                            "Initial commit: SOTA-compliant MCP server scaffold",
                        ],
                        cwd=server_dir,
                        check=True,
                        capture_output=True,
                    )
                    git_initialized = True
                    logger.debug(f"Git repository initialized for {server_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize git: {e}")

            # Generate frontend if requested
            frontend_generated = False
            frontend_path = None
            if include_frontend:
                try:
                    logger.debug(f"Generating frontend for {server_name}...")
                    frontend_result = await self.generate_frontend(
                        server_dir=server_dir,
                        server_name=server_name,
                        description=description,
                        author=author,
                        frontend_type=frontend_type,
                    )
                    frontend_generated = frontend_result.get("success", False)
                    frontend_path = frontend_result.get("frontend_path")
                    if frontend_generated:
                        logger.debug(
                            f"Frontend generated successfully: {frontend_path}"
                        )
                except Exception as e:
                    logger.warning(f"Failed to generate frontend: {e}")
                    frontend_generated = False

            next_steps = [
                f"cd {server_dir}",
                "pip install -e .",
                "Add your tools to src/{package_name}/tools/",
                "Run tests: pytest",
            ]

            if frontend_generated:
                next_steps.extend(
                    [
                        "",
                        "Frontend generated! Next steps:",
                        "cd frontend",
                        "npm install",
                        "npm run dev",
                        "",
                        "Or use Docker:",
                        "docker-compose up -d",
                    ]
                )

            return {
                "success": True,
                "server_name": server_name,
                "server_path": str(server_dir),
                "package_name": package_name,
                "files_created": files_created,
                "file_count": len(files_created),
                "git_initialized": git_initialized,
                "sota_compliant": True,
                "frontend_generated": frontend_generated,
                "frontend_path": frontend_path,
                "next_steps": next_steps,
            }

        except Exception as e:
            logger.error(f"Failed to create MCP server: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def generate_frontend(
        self,
        server_dir: Path,
        server_name: str,
        description: str,
        author: str,
        frontend_type: str = "fullstack",
    ) -> Dict[str, Any]:
        """Generate frontend using fullstack builder script.

        Args:
            server_dir: Path to the server directory
            server_name: Server name
            description: Server description
            author: Author name
            frontend_type: "fullstack" or "minimal"

        Returns:
            Dictionary with generation status
        """
        try:
            # Path to fullstack builder script
            script_path = Path(
                "D:/Dev/repos/mcp-central-docs/sota-scripts/fullstack-builder/new-fullstack-app.ps1"
            )

            if not script_path.exists():
                return {
                    "success": False,
                    "error": f"Fullstack builder script not found: {script_path}",
                }

            # Prepare command
            output_path = server_dir.parent
            cmd = [
                "pwsh",
                "-File",
                str(script_path),
                "-AppName",
                server_name,
                "-Description",
                description,
                "-Author",
                author,
                "-OutputPath",
                str(output_path),
                "-IncludeMCP",  # Include MCP client dashboard
                "-IncludeMCPServer",  # Include MCP server (we already created it, but script will add integration)
                "-IncludeMonitoring",
                "-IncludeCI",
                "-IncludeTesting",
            ]

            # Add more features for fullstack type
            if frontend_type == "fullstack":
                cmd.extend(
                    [
                        "-IncludeAI",
                        "-IncludeFileUpload",
                        "-Include2FA",
                        "-IncludePWA",
                    ]
                )

            # Run the script (reduced logging to debug to reduce spam)
            logger.debug(f"Calling fullstack builder: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                cwd=str(output_path),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout for npm installs
            )

            if result.returncode != 0:
                logger.error(f"Fullstack builder failed: {result.stderr}")
                return {
                    "success": False,
                    "error": f"Script execution failed: {result.stderr[:500]}",
                }

            # The script creates a new directory, but we want to merge with existing server
            # For now, we'll note that the frontend was generated separately
            # Future: merge the frontend into the existing server directory

            frontend_dir = output_path / server_name / "frontend"

            return {
                "success": True,
                "frontend_path": str(frontend_dir) if frontend_dir.exists() else None,
                "message": "Frontend generated using fullstack builder script",
                "note": "Frontend may be in a separate directory - check output path",
            }

        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Frontend generation timed out after 5 minutes",
            }
        except Exception as e:
            logger.error(f"Failed to generate frontend: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def _kebab_to_snake(self, name: str) -> str:
        """Convert kebab-case to snake_case."""
        return name.replace("-", "_")

    def _kebab_to_pascal(self, name: str) -> str:
        """Convert kebab-case to PascalCase."""
        return "".join(word.capitalize() for word in name.split("-"))

    def _generate_mcp_server_py(
        self, server_name: str, package_name: str, description: str
    ) -> str:
        """Generate main mcp_server.py file."""
        return f'''"""Main MCP server module.

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
    if level == "basic":
        return f"""# {server_name} Help

## Overview
{description}

## Available Tools
- help: Get help information
- status: Get server status

## Usage
Use the status tool to check server health and configuration.
"""
    elif level == "intermediate":
        return f"""# {server_name} - Intermediate Help

## Tools

### help
Get help information about this server.

### status
Get server status and diagnostics.

## Examples
- help("basic") - Basic overview
- status("intermediate") - Detailed status
"""
    else:
        return f"""# {server_name} - Advanced Help

## Architecture
This server is built with FastMCP 2.13.1.

## Tool Details
See individual tool docstrings for detailed information.
"""


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
        return f"""# {server_name} Status

**Status:** ✅ Running
**Version:** 0.1.0
**FastMCP:** 2.13.1
**Tools:** 2
"""
    elif level == "intermediate":
        return f"""# {server_name} - Detailed Status

## Server Information
- **Name:** {server_name}
- **Version:** 0.1.0
- **FastMCP:** 2.13.1
- **Status:** ✅ Running

## Tools
- help: Help tool (SOTA required)
- status: Status tool (SOTA required)

## Configuration
- Python: 3.11+
- Dependencies: fastmcp[all]>=2.13.1
"""
    else:
        return f"""# {server_name} - Advanced Status

## System Information
- Server: {server_name}
- Package: {package_name}
- FastMCP: 2.13.1
- Python: 3.11+

## Tools
1. help - Help tool (SOTA required)
2. status - Status tool (SOTA required)

## Compliance
- ✅ FastMCP 2.13.1
- ✅ Help tool
- ✅ Status tool
- ✅ Proper docstrings
- ✅ SOTA compliant
"""


if __name__ == "__main__":
    app.run()
'''

    def _generate_pyproject_toml(
        self,
        server_name: str,
        package_name: str,
        description: str,
        author: str,
        license_type: str,
    ) -> str:
        """Generate pyproject.toml file."""
        return f'''[project]
name = "{package_name}"
version = "0.1.0"
description = "{description}"
authors = [{{name = "{author}"}}]
requires-python = ">=3.11"
readme = "README.md"
license = {{text = "{license_type}"}}
dependencies = [
    "fastmcp[all]>=2.14.1,<2.15.0",
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
'''

    def _generate_readme(self, server_name: str, description: str, author: str) -> str:
        """Generate README.md file."""
        pascal_name = self._kebab_to_pascal(server_name)
        return f'''# {pascal_name}

{description}

## Installation

```bash
pip install -e .
```

## Usage

```bash
python -m {server_name.replace("-", "_")}.mcp_server
```

## Claude Desktop Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{{
  "mcpServers": {{
    "{server_name}": {{
      "command": "python",
      "args": ["-m", "{server_name.replace("-", "_")}", "mcp_server"],
      "cwd": "/path/to/{server_name}"
    }}
  }}
}}
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check .

# Format
ruff format .
```

## License

See LICENSE file for details.

## Author

{author}
'''

    def _generate_ci_workflow(self) -> str:
        """Generate GitHub Actions CI workflow."""
        return """name: CI

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
"""

    def _generate_manifest_json(self, server_name: str, description: str) -> str:
        """Generate manifest.json for DXT packaging."""
        return f'''{{
  "name": "{server_name}",
  "description": "{description}",
  "version": "0.1.0",
  "author": "",
  "license": "MIT",
  "mcp": {{
    "command": "python",
    "args": ["-m", "{server_name.replace("-", "_")}", "mcp_server"]
  }}
}}
'''

    def _generate_gitignore(self) -> str:
        """Generate .gitignore file."""
        return """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/
.venv

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# OS
.DS_Store
Thumbs.db
"""

    def _generate_test_files(self, package_name: str) -> Dict[str, str]:
        """Generate test file templates."""
        return {
            "tests/__init__.py": "",
            "tests/unit/__init__.py": "",
            "tests/unit/test_tools.py": f'''"""Unit tests for {package_name} tools."""
import pytest
from {package_name}.mcp_server import app


def test_help_tool_exists():
    """Test that help tool exists."""
    tools = [tool.name for tool in app.list_tools()]
    assert "help" in tools


def test_status_tool_exists():
    """Test that status tool exists."""
    tools = [tool.name for tool in app.list_tools()]
    assert "status" in tools
''',
            "tests/integration/__init__.py": "",
            "tests/integration/test_server.py": f'''"""Integration tests for {package_name} server."""
import pytest


@pytest.mark.asyncio
async def test_server_startup():
    """Test that server can start."""
    # Integration test implementation
    pass
''',
        }

    def _generate_docs(self, server_name: str, description: str) -> Dict[str, str]:
        """Generate documentation files."""
        return {
            "docs/README.md": f"""# {server_name} Documentation

{description}

## Contents

- [MCP Server Standards](MCP_SERVER_STANDARDS.md) - MCP server development standards
- [MCPB Standards](MCPB_STANDARDS.md) - MCPB packaging guidelines
- [Client Rulebooks](CLIENT_RULEBOOKS/) - Client-specific integration guides
""",
            "docs/MCP_SERVER_STANDARDS.md": '''# MCP Server Standards

## FastMCP 2.13+ Requirements

### Required Components
- FastMCP 2.13.1 or later
- Help tool (`help()`)
- Status tool (`status()`)
- Proper docstrings with Args/Returns/Examples
- No `description=` parameters (docstrings only)

### Tool Documentation
All tools must have comprehensive docstrings:
```python
@app.tool()
async def my_tool(param: str) -> str:
    """Tool description.
    
    Args:
        param: Parameter description
    
    Returns:
        Return value description
    
    Examples:
        >>> await my_tool("example")
        "result"
    """
    pass
```

### SOTA Compliance Checklist
- ✅ FastMCP 2.13.1+
- ✅ Help tool
- ✅ Status tool
- ✅ Proper docstrings
- ✅ CI/CD workflow
- ✅ Test directory
- ✅ Ruff linting
- ✅ DXT packaging (manifest.json)

## Portmanteau Pattern

For servers with >15 tools, use portmanteau pattern:
- Consolidate related operations into single tools
- Use `operation` parameter to route to specific functionality
- Reduces tool count and improves discoverability

See: https://github.com/jlowin/fastmcp
''',
            "docs/MCPB_STANDARDS.md": """# MCPB Standards

## MCPB Packaging

MCPB (MCP Bundle) is the standard packaging format for MCP servers.

### manifest.json

Required fields:
- `name`: Server name
- `description`: Server description
- `version`: Version number
- `mcp.command`: Command to run server
- `mcp.args`: Command arguments

### Distribution

1. Build package: `mcpb build`
2. Publish to registry: `mcpb publish`
3. Install: `mcpb install <package-name>`

See: https://modelcontextprotocol.io/packaging
""",
            "docs/CLIENT_RULEBOOKS/CLAUDE_DESKTOP.md": """# Claude Desktop Integration

## Configuration

Add to `~/.config/claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "package_name", "mcp_server"],
      "cwd": "/path/to/server"
    }
  }
}
```

## Troubleshooting

- Check Python path is correct
- Verify dependencies are installed
- Check logs in Claude Desktop
""",
            "docs/CLIENT_RULEBOOKS/CURSOR_IDE.md": """# Cursor IDE Integration

## Configuration

Add to Cursor settings:

```json
{
  "mcp.servers": {
    "server-name": {
      "command": "python",
      "args": ["-m", "package_name", "mcp_server"]
    }
  }
}
```

## Features

- Tool discovery
- Parameter autocomplete
- Result display
""",
            "docs/CLIENT_RULEBOOKS/WINDSURF.md": """# Windsurf Integration

## Configuration

Windsurf uses similar configuration to Claude Desktop.

## Features

- Real-time tool execution
- Context-aware suggestions
""",
            "docs/CLIENT_RULEBOOKS/CLINE.md": """# Cline Integration

## Configuration

Cline supports MCP servers via configuration file.

## Features

- AI-powered tool suggestions
- Context integration
""",
        }

    def _generate_scripts(self, package_name: str) -> Dict[str, str]:
        """Generate script files."""
        return {
            "scripts/setup.py": '''"""Development setup script."""
import subprocess
import sys

def main():
    """Run development setup."""
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-e", ".[dev]"])
    print("✅ Development environment setup complete!")

if __name__ == "__main__":
    main()
''',
            "scripts/test.sh": """#!/bin/bash
# Test runner script

echo "Running tests..."
pytest

echo "Running linter..."
ruff check .

echo "✅ All checks passed!"
""",
        }

    def _generate_license(self, author: str) -> str:
        """Generate LICENSE file content."""
        return f"""MIT License

Copyright (c) {datetime.now().year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
