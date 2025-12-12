"""Enhanced repository detail collector for comprehensive analysis.

Collects detailed information about MCP repositories to enable AI clients
to answer questions without re-analyzing, saving tokens and ensuring accuracy.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import tomllib  # Python 3.11+
except ImportError:
    try:
        import tomli as tomllib  # Fallback for older Python
    except ImportError:
        tomllib = None  # Will handle gracefully


def collect_repo_details(repo_path: Path) -> Dict[str, Any]:
    """Collect comprehensive details about a repository.
    
    Returns a structured JSON with all relevant information for AI analysis.
    """
    details = {
        "metadata": _collect_metadata(repo_path),
        "structure": _collect_structure(repo_path),
        "dependencies": _collect_dependencies(repo_path),
        "tools": _collect_tools(repo_path),
        "configuration": _collect_configuration(repo_path),
        "code_quality": _collect_code_quality(repo_path),
        "documentation": _collect_documentation(repo_path),
        "testing": _collect_testing_info(repo_path),
        "ci_cd": _collect_ci_cd_info(repo_path),
    }
    
    return details


def _collect_metadata(repo_path: Path) -> Dict[str, Any]:
    """Collect repository metadata."""
    metadata = {
        "name": repo_path.name,
        "path": str(repo_path),
        "has_readme": False,
        "has_license": False,
        "license_type": None,
        "description": None,
        "author": None,
        "version": None,
        "python_version": None,
    }
    
    # Check README
    for readme in ["README.md", "README.rst", "README.txt"]:
        if (repo_path / readme).exists():
            metadata["has_readme"] = True
            break
    
    # Check LICENSE
    for license_file in ["LICENSE", "LICENSE.txt", "LICENSE.md"]:
        license_path = repo_path / license_file
        if license_path.exists():
            metadata["has_license"] = True
            try:
                content = license_path.read_text(encoding='utf-8')[:200].lower()
                if "mit" in content:
                    metadata["license_type"] = "MIT"
                elif "apache" in content:
                    metadata["license_type"] = "Apache-2.0"
                elif "gpl" in content:
                    metadata["license_type"] = "GPL"
                elif "bsd" in content:
                    metadata["license_type"] = "BSD"
            except Exception:
                pass
            break
    
    # Extract from pyproject.toml
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists() and tomllib:
        try:
            content = pyproject_file.read_text(encoding='utf-8')
            data = tomllib.loads(content)
            
            project = data.get("project", {})
            metadata["description"] = project.get("description")
            metadata["version"] = project.get("version")
            
            authors = project.get("authors", [])
            if authors:
                metadata["author"] = authors[0].get("name") if isinstance(authors[0], dict) else str(authors[0])
            
            requires_python = project.get("requires-python")
            if requires_python:
                metadata["python_version"] = requires_python
        except Exception:
            pass
    
    return metadata


def _collect_structure(repo_path: Path) -> Dict[str, Any]:
    """Collect repository structure information."""
    structure = {
        "directories": [],
        "file_counts": {
            "python": 0,
            "markdown": 0,
            "yaml": 0,
            "json": 0,
            "toml": 0,
            "other": 0,
        },
        "has_src_layout": False,
        "has_tests_dir": False,
        "has_docs_dir": False,
        "main_package": None,
    }
    
    # Find main directories
    for item in repo_path.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            structure["directories"].append(item.name)
            
            if item.name == "src":
                structure["has_src_layout"] = True
            elif item.name in ["tests", "test"]:
                structure["has_tests_dir"] = True
            elif item.name in ["docs", "documentation"]:
                structure["has_docs_dir"] = True
    
    # Count files by type
    for py_file in repo_path.rglob("*.py"):
        if "__pycache__" not in str(py_file):
            structure["file_counts"]["python"] += 1
    
    for md_file in repo_path.rglob("*.md"):
        structure["file_counts"]["markdown"] += 1
    
    for yaml_file in repo_path.rglob("*.yml"):
        structure["file_counts"]["yaml"] += 1
    for yaml_file in repo_path.rglob("*.yaml"):
        structure["file_counts"]["yaml"] += 1
    
    for json_file in repo_path.rglob("*.json"):
        structure["file_counts"]["json"] += 1
    
    for toml_file in repo_path.rglob("*.toml"):
        structure["file_counts"]["toml"] += 1
    
    # Find main package
    if structure["has_src_layout"]:
        src_dir = repo_path / "src"
        for item in src_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                structure["main_package"] = item.name
                break
    else:
        for item in repo_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and (item / "__init__.py").exists():
                structure["main_package"] = item.name
                break
    
    return structure


def _collect_dependencies(repo_path: Path) -> Dict[str, Any]:
    """Collect dependency information."""
    deps = {
        "fastmcp_version": None,
        "python_dependencies": [],
        "dev_dependencies": [],
        "has_requirements_txt": False,
        "has_pyproject_toml": False,
        "total_dependencies": 0,
    }
    
    # Check requirements.txt
    req_file = repo_path / "requirements.txt"
    if req_file.exists():
        deps["has_requirements_txt"] = True
        try:
            content = req_file.read_text(encoding='utf-8')
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith('#'):
                    # Extract package name (before ==, >=, etc.)
                    pkg = re.split(r'[>=<!=]', line)[0].strip()
                    if pkg:
                        deps["python_dependencies"].append(pkg)
                        if "fastmcp" in pkg.lower():
                            version_match = re.search(r'fastmcp.*?(\d+\.\d+\.?\d*)', line, re.IGNORECASE)
                            if version_match:
                                deps["fastmcp_version"] = version_match.group(1)
        except Exception:
            pass
    
    # Check pyproject.toml
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists() and tomllib:
        deps["has_pyproject_toml"] = True
        try:
            content = pyproject_file.read_text(encoding='utf-8')
            data = tomllib.loads(content)
            
            project = data.get("project", {})
            dependencies = project.get("dependencies", [])
            for dep in dependencies:
                if isinstance(dep, str):
                    pkg = re.split(r'[>=<!=]', dep)[0].strip()
                    if pkg:
                        deps["python_dependencies"].append(pkg)
                        if "fastmcp" in pkg.lower() and not deps["fastmcp_version"]:
                            version_match = re.search(r'fastmcp.*?(\d+\.\d+\.?\d*)', dep, re.IGNORECASE)
                            if version_match:
                                deps["fastmcp_version"] = version_match.group(1)
            
            # Check dev dependencies
            optional_deps = project.get("optional-dependencies", {})
            dev_deps = optional_deps.get("dev", [])
            for dep in dev_deps:
                if isinstance(dep, str):
                    pkg = re.split(r'[>=<!=]', dep)[0].strip()
                    if pkg:
                        deps["dev_dependencies"].append(pkg)
        except Exception:
            pass
    
    # Remove duplicates and sort
    deps["python_dependencies"] = sorted(list(set(deps["python_dependencies"])))
    deps["dev_dependencies"] = sorted(list(set(deps["dev_dependencies"])))
    deps["total_dependencies"] = len(deps["python_dependencies"]) + len(deps["dev_dependencies"])
    
    return deps


def _collect_tools(repo_path: Path) -> Dict[str, Any]:
    """Collect detailed tool information."""
    tools_info = {
        "total_count": 0,
        "tools": [],
        "has_help_tool": False,
        "has_status_tool": False,
        "tool_files": [],
        "portmanteau_tools": [],
    }
    
    tool_patterns = [
        (r'@app\.tool\(\)', "fastmcp"),
        (r'@mcp\.tool\(\)', "mcp"),
        (r'@tool\(', "generic"),
    ]
    
    src_dirs = [repo_path / "src", repo_path]
    
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        
        for py_file in src_dir.rglob("*.py"):
            if "test" in str(py_file).lower() or "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                file_tools = []
                
                # Find all tool definitions
                for pattern, tool_type in tool_patterns:
                    matches = list(re.finditer(pattern, content))
                    for match in matches:
                        # Find the function definition after the decorator
                        func_match = re.search(
                            r'(?:async\s+)?def\s+(\w+)\s*\([^)]*\)',
                            content[match.end():match.end()+500]
                        )
                        if func_match:
                            func_name = func_match.group(1)
                            
                            # Extract docstring
                            docstring = _extract_docstring(content, match.end())
                            
                            # Check if it's help or status
                            if func_name.lower() == "help":
                                tools_info["has_help_tool"] = True
                            elif func_name.lower() == "status":
                                tools_info["has_status_tool"] = True
                            
                            tool_info = {
                                "name": func_name,
                                "type": tool_type,
                                "file": str(py_file.relative_to(repo_path)),
                                "has_docstring": bool(docstring),
                                "docstring_preview": docstring[:200] if docstring else None,
                            }
                            
                            file_tools.append(tool_info)
                            tools_info["total_count"] += 1
                
                if file_tools:
                    if str(py_file.relative_to(repo_path)) not in tools_info["tool_files"]:
                        tools_info["tool_files"].append(str(py_file.relative_to(repo_path)))
                    tools_info["tools"].extend(file_tools)
            
            except Exception:
                pass
    
    # Check for portmanteau tools
    portmanteau_paths = [
        repo_path / "src" / repo_path.name.replace('-', '_') / "tools" / "portmanteau",
        repo_path / "src" / repo_path.name.replace('-', '_') / "portmanteau",
        repo_path / repo_path.name.replace('-', '_') / "portmanteau",
        repo_path / "portmanteau",
    ]
    
    for p in portmanteau_paths:
        if p.exists():
            for py_file in p.glob("*.py"):
                tools_info["portmanteau_tools"].append(str(py_file.relative_to(repo_path)))
            break
    
    return tools_info


def _extract_docstring(content: str, start_pos: int) -> Optional[str]:
    """Extract docstring from function definition."""
    # Look for triple-quoted docstring after function def
    docstring_pattern = r'"""([^"]*(?:"""[^"]*)*)"""'
    match = re.search(docstring_pattern, content[start_pos:start_pos+2000])
    if match:
        return match.group(1).strip()
    
    # Try single quotes
    docstring_pattern = r"'''([^']*(?:'''[^']*)*)'''"
    match = re.search(docstring_pattern, content[start_pos:start_pos+2000])
    if match:
        return match.group(1).strip()
    
    return None


def _collect_configuration(repo_path: Path) -> Dict[str, Any]:
    """Collect configuration file information."""
    config = {
        "files": [],
        "has_ruff_config": False,
        "has_pytest_config": False,
        "has_coverage_config": False,
        "has_black_config": False,
        "has_mypy_config": False,
    }
    
    config_files = [
        "pyproject.toml",
        "ruff.toml",
        ".ruff.toml",
        "pytest.ini",
        ".coveragerc",
        "setup.cfg",
        "tox.ini",
        ".pre-commit-config.yaml",
    ]
    
    for config_file in config_files:
        config_path = repo_path / config_file
        if config_path.exists():
            config["files"].append(config_file)
            
            if "ruff" in config_file:
                config["has_ruff_config"] = True
            elif "pytest" in config_file:
                config["has_pytest_config"] = True
            elif "coverage" in config_file:
                config["has_coverage_config"] = True
    
    # Check pyproject.toml for tool configs
    pyproject_file = repo_path / "pyproject.toml"
    if pyproject_file.exists():
        try:
            content = pyproject_file.read_text(encoding='utf-8')
            if '[tool.ruff]' in content:
                config["has_ruff_config"] = True
            if '[tool.pytest' in content:
                config["has_pytest_config"] = True
            if '[tool.coverage' in content:
                config["has_coverage_config"] = True
            if '[tool.black]' in content:
                config["has_black_config"] = True
            if '[tool.mypy]' in content:
                config["has_mypy_config"] = True
        except Exception:
            pass
    
    return config


def _collect_code_quality(repo_path: Path) -> Dict[str, Any]:
    """Collect code quality metrics."""
    quality = {
        "has_logging": False,
        "logging_type": None,  # "logging" or "structlog"
        "print_statements": 0,
        "bare_excepts": 0,
        "lazy_errors": 0,
        "type_hints_usage": 0,  # Files with type hints
        "total_python_files": 0,
    }
    
    LOGGING_PATTERNS = [
        (r'import\s+logging', "logging"),
        (r'import\s+structlog', "structlog"),
        (r'from\s+logging\s+import', "logging"),
        (r'from\s+structlog\s+import', "structlog"),
    ]
    
    BAD_PATTERNS = [
        (r'^\s*print\s*\(', "print"),
        (r'except\s*:', "bare_except"),
        (r'except\s+Exception\s*:', "bare_except"),
    ]
    
    src_dirs = [repo_path / "src", repo_path]
    
    for src_dir in src_dirs:
        if not src_dir.exists():
            continue
        
        for py_file in src_dir.rglob("*.py"):
            if "test" in str(py_file).lower() or "__pycache__" in str(py_file):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8')
                quality["total_python_files"] += 1
                
                # Check logging
                for pattern, log_type in LOGGING_PATTERNS:
                    if re.search(pattern, content):
                        quality["has_logging"] = True
                        if not quality["logging_type"]:
                            quality["logging_type"] = log_type
                
                # Check for type hints
                if re.search(r':\s*\w+(\[.*?\])?\s*=', content) or re.search(r'->\s*\w+', content):
                    quality["type_hints_usage"] += 1
                
                # Check bad patterns
                is_test = "test" in str(py_file).lower()
                for pattern, pattern_type in BAD_PATTERNS:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    if pattern_type == "print" and not is_test:
                        quality["print_statements"] += len(matches)
                    elif pattern_type == "bare_except":
                        quality["bare_excepts"] += len(matches)
            
            except Exception:
                pass
    
    return quality


def _collect_documentation(repo_path: Path) -> Dict[str, Any]:
    """Collect documentation information."""
    docs = {
        "has_readme": False,
        "has_changelog": False,
        "has_contributing": False,
        "has_license": False,
        "doc_files": [],
        "readme_preview": None,
    }
    
    # Check common doc files
    doc_files = [
        "README.md",
        "README.rst",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "LICENSE",
    ]
    
    for doc_file in doc_files:
        doc_path = repo_path / doc_file
        if doc_path.exists():
            docs["doc_files"].append(doc_file)
            
            if "README" in doc_file:
                docs["has_readme"] = True
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    docs["readme_preview"] = content[:500]  # First 500 chars
                except Exception:
                    pass
            elif "CHANGELOG" in doc_file:
                docs["has_changelog"] = True
            elif "CONTRIBUTING" in doc_file:
                docs["has_contributing"] = True
            elif "LICENSE" in doc_file:
                docs["has_license"] = True
    
    # Check docs directory
    docs_dir = repo_path / "docs"
    if docs_dir.exists():
        for doc_file in docs_dir.rglob("*.md"):
            docs["doc_files"].append(str(doc_file.relative_to(repo_path)))
    
    return docs


def _collect_testing_info(repo_path: Path) -> Dict[str, Any]:
    """Collect testing information."""
    testing = {
        "has_tests": False,
        "test_directory": None,
        "test_file_count": 0,
        "has_unit_tests": False,
        "has_integration_tests": False,
        "test_framework": None,  # "pytest", "unittest", etc.
        "has_test_config": False,
    }
    
    test_dirs = ["tests", "test"]
    
    for test_dir_name in test_dirs:
        test_dir = repo_path / test_dir_name
        if test_dir.exists():
            testing["has_tests"] = True
            testing["test_directory"] = test_dir_name
            
            # Count test files
            test_files = list(test_dir.rglob("test_*.py")) + list(test_dir.rglob("*_test.py"))
            testing["test_file_count"] = len(test_files)
            
            # Check for unit tests
            unit_dir = test_dir / "unit"
            if unit_dir.exists() and any(unit_dir.glob("test_*.py")):
                testing["has_unit_tests"] = True
            
            # Check for integration tests
            integration_dir = test_dir / "integration"
            if integration_dir.exists() and any(integration_dir.glob("test_*.py")):
                testing["has_integration_tests"] = True
            
            # Detect test framework
            if test_files:
                try:
                    sample_file = test_files[0]
                    content = sample_file.read_text(encoding='utf-8')
                    if "import pytest" in content or "from pytest" in content:
                        testing["test_framework"] = "pytest"
                    elif "import unittest" in content:
                        testing["test_framework"] = "unittest"
                except Exception:
                    pass
            
            break
    
    # Check for pytest config
    if (repo_path / "pytest.ini").exists() or (repo_path / "pyproject.toml").exists():
        try:
            pyproject_content = (repo_path / "pyproject.toml").read_text(encoding='utf-8')
            if '[tool.pytest' in pyproject_content:
                testing["has_test_config"] = True
        except Exception:
            pass
    
    return testing


def _collect_ci_cd_info(repo_path: Path) -> Dict[str, Any]:
    """Collect CI/CD information."""
    ci_cd = {
        "has_ci": False,
        "ci_provider": None,  # "github", "gitlab", etc.
        "workflow_count": 0,
        "workflows": [],
        "has_ruff_in_ci": False,
        "has_pytest_in_ci": False,
    }
    
    # Check GitHub Actions
    github_workflows = repo_path / ".github" / "workflows"
    if github_workflows.exists():
        ci_cd["has_ci"] = True
        ci_cd["ci_provider"] = "github"
        
        workflow_files = list(github_workflows.glob("*.yml")) + list(github_workflows.glob("*.yaml"))
        ci_cd["workflow_count"] = len(workflow_files)
        
        for workflow_file in workflow_files:
            workflow_name = workflow_file.name
            ci_cd["workflows"].append(workflow_name)
            
            try:
                content = workflow_file.read_text(encoding='utf-8').lower()
                if "ruff" in content:
                    ci_cd["has_ruff_in_ci"] = True
                if "pytest" in content:
                    ci_cd["has_pytest_in_ci"] = True
            except Exception:
                pass
    
    # Check GitLab CI
    gitlab_ci = repo_path / ".gitlab-ci.yml"
    if gitlab_ci.exists():
        ci_cd["has_ci"] = True
        ci_cd["ci_provider"] = "gitlab"
        ci_cd["workflow_count"] = 1
        ci_cd["workflows"].append(".gitlab-ci.yml")
    
    return ci_cd
