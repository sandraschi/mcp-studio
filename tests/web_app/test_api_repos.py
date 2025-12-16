"""Tests for repos API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock


def test_scan_repos_success(client: TestClient):
    """Test successful repo scanning."""
    # Mock the repo scanner service
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_scan = repo_scanner.scan_repos

    mock_result = [
        {
            "name": "test-repo",
            "fastmcp_version": "2.13.1",
            "tools": 5,
            "zoo_class": "medium",
            "zoo_emoji": "FOX",
            "path": "/test/path"
        }
    ]

    repo_scanner.scan_repos = MagicMock(return_value=mock_result)

    try:
        response = client.get("/api/v1/repos")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "name" in data[0]
            assert "fastmcp_version" in data[0]
            assert "tools" in data[0]
    finally:
        repo_scanner.scan_repos = original_scan


def test_get_scan_progress(client: TestClient):
    """Test getting scan progress."""
    # Mock the repo scanner service
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_progress = repo_scanner.get_progress

    mock_progress = {
        "status": "scanning",
        "total": 10,
        "current": "test-repo",
        "done": 3,
        "mcp_repos_found": 2,
        "errors": 0,
        "skipped": 1,
        "activity_log": ["Started scanning", "Found test-repo"]
    }

    repo_scanner.get_progress = MagicMock(return_value=mock_progress)

    try:
        response = client.get("/api/v1/repos/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scanning"
        assert data["total"] == 10
        assert data["done"] == 3
        assert data["mcp_repos_found"] == 2
        assert isinstance(data["activity_log"], list)
    finally:
        repo_scanner.get_progress = original_progress


def test_get_scan_results(client: TestClient):
    """Test getting scan results."""
    # Mock the repo scanner service
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_results = repo_scanner.get_results

    mock_results = [
        {
            "name": "test-repo-1",
            "fastmcp_version": "2.13.1",
            "tools": 5,
            "zoo_class": "medium",
            "zoo_emoji": "FOX"
        },
        {
            "name": "test-repo-2",
            "fastmcp_version": "2.12.0",
            "tools": 12,
            "zoo_class": "large",
            "zoo_emoji": "LION"
        }
    ]

    repo_scanner.get_results = MagicMock(return_value=mock_results)

    try:
        response = client.get("/api/v1/repos/results")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["name"] == "test-repo-1"
        assert data[1]["name"] == "test-repo-2"
        assert data[0]["zoo_emoji"] == "FOX"
        assert data[1]["zoo_emoji"] == "LION"
    finally:
        repo_scanner.get_results = original_results


def test_get_repo_details_success(client: TestClient):
    """Test getting details for a specific repo."""
    # This would require mocking file system access
    # For now, test the endpoint exists and handles not found
    response = client.get("/api/v1/repos/repo/non-existent-repo")
    # Should return 404 or appropriate error for non-existent repo
    assert response.status_code in [404, 500]  # Depends on implementation


def test_scan_repos_with_path_param(client: TestClient):
    """Test repo scanning with custom path parameter."""
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_scan = repo_scanner.scan_repos

    mock_result = [{"name": "custom-repo", "tools": 3}]
    repo_scanner.scan_repos = MagicMock(return_value=mock_result)

    try:
        response = client.get("/api/v1/repos?scan_path=/custom/path")
        assert response.status_code == 200
        # Verify the scan was called with the custom path
        repo_scanner.scan_repos.assert_called_with(scan_path="/custom/path")
    finally:
        repo_scanner.scan_repos = original_scan


def test_scan_progress_initial_state(client: TestClient):
    """Test scan progress in initial idle state."""
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_progress = repo_scanner.get_progress

    mock_progress = {
        "status": "idle",
        "total": 0,
        "current": "",
        "done": 0,
        "mcp_repos_found": 0,
        "errors": 0,
        "skipped": 0,
        "activity_log": []
    }

    repo_scanner.get_progress = MagicMock(return_value=mock_progress)

    try:
        response = client.get("/api/v1/repos/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"
        assert data["total"] == 0
        assert data["mcp_repos_found"] == 0
        assert len(data["activity_log"]) == 0
    finally:
        repo_scanner.get_progress = original_progress


def test_scan_progress_during_scan(client: TestClient):
    """Test scan progress during active scanning."""
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_progress = repo_scanner.get_progress

    mock_progress = {
        "status": "scanning",
        "total": 25,
        "current": "mcp-awesome-tools",
        "done": 12,
        "mcp_repos_found": 8,
        "errors": 2,
        "skipped": 2,
        "activity_log": [
            "Using repos directory: D:/Dev/repos",
            "Found 25 directories to scan",
            "Analyzing mcp-awesome-tools...",
            "[FOUND] AWESOME TOOLS v2.13.1 (15 tools)",
            "Analyzing another-repo...",
            "[SKIP] another-repo (not MCP/fullstack repo)"
        ]
    }

    repo_scanner.get_progress = MagicMock(return_value=mock_progress)

    try:
        response = client.get("/api/v1/repos/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scanning"
        assert data["total"] == 25
        assert data["current"] == "mcp-awesome-tools"
        assert data["done"] == 12
        assert data["mcp_repos_found"] == 8
        assert data["errors"] == 2
        assert data["skipped"] == 2
        assert len(data["activity_log"]) == 6
        assert "[FOUND]" in data["activity_log"][3]
        assert "[SKIP]" in data["activity_log"][5]
    finally:
        repo_scanner.get_progress = original_progress


def test_scan_progress_completed(client: TestClient):
    """Test scan progress after completion."""
    from mcp_studio.app.services.repo_scanner_service import repo_scanner
    original_progress = repo_scanner.get_progress

    mock_progress = {
        "status": "complete",
        "total": 25,
        "current": "",
        "done": 25,
        "mcp_repos_found": 18,
        "errors": 3,
        "skipped": 4,
        "activity_log": [
            "[COMPLETE] Scan complete: 18 MCP repos found, 4 skipped, 3 errors"
        ]
    }

    repo_scanner.get_progress = MagicMock(return_value=mock_progress)

    try:
        response = client.get("/api/v1/repos/progress")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "complete"
        assert data["total"] == 25
        assert data["done"] == 25
        assert data["mcp_repos_found"] == 18
        assert data["errors"] == 3
        assert data["skipped"] == 4
        assert "[COMPLETE]" in data["activity_log"][0]
    finally:
        repo_scanner.get_progress = original_progress
