"""Tests for the Hook model."""

import pytest

from vibelens.models.extension.hook import Hook


def test_hook_defaults():
    """Hook with only name should have sensible defaults."""
    hook = Hook(name="my-hook")
    assert hook.name == "my-hook"
    assert hook.description == ""
    assert hook.topics == []
    assert hook.hook_config == {}
    assert hook.content_hash == ""
    assert hook.installed_in == []


def test_hook_full_fields():
    """Hook with all fields set."""
    config = {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "/bin/echo"}],
            }
        ]
    }
    hook = Hook(
        name="safety-guard",
        description="Blocks dangerous commands",
        topics=["safety", "bash"],
        hook_config=config,
        content_hash="abc123",
        installed_in=["claude"],
    )
    assert hook.description == "Blocks dangerous commands"
    assert hook.topics == ["safety", "bash"]
    assert hook.hook_config == config
    assert hook.installed_in == ["claude"]


def test_hook_name_validation_rejects_non_kebab():
    """Non-kebab-case names are rejected."""
    with pytest.raises(ValueError, match="kebab-case"):
        Hook(name="Not Valid")

    with pytest.raises(ValueError, match="kebab-case"):
        Hook(name="camelCase")

    with pytest.raises(ValueError, match="kebab-case"):
        Hook(name="UPPER")


def test_hook_name_validation_accepts_kebab():
    """Valid kebab-case names are accepted."""
    assert Hook(name="multi-word-hook").name == "multi-word-hook"
    assert Hook(name="simple").name == "simple"
    assert Hook(name="a1-b2-c3").name == "a1-b2-c3"


def test_hook_serialization():
    """Hook serializes to dict cleanly."""
    hook = Hook(
        name="my-hook",
        description="desc",
        topics=["a"],
        hook_config={"PreToolUse": []},
    )
    data = hook.model_dump()
    assert data["name"] == "my-hook"
    assert data["topics"] == ["a"]
    assert data["hook_config"] == {"PreToolUse": []}
    assert data["installed_in"] == []
