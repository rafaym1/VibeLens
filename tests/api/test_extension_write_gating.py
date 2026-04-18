"""Verify demo mode blocks extension write routes."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app


@pytest.fixture
def demo_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    monkeypatch.setenv("VIBELENS_MODE", "demo")
    (tmp_path / ".claude").mkdir()
    app = create_app()
    return TestClient(app)


def test_catalog_install_blocked_in_demo(demo_client: TestClient):
    resp = demo_client.post(
        "/api/extensions/catalog/test-item/install",
        json={"target_platforms": ["claude"], "overwrite": True},
    )
    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_restricted"


def test_plugin_uninstall_blocked_in_demo(demo_client: TestClient):
    resp = demo_client.delete("/api/extensions/plugins/foo/agents/claude")
    assert resp.status_code == 403
    assert resp.json()["detail"] == "demo_mode_restricted"


def test_plugin_install_blocked_in_demo(demo_client: TestClient):
    resp = demo_client.post(
        "/api/extensions/plugins",
        json={"name": "x", "content": "{}", "sync_to": []},
    )
    assert resp.status_code == 403


def test_plugin_delete_blocked_in_demo(demo_client: TestClient):
    resp = demo_client.delete("/api/extensions/plugins/foo")
    assert resp.status_code == 403


def test_skill_install_blocked_in_demo(demo_client: TestClient):
    resp = demo_client.post(
        "/api/extensions/skills",
        json={"name": "x", "content": "y", "sync_to": []},
    )
    assert resp.status_code == 403


def test_get_agents_open_in_demo(demo_client: TestClient):
    resp = demo_client.get("/api/extensions/agents")
    assert resp.status_code == 200
