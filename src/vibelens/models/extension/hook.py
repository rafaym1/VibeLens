"""Hook metadata model parsed from flat .json hook files."""

import re

from pydantic import BaseModel, Field, field_validator

VALID_HOOK_NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


class Hook(BaseModel):
    """Parsed hook metadata from a flat .json file.

    Unlike commands/subagents which live as individual agent files, hooks
    are merged into each agent's ``settings.json`` under the ``hooks`` key.
    The central store remains a single ``{name}.json`` per hook.
    """

    name: str = Field(description="Kebab-case hook identifier (filename without .json).")
    description: str = Field(default="", description="Human description of the hook.")
    tags: list[str] = Field(default_factory=list, description="Tags for discovery.")
    hook_config: dict[str, list[dict]] = Field(
        default_factory=dict,
        description="Event-name to list-of-hook-groups mapping (e.g. PreToolUse).",
    )
    content_hash: str = Field(default="", description="SHA256 of raw JSON content.")
    installed_in: list[str] = Field(default_factory=list, description="Agent keys where installed.")

    @field_validator("name")
    @classmethod
    def validate_kebab_case(cls, v: str) -> str:
        """Ensure name is valid kebab-case."""
        if not VALID_HOOK_NAME.match(v):
            raise ValueError(f"Hook name must be kebab-case: {v!r}")
        return v
