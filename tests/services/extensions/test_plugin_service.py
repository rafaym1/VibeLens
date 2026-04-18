"""Tests for PluginService + PluginStore parity with SkillService."""

import json
from pathlib import Path

import pytest

from vibelens.services.extensions.plugin_service import PluginService
from vibelens.storage.extension.plugin_stores import PluginStore

MANIFEST_TEMPLATE = {
    "name": "my-plugin",
    "version": "1.0.0",
    "description": "Example plugin.",
    "keywords": ["testing"],
}


def _manifest_text(name: str = "my-plugin", version: str = "1.0.0") -> str:
    data = dict(MANIFEST_TEMPLATE, name=name, version=version)
    return json.dumps(data, indent=2)


@pytest.fixture
def service(tmp_path: Path) -> PluginService:
    central = PluginStore(tmp_path / "central", create=True)
    cursor_store = PluginStore(tmp_path / "cursor_plugins", create=True)
    return PluginService(central=central, agents={"cursor": cursor_store})


def test_install_writes_central_and_syncs(service: PluginService, tmp_path: Path):
    service.install(
        name="my-plugin", content=_manifest_text(), sync_to=["cursor"]
    )
    central_manifest = tmp_path / "central" / "my-plugin" / ".claude-plugin" / "plugin.json"
    cursor_manifest = (
        tmp_path / "cursor_plugins" / "my-plugin" / ".claude-plugin" / "plugin.json"
    )
    assert central_manifest.is_file()
    assert cursor_manifest.is_file()


def test_get_item_returns_parsed_plugin(service: PluginService):
    service.install(name="my-plugin", content=_manifest_text())
    plugin = service.get_item("my-plugin")
    assert plugin.name == "my-plugin"
    assert plugin.version == "1.0.0"
    assert "testing" in plugin.tags
    assert plugin.installed_in == []


def test_list_items_includes_installed_in(service: PluginService):
    service.install(
        name="my-plugin", content=_manifest_text(), sync_to=["cursor"]
    )
    items, total = service.list_items()
    assert total == 1
    assert items[0].installed_in == ["cursor"]


def test_modify_rewrites_central_and_resyncs(service: PluginService, tmp_path: Path):
    service.install(
        name="my-plugin", content=_manifest_text(), sync_to=["cursor"]
    )
    service.modify(name="my-plugin", content=_manifest_text(version="2.0.0"))
    cursor_manifest = (
        tmp_path / "cursor_plugins" / "my-plugin" / ".claude-plugin" / "plugin.json"
    )
    data = json.loads(cursor_manifest.read_text())
    assert data["version"] == "2.0.0"


def test_uninstall_removes_central_and_agents(service: PluginService, tmp_path: Path):
    service.install(
        name="my-plugin", content=_manifest_text(), sync_to=["cursor"]
    )
    removed_from = service.uninstall("my-plugin")
    assert removed_from == ["cursor"]
    assert not (tmp_path / "central" / "my-plugin").exists()
    assert not (tmp_path / "cursor_plugins" / "my-plugin").exists()


def test_uninstall_from_agent_keeps_central(service: PluginService, tmp_path: Path):
    service.install(
        name="my-plugin", content=_manifest_text(), sync_to=["cursor"]
    )
    service.uninstall_from_agent("my-plugin", "cursor")
    assert (tmp_path / "central" / "my-plugin" / ".claude-plugin" / "plugin.json").is_file()
    assert not (tmp_path / "cursor_plugins" / "my-plugin").exists()


def test_import_from_agent_copies_back_to_central(tmp_path: Path):
    central = PluginStore(tmp_path / "central", create=True)
    cursor_store = PluginStore(tmp_path / "cursor_plugins", create=True)
    cursor_store.write("handcrafted", _manifest_text(name="handcrafted"))
    # Ensure manifest is in the expected layout
    manifest_dir = tmp_path / "cursor_plugins" / "handcrafted" / ".claude-plugin"
    assert (manifest_dir / "plugin.json").is_file()

    service = PluginService(central=central, agents={"cursor": cursor_store})
    imported = service.import_all_from_agent("cursor")
    assert "handcrafted" in imported
    assert central.exists("handcrafted")
