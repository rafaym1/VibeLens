"""Tests for the extension install endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app
from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import AgentExtensionItem
from vibelens.storage.extension.catalog import CatalogSnapshot


def _make_snapshot() -> CatalogSnapshot:
    """Create a minimal catalog with one installable skill."""
    items = [
        AgentExtensionItem(
            extension_id="bwc:skill:test-skill",
            extension_type=AgentExtensionType.SKILL,
            name="test-skill",
            description="A test skill",
            tags=["testing"],
            category="testing",
            platforms=["claude_code"],
            quality_score=80.0,
            popularity=0.5,
            updated_at="2026-04-01T00:00:00Z",
            source_url="https://github.com/test/repo",
            repo_full_name="test/repo",
            install_method="skill_file",
            install_content="# Test Skill\nContent here.",
        ),
    ]
    return CatalogSnapshot(version="2026-04-13", schema_version=1, items=items)


@pytest.fixture
def client():
    """Create test client with mocked catalog."""
    with patch("vibelens.services.extensions.catalog.load_catalog", return_value=_make_snapshot()):
        app = create_app()
        yield TestClient(app)


def test_install_requires_target_platforms(client):
    """POST with empty body returns 422, not 500 TypeError."""
    resp = client.post("/api/extensions/catalog/bwc:skill:test-skill/install", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "target_platforms" in str(body)
    print(f"Empty body rejected with 422: {body}")


def test_install_rejects_empty_target_platforms(client):
    """POST with empty target_platforms list returns 422."""
    resp = client.post(
        "/api/extensions/catalog/bwc:skill:test-skill/install",
        json={"target_platforms": []},
    )
    assert resp.status_code == 422
    print("Empty list rejected with 422")


def test_install_happy_path(client, tmp_path):
    """POST with valid target_platforms installs successfully."""
    fake_path = tmp_path / "installed-skill.md"
    with patch(
        "vibelens.api.extensions.catalog.install_extension",
        return_value=("test-skill", fake_path),
    ):
        resp = client.post(
            "/api/extensions/catalog/bwc:skill:test-skill/install",
            json={"target_platforms": ["claude_code"]},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["installed_path"] == str(fake_path)
    assert "claude_code" in data["results"]
    assert data["results"]["claude_code"]["success"] is True
    print(f"Happy-path install succeeded: {data['message']}")
