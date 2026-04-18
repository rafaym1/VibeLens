"""Tests for Claude plugin installer (4-file JSON merge)."""

import json
from pathlib import Path

import pytest

from vibelens.storage.extension.plugin_stores.claude_installer import (
    ClaudePluginInstallRequest,
    install_claude_plugin,
    uninstall_claude_plugin,
)


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", staticmethod(lambda: tmp_path))
    return tmp_path


def _make_install_request(version: str = "1.2.3") -> ClaudePluginInstallRequest:
    manifest = {
        "name": "my-plugin",
        "version": version,
        "description": "test plugin",
    }
    return ClaudePluginInstallRequest(
        name="my-plugin",
        description="test",
        install_content=json.dumps({"plugin.json": manifest}),
        source_url="",
        log_id="test/my-plugin",
    )


def test_install_creates_all_four_files(fake_home):
    install_claude_plugin(request=_make_install_request(), overwrite=True)

    vibelens_marketplace = fake_home / ".vibelens" / "claude_marketplace"
    assert (vibelens_marketplace / ".claude-plugin" / "marketplace.json").is_file()
    assert (fake_home / ".claude" / "plugins" / "known_marketplaces.json").is_file()
    assert (fake_home / ".claude" / "plugins" / "installed_plugins.json").is_file()
    assert (fake_home / ".claude" / "settings.json").is_file()
    assert (
        fake_home / ".claude" / "plugins" / "cache" / "vibelens" / "my-plugin" / "1.2.3"
    ).is_dir()


def test_install_settings_enables_plugin(fake_home):
    install_claude_plugin(request=_make_install_request(), overwrite=True)
    settings = json.loads((fake_home / ".claude" / "settings.json").read_text())
    assert settings["enabledPlugins"]["my-plugin@vibelens"] is True


def test_install_preserves_unrelated_settings(fake_home):
    settings_path = fake_home / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(
        json.dumps({"alwaysThinkingEnabled": False, "userKey": "keep-me"})
    )

    install_claude_plugin(request=_make_install_request(), overwrite=True)

    settings = json.loads(settings_path.read_text())
    assert settings["alwaysThinkingEnabled"] is False
    assert settings["userKey"] == "keep-me"
    assert settings["enabledPlugins"]["my-plugin@vibelens"] is True


def test_install_installed_plugins_version_2(fake_home):
    install_claude_plugin(request=_make_install_request(), overwrite=True)
    state = json.loads(
        (fake_home / ".claude" / "plugins" / "installed_plugins.json").read_text()
    )
    assert state["version"] == 2
    entry = state["plugins"]["my-plugin@vibelens"][0]
    assert entry["version"] == "1.2.3"
    assert entry["scope"] == "user"
    assert "cache/vibelens/my-plugin/1.2.3" in entry["installPath"]


def test_schema_drift_guard(fake_home):
    state_path = fake_home / ".claude" / "plugins" / "installed_plugins.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"version": 3, "plugins": {}}))

    with pytest.raises(RuntimeError, match="unsupported installed_plugins.json version"):
        install_claude_plugin(request=_make_install_request(), overwrite=True)


def test_install_rejects_existing_when_overwrite_false(fake_home):
    install_claude_plugin(request=_make_install_request(), overwrite=True)
    with pytest.raises(FileExistsError):
        install_claude_plugin(request=_make_install_request(), overwrite=False)


def test_install_rejects_malformed_install_content(fake_home):
    request = ClaudePluginInstallRequest(
        name="broken",
        description="",
        install_content=json.dumps({"not_plugin_json": {}}),
        source_url="",
        log_id="broken",
    )
    with pytest.raises(ValueError, match="must include 'plugin.json'"):
        install_claude_plugin(request=request, overwrite=True)


def test_uninstall_removes_only_vibelens_entries(fake_home):
    state_path = fake_home / ".claude" / "plugins" / "installed_plugins.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(
            {
                "version": 2,
                "plugins": {
                    "other@someone-else": [
                        {"scope": "user", "installPath": "x", "version": "1.0.0"}
                    ]
                },
            }
        )
    )
    settings_path = fake_home / ".claude" / "settings.json"
    settings_path.write_text(
        json.dumps({"enabledPlugins": {"other@someone-else": True}})
    )

    install_claude_plugin(request=_make_install_request(), overwrite=True)
    uninstall_claude_plugin(name="my-plugin")

    state = json.loads(state_path.read_text())
    assert "my-plugin@vibelens" not in state["plugins"]
    assert "other@someone-else" in state["plugins"]

    settings = json.loads(settings_path.read_text())
    assert "my-plugin@vibelens" not in settings["enabledPlugins"]
    assert settings["enabledPlugins"]["other@someone-else"] is True
