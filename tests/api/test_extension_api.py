"""Tests for the extension install endpoint."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app
from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import AgentExtensionItem
from vibelens.storage.extension.catalog import CatalogManifest, CatalogSnapshot


def _make_snapshot() -> CatalogSnapshot:
    items = [
        AgentExtensionItem(
            extension_id="bwc:skill:test-skill",
            extension_type=AgentExtensionType.SKILL,
            name="test-skill",
            description="A test skill",
            topics=["testing"],
            source_url="https://github.com/test/repo/tree/main/skills/test",
            repo_full_name="test/repo",
            discovery_source="seed",
            quality_score=80.0,
            popularity=0.5,
            stars=10,
            forks=0,
        ),
        AgentExtensionItem(
            extension_id="bwc:hook:test-hook",
            extension_type=AgentExtensionType.HOOK,
            name="test-hook",
            description="A test hook",
            topics=["hook"],
            source_url="https://github.com/test/repo/tree/main/hooks/test",
            repo_full_name="test/repo",
            discovery_source="seed",
            quality_score=40.0,
            popularity=0.2,
            stars=5,
            forks=0,
        ),
    ]
    manifest = CatalogManifest(
        generated_on="2026-04-13",
        hub_source="test",
        total=len(items),
        item_counts={"skill": 1, "hook": 1},
        file_sizes={},
    )
    return CatalogSnapshot(manifest=manifest, items=items, data_dir=Path("/nonexistent"))


@pytest.fixture
def client():
    snapshot = _make_snapshot()
    with (
        patch("vibelens.services.extensions.catalog.load_catalog", return_value=snapshot),
        patch("vibelens.api.extensions.catalog.load_catalog", return_value=snapshot),
    ):
        app = create_app()
        yield TestClient(app)


def test_install_requires_target_platforms(client):
    resp = client.post("/api/extensions/catalog/bwc:skill:test-skill/install", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert "target_platforms" in str(body)


def test_install_rejects_empty_target_platforms(client):
    resp = client.post(
        "/api/extensions/catalog/bwc:skill:test-skill/install",
        json={"target_platforms": []},
    )
    assert resp.status_code == 422


def test_install_happy_path(client, tmp_path):
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


def test_install_hook_returns_501(client):
    """Catalog HOOK install is gated this release."""
    resp = client.post(
        "/api/extensions/catalog/bwc:hook:test-hook/install",
        json={"target_platforms": ["claude"]},
    )
    assert resp.status_code == 501
    body = resp.json()
    assert "hook" in body["detail"].lower()
