"""Tests for extension catalog API endpoints."""

from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app
from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import AgentExtensionItem
from vibelens.storage.extension.catalog import CatalogManifest, CatalogSnapshot


def _make_item(
    *,
    extension_id: str,
    extension_type: AgentExtensionType,
    name: str,
    description: str,
    topics: list[str] | None = None,
) -> AgentExtensionItem:
    return AgentExtensionItem(
        extension_id=extension_id,
        extension_type=extension_type,
        name=name,
        description=description,
        topics=topics or [],
        source_url=f"https://github.com/test/{name}/tree/main",
        repo_full_name=f"test/{name}",
        discovery_source="seed",
        quality_score=80.0,
        popularity=0.5,
        stars=10,
        forks=0,
    )


def _make_snapshot() -> CatalogSnapshot:
    items = [
        _make_item(
            extension_id="bwc:skill:test-skill",
            extension_type=AgentExtensionType.SKILL,
            name="test-skill",
            description="A test skill",
            topics=["testing"],
        ),
        _make_item(
            extension_id="bwc:plugin:test-plugin",
            extension_type=AgentExtensionType.PLUGIN,
            name="test-plugin",
            description="A test plugin",
            topics=["plugin"],
        ),
    ]
    manifest = CatalogManifest(
        generated_on="2026-04-13",
        hub_source="test",
        total=len(items),
        item_counts={"skill": 1, "plugin": 1},
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


def test_list_extensions(client):
    resp = client.get("/api/extensions/catalog")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    print(f"Listed {data['total']} items")


def test_list_extensions_search(client):
    resp = client.get("/api/extensions/catalog?search=plugin")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["extension_id"] == "bwc:plugin:test-plugin"


def test_list_extensions_type_filter(client):
    resp = client.get("/api/extensions/catalog?extension_type=skill")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["extension_type"] == "skill"


def test_list_extensions_accepts_deprecated_category_param(client):
    """Old clients passing ?category=... still get 200 (param ignored)."""
    resp = client.get("/api/extensions/catalog?category=testing")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_list_extensions_accepts_deprecated_platform_param(client):
    resp = client.get("/api/extensions/catalog?platform=claude")
    assert resp.status_code == 200
    assert resp.json()["total"] == 2


def test_meta_returns_topics(client):
    resp = client.get("/api/extensions/catalog/meta")
    assert resp.status_code == 200
    data = resp.json()
    assert "topics" in data
    assert sorted(data["topics"]) == ["plugin", "testing"]


def test_get_extension_item_returns_summary_when_offsets_empty(client):
    """Detail endpoint falls back to summary when get_full has no offsets."""
    resp = client.get("/api/extensions/catalog/bwc:skill:test-skill")
    assert resp.status_code == 200
    body = resp.json()
    assert body["extension_id"] == "bwc:skill:test-skill"
    # Detail-only fields stay None when hydration falls back to summary.
    assert body["item_metadata"] is None


def test_get_extension_item_not_found(client):
    resp = client.get("/api/extensions/catalog/nonexistent")
    assert resp.status_code == 404
