"""Tests for the Subagent model."""

import pytest

from vibelens.models.extension.subagent import Subagent


def test_subagent_defaults():
    """Subagent with only name should have sensible defaults."""
    subagent = Subagent(name="my-subagent")
    assert subagent.name == "my-subagent"
    assert subagent.description == ""
    assert subagent.tags == []
    assert subagent.content_hash == ""
    assert subagent.installed_in == []


def test_subagent_full_fields():
    """Subagent with all fields set."""
    subagent = Subagent(
        name="test-subagent",
        description="A test subagent",
        tags=["testing", "demo"],
        content_hash="abc123",
        installed_in=["claude", "codex"],
    )
    assert subagent.description == "A test subagent"
    assert subagent.tags == ["testing", "demo"]
    assert subagent.installed_in == ["claude", "codex"]


def test_subagent_name_validation_rejects_non_kebab():
    """Non-kebab-case names are rejected."""
    with pytest.raises(ValueError, match="kebab-case"):
        Subagent(name="Not Valid")

    with pytest.raises(ValueError, match="kebab-case"):
        Subagent(name="camelCase")


def test_subagent_name_validation_accepts_kebab():
    """Valid kebab-case names are accepted."""
    subagent = Subagent(name="multi-word-subagent")
    assert subagent.name == "multi-word-subagent"

    subagent = Subagent(name="simple")
    assert subagent.name == "simple"


def test_subagent_serialization():
    """Subagent serializes to dict cleanly."""
    subagent = Subagent(name="my-subagent", description="desc", tags=["a"])
    data = subagent.model_dump()
    assert data["name"] == "my-subagent"
    assert data["tags"] == ["a"]
    assert data["installed_in"] == []
