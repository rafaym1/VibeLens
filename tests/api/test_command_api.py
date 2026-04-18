"""Integration tests for the command management API."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from vibelens.api.extensions.factory import build_typed_router
from vibelens.models.enums import AgentExtensionType
from vibelens.services.extensions.command_service import CommandService
from vibelens.storage.extension.command_store import CommandStore

SAMPLE_COMMAND_MD = """\
---
description: Test command
tags:
  - test
---
# Test Command
"""


@pytest.fixture
def command_service(tmp_path):
    central = CommandStore(root=tmp_path / "central", create=True)
    agents = {
        "claude": CommandStore(root=tmp_path / "claude", create=True),
    }
    return CommandService(central=central, agents=agents)


@pytest.fixture
def client(command_service):
    router = build_typed_router(lambda: command_service, AgentExtensionType.COMMAND)
    app = FastAPI()
    app.include_router(router, prefix="/api/extensions")
    return TestClient(app)


class TestListCommands:
    def test_returns_empty_list(self, client):
        res = client.get("/api/extensions/commands")
        assert res.status_code == 200
        data = res.json()
        assert data["items"] == []
        assert data["total"] == 0
        assert "sync_targets" in data

    def test_returns_installed_commands(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.get("/api/extensions/commands")
        data = res.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "my-command"

    def test_search_filters(self, client, command_service):
        command_service.install(name="alpha", content=SAMPLE_COMMAND_MD)
        command_service.install(name="beta", content=SAMPLE_COMMAND_MD)
        res = client.get("/api/extensions/commands?search=alpha")
        data = res.json()
        assert data["total"] == 1

    def test_pagination(self, client, command_service):
        for i in range(3):
            command_service.install(name=f"cmd-{i:02d}", content=SAMPLE_COMMAND_MD)
        res = client.get("/api/extensions/commands?page=2&page_size=2")
        data = res.json()
        assert data["total"] == 3
        assert len(data["items"]) == 1


class TestGetCommand:
    def test_returns_command_with_content(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.get("/api/extensions/commands/my-command")
        assert res.status_code == 200
        data = res.json()
        assert data["item"]["name"] == "my-command"
        assert "Test command" in data["content"]
        assert "path" in data

    def test_not_found(self, client):
        res = client.get("/api/extensions/commands/nonexistent")
        assert res.status_code == 404


class TestInstallCommand:
    def test_installs_new_command(self, client):
        res = client.post(
            "/api/extensions/commands",
            json={"name": "new-command", "content": SAMPLE_COMMAND_MD},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["name"] == "new-command"

    def test_rejects_duplicate(self, client, command_service):
        command_service.install(name="existing", content=SAMPLE_COMMAND_MD)
        res = client.post(
            "/api/extensions/commands",
            json={"name": "existing", "content": SAMPLE_COMMAND_MD},
        )
        assert res.status_code == 409

    def test_rejects_invalid_name(self, client):
        res = client.post(
            "/api/extensions/commands",
            json={"name": "Not Valid", "content": SAMPLE_COMMAND_MD},
        )
        assert res.status_code == 422


class TestModifyCommand:
    def test_updates_command(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.put(
            "/api/extensions/commands/my-command",
            json={"content": "---\ndescription: Updated\n---\nNew body."},
        )
        assert res.status_code == 200
        assert res.json()["description"] == "Updated"

    def test_not_found(self, client):
        res = client.put(
            "/api/extensions/commands/nonexistent",
            json={"content": "some content"},
        )
        assert res.status_code == 404


class TestUninstallCommand:
    def test_deletes_command(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.delete("/api/extensions/commands/my-command")
        assert res.status_code == 200
        data = res.json()
        assert data["deleted"] == "my-command"

    def test_not_found(self, client):
        res = client.delete("/api/extensions/commands/nonexistent")
        assert res.status_code == 404


class TestSyncCommand:
    def test_syncs_to_agent(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.post(
            "/api/extensions/commands/my-command/agents",
            json={"agents": ["claude"]},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["results"]["claude"] is True

    def test_not_found(self, client):
        res = client.post(
            "/api/extensions/commands/nonexistent/agents",
            json={"agents": ["claude"]},
        )
        assert res.status_code == 404


class TestUnsyncCommand:
    def test_unsyncs_from_agent(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD, sync_to=["claude"])
        res = client.delete("/api/extensions/commands/my-command/agents/claude")
        assert res.status_code == 200

    def test_agent_not_found(self, client, command_service):
        command_service.install(name="my-command", content=SAMPLE_COMMAND_MD)
        res = client.delete("/api/extensions/commands/my-command/agents/unknown")
        assert res.status_code == 404


class TestImportFromAgent:
    def test_imports_all(self, client, command_service):
        command_service._agents["claude"].write("agent-cmd", SAMPLE_COMMAND_MD)
        res = client.post("/api/extensions/commands/import/claude")
        assert res.status_code == 200
        data = res.json()
        assert "agent-cmd" in data["imported"]

    def test_unknown_agent(self, client):
        res = client.post("/api/extensions/commands/import/unknown")
        assert res.status_code == 404
