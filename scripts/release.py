#!/usr/bin/env python3
"""
Release script for MCP Studio.

This script automates the process of creating a new release:
1. Bumps the version
2. Updates the changelog
3. Creates a git tag
4. Builds the package
5. Publishes to PyPI
6. Creates a GitHub release
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

def run_command(cmd: list[str], cwd: Optional[Path] = None) -> str:
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or Path.cwd(),
            check=True,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(cmd)}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def get_current_version() -> str:
    """Get the current version from pyproject.toml."""
    pyproject = Path("pyproject.toml").read_text()
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', pyproject)
    if not match:
        raise ValueError("Could not find version in pyproject.toml")
    return match.group(1)

def bump_version(part: str = "patch") -> str:
    """Bump the version number."""
    current = get_current_version()
    major, minor, patch = map(int, current.split("."))
    
    if part == "major":
        new_version = f"{major + 1}.0.0"
    elif part == "minor":
        new_version = f"{major}.{minor + 1}.0"
    else:  # patch
        new_version = f"{major}.{minor}.{patch + 1}"
    
    # Update pyproject.toml
    pyproject = Path("pyproject.toml").read_text()
    pyproject = re.sub(
        r'(version\s*=\s*["\'])[^"\']+(["\'])',
        f'\\g<1>{new_version}\\g<2>',
        pyproject
    )
    Path("pyproject.toml").write_text(pyproject)
    
    # Also update setup.py if it exists
    if Path("setup.py").exists():
        setup_py = Path("setup.py").read_text()
        setup_py = re.sub(
            r'(version\s*=\s*["\'])[^"\']+(["\'])',
            f'\\g<1>{new_version}\\g<2>',
            setup_py
        )
        Path("setup.py").write_text(setup_py)
    
    return new_version

def update_changelog(version: str) -> None:
    """Update the changelog with the new version."""
    changelog = Path("CHANGELOG.md")
    if not changelog.exists():
        changelog.write_text("# Changelog\n\n")
    
    current_changelog = changelog.read_text()
    new_changelog = f"# Changelog\n\n## [{version}] - {run_command(['date', '+%Y-%m-%d'])} - Unreleased\n\n### Added\n- Initial release\n\n{current_changelog.split('# Changelog', 1)[1].lstrip()}"
    
    changelog.write_text(new_changelog)

def create_release(version: str) -> None:
    """Create a new release."""
    # Update version and changelog
    update_changelog(version)
    
    # Commit changes
    run_command(["git", "add", "pyproject.toml", "setup.py", "CHANGELOG.md"])
    run_command(["git", "commit", "-m", f"chore: bump version to {version}"])
    
    # Create tag
    run_command(["git", "tag", f"v{version}"])
    
    # Push changes and tags
    run_command(["git", "push"])
    run_command(["git", "push", "--tags"])
    
    # Build and publish
    run_command(["python", "-m", "build"])
    run_command(["twine", "upload", "dist/*"])
    
    print(f"\n🎉 Successfully released version {version}!")
    print(f"🔗 https://github.com/sandraschi/mcp-studio/releases/tag/v{version}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Release script for MCP Studio")
    parser.add_argument(
        "part",
        nargs="?",
        default="patch",
        choices={"major", "minor", "patch"},
        help="Part of version to bump (default: %(default)s)",
    )
    
    args = parser.parse_args()
    new_version = bump_version(args.part)
    create_release(new_version)
