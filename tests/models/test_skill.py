"""Tests for the Skill model."""

from vibelens.models.extension.skill import Skill


def test_skill_defaults():
    """Skill with only name should have sensible defaults."""
    skill = Skill(name="my-skill")
    assert skill.name == "my-skill"
    assert skill.description == ""
    assert skill.topics == []
    assert skill.allowed_tools == []
    assert skill.content_hash == ""
    assert skill.installed_in == []


def test_skill_full_fields():
    """Skill with all fields set."""
    skill = Skill(
        name="test-skill",
        description="A test skill",
        topics=["testing", "demo"],
        allowed_tools=["Bash", "Read"],
        content_hash="abc123",
        installed_in=["claude", "codex"],
    )
    assert skill.description == "A test skill"
    assert skill.topics == ["testing", "demo"]
    assert skill.allowed_tools == ["Bash", "Read"]
    assert skill.installed_in == ["claude", "codex"]


def test_skill_name_validation_rejects_non_kebab():
    """Non-kebab-case names are rejected."""
    import pytest

    with pytest.raises(ValueError, match="kebab-case"):
        Skill(name="Not Valid")

    with pytest.raises(ValueError, match="kebab-case"):
        Skill(name="camelCase")


def test_skill_name_validation_accepts_kebab():
    """Valid kebab-case names are accepted."""
    skill = Skill(name="multi-word-skill")
    assert skill.name == "multi-word-skill"

    skill = Skill(name="simple")
    assert skill.name == "simple"


def test_skill_serialization():
    """Skill serializes to dict cleanly."""
    skill = Skill(name="my-skill", description="desc", topics=["a"])
    data = skill.model_dump()
    assert data["name"] == "my-skill"
    assert data["topics"] == ["a"]
    assert data["installed_in"] == []


def test_skill_accepts_legacy_tags_alias():
    """Existing YAML frontmatter uses `tags:`; must still load."""
    skill = Skill.model_validate({"name": "demo", "description": "x", "tags": ["a", "b"]})
    assert skill.topics == ["a", "b"]


def test_skill_accepts_topics_directly():
    """New code can use `topics:` directly."""
    skill = Skill.model_validate({"name": "demo", "description": "x", "topics": ["a"]})
    assert skill.topics == ["a"]


def test_skill_dumps_topics_by_default():
    """model_dump emits the field name (topics), not the alias."""
    skill = Skill(name="demo", description="x", topics=["a"])
    dumped = skill.model_dump()
    assert "topics" in dumped
    assert "tags" not in dumped
