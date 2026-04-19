"""Tests for the /extensions/{type}s/{name}/tree + /files endpoints."""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vibelens.api.extensions.factory import build_typed_router
from vibelens.models.enums import AgentExtensionType
from vibelens.services.extensions.plugin_service import PluginService
from vibelens.services.extensions.skill_service import SkillService
from vibelens.services.extensions.subagent_service import SubagentService
from vibelens.storage.extension.plugin_stores import PluginStore
from vibelens.storage.extension.skill_store import SkillStore
from vibelens.storage.extension.subagent_store import SubagentStore

SKILL_MD = """\
---
description: A sample skill
tags: []
---
# sample
body
"""

SUBAGENT_MD = """\
---
name: reviewer
description: A sample subagent
---
body
"""


@pytest.fixture
def skill_client(tmp_path):
    central = SkillStore(root=tmp_path / "central", create=True)
    service = SkillService(central=central, agents={})
    service.install(name="frontend-design", content=SKILL_MD)
    # Add a sibling file to exercise the tree walk
    (central._item_path("frontend-design").parent / "LICENSE.txt").write_text(
        "MIT License"
    )
    app = FastAPI()
    app.include_router(
        build_typed_router(lambda: service, AgentExtensionType.SKILL),
        prefix="/api/extensions",
    )
    return TestClient(app)


@pytest.fixture
def subagent_client(tmp_path):
    central = SubagentStore(root=tmp_path / "central", create=True)
    service = SubagentService(central=central, agents={})
    service.install(name="reviewer", content=SUBAGENT_MD)
    app = FastAPI()
    app.include_router(
        build_typed_router(lambda: service, AgentExtensionType.SUBAGENT),
        prefix="/api/extensions",
    )
    return TestClient(app)


class TestSkillTree:
    def test_tree_lists_skill_and_sibling_files(self, skill_client):
        res = skill_client.get("/api/extensions/skills/frontend-design/tree")
        assert res.status_code == 200
        data = res.json()
        paths = {e["path"] for e in data["entries"]}
        assert "SKILL.md" in paths
        assert "LICENSE.txt" in paths
        assert data["name"] == "frontend-design"
        assert data["truncated"] is False

    def test_file_returns_content(self, skill_client):
        res = skill_client.get("/api/extensions/skills/frontend-design/files/SKILL.md")
        assert res.status_code == 200
        data = res.json()
        assert data["path"] == "SKILL.md"
        assert "# sample" in data["content"]
        assert data["truncated"] is False

    def test_raw_dotdot_path_is_normalized_by_fastapi(self, skill_client):
        """Unencoded ``..`` segments are stripped by FastAPI before the handler
        runs; the route just doesn't match and returns 404.
        """
        res = skill_client.get(
            "/api/extensions/skills/frontend-design/files/../../escape"
        )
        assert res.status_code == 404

    def test_percent_encoded_dotdot_is_rejected_by_guard(self, skill_client):
        """Percent-encoded ``..`` slips past FastAPI's normalization and
        arrives at the handler, which must reject it via the
        ``is_relative_to`` check - not silently read an out-of-root file.
        """
        # Path segment is ``%2e%2e%2fescape`` -> decoded to ``../escape``
        res = skill_client.get(
            "/api/extensions/skills/frontend-design/files/%2e%2e%2fescape"
        )
        assert res.status_code == 404

    def test_absolute_path_is_rejected(self, skill_client):
        """An absolute path should not be resolvable from inside the item root."""
        res = skill_client.get(
            "/api/extensions/skills/frontend-design/files/%2fetc%2fhosts"
        )
        assert res.status_code == 404

    def test_unknown_skill_returns_404(self, skill_client):
        res = skill_client.get("/api/extensions/skills/does-not-exist/tree")
        assert res.status_code == 404


class TestSubagentTree:
    def test_tree_lists_single_file(self, subagent_client):
        res = subagent_client.get("/api/extensions/subagents/reviewer/tree")
        assert res.status_code == 200
        data = res.json()
        assert len(data["entries"]) == 1
        assert data["entries"][0]["kind"] == "file"
        assert data["entries"][0]["path"].endswith(".md")

    def test_file_returns_content(self, subagent_client):
        res = subagent_client.get("/api/extensions/subagents/reviewer/tree")
        filename = res.json()["entries"][0]["path"]
        res2 = subagent_client.get(
            f"/api/extensions/subagents/reviewer/files/{filename}"
        )
        assert res2.status_code == 200
        assert "body" in res2.json()["content"]


@pytest.fixture
def plugin_client(tmp_path):
    """Plugin store writes <name>/.claude-plugin/plugin.json - verify the tree
    endpoint exposes the plugin dir root, not the inner .claude-plugin dir.
    """
    central = PluginStore(root=tmp_path / "central", create=True)
    service = PluginService(central=central, agents={})
    manifest = json.dumps(
        {
            "name": "my-plugin",
            "version": "1.0.0",
            "description": "A sample plugin",
            "keywords": [],
        },
        indent=2,
    )
    service.install(name="my-plugin", content=manifest)
    # Drop a sibling asset under the plugin dir so the tree walk has more than
    # just the manifest to return.
    plugin_dir = tmp_path / "central" / "my-plugin"
    (plugin_dir / "skills").mkdir()
    (plugin_dir / "skills" / "hello.md").write_text("# hello\n")

    app = FastAPI()
    app.include_router(
        build_typed_router(lambda: service, AgentExtensionType.PLUGIN),
        prefix="/api/extensions",
    )
    return TestClient(app)


class TestPluginTree:
    def test_tree_walks_full_plugin_dir_not_manifest_dir(self, plugin_client):
        res = plugin_client.get("/api/extensions/plugins/my-plugin/tree")
        assert res.status_code == 200
        data = res.json()
        paths = {e["path"] for e in data["entries"]}
        # Manifest should appear under .claude-plugin/, not at the top level.
        assert ".claude-plugin/plugin.json" in paths
        # Sibling asset must be reachable too - proves we walk the plugin root,
        # not the manifest's containing .claude-plugin/ dir.
        assert "skills/hello.md" in paths
        assert "skills" in paths
        print(f"plugin tree paths: {sorted(paths)}")

    def test_file_read_reaches_nested_manifest(self, plugin_client):
        res = plugin_client.get(
            "/api/extensions/plugins/my-plugin/files/.claude-plugin/plugin.json"
        )
        assert res.status_code == 200
        data = res.json()
        assert "my-plugin" in data["content"]

    def test_file_read_reaches_sibling_asset(self, plugin_client):
        res = plugin_client.get(
            "/api/extensions/plugins/my-plugin/files/skills/hello.md"
        )
        assert res.status_code == 200
        assert "# hello" in res.json()["content"]
