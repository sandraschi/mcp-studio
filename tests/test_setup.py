#!/usr/bin/env python3
"""
Test script to verify MCP Studio can start and basic functionality works
"""

import sys
import os
from pathlib import Path

# Add src to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def test_imports():
    """Test that we can import the main modules."""
    try:
        print("🧪 Testing imports...")
        
        # Test FastAPI
        import fastapi
        print(f"   ✅ FastAPI {fastapi.__version__}")
        
        # Test Pydantic  
        import pydantic
        print(f"   ✅ Pydantic {pydantic.__version__}")
        
        # Test other core deps
        import structlog
        print("   ✅ Structlog")
        
        import aiohttp
        print("   ✅ aiohttp")
        
        # Test FastMCP
        try:
            import fastmcp
            print("   ✅ FastMCP")
        except ImportError:
            print("   ⚠️  FastMCP not available (will install later)")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")
        return False

def test_mcp_studio_structure():
    """Test that MCP Studio code structure is accessible."""
    try:
        print("🏗️  Testing MCP Studio structure...")
        
        # Test main app structure
        from mcp_studio import main
        print("   ✅ Main module accessible")
        
        from mcp_studio.app.core import config
        print("   ✅ Config module accessible")
        
        from mcp_studio.app.services import discovery_service
        print("   ✅ Discovery service accessible")
        
        # Test that we can create the FastAPI app (without starting it)
        app = main.app
        print("   ✅ FastAPI app created successfully")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Structure test failed: {e}")
        return False
    except Exception as e:
        print(f"   ❌ App creation failed: {e}")
        return False

def test_config_parser():
    """Test our MCP config parser."""
    try:
        print("📋 Testing MCP config parser...")
        
        # Import our config parser
        sys.path.insert(0, str(project_root))
        from mcp_config_parser import MCPConfigParser
        
        parser = MCPConfigParser()
        print("   ✅ Config parser created")
        
        # Test Claude Desktop config parsing (should work)
        claude_servers = parser.parse_claude_desktop_config()
        print(f"   ✅ Found {len(claude_servers)} Claude servers")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Config parser test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing MCP Studio development environment...")
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python: {sys.executable}")
    print(f"📦 Python path: {sys.path[0]}")
    
    all_passed = True
    
    # Test basic imports
    if not test_imports():
        all_passed = False
    
    print()
    
    # Test MCP Studio structure
    if not test_mcp_studio_structure():
        all_passed = False
        print("   💡 This is expected if dependencies aren't installed yet")
    
    print()
    
    # Test our config parser
    if not test_config_parser():
        all_passed = False
    
    print()
    print("="*50)
    if all_passed:
        print("✅ All tests passed! Environment is ready.")
        print("🚀 Run setup_dev.bat to complete setup if needed")
    else:
        print("⚠️  Some tests failed - run setup_dev.bat to install dependencies")
    print("="*50)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
