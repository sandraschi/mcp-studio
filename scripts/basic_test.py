"""
Simple test runner that doesn't require external dependencies
"""
import sys
import os
from pathlib import Path

def basic_test():
    """Run basic tests without external dependencies."""
    project_root = Path(__file__).parent
    
    print("🧪 Basic MCP Studio Environment Test")
    print(f"📁 Project: {project_root}")
    print(f"🐍 Python: {sys.executable}")
    print(f"📦 Python version: {sys.version}")
    
    # Test file structure
    print("\n📁 Testing file structure...")
    
    required_files = [
        "src/mcp_studio/main.py",
        "src/mcp_studio/app/core/config.py", 
        "pyproject.toml",
        "mcp_config_parser.py"
    ]
    
    all_files_exist = True
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            all_files_exist = False
    
    # Test our config parser
    print("\n📋 Testing MCP config parser...")
    try:
        sys.path.insert(0, str(project_root))
        
        # Test basic config discovery
        appdata = os.environ.get('APPDATA', '')
        claude_config = Path(appdata) / "Claude" / "claude_desktop_config.json"
        
        if claude_config.exists():
            print(f"   ✅ Claude config found: {claude_config}")
            
            # Try to parse it
            import json
            with open(claude_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            mcp_servers = config.get('mcpServers', {})
            print(f"   ✅ Found {len(mcp_servers)} MCP servers in Claude config")
            
            # List a few
            for i, (server_id, _) in enumerate(mcp_servers.items()):
                if i < 3:  # Show first 3
                    print(f"      - {server_id}")
                elif i == 3:
                    print(f"      - ... and {len(mcp_servers) - 3} more")
                    break
        else:
            print(f"   ⚠️  Claude config not found at: {claude_config}")
            
    except Exception as e:
        print(f"   ❌ Config parser test failed: {e}")
        return False
    
    # Test Python environment
    print("\n🐍 Testing Python environment...")
    
    # Check if we're in a venv
    venv_path = project_root / "venv"
    if venv_path.exists():
        print(f"   ✅ Virtual environment found: {venv_path}")
    else:
        print(f"   ⚠️  No virtual environment found - run setup_dev.bat")
    
    # Test basic imports
    print("\n📦 Testing basic imports...")
    basic_modules = ['json', 'pathlib', 'os', 'sys']
    for module in basic_modules:
        try:
            __import__(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module}")
            
    print("\n" + "="*50)
    if all_files_exist:
        print("✅ Basic structure test PASSED")
        print("🚀 Ready for dependency installation")
        print("\n📋 Next steps:")
        print("   1. Run setup_dev.bat to install dependencies")
        print("   2. Test with: python test_setup.py")
        print("   3. Start server: python -m uvicorn src.mcp_studio.main:app --reload")
    else:
        print("❌ Basic structure test FAILED") 
        print("🔧 Some files are missing - check the project structure")
    print("="*50)
    
    return all_files_exist

if __name__ == "__main__":
    success = basic_test()
    input("\nPress Enter to continue...")
    sys.exit(0 if success else 1)
