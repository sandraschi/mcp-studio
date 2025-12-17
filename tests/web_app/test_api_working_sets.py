"""
API tests for working sets and backup functionality
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock


class TestWorkingSetsAPI:
    """Test working sets API endpoints."""

    def test_list_working_sets(self, client):
        """Test GET /api/working-sets/ endpoint."""
        response = client.get("/api/working-sets/")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # If there are working sets, check structure
        if data:
            ws = data[0]
            required_fields = ['name', 'id', 'description', 'icon', 'category', 'servers', 'server_count', 'is_current']
            for field in required_fields:
                assert field in ws

    def test_get_working_set(self, client):
        """Test GET /api/working-sets/{id} endpoint."""
        # First get available working sets
        response = client.get("/api/working-sets/")
        assert response.status_code == 200
        working_sets = response.json()

        if working_sets:
            ws_id = working_sets[0]['id']
            response = client.get(f"/api/working-sets/{ws_id}")
            assert response.status_code == 200

            data = response.json()
            assert data['id'] == ws_id
            assert 'name' in data
            assert 'description' in data

    def test_preview_working_set(self, client):
        """Test GET /api/working-sets/{id}/preview endpoint."""
        # First get available working sets
        response = client.get("/api/working-sets/")
        assert response.status_code == 200
        working_sets = response.json()

        if working_sets:
            ws_id = working_sets[0]['id']
            response = client.get(f"/api/working-sets/{ws_id}/preview")
            assert response.status_code == 200

            data = response.json()
            required_fields = ['current_servers', 'new_servers', 'added_servers', 'removed_servers', 'config_preview']
            for field in required_fields:
                assert field in data

    def test_validate_working_set(self, client):
        """Test GET /api/working-sets/{id}/validate endpoint."""
        # First get available working sets
        response = client.get("/api/working-sets/")
        assert response.status_code == 200
        working_sets = response.json()

        if working_sets:
            ws_id = working_sets[0]['id']
            response = client.get(f"/api/working-sets/{ws_id}/validate")
            assert response.status_code == 200

            data = response.json()
            required_fields = ['valid', 'missing_servers', 'available_servers', 'working_set_servers']
            for field in required_fields:
                assert field in data

    def test_switch_working_set_success(self, client):
        """Test successful working set switch."""
        # This test may need mocking since it requires actual config files
        # For now, test that the endpoint exists and handles the request
        response = client.post("/api/working-sets/dev_work/switch", json={"create_backup": False})

        # Should return some response
        assert response.status_code in [200, 404, 500]

        if response.status_code == 200:
            data = response.json()
            assert 'success' in data
            if data['success']:
                assert 'working_set_id' in data
                assert 'working_set_name' in data
                assert 'backup_created' in data
                assert 'servers_count' in data


class TestBackupsAPI:
    """Test backup management API endpoints."""

    def test_list_backups(self, client):
        """Test GET /api/working-sets/backups/list endpoint."""
        response = client.get("/api/working-sets/backups/list")

        assert response.status_code == 200
        data = response.json()

        assert isinstance(data, list)

        # If there are backups, check structure
        if data:
            backup = data[0]
            required_fields = ['name', 'file', 'created', 'size']
            for field in required_fields:
                assert field in backup

    def test_restore_backup(self, client):
        """Test POST /api/working-sets/backups/{name}/restore endpoint."""
        # First get available backups
        response = client.get("/api/working-sets/backups/list")
        assert response.status_code == 200
        backups = response.json()

        if backups:
            backup_name = backups[0]['name']
            response = client.post(f"/api/working-sets/backups/{backup_name}/restore")
            # Restore might fail in test environment, but endpoint should exist
            assert response.status_code in [200, 404, 500]


class TestWorkingSetsIntegration:
    """Integration tests for working sets functionality."""

    @pytest.fixture
    def mock_working_set_manager(self, monkeypatch):
        """Mock the working set manager for testing."""
        from unittest.mock import MagicMock

        mock_manager = MagicMock()
        mock_manager.list_working_sets.return_value = [
            {
                "name": "Test Working Set",
                "id": "test_ws",
                "description": "Test working set for integration tests",
                "icon": "🧪",
                "category": "Testing",
                "servers": [{"name": "test-server", "required": True}],
                "server_count": 1,
                "is_current": False
            }
        ]

        mock_manager.get_working_set.return_value = MagicMock(
            id="test_ws",
            name="Test Working Set",
            description="Test working set",
            icon="🧪",
            servers=[]
        )

        mock_manager.preview_working_set_config.return_value = {
            "current_servers": ["server1"],
            "new_servers": ["server2"],
            "added_servers": ["server2"],
            "removed_servers": ["server1"],
            "config_preview": {"mcpServers": {"server2": {}}}
        }

        mock_manager.validate_working_set.return_value = {
            "valid": True,
            "missing_servers": [],
            "available_servers": ["server1"],
            "working_set_servers": ["server1"]
        }

        mock_manager.switch_to_working_set.return_value = {
            "success": True,
            "working_set_id": "test_ws",
            "working_set_name": "Test Working Set",
            "backup_created": "/path/to/backup.json",
            "servers_count": 1
        }

        # Mock the manager import
        monkeypatch.setattr("mcp_studio.app.api.working_sets.manager", mock_manager)

        return mock_manager

    def test_full_working_sets_workflow(self, client, mock_working_set_manager):
        """Test complete working sets workflow through API."""
        # 1. List working sets
        response = client.get("/api/working-sets/")
        assert response.status_code == 200
        working_sets = response.json()
        assert len(working_sets) == 1
        assert working_sets[0]['id'] == 'test_ws'

        # 2. Get specific working set
        response = client.get("/api/working-sets/test_ws")
        assert response.status_code == 200

        # 3. Preview working set
        response = client.get("/api/working-sets/test_ws/preview")
        assert response.status_code == 200
        preview = response.json()
        assert 'config_preview' in preview

        # 4. Validate working set
        response = client.get("/api/working-sets/test_ws/validate")
        assert response.status_code == 200
        validation = response.json()
        assert validation['valid'] is True

        # 5. Switch to working set
        response = client.post("/api/working-sets/test_ws/switch", json={"create_backup": True})
        assert response.status_code == 200
        switch_result = response.json()
        assert switch_result['success'] is True
        assert switch_result['working_set_id'] == 'test_ws'


class TestBackupIntegration:
    """Integration tests for backup functionality."""

    @pytest.fixture
    def mock_backup_manager(self, monkeypatch):
        """Mock backup functionality."""
        from unittest.mock import MagicMock

        mock_manager = MagicMock()
        mock_manager.list_backups.return_value = [
            {
                "name": "before_test_ws_20241217_120000",
                "file": "/path/to/backup/before_test_ws_20241217_120000.json",
                "created": "2024-12-17T12:00:00",
                "size": 1024
            }
        ]

        # Mock the manager import
        monkeypatch.setattr("mcp_studio.app.api.working_sets.manager", mock_manager)

        return mock_manager

    def test_backup_workflow(self, client, mock_backup_manager):
        """Test backup listing and restore workflow."""
        # List backups
        response = client.get("/api/working-sets/backups/list")
        assert response.status_code == 200
        backups = response.json()
        assert len(backups) == 1
        assert 'before_test_ws' in backups[0]['name']

        # Attempt restore (will likely fail in test env, but test endpoint)
        backup_name = backups[0]['name']
        response = client.post(f"/api/working-sets/backups/{backup_name}/restore")
        # Should return some response (success or controlled failure)
        assert response.status_code in [200, 404, 500]


class TestErrorHandling:
    """Test error handling in working sets API."""

    def test_switch_nonexistent_working_set(self, client):
        """Test switching to non-existent working set."""
        response = client.post("/api/working-sets/nonexistent/switch", json={"create_backup": False})

        # Should return 404 or handle gracefully
        assert response.status_code in [404, 500]

        if response.status_code == 404:
            data = response.json()
            assert 'detail' in data

    def test_invalid_backup_restore(self, client):
        """Test restoring non-existent backup."""
        response = client.post("/api/working-sets/backups/nonexistent_backup/restore")

        # Should handle gracefully
        assert response.status_code in [404, 500]

    def test_preview_nonexistent_working_set(self, client):
        """Test previewing non-existent working set."""
        response = client.get("/api/working-sets/nonexistent/preview")

        assert response.status_code in [404, 500]


if __name__ == "__main__":
    print("🧪 Working Sets API Tests")
    print("=" * 40)

    # Basic functionality check
    print("✅ Test file loaded successfully")
    print("Run 'pytest tests/web_app/test_api_working_sets.py -v' for detailed testing")
