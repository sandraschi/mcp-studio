import sys
import os
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

# Add project root to sys.path to allow importing studio_dashboard
sys.path.append(str(Path(__file__).parent.parent))

# Import the module to test
# We might need to mock incomplete dependencies if they cause import errors
with patch.dict(sys.modules, {"fastmcp": MagicMock(), "mcp": MagicMock()}):
    import studio_dashboard
    from studio_dashboard import detect_fullstack_features, analyze_repo, scan_repos, state


@pytest.fixture
def mock_repo_path():
    path = MagicMock(spec=Path)
    path.name = "test-repo"
    path.__str__.return_value = "/path/to/test-repo"
    path.exists.return_value = True
    path.is_dir.return_value = True
    return path


def test_detect_fullstack_features_frontend(mock_repo_path):
    # Mock package.json existence and content
    package_json = MagicMock(spec=Path)
    package_json.exists.return_value = True

    # Mock reading package.json
    with patch(
        "builtins.open",
        mock_open(read_data='{"dependencies": {"react": "^18.0.0", "next": "^13.0.0"}}'),
    ):
        # We need to ensure path / "package.json" returns our mock
        mock_repo_path.__truediv__.side_effect = (
            lambda x: package_json if x == "package.json" else MagicMock(exists=False)
        )

        features = detect_fullstack_features(mock_repo_path)

        assert "react" in features["frontend"]
        assert "next" in features["frontend"]
        assert (
            features["is_fullstack"] is False
        )  # context: needs backend too, or be explicitly determined fullstack


def test_detect_fullstack_features_backend(mock_repo_path):
    # Mock requirements.txt
    req_txt = MagicMock(spec=Path)
    req_txt.exists.return_value = True
    req_txt.read_text.return_value = "fastapi==0.100.0\nuvicorn\n"

    mock_repo_path.__truediv__.side_effect = (
        lambda x: req_txt if x == "requirements.txt" else MagicMock(exists=False)
    )

    features = detect_fullstack_features(mock_repo_path)

    assert "fastapi" in features["backend"]


def test_detect_fullstack_features_infrastructure(mock_repo_path):
    # Mock Dockerfile and docker-compose.yml
    dockerfile = MagicMock(spec=Path)
    dockerfile.exists.return_value = True

    compose = MagicMock(spec=Path)
    compose.exists.return_value = True

    def side_effect(arg):
        if arg == "Dockerfile":
            return dockerfile
        if arg == "docker-compose.yml":
            return compose
        return MagicMock(spec=Path, exists=lambda: False)

    mock_repo_path.__truediv__.side_effect = side_effect

    features = detect_fullstack_features(mock_repo_path)

    assert "Dockerfile" in features["infrastructure"]
    assert "Docker Compose" in features["infrastructure"]


def test_analyze_repo_integration(mock_repo_path):
    # Test the full analyze_repo flow with mocked file system
    # We want to simulate a valid MCP repo so it returns info

    # Mock pyproject.toml with fastmcp
    pyproject = MagicMock(spec=Path)
    pyproject.exists.return_value = True
    pyproject.read_text.return_value = '[project]\ndependencies = ["fastmcp>=0.1.0"]'

    # Mock side effects for path joins
    def side_effect(arg):
        if arg == "pyproject.toml":
            return pyproject
        if arg == "requirements.txt":
            return MagicMock(exists=False)
        return MagicMock(
            spec=Path, exists=lambda: False
        )  # For other files like package.json checks inside detect_fullstack

    mock_repo_path.__truediv__.side_effect = side_effect

    # Mock detect_fullstack_features to return empty safe defaults to avoid complex mocking loop
    with patch("studio_dashboard.detect_fullstack_features") as mock_detect:
        mock_detect.return_value = {
            "is_fullstack": False,
            "frontend": [],
            "backend": [],
            "infrastructure": [],
            "database": [],
            "documentation": [],
            "git": {"branch": "main", "dirty": False},
            "runtime": {"running": False},
        }

        info = analyze_repo(mock_repo_path)

        assert info is not None
        assert info["name"] == "test-repo"
        assert info["fastmcp_version"] is not None


def test_scan_repos_logging(mock_repo_path):
    # Test that scan_repos populates the activity log

    # Mock REPOS_DIR
    with patch("studio_dashboard.REPOS_DIR") as mock_repos_dir:
        mock_repos_dir.exists.return_value = True
        mock_repos_dir.iterdir.return_value = [mock_repo_path]

        # Mock analyze_repo to return a valid result
        with patch("studio_dashboard.analyze_repo") as mock_analyze:
            mock_analyze.return_value = {
                "name": "test-repo",
                "zoo_emoji": "🦁",
                "status_emoji": "✅",
                "fastmcp_version": "1.0",
                "tools": 5,
            }

            # Run scan
            results = scan_repos()

            assert len(results) == 1
            assert results[0]["name"] == "test-repo"

            # Check log
            log = state["scan_progress"]["activity_log"]
            assert len(log) > 0
            assert any("Starting scan" in msg for msg in log)
            assert any("Found test-repo" in msg for msg in log)
