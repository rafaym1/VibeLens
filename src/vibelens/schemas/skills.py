"""Skill API schemas — request models for skill management."""

from pydantic import BaseModel, Field


class SkillWriteRequest(BaseModel):
    """Request body for creating or updating a skill."""

    name: str = Field(description="Skill name in kebab-case.")
    content: str = Field(description="Full SKILL.md content including frontmatter.")


class SkillLoadRequest(BaseModel):
    """Request body for loading skills from an agent-native store into the central store."""

    overwrite: bool = Field(default=False, description="Overwrite existing central skills.")


class SkillSyncRequest(BaseModel):
    """Request body for syncing a skill to agent interfaces."""

    targets: list[str] = Field(
        description="Agent interface keys to sync to (e.g. 'claude_code', 'codex')."
    )


class FeaturedSkillInstallRequest(BaseModel):
    """Request body for installing a featured skill from the catalog."""

    slug: str = Field(description="Skill slug from featured-skills.json.")
    targets: list[str] = Field(
        default_factory=list,
        description="Agent interface keys to install to. Empty = central only.",
    )
