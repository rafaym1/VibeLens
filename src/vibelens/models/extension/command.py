"""Command metadata model parsed from flat .md command files."""

import re

from pydantic import BaseModel, Field, field_validator

VALID_COMMAND_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Command(BaseModel):
    """Parsed command metadata from a flat .md file."""

    name: str = Field(description="Kebab-case command identifier (filename without .md).")
    description: str = Field(default="", description="From frontmatter.")
    tags: list[str] = Field(default_factory=list, description="From frontmatter.")
    content_hash: str = Field(default="", description="SHA256 of raw .md content.")
    installed_in: list[str] = Field(default_factory=list, description="Agent keys where installed.")

    @field_validator("name")
    @classmethod
    def validate_kebab_case(cls, v: str) -> str:
        """Ensure name is valid kebab-case."""
        if not VALID_COMMAND_NAME.match(v):
            raise ValueError(f"Command name must be kebab-case: {v!r}")
        return v
