"""Platform registry and capability matrix tests."""

from dataclasses import replace
from unittest.mock import patch

import pytest

from vibelens.models.enums import AgentExtensionType, ExtensionSource
from vibelens.services.extensions.platforms import (
    PLATFORMS,
    get_platform,
    installed_platforms,
)


def test_claude_supports_all_five_types():
    claude = PLATFORMS[ExtensionSource.CLAUDE]
    assert claude.supported_types == frozenset(
        {
            AgentExtensionType.SKILL,
            AgentExtensionType.COMMAND,
            AgentExtensionType.SUBAGENT,
            AgentExtensionType.HOOK,
            AgentExtensionType.PLUGIN,
        }
    )


def test_codex_does_not_support_command():
    codex = PLATFORMS[ExtensionSource.CODEX]
    assert AgentExtensionType.COMMAND not in codex.supported_types
    assert AgentExtensionType.SKILL in codex.supported_types
    assert AgentExtensionType.SUBAGENT in codex.supported_types


def test_openhands_skill_only():
    openhands = PLATFORMS[ExtensionSource.OPENHANDS]
    assert openhands.supported_types == frozenset({AgentExtensionType.SKILL})


def test_install_key_removed():
    claude = PLATFORMS[ExtensionSource.CLAUDE]
    assert not hasattr(claude, "install_key")


def test_hook_config_key_is_tuple():
    claude = PLATFORMS[ExtensionSource.CLAUDE]
    assert claude.hook_config_key == ("hooks",)
    assert isinstance(claude.hook_config_key, tuple)


def test_cursor_hook_config_path_is_hooks_json():
    cursor = PLATFORMS[ExtensionSource.CURSOR]
    assert cursor.hook_config_path is not None
    assert cursor.hook_config_path.name == "hooks.json"


def test_codex_hook_config_path_is_hooks_json():
    codex = PLATFORMS[ExtensionSource.CODEX]
    assert codex.hook_config_path is not None
    assert codex.hook_config_path.name == "hooks.json"


def test_get_platform_returns_claude():
    claude = get_platform("claude")
    assert claude.source == ExtensionSource.CLAUDE


def test_get_platform_unknown_raises():
    with pytest.raises(ValueError, match="Unknown agent"):
        get_platform("does-not-exist")


def test_installed_platforms_filters_by_root_exists(tmp_path):
    fake_claude_root = tmp_path / "claude_root"
    fake_claude_root.mkdir()
    fake_cursor_root = tmp_path / "cursor_root"  # intentionally not created

    fake_claude = replace(PLATFORMS[ExtensionSource.CLAUDE], root=fake_claude_root)
    fake_cursor = replace(PLATFORMS[ExtensionSource.CURSOR], root=fake_cursor_root)

    override = {
        ExtensionSource.CLAUDE: fake_claude,
        ExtensionSource.CURSOR: fake_cursor,
    }
    with patch.dict(PLATFORMS, override):
        installed = installed_platforms()
        assert "claude" in installed
        assert "cursor" not in installed
