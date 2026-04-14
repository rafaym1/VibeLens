"""Unified skill metadata models."""

import hashlib
import re
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator

from vibelens.models.skill.source import SkillSourceInfo

# Enforces kebab-case naming (e.g. "test-fix-loop", "commit-with-review")
VALID_SKILL_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class SkillInfo(BaseModel):
    """Simplified skill metadata shared across central and agent stores."""

    name: str = Field(description="Skill identifier in kebab-case.")
    description: str = Field(description="Trigger description from frontmatter.")
    sources: list[SkillSourceInfo] = Field(
        default_factory=list,
        description="All known sources from which this skill was loaded or is available.",
    )
    central_path: Path | None = Field(
        default=None,
        description="Absolute path to the managed copy under ~/.vibelens/skills, if present.",
    )
    content_hash: str = Field(description="Stable hash of the SKILL.md content.")
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata from frontmatter."
    )

    @field_validator("name")
    @classmethod
    def validate_kebab_case(cls, v: str) -> str:
        """Ensure name is valid kebab-case."""
        if not VALID_SKILL_NAME.match(v):
            raise ValueError(f"Skill name must be kebab-case: {v!r}")
        return v

    @classmethod
    def hash_content(cls, content: str) -> str:
        """Return a stable content hash for SKILL.md."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
