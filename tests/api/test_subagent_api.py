"""Integration tests for the subagent management API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vibelens.api.subagent import router
from vibelens.models.enums import AgentType
from vibelens.services.extensions.subagent_service import SubagentService
from vibelens.storage.extension.subagent_store import SubagentStore

SAMPLE_SUBAGENT_MD = """\
---
description: Test subagent
tags:
  - test
---
# Test Subagent
"""


@pytest.fixture
def subagent_service(tmp_path):
    central = SubagentStore(root=tmp_path / "central", create=True)
    agents = {
        AgentType.CLAUDE: SubagentStore(root=tmp_path / "claude", create=True),
    }
    return SubagentService(central=central, agents=agents)


@pytest.fixture
def client(subagent_service, monkeypatch):
    import vibelens.api.subagent as subagent_api
    monkeypatch.setattr(subagent_api, "get_subagent_service", lambda: subagent_service)

    app = FastAPI()
    app.include_router(router, prefix="/api")
    return TestClient(app)


class TestListSubagents:
    def test_returns_empty_list(self, client):
        res = client.get("/api/subagents")
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert "sync_targets" in data

    def test_returns_installed_subagents(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.get("/api/subagents")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "my-subagent"

    def test_search_filters(self, client, subagent_service):
        subagent_service.install(name="alpha", content=SAMPLE_SUBAGENT_MD)
        subagent_service.install(name="beta", content=SAMPLE_SUBAGENT_MD)
        res = client.get("/api/subagents?search=alpha")
        data = res.json()
        assert data["total"] == 1

    def test_pagination(self, client, subagent_service):
        for i in range(3):
            subagent_service.install(name=f"sub-{i:02d}", content=SAMPLE_SUBAGENT_MD)
        res = client.get("/api/subagents?page=2&page_size=2")
        data = res.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1


class TestGetSubagent:
    def test_returns_subagent_with_content(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.get("/api/subagents/my-subagent")
        assert res.status_code == 200
        data = res.json()
        assert data["item"]["name"] == "my-subagent"
        assert "Test subagent" in data["content"]
        assert "path" in data

    def test_not_found(self, client):
        res = client.get("/api/subagents/nonexistent")
        assert res.status_code == 404


class TestInstallSubagent:
    def test_installs_new_subagent(self, client):
        res = client.post(
            "/api/subagents",
            json={"name": "new-subagent", "content": SAMPLE_SUBAGENT_MD},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "new-subagent"

    def test_rejects_duplicate(self, client, subagent_service):
        subagent_service.install(name="existing", content=SAMPLE_SUBAGENT_MD)
        res = client.post(
            "/api/subagents",
            json={"name": "existing", "content": SAMPLE_SUBAGENT_MD},
        )
        assert res.status_code == 409

    def test_rejects_invalid_name(self, client):
        res = client.post(
            "/api/subagents",
            json={"name": "Not Valid", "content": SAMPLE_SUBAGENT_MD},
        )
        assert res.status_code == 422


class TestModifySubagent:
    def test_updates_subagent(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.put(
            "/api/subagents/my-subagent",
            json={"content": "---\ndescription: Updated\n---\nNew body."},
        )
        assert res.status_code == 200
        assert res.json()["description"] == "Updated"

    def test_not_found(self, client):
        res = client.put(
            "/api/subagents/nonexistent",
            json={"content": "some content"},
        )
        assert res.status_code == 404


class TestUninstallSubagent:
    def test_deletes_subagent(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.delete("/api/subagents/my-subagent")
        assert res.status_code == 200
        data = res.json()
        assert data["deleted"] == "my-subagent"

    def test_not_found(self, client):
        res = client.delete("/api/subagents/nonexistent")
        assert res.status_code == 404


class TestSyncSubagent:
    def test_syncs_to_agent(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.post(
            "/api/subagents/my-subagent/agents",
            json={"agents": ["claude"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["results"]["claude"] is True

    def test_not_found(self, client):
        res = client.post(
            "/api/subagents/nonexistent/agents",
            json={"agents": ["claude"]},
        )
        assert res.status_code == 404


class TestUnsyncSubagent:
    def test_unsyncs_from_agent(self, client, subagent_service):
        subagent_service.install(
            name="my-subagent", content=SAMPLE_SUBAGENT_MD, sync_to=["claude"]
        )
        res = client.delete("/api/subagents/my-subagent/agents/claude")
        assert res.status_code == 200

    def test_agent_not_found(self, client, subagent_service):
        subagent_service.install(name="my-subagent", content=SAMPLE_SUBAGENT_MD)
        res = client.delete("/api/subagents/my-subagent/agents/unknown")
        assert res.status_code == 404


class TestImportFromAgent:
    def test_imports_all(self, client, subagent_service):
        subagent_service._agents["claude"].write("agent-sub", SAMPLE_SUBAGENT_MD)
        res = client.post("/api/subagents/import/claude")
        assert res.status_code == 200
        data = res.json()
        assert "agent-sub" in data["imported"]

    def test_unknown_agent(self, client):
        res = client.post("/api/subagents/import/unknown")
        assert res.status_code == 404
