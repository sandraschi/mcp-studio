#!/usr/bin/env python3
"""
Import test script for MCP Studio

This script tests all imports to identify missing modules, syntax errors,
and other import-related issues in the MCP Studio codebase.
"""

import sys
import traceback
from pathlib import Path
import pytest

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def _test_import(module_name: str, description: str = "") -> bool:
    """Test importing a module and report results."""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except Exception as e:
        print(f"❌ {module_name} - {description}")
        print(f"   Error: {type(e).__name__}: {e}")
        if "SyntaxError" in str(type(e)):
            print(f"   {traceback.format_exc().splitlines()[-2]}")
        return False

def test_external_dependencies():
    """Test external dependencies can be imported."""
    deps = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("structlog", "Structured logging"),
        ("aiofiles", "Async file operations"),
        ("aiohttp", "Async HTTP client"),
        ("fastmcp", "FastMCP framework"),
        ("psutil", "System utilities"),
        ("watchdog", "File system monitoring"),
    ]
    
    failed_deps = []
    for dep, desc in deps:
        if not _test_import(dep, desc):
            failed_deps.append(dep)
    
    assert len(failed_deps) == 0, f"Failed to import: {', '.join(failed_deps)}"

def test_core_modules():
    """Test core application modules can be imported."""
    core_modules = [
        ("mcp_studio.app.core.config", "Configuration management"),
        ("mcp_studio.app.core.logging", "Logging configuration"),
        ("mcp_studio.app.core.logging_utils", "Logging utilities"),
        ("mcp_studio.app.core.lifespan", "Application lifespan"),
        ("mcp_studio.app.core.enums", "Common enums"),
        ("mcp_studio.app.core.types", "Type definitions"),
        ("mcp_studio.app.core.security", "Security utilities"),
        ("mcp_studio.app.core.websocket", "WebSocket handling"),
    ]
    
    failed_core = []
    for module, desc in core_modules:
        if not _test_import(module, desc):
            failed_core.append(module)
    
    assert len(failed_core) == 0, f"Failed to import: {', '.join(failed_core)}"

def test_model_modules():
    """Test data model modules can be imported."""
    model_modules = [
        ("mcp_studio.app.models.mcp", "MCP data models"),
        ("mcp_studio.app.models.server", "Server models"),
    ]
    
    failed_models = []
    for module, desc in model_modules:
        if not _test_import(module, desc):
            failed_models.append(module)
    
    assert len(failed_models) == 0, f"Failed to import: {', '.join(failed_models)}"

def test_service_modules():
    """Test service modules can be imported."""
    service_modules = [
        ("mcp_studio.app.services", "Services module"),
        ("mcp_studio.app.services.config_service", "Configuration service"),
        ("mcp_studio.app.services.discovery_service", "Discovery service"),
        ("mcp_studio.app.services.server_service", "Server service"),
        ("mcp_studio.app.services.tool_service", "Tool service"),
    ]
    
    failed_services = []
    for module, desc in service_modules:
        if not _test_import(module, desc):
            failed_services.append(module)
    
    assert len(failed_services) == 0, f"Failed to import: {', '.join(failed_services)}"

def test_api_modules():
    """Test API modules can be imported."""
    api_modules = [
        ("mcp_studio.app.api", "API router"),
        ("mcp_studio.app.api.health", "Health endpoints"),
        ("mcp_studio.app.api.servers", "Server endpoints"),
        ("mcp_studio.app.api.tools", "Tool endpoints"),
        ("mcp_studio.app.api.discovery", "Discovery endpoints"),
        ("mcp_studio.app.api.web", "Web interface"),
    ]
    
    failed_api = []
    for module, desc in api_modules:
        if not _test_import(module, desc):
            failed_api.append(module)
    
    assert len(failed_api) == 0, f"Failed to import: {', '.join(failed_api)}"

def test_tool_modules():
    """Test tool modules can be imported."""
    tool_modules = [
        ("mcp_studio.tools", "Tools module"),
        ("mcp_studio.tools.decorators", "Tool decorators"),
        ("mcp_studio.tools.discovery", "Discovery tools"),
        ("mcp_studio.tools.server", "Server tools"),
        ("mcp_studio.tools.utility", "Utility tools"),
        ("mcp_studio.tools.development", "Development tools"),
        ("mcp_studio.tools.data", "Data tools"),
        ("mcp_studio.tools.files", "File tools"),
    ]
    
    failed_tools = []
    for module, desc in tool_modules:
        if not _test_import(module, desc):
            failed_tools.append(module)
    
    assert len(failed_tools) == 0, f"Failed to import: {', '.join(failed_tools)}"

def test_main_modules():
    """Test main application modules can be imported."""
    main_modules = [
        ("mcp_studio", "Main package"),
        ("mcp_studio.main", "Application entry point"),
    ]
    
    failed_main = []
    for module, desc in main_modules:
        if not _test_import(module, desc):
            failed_main.append(module)
    
    assert len(failed_main) == 0, f"Failed to import: {', '.join(failed_main)}"

def main():
    """Run all import tests."""
    print("MCP Studio Import Test")
    print("=" * 50)

    # Test external dependencies
    print("\n📦 External Dependencies:")
    deps = [
        ("fastapi", "FastAPI web framework"),
        ("uvicorn", "ASGI server"),
        ("pydantic", "Data validation"),
        ("structlog", "Structured logging"),
        ("aiofiles", "Async file operations"),
        ("aiohttp", "Async HTTP client"),
        ("fastmcp", "FastMCP framework"),
        ("psutil", "System utilities"),
        ("watchdog", "File system monitoring"),
    ]

    failed_deps = []
    for dep, desc in deps:
        if not test_import(dep, desc):
            failed_deps.append(dep)

    # Test core modules
    print("\n🏗️ Core Application Modules:")
    core_modules = [
        ("mcp_studio.app.core.config", "Configuration management"),
        ("mcp_studio.app.core.logging", "Logging configuration"),
        ("mcp_studio.app.core.logging_utils", "Logging utilities"),
        ("mcp_studio.app.core.lifespan", "Application lifespan"),
        ("mcp_studio.app.core.enums", "Common enums"),
        ("mcp_studio.app.core.types", "Type definitions"),
        ("mcp_studio.app.core.security", "Security utilities"),
        ("mcp_studio.app.core.websocket", "WebSocket handling"),
    ]

    failed_core = []
    for module, desc in core_modules:
        if not test_import(module, desc):
            failed_core.append(module)

    # Test models
    print("\n📋 Data Models:")
    model_modules = [
        ("mcp_studio.app.models.mcp", "MCP data models"),
        ("mcp_studio.app.models.server", "Server models"),
    ]

    failed_models = []
    for module, desc in model_modules:
        if not test_import(module, desc):
            failed_models.append(module)

    # Test services
    print("\n🔧 Services:")
    service_modules = [
        ("mcp_studio.app.services", "Services module"),
        ("mcp_studio.app.services.config_service", "Configuration service"),
        ("mcp_studio.app.services.discovery_service", "Discovery service"),
        ("mcp_studio.app.services.server_service", "Server service"),
        ("mcp_studio.app.services.tool_service", "Tool service"),
    ]

    failed_services = []
    for module, desc in service_modules:
        if not test_import(module, desc):
            failed_services.append(module)

    # Test API modules
    print("\n🌐 API Modules:")
    api_modules = [
        ("mcp_studio.app.api", "API router"),
        ("mcp_studio.app.api.health", "Health endpoints"),
        ("mcp_studio.app.api.servers", "Server endpoints"),
        ("mcp_studio.app.api.tools", "Tool endpoints"),
        ("mcp_studio.app.api.discovery", "Discovery endpoints"),
        ("mcp_studio.app.api.web", "Web interface"),
    ]

    failed_api = []
    for module, desc in api_modules:
        if not test_import(module, desc):
            failed_api.append(module)

    # Test tools
    print("\n🛠️ Tools:")
    tool_modules = [
        ("mcp_studio.tools", "Tools module"),
        ("mcp_studio.tools.decorators", "Tool decorators"),
        ("mcp_studio.tools.discovery", "Discovery tools"),
        ("mcp_studio.tools.server", "Server tools"),
        ("mcp_studio.tools.utility", "Utility tools"),
        ("mcp_studio.tools.development", "Development tools"),
        ("mcp_studio.tools.data", "Data tools"),
        ("mcp_studio.tools.files", "File tools"),
    ]

    failed_tools = []
    for module, desc in tool_modules:
        if not test_import(module, desc):
            failed_tools.append(module)

    # Test main modules
    print("\n🚀 Main Application:")
    main_modules = [
        ("mcp_studio", "Main package"),
        ("mcp_studio.main", "Application entry point"),
    ]

    failed_main = []
    for module, desc in main_modules:
        if not test_import(module, desc):
            failed_main.append(module)

    # Summary
    print("\n" + "=" * 50)
    print("📊 Import Test Summary")
    print("=" * 50)

    total_tests = len(deps) + len(core_modules) + len(model_modules) + len(service_modules) + len(api_modules) + len(tool_modules) + len(main_modules)
    total_failed = len(failed_deps) + len(failed_core) + len(failed_models) + len(failed_services) + len(failed_api) + len(failed_tools) + len(failed_main)
    total_passed = total_tests - total_failed

    print(f"Total tests: {total_tests}")
    print(f"Passed: {total_passed}")
    print(f"Failed: {total_failed}")
    print(f"Success rate: {(total_passed/total_tests*100):.1f}%")

    if total_failed > 0:
        print("\n❌ Failed imports:")
        all_failed = failed_deps + failed_core + failed_models + failed_services + failed_api + failed_tools + failed_main
        for module in all_failed:
            print(f"   - {module}")

        print("\n🔧 Recommended actions:")
        if failed_deps:
            print("   1. Install missing dependencies:")
            print(f"      pip install {' '.join(failed_deps)}")

        if failed_core or failed_models or failed_services or failed_api or failed_tools or failed_main:
            print("   2. Fix syntax errors and missing modules")
            print("   3. Check import paths and module structure")
            print("   4. Ensure all __init__.py files exist")

    return total_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
