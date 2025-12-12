"""Test CRUD tools for MCP Studio.

Tests for create_mcp_server, update_mcp_server, and delete_mcp_server.
"""

import pytest
from pathlib import Path
import shutil
import subprocess

from mcp_studio.tools.server_scaffold import create_mcp_server
from mcp_studio.tools.server_updater import update_mcp_server
from mcp_studio.tools.server_deleter import delete_mcp_server


TEST_SERVERS_DIR = Path("D:/Dev/repos/test-servers")
TEST_SERVER_NAME = "test-crud-server"


@pytest.fixture(autouse=True)
def cleanup_test_servers():
    """Clean up test servers before and after tests."""
    # Cleanup before
    test_server = TEST_SERVERS_DIR / TEST_SERVER_NAME
    if test_server.exists():
        shutil.rmtree(test_server)
    
    yield
    
    # Cleanup after
    if test_server.exists():
        shutil.rmtree(test_server)


@pytest.mark.asyncio
async def test_create_mcp_server_basic():
    """Test basic MCP server creation."""
    result = await create_mcp_server(
        server_name=TEST_SERVER_NAME,
        description="Test MCP server for CRUD testing",
        author="Test Author",
        target_path=str(TEST_SERVERS_DIR),
        include_examples=True,
        init_git=False,  # Skip git for faster tests
        include_frontend=False
    )
    
    assert result["success"] is True
    assert "server_path" in result
    
    server_path = Path(result["server_path"])
    assert server_path.exists()
    assert (server_path / "src").exists()
    assert (server_path / "pyproject.toml").exists()
    assert (server_path / "README.md").exists()
    assert (server_path / ".github" / "workflows" / "ci.yml").exists()


@pytest.mark.asyncio
async def test_create_mcp_server_with_git():
    """Test MCP server creation with git initialization."""
    result = await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-git",
        description="Test server with git",
        author="Test Author",
        target_path=str(TEST_SERVERS_DIR),
        init_git=True,
        include_frontend=False
    )
    
    assert result["success"] is True
    server_path = Path(result["server_path"])
    assert (server_path / ".git").exists()


@pytest.mark.asyncio
async def test_create_mcp_server_already_exists():
    """Test error handling when server already exists."""
    # Create server first
    await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-exists",
        description="Test",
        author="Test",
        target_path=str(TEST_SERVERS_DIR),
        init_git=False,
        include_frontend=False
    )
    
    # Try to create again
    result = await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-exists",
        description="Test",
        author="Test",
        target_path=str(TEST_SERVERS_DIR),
        init_git=False,
        include_frontend=False
    )
    
    assert result["success"] is False
    assert "already exists" in result["error"].lower()


@pytest.mark.asyncio
async def test_update_mcp_server_dry_run():
    """Test update_mcp_server in dry-run mode."""
    # First create a server
    create_result = await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-update",
        description="Test server for update",
        author="Test",
        target_path=str(TEST_SERVERS_DIR),
        init_git=False,
        include_frontend=False
    )
    
    assert create_result["success"] is True
    server_path = create_result["server_path"]
    
    # Try to update (should detect everything is already there)
    update_result = await update_mcp_server(
        repo_path=server_path,
        components=None,  # Auto-detect
        dry_run=True
    )
    
    assert "success" in update_result
    assert update_result.get("dry_run") is True


@pytest.mark.asyncio
async def test_delete_mcp_server_dry_run():
    """Test delete_mcp_server in dry-run mode."""
    # Create a server first
    create_result = await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-delete",
        description="Test server for deletion",
        author="Test",
        target_path=str(TEST_SERVERS_DIR),
        init_git=False,
        include_frontend=False
    )
    
    assert create_result["success"] is True
    server_path = create_result["server_path"]
    
    # Dry-run deletion
    delete_result = await delete_mcp_server(
        repo_path=server_path,
        force=False,
        backup=False,
        dry_run=True
    )
    
    assert delete_result["success"] is True
    assert delete_result.get("dry_run") is True
    assert delete_result.get("would_delete") is True
    
    # Server should still exist
    assert Path(server_path).exists()


@pytest.mark.asyncio
async def test_delete_mcp_server_actual():
    """Test actual deletion of a server."""
    # Create a server
    create_result = await create_mcp_server(
        server_name=f"{TEST_SERVER_NAME}-delete-actual",
        description="Test server for actual deletion",
        author="Test",
        target_path=str(TEST_SERVERS_DIR),
        init_git=False,
        include_frontend=False
    )
    
    assert create_result["success"] is True
    server_path = create_result["server_path"]
    assert Path(server_path).exists()
    
    # Actually delete it
    delete_result = await delete_mcp_server(
        repo_path=server_path,
        force=True,  # Skip safety checks for test
        backup=False,
        dry_run=False
    )
    
    assert delete_result["success"] is True
    assert delete_result.get("deleted") is True
    
    # Server should be gone
    assert not Path(server_path).exists()


def test_pre_commit_hooks():
    """Test that pre-commit hooks are configured correctly."""
    # Check that .pre-commit-config.yaml exists
    config_path = Path(__file__).parent.parent / ".pre-commit-config.yaml"
    assert config_path.exists(), "Pre-commit config should exist"
    
    # Check that ruff is configured (not black)
    config_content = config_path.read_text()
    assert "ruff-pre-commit" in config_content, "Should use ruff, not black"
    assert "black" not in config_content, "Should not use outdated black"
    assert "isort" not in config_content, "Should not use outdated isort"
    assert "flake8" not in config_content, "Should not use outdated flake8"
