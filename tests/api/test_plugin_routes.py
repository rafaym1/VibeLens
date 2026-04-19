"""Integration tests for the factory-generated /extensions/plugins routes."""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app
from vibelens.services.extensions.platforms import rebuild_platforms


def _manifest_text(name: str = "my-plugin", version: str = "1.0.0") -> str:
    return json.dumps(
        {
            "name": name,
            "version": version,
            "description": "Example plugin.",
            "keywords": ["testing"],
        },
        indent=2,
    )


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".claude").mkdir()
    rebuild_platforms()
    try:
        yield TestClient(create_app())
    finally:
        rebuild_platforms()


def test_list_empty_plugins(client: TestClient):
    resp = client.get("/api/extensions/plugins")
    assert resp.status_code == 200
    body = resp.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_install_and_list_plugin(client: TestClient):
    resp = client.post(
        "/api/extensions/plugins",
        json={"name": "my-plugin", "content": _manifest_text(), "sync_to": []},
    )
    assert resp.status_code == 200
    resp_list = client.get("/api/extensions/plugins")
    body = resp_list.json()
    assert body["total"] == 1
    assert body["items"][0]["name"] == "my-plugin"
    assert body["items"][0]["version"] == "1.0.0"


def test_get_plugin_detail(client: TestClient):
    client.post(
        "/api/extensions/plugins",
        json={"name": "my-plugin", "content": _manifest_text(), "sync_to": []},
    )
    resp = client.get("/api/extensions/plugins/my-plugin")
    assert resp.status_code == 200
    body = resp.json()
    assert body["item"]["name"] == "my-plugin"
    assert "plugin.json" in body["path"]
    manifest = json.loads(body["content"])
    assert manifest["version"] == "1.0.0"


def test_modify_updates_version(client: TestClient):
    client.post(
        "/api/extensions/plugins",
        json={"name": "my-plugin", "content": _manifest_text(), "sync_to": []},
    )
    resp = client.put(
        "/api/extensions/plugins/my-plugin",
        json={"content": _manifest_text(version="2.0.0")},
    )
    assert resp.status_code == 200
    resp_detail = client.get("/api/extensions/plugins/my-plugin")
    manifest = json.loads(resp_detail.json()["content"])
    assert manifest["version"] == "2.0.0"


def test_uninstall_plugin(client: TestClient):
    client.post(
        "/api/extensions/plugins",
        json={"name": "my-plugin", "content": _manifest_text(), "sync_to": []},
    )
    resp = client.delete("/api/extensions/plugins/my-plugin")
    assert resp.status_code == 200
    assert resp.json()["deleted"] == "my-plugin"
    resp_list = client.get("/api/extensions/plugins")
    assert resp_list.json()["total"] == 0


def test_unknown_plugin_returns_404(client: TestClient):
    resp = client.get("/api/extensions/plugins/does-not-exist")
    assert resp.status_code == 404
