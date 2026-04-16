"""Command metadata model parsed from flat .md command files."""

from pydantic import BaseModel, Field, field_validator

from vibelens.storage.extension.base_store import VALID_EXTENSION_NAME


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
        if not VALID_EXTENSION_NAME.match(v):
            raise ValueError(f"Command name must be kebab-case: {v!r}")
        return v
