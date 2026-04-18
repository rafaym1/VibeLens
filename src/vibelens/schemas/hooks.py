"""Hook API schemas — hook-specific request/response models."""

from pydantic import BaseModel, ConfigDict, Field

from vibelens.models.extension.hook import Hook
from vibelens.schemas.extensions import SyncTargetResponse


class HookInstallRequest(BaseModel):
    """Create a new hook (structured fields, not raw content)."""

    model_config = ConfigDict(populate_by_name=True)

    name: str = Field(description="Kebab-case hook name.")
    description: str = Field(default="", description="Hook description.")
    topics: list[str] = Field(
        default_factory=list,
        alias="tags",
        description="Topics for discovery; accepts legacy `tags` key.",
    )
    hook_config: dict[str, list[dict]] = Field(
        description="Event-name to list-of-hook-groups mapping.",
    )
    sync_to: list[str] = Field(
        default_factory=list, description="Agent keys to sync to after install."
    )


class HookModifyRequest(BaseModel):
    """Partially update a hook. None fields are left unchanged."""

    model_config = ConfigDict(populate_by_name=True)

    description: str | None = Field(default=None)
    topics: list[str] | None = Field(default=None, alias="tags")
    hook_config: dict[str, list[dict]] | None = Field(default=None)


class HookDetailResponse(BaseModel):
    """Full hook detail including raw JSON content."""

    hook: Hook = Field(description="Hook metadata.")
    content: str = Field(description="Raw JSON text.")
    path: str = Field(description="Central store file path.")


class HookListResponse(BaseModel):
    """Paginated hook listing with sync targets."""

    items: list[Hook] = Field(description="Page of hooks.")
    total: int
    page: int
    page_size: int
    sync_targets: list[SyncTargetResponse] = Field(description="Agent platforms available.")
