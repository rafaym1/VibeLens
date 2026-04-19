"""Tests for GET /extensions/agents."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from vibelens.app import create_app
from vibelens.services.extensions.platforms import rebuild_platforms


@pytest.fixture
def client_with_fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    (tmp_path / ".claude").mkdir()
    # Rebuild the platform table against the patched home so ``PLATFORMS``
    # reflects ``tmp_path`` instead of the real user dir.
    rebuild_platforms()
    try:
        yield TestClient(create_app())
    finally:
        rebuild_platforms()


def test_agents_endpoint_returns_list(client_with_fake_home: TestClient):
    resp = client_with_fake_home.get("/api/extensions/agents")
    assert resp.status_code == 200
    body = resp.json()
    assert "agents" in body

    claude = next((a for a in body["agents"] if a["key"] == "claude"), None)
    assert claude is not None
    assert claude["installed"] is True
    assert "skill" in claude["supported_types"]
    assert "plugin" in claude["supported_types"]

    cursor = next((a for a in body["agents"] if a["key"] == "cursor"), None)
    assert cursor is not None
    assert cursor["installed"] is False


def test_agents_endpoint_includes_all_known_platforms(client_with_fake_home: TestClient):
    resp = client_with_fake_home.get("/api/extensions/agents")
    body = resp.json()
    keys = {a["key"] for a in body["agents"]}
    assert {"claude", "codex", "cursor", "opencode", "gemini", "copilot"}.issubset(keys)
