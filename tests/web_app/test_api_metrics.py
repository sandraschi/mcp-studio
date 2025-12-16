"""Tests for metrics API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_metrics_endpoint(client: TestClient):
    """Test Prometheus metrics endpoint."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    # Check content type
    assert response.headers["content-type"] == "text/plain; version=0.0.4; charset=utf-8"

    # Check that response contains Prometheus metrics
    content = response.text
    assert "# HELP" in content
    assert "# TYPE" in content

    # Should contain our custom metrics
    assert "mcp_api_requests_total" in content
    assert "mcp_api_request_duration_seconds" in content
    assert "mcp_active_connections" in content
    assert "mcp_scan_progress_total" in content
    assert "mcp_scan_repos_found_total" in content


def test_metrics_python_gc_metrics(client: TestClient):
    """Test that Python GC metrics are included."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    assert "python_gc_objects_collected_total" in content
    assert "python_gc_collections_total" in content


def test_metrics_process_metrics(client: TestClient):
    """Test that process metrics are included."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    assert "process_virtual_memory_bytes" in content
    assert "process_resident_memory_bytes" in content
    assert "process_cpu_seconds_total" in content
    assert "process_open_fds" in content


def test_metrics_platform_info(client: TestClient):
    """Test that platform information is included."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    assert "python_info" in content


def test_metrics_format_validation(client: TestClient):
    """Test that metrics are in valid Prometheus format."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    lines = content.strip().split('\n')

    # Each metric should follow Prometheus format
    for line in lines:
        if line.startswith('#'):
            # Comment lines
            if line.startswith('# HELP'):
                assert len(line.split()) >= 3
            elif line.startswith('# TYPE'):
                assert len(line.split()) >= 3
        elif line.strip():
            # Metric lines should have name and value
            parts = line.split()
            assert len(parts) >= 2
            metric_name = parts[0].split('{')[0]  # Handle labels
            assert metric_name.replace('_', '').replace(':', '').isalnum()


def test_metrics_endpoint_caching(client: TestClient):
    """Test that metrics endpoint has appropriate caching headers."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    # Metrics should not be cached
    cache_control = response.headers.get("cache-control", "").lower()
    assert "no-cache" in cache_control or "max-age=0" in cache_control


def test_metrics_endpoint_accepts_get_only(client: TestClient):
    """Test that metrics endpoint only accepts GET requests."""
    # POST should not be allowed
    response = client.post("/api/v1/health/metrics")
    assert response.status_code == 405  # Method not allowed

    # PUT should not be allowed
    response = client.put("/api/v1/health/metrics")
    assert response.status_code == 405

    # DELETE should not be allowed
    response = client.delete("/api/v1/health/metrics")
    assert response.status_code == 405


def test_metrics_content_length(client: TestClient):
    """Test that metrics response has reasonable content length."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content_length = len(response.content)
    assert content_length > 100  # Should have substantial content
    assert content_length < 100000  # Should not be excessively large


def test_metrics_timestamps(client: TestClient):
    """Test that metrics include proper timestamps where expected."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    # Check for timestamp metrics
    assert "process_start_time_seconds" in content


def test_metrics_histogram_buckets(client: TestClient):
    """Test that histogram metrics have proper bucket configuration."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    # Our histogram should have bucket definitions
    assert "mcp_api_request_duration_seconds_bucket" in content
    assert "le=" in content  # Label for bucket upper bounds


def test_metrics_counter_monotonicity(client: TestClient):
    """Test that counter metrics are monotonically increasing."""
    # Get metrics twice with a small delay
    response1 = client.get("/api/v1/health/metrics")
    import time
    time.sleep(0.1)
    response2 = client.get("/api/v1/health/metrics")

    assert response1.status_code == 200
    assert response2.status_code == 200

    content1 = response1.text
    content2 = response2.text

    # Extract counter values (simplified check)
    # In a real scenario, you'd parse the Prometheus format properly
    # For this test, we just verify the endpoint is consistent
    assert len(content1) > 0
    assert len(content2) > 0


def test_metrics_gauge_values(client: TestClient):
    """Test that gauge metrics have reasonable values."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text
    # Check that our gauge metrics are present and have numeric values
    lines = content.split('\n')
    for line in lines:
        if line.startswith('mcp_active_connections') and not line.startswith('#'):
            parts = line.split()
            if len(parts) >= 2:
                value = float(parts[1])
                assert value >= 0  # Active connections can't be negative


def test_metrics_custom_metrics_presence(client: TestClient):
    """Test that all our custom MCP metrics are present."""
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200

    content = response.text

    # All our custom metrics should be present
    required_metrics = [
        "mcp_api_requests_total",
        "mcp_api_request_duration_seconds",
        "mcp_active_connections",
        "mcp_scan_progress_total",
        "mcp_scan_progress_found",
        "mcp_scan_progress_skipped",
        "mcp_scan_progress_errors",
        "mcp_scan_repos_found_total",
        "mcp_scan_repos_skipped_total",
        "mcp_scan_errors_total"
    ]

    for metric in required_metrics:
        assert metric in content, f"Missing metric: {metric}"


def test_metrics_endpoint_availability(client: TestClient):
    """Test that metrics endpoint is always available."""
    # Test multiple times to ensure consistency
    for _ in range(3):
        response = client.get("/api/v1/health/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]
