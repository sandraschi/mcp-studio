#!/usr/bin/env python3
"""
MCP Studio Development Environment Setup
Handles venv creation, dependency installation, and basic config
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return success status."""
    try:
        print(f"🔧 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        if result.stdout.strip():
            print(f"   ✅ {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e.stderr.strip()}")
        return False

def setup_mcp_studio():
    """Setup MCP Studio development environment."""
    project_root = Path(__file__).parent
    venv_path = project_root / "venv"
    
    print("🚀 Setting up MCP Studio development environment...")
    print(f"📁 Project root: {project_root}")
    
    # Create virtual environment
    if not venv_path.exists():
        print("\n📦 Creating virtual environment...")
        if not run_command([sys.executable, "-m", "venv", "venv"], cwd=project_root):
            print("❌ Failed to create virtual environment")
            return False
    else:
        print("\n📦 Virtual environment already exists")
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = venv_path / "Scripts" / "pip.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Linux/Mac
        pip_path = venv_path / "bin" / "pip"
        python_path = venv_path / "bin" / "python"
    
    print(f"🐍 Using Python: {python_path}")
    print(f"📦 Using pip: {pip_path}")
    
    # Upgrade pip
    print("\n⬆️  Upgrading pip...")
    if not run_command([str(python_path), "-m", "pip", "install", "--upgrade", "pip"], cwd=project_root):
        print("❌ Failed to upgrade pip")
        return False
    
    # Install main dependencies
    print("\n📚 Installing dependencies...")
    deps = [
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0", 
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "fastmcp>=2.11.0",
        "structlog>=23.0.0",
        "aiofiles>=23.0.0",
        "watchdog>=3.0.0",
        "python-multipart>=0.0.6",
        "jinja2>=3.0.0",
        "aiohttp>=3.9.0"
    ]
    
    for dep in deps:
        print(f"   Installing {dep}...")
        if not run_command([str(pip_path), "install", dep], cwd=project_root):
            print(f"❌ Failed to install {dep}")
            return False
    
    # Install development dependencies
    print("\n🛠️  Installing development dependencies...")
    dev_deps = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0", 
        "black>=23.0.0",
        "isort>=5.12.0"
    ]
    
    for dep in dev_deps:
        print(f"   Installing {dep}...")
        if not run_command([str(pip_path), "install", dep], cwd=project_root):
            print(f"⚠️  Warning: Failed to install {dep} (non-critical)")
    
    # Create basic .env file
    env_file = project_root / ".env"
    if not env_file.exists():
        print("\n⚙️  Creating .env file...")
        with open(env_file, 'w') as f:
            f.write("""# MCP Studio Environment Configuration
DEBUG=true
LOG_LEVEL=INFO
HOST=127.0.0.1
PORT=8000
""")
        print("   ✅ .env file created")
    else:
        print("\n⚙️  .env file already exists")
    
    # Test the installation
    print("\n🧪 Testing installation...")
    test_cmd = [str(python_path), "-c", "import fastapi, fastmcp, structlog; print('All imports successful!')"]
    if run_command(test_cmd, cwd=project_root):
        print("✅ Installation test passed!")
    else:
        print("❌ Installation test failed")
        return False
    
    # Show next steps
    print("\n" + "="*50)
    print("🎉 MCP Studio development environment ready!")
    print("="*50)
    print(f"📁 Project: {project_root}")
    print(f"🐍 Python: {python_path}")
    print(f"📦 Pip: {pip_path}")
    print("\n🚀 To run the development server:")
    print(f"   cd {project_root}")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python -m uvicorn src.mcp_studio.main:app --reload")
    print("\n🌐 Then visit: http://localhost:8000")
    
    return True

if __name__ == "__main__":
    success = setup_mcp_studio()
    sys.exit(0 if success else 1)
