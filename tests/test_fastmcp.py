#!/usr/bin/env python3
"""Test fastmcp imports to identify what's available."""

import sys
from pathlib import Path

def test_fastmcp_imports():
    """Test various fastmcp imports to see what's available."""
    print("Testing fastmcp imports...")

    try:
        import fastmcp
        print(f"✅ fastmcp imported successfully")
        print(f"   Version: {getattr(fastmcp, '__version__', 'unknown')}")
        print(f"   Available attributes: {dir(fastmcp)}")
    except ImportError as e:
        print(f"❌ Cannot import fastmcp: {e}")
        return False

    # Test FastMCP class
    try:
        from fastmcp import FastMCP
        print("✅ FastMCP class available")
    except ImportError as e:
        print(f"❌ Cannot import FastMCP: {e}")

    # Test MCPClient class
    try:
        from fastmcp import MCPClient
        print("✅ MCPClient class available")
    except ImportError as e:
        print(f"❌ Cannot import MCPClient: {e}")
        print("   This might not be available in this version of fastmcp")

    # Test other common MCP classes
    try:
        from fastmcp import MCPServer
        print("✅ MCPServer class available")
    except ImportError as e:
        print(f"❌ Cannot import MCPServer: {e}")

    # Test tool decorators
    try:
        from fastmcp import tool
        print("✅ @tool decorator available")
    except ImportError as e:
        print(f"❌ Cannot import @tool decorator: {e}")

    print("\nAll available exports from fastmcp:")
    try:
        import fastmcp
        exports = [name for name in dir(fastmcp) if not name.startswith('_')]
        for export in sorted(exports):
            print(f"   - {export}")
    except Exception as e:
        print(f"   Error listing exports: {e}")

    return True

if __name__ == "__main__":
    test_fastmcp_imports()
