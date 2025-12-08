#!/usr/bin/env python3
"""
Update README installation instructions across all MCP repos in d:/dev/repos

Standardizes installation sections following priority:
1. MCPB (drop into Claude Desktop settings)
2. npm/npx (if available)
3. Clone repo and add JSON snippet (with client-specific hints)
4. Python setup (last resort)
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional, List

REPOS_DIR = Path(r"D:\Dev\repos")

def detect_installation_methods(repo_path: Path) -> Dict[str, any]:
    """Detect available installation methods for an MCP server."""
    methods = {
        "mcpb": False,
        "npm": False,
        "npx": False,
        "python": True,  # Always available as fallback
        "mcpb_path": None,
        "npm_package": None,
        "npx_command": None,
        "pyproject_entrypoint": None
    }
    
    # Check for MCPB (manifest.json)
    manifest_path = repo_path / "manifest.json"
    if manifest_path.exists():
        methods["mcpb"] = True
        methods["mcpb_path"] = str(manifest_path)
    
    # Check for npm/npx setup (package.json)
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json, 'r', encoding='utf-8') as f:
                pkg = json.load(f)
            
            # Check for bin field (npx support)
            if "bin" in pkg:
                methods["npx"] = True
                if isinstance(pkg["bin"], dict):
                    methods["npx_command"] = list(pkg["bin"].keys())[0]
                elif isinstance(pkg["bin"], str):
                    methods["npx_command"] = pkg.get("name", repo_path.name)
            
            # Check for name field (npm package)
            if "name" in pkg:
                methods["npm"] = True
                methods["npm_package"] = pkg["name"]
        except Exception:
            pass
    
    # Check for pyproject.toml entrypoint
    pyproject = repo_path / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            # Look for [project.scripts] or [tool.poetry.scripts]
            if "[project.scripts]" in content or "[tool.poetry.scripts]" in content:
                methods["pyproject_entrypoint"] = True
        except Exception:
            pass
    
    return methods

def parse_pyproject_entrypoint(repo_path: Path) -> Optional[Dict]:
    """Parse pyproject.toml to find the MCP server entrypoint."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return None
    
    try:
        content = pyproject.read_text()
        
        # Look for [project.scripts] section
        if "[project.scripts]" in content:
            match = re.search(r'\[project\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if match:
                script_name, entry = match.groups()
                if ":" in entry:
                    module_path = entry.split(":")[0]
                    return {
                        "command": "python",
                        "args": ["-m", module_path],
                        "cwd": str(repo_path),
                        "env": {"PYTHONPATH": str(repo_path / "src")} if (repo_path / "src").exists() else {}
                    }
        
        # Look for [tool.poetry.scripts]
        if "[tool.poetry.scripts]" in content:
            match = re.search(r'\[tool\.poetry\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if match:
                script_name, entry = match.groups()
                if ":" in entry:
                    module_path = entry.split(":")[0]
                    return {
                        "command": "python",
                        "args": ["-m", module_path],
                        "cwd": str(repo_path),
                        "env": {"PYTHONPATH": str(repo_path / "src")} if (repo_path / "src").exists() else {}
                    }
    except Exception:
        pass
    
    return None

def infer_python_config(repo_path: Path) -> Optional[Dict]:
    """Infer Python config from repo structure."""
    server_files = [
        repo_path / "fastmcp_server.py",
        repo_path / "mcp_server.py",
        repo_path / "server.py",
        repo_path / "main.py"
    ]
    
    for server_file in server_files:
        if server_file.exists():
            if (repo_path / "src").exists():
                pkg_name = repo_path.name.replace("-", "_")
                return {
                    "command": "python",
                    "args": ["-m", pkg_name],
                    "cwd": str(repo_path),
                    "env": {"PYTHONPATH": str(repo_path / "src")}
                }
            else:
                return {
                    "command": "python",
                    "args": [str(server_file.relative_to(repo_path))],
                    "cwd": str(repo_path),
                    "env": {}
                }
    return None

def generate_json_snippet(server_id: str, config: Dict) -> str:
    """Generate JSON snippet for MCP config."""
    snippet = {
        "command": config["command"],
        "args": config["args"]
    }
    if config.get("cwd"):
        snippet["cwd"] = config["cwd"]
    if config.get("env"):
        snippet["env"] = config["env"]
    
    return json.dumps({server_id: snippet}, indent=2)

def generate_installation_section(repo_path: Path, repo_name: str) -> str:
    """Generate standardized installation section."""
    methods = detect_installation_methods(repo_path)
    
    # Determine Python config
    python_config = parse_pyproject_entrypoint(repo_path) or infer_python_config(repo_path)
    if not python_config:
        python_config = {
            "command": "python",
            "args": ["-m", repo_name.replace("-", "_")],
            "cwd": str(repo_path),
            "env": {}
        }
    
    server_id = repo_name.replace("_", "-").lower()
    json_snippet = generate_json_snippet(server_id, python_config)
    
    sections = []
    sections.append("## Installation\n")
    
    # Method 1: MCPB
    if methods["mcpb"]:
        sections.append("### Method 1: MCPB (Recommended)\n")
        sections.append("1. Open **Claude Desktop**\n")
        sections.append("2. Go to **Settings → Developer → Add MCP Server**\n")
        sections.append(f"3. Paste the path to `manifest.json` or drag & drop the file:\n")
        sections.append(f"   ```\n   {methods['mcpb_path']}\n   ```\n")
        sections.append("\n")
    
    # Method 2: npm/npx
    if methods["npx"]:
        sections.append("### Method 2: npm/npx\n")
        sections.append("```bash\n")
        if methods["npx_command"]:
            sections.append(f"npx -y {methods['npx_command']}\n")
        else:
            sections.append(f"npx -y {methods['npm_package'] or repo_name}\n")
        sections.append("```\n")
        sections.append("\n")
        sections.append("Then add to your MCP client config (see Method 3 for config locations).\n")
        sections.append("\n")
    elif methods["npm"]:
        sections.append("### Method 2: npm\n")
        sections.append("```bash\n")
        sections.append(f"npm install -g {methods['npm_package']}\n")
        sections.append("```\n")
        sections.append("\n")
        sections.append("Then add to your MCP client config (see Method 3 for config locations).\n")
        sections.append("\n")
    
    # Method 3: Clone and JSON snippet
    method_num = 3 if (methods["mcpb"] or methods["npm"] or methods["npx"]) else 1
    sections.append(f"### Method {method_num}: Clone Repository and Add JSON Snippet\n")
    sections.append("1. Clone this repository:\n")
    sections.append("   ```bash\n")
    sections.append(f"   git clone <repository-url> {repo_name}\n")
    sections.append(f"   cd {repo_name}\n")
    sections.append("   ```\n")
    sections.append("\n")
    sections.append("2. Add the following to your MCP client configuration:\n")
    sections.append("\n")
    sections.append("   **Claude Desktop** (`%APPDATA%\\Claude\\claude_desktop_config.json` on Windows, `~/.config/Claude/claude_desktop_config.json` on Linux/Mac):\n")
    sections.append("   ```json\n")
    sections.append("   {\n")
    sections.append('     "mcpServers": {\n')
    # Indent the snippet
    snippet_lines = json_snippet.split('\n')
    for line in snippet_lines:
        if line.strip():  # Skip empty lines
            sections.append(f"       {line}\n")
    sections.append("     }\n")
    sections.append("   }\n")
    sections.append("   ```\n")
    sections.append("\n")
    sections.append("   **Cursor** (`~/.cursor/mcp.json` or `%APPDATA%\\Cursor\\User\\globalStorage\\...\\cline_mcp_settings.json`):\n")
    sections.append("   ```json\n")
    sections.append("   {\n")
    sections.append('     "mcpServers": {\n')
    for line in snippet_lines:
        sections.append(f"       {line}\n")
    sections.append("     }\n")
    sections.append("   }\n")
    sections.append("   ```\n")
    sections.append("\n")
    sections.append("   **Windsurf IDE** (`%APPDATA%\\Codeium\\Windsurf\\mcp_config.json`):\n")
    sections.append("   ```json\n")
    sections.append("   {\n")
    sections.append('     "mcpServers": {\n')
    for line in snippet_lines:
        sections.append(f"       {line}\n")
    sections.append("     }\n")
    sections.append("   }\n")
    sections.append("   ```\n")
    sections.append("\n")
    sections.append("   **Zed Editor** (`~/.config/zed/settings.json` or `~/Library/Application Support/Zed/settings.json` on Mac):\n")
    sections.append("   ```json\n")
    sections.append("   {\n")
    sections.append('     "mcpServers": {\n')
    for line in snippet_lines:
        sections.append(f"       {line}\n")
    sections.append("     }\n")
    sections.append("   }\n")
    sections.append("   ```\n")
    sections.append("\n")
    sections.append("   **Antigravity IDE** (`%APPDATA%\\Antigravity\\mcp_config.json`):\n")
    sections.append("   ```json\n")
    sections.append("   {\n")
    sections.append('     "mcpServers": {\n')
    for line in snippet_lines:
        sections.append(f"       {line}\n")
    sections.append("     }\n")
    sections.append("   }\n")
    sections.append("   ```\n")
    sections.append("\n")
    
    # Method 4: Python setup (last resort)
    method_num = 4 if (methods["mcpb"] or methods["npm"] or methods["npx"]) else 2
    sections.append(f"### Method {method_num}: Python Setup (Advanced)\n")
    sections.append("\n")
    sections.append("For development or if other methods don't work:\n")
    sections.append("\n")
    sections.append("```bash\n")
    sections.append(f"cd {repo_name}\n")
    sections.append("pip install -e .\n")
    sections.append("```\n")
    sections.append("\n")
    sections.append("Then use the JSON snippet from Method 3 above.\n")
    sections.append("\n")
    
    return "".join(sections)

def update_readme(repo_path: Path, repo_name: str, dry_run: bool = False) -> bool:
    """Update README with standardized installation section."""
    readme_files = [
        repo_path / "README.md",
        repo_path / "README.rst",
        repo_path / "README.txt",
        repo_path / "README"
    ]
    
    readme_path = None
    for readme_file in readme_files:
        if readme_file.exists():
            readme_path = readme_file
            break
    
    if not readme_path:
        # Create README.md if it doesn't exist
        readme_path = repo_path / "README.md"
        if not dry_run:
            readme_path.write_text(f"# {repo_name}\n\n", encoding='utf-8')
        print(f"  📝 Creating {readme_path.name}")
    
    try:
        content = readme_path.read_text(encoding='utf-8', errors='ignore')
    except Exception as e:
        print(f"  ❌ Error reading {readme_path.name}: {e}")
        return False
    
    # Generate new installation section
    new_section = generate_installation_section(repo_path, repo_name)
    
    # Find and replace installation section
    # Look for various patterns
    patterns = [
        r'##\s+Installation\s*\n.*?(?=\n##\s+|\Z)',
        r'##\s+Install\s*\n.*?(?=\n##\s+|\Z)',
        r'##\s+Getting Started\s*\n.*?(?=\n##\s+|\Z)',
        r'##\s+Setup\s*\n.*?(?=\n##\s+|\Z)',
    ]
    
    replaced = False
    for pattern in patterns:
        if re.search(pattern, content, re.DOTALL | re.IGNORECASE):
            content = re.sub(pattern, new_section.rstrip(), content, flags=re.DOTALL | re.IGNORECASE)
            replaced = True
            break
    
    if not replaced:
        # Insert after title or at end
        if re.match(r'^#\s+.*?\n', content):
            # Insert after first heading
            content = re.sub(r'(^#\s+.*?\n)', r'\1\n' + new_section, content, count=1)
        else:
            # Append at end
            content = content.rstrip() + "\n\n" + new_section
    
    if not dry_run:
        readme_path.write_text(content, encoding='utf-8')
        print(f"  ✅ Updated {readme_path.name}")
    else:
        print(f"  🔍 Would update {readme_path.name}")
        print(f"     Preview:\n{new_section[:500]}...")
    
    return True

def main():
    """Main function to update all READMEs."""
    import sys
    
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    
    if not REPOS_DIR.exists():
        print(f"❌ Repos directory not found: {REPOS_DIR}")
        sys.exit(1)
    
    print(f"🔍 Scanning {REPOS_DIR} for MCP repos...")
    print("")
    
    repos = [d for d in REPOS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    print(f"Found {len(repos)} directories to check")
    print("")
    
    updated = 0
    skipped = 0
    errors = 0
    
    for repo_path in sorted(repos):
        repo_name = repo_path.name
        print(f"📦 {repo_name}")
        
        # Check if it's an MCP repo (has fastmcp in requirements or pyproject)
        is_mcp = False
        for config_file in [repo_path / "requirements.txt", repo_path / "pyproject.toml"]:
            if config_file.exists():
                try:
                    content = config_file.read_text(encoding='utf-8', errors='ignore')
                    if "fastmcp" in content.lower():
                        is_mcp = True
                        break
                except Exception as e:
                    print(f"  ⚠️  Error reading {config_file.name}: {e}")
        
        if not is_mcp:
            print(f"  ⏭️  Skipping (not an MCP repo)")
            skipped += 1
            continue
        
        try:
            if update_readme(repo_path, repo_name, dry_run=dry_run):
                updated += 1
            else:
                errors += 1
        except Exception as e:
            import traceback
            print(f"  ❌ Error: {e}")
            if "--verbose" in sys.argv or "-v" in sys.argv:
                traceback.print_exc()
            errors += 1
        
        print("")
    
    print("=" * 60)
    print(f"✅ Updated: {updated}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"❌ Errors: {errors}")
    if dry_run:
        print("\n💡 This was a dry run. Run without --dry-run to apply changes.")

if __name__ == "__main__":
    main()
