"""Subagent metadata model parsed from flat .md subagent files."""

from pydantic import BaseModel, Field, field_validator

from vibelens.storage.extension.base_store import VALID_EXTENSION_NAME


class Subagent(BaseModel):
    """Parsed subagent metadata from a flat .md file."""

    name: str = Field(description="Kebab-case subagent identifier (filename without .md).")
    description: str = Field(default="", description="From frontmatter.")
    tags: list[str] = Field(default_factory=list, description="From frontmatter.")
    content_hash: str = Field(default="", description="SHA256 of raw .md content.")
    installed_in: list[str] = Field(
        default_factory=list,
        description="Agent keys where installed. Populated by service, not storage.",
    )

    @field_validator("name")
    @classmethod
    def validate_kebab_case(cls, v: str) -> str:
        """Ensure name is valid kebab-case."""
        if not VALID_EXTENSION_NAME.match(v):
            raise ValueError(f"Subagent name must be kebab-case: {v!r}")
        return v
