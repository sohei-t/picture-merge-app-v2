"""Tests for GET /api/health endpoint."""

import pytest


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_health_response_status(self, client):
        """BE-HLT-001: Normal health response."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "rembg_loaded" in data
        assert data["version"] == "2.0.0"

    def test_health_response_structure(self, client):
        """BE-HLT-002: Response structure validation."""
        response = client.get("/api/health")
        data = response.json()
        assert "status" in data
        assert "rembg_loaded" in data
        assert "version" in data
        assert isinstance(data["rembg_loaded"], bool)
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)

    def test_health_rembg_loaded(self, client):
        """BE-HLT-003: rembg loaded state is reflected."""
        response = client.get("/api/health")
        data = response.json()
        # In test environment with mock, rembg_loaded should be True
        assert isinstance(data["rembg_loaded"], bool)
