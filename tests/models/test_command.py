"""Tests for the Command model."""

import pytest

from vibelens.models.extension.command import Command


def test_command_defaults():
    """Command with only name should have sensible defaults."""
    command = Command(name="my-command")
    assert command.name == "my-command"
    assert command.description == ""
    assert command.tags == []
    assert command.content_hash == ""
    assert command.installed_in == []


def test_command_full_fields():
    """Command with all fields set."""
    command = Command(
        name="test-command",
        description="A test command",
        tags=["testing", "demo"],
        content_hash="abc123",
        installed_in=["claude", "codex"],
    )
    assert command.description == "A test command"
    assert command.tags == ["testing", "demo"]
    assert command.installed_in == ["claude", "codex"]


def test_command_name_validation_rejects_non_kebab():
    """Non-kebab-case names are rejected."""
    with pytest.raises(ValueError, match="kebab-case"):
        Command(name="Not Valid")

    with pytest.raises(ValueError, match="kebab-case"):
        Command(name="camelCase")


def test_command_name_validation_accepts_kebab():
    """Valid kebab-case names are accepted."""
    command = Command(name="multi-word-command")
    assert command.name == "multi-word-command"

    command = Command(name="simple")
    assert command.name == "simple"


def test_command_serialization():
    """Command serializes to dict cleanly."""
    command = Command(name="my-command", description="desc", tags=["a"])
    data = command.model_dump()
    assert data["name"] == "my-command"
    assert data["tags"] == ["a"]
    assert data["installed_in"] == []
