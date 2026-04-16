"""Hook API schemas — request and response models."""

from pydantic import BaseModel, Field

from vibelens.models.extension.hook import Hook


class HookInstallRequest(BaseModel):
    """Create a new hook."""

    name: str = Field(description="Kebab-case hook name.")
    description: str = Field(default="", description="Hook description.")
    tags: list[str] = Field(default_factory=list, description="Tags for discovery.")
    hook_config: dict[str, list[dict]] = Field(
        description="Event-name to list-of-hook-groups mapping (e.g. PreToolUse).",
    )
    sync_to: list[str] = Field(
        default_factory=list, description="Agent keys to sync to after install."
    )


class HookModifyRequest(BaseModel):
    """Partially update a hook. None fields are left unchanged."""

    description: str | None = Field(default=None, description="New description.")
    tags: list[str] | None = Field(default=None, description="New tags.")
    hook_config: dict[str, list[dict]] | None = Field(default=None, description="New hook_config.")


class HookSyncRequest(BaseModel):
    """Sync a hook to specific agents."""

    agents: list[str] = Field(description="Agent keys to sync to.")


class HookSyncTargetResponse(BaseModel):
    """An agent platform available for hook sync."""

    agent: str = Field(description="Agent identifier (e.g. 'claude').")
    hook_count: int = Field(description="Number of managed hooks in agent's settings.json.")
    settings_path: str = Field(description="Path to agent's settings.json.")


class HookDetailResponse(BaseModel):
    """Full hook detail including raw JSON content."""

    hook: Hook = Field(description="Hook metadata with install status.")
    content: str = Field(description="Raw JSON text.")
    path: str = Field(description="Central store file path.")


class HookListResponse(BaseModel):
    """Paginated hook listing with available sync targets."""

    items: list[Hook] = Field(description="Page of hooks with install status.")
    total: int = Field(description="Total matching hooks.")
    page: int = Field(description="Current page number.")
    page_size: int = Field(description="Items per page.")
    sync_targets: list[HookSyncTargetResponse] = Field(
        description="Agent platforms available for sync."
    )
