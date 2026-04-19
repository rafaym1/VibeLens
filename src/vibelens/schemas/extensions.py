"""Extension API schemas — unified for all types + catalog-specific."""

from typing import Literal

from pydantic import BaseModel, Field


class SyncTargetResponse(BaseModel):
    """Unified sync target for all extension types."""

    agent: str = Field(description="Agent identifier (e.g. 'claude').")
    count: int = Field(description="Number of extensions of this type in agent.")
    dir: str = Field(description="Agent directory or settings path.")


class ExtensionInstallRequest(BaseModel):
    """Install a new file-based extension."""

    name: str = Field(description="Kebab-case extension name.")
    content: str = Field(description="Full file content.")
    sync_to: list[str] = Field(
        default_factory=list, description="Agent keys to sync to after install."
    )


class ExtensionModifyRequest(BaseModel):
    """Update extension content."""

    content: str = Field(description="New file content.")


class ExtensionSyncRequest(BaseModel):
    """Sync extension to specific agents."""

    agents: list[str] = Field(description="Agent keys to sync to.")


class ExtensionDetailResponse(BaseModel):
    """Full extension detail including content."""

    item: dict = Field(description="Extension metadata (Skill/Command/Subagent/Hook).")
    content: str = Field(description="Raw file text.")
    path: str = Field(description="Central store path.")


class ExtensionListResponse(BaseModel):
    """Paginated extension listing with sync targets. Used by all types."""

    items: list[dict] = Field(description="Page of extensions.")
    total: int = Field(description="Total matching.")
    page: int = Field(description="Current page.")
    page_size: int = Field(description="Items per page.")
    sync_targets: list[SyncTargetResponse] = Field(description="Agent platforms available.")


class ExtensionTreeEntry(BaseModel):
    """One entry in an on-disk extension file tree."""

    path: str = Field(description="Path relative to the extension root, posix-style.")
    kind: Literal["file", "dir"] = Field(description="Entry kind.")
    size: int | None = Field(default=None, description="File byte size (None for dirs).")


class ExtensionTreeResponse(BaseModel):
    """On-disk file tree rooted at the extension's central store dir."""

    name: str = Field(description="Extension name.")
    root: str = Field(description="Absolute on-disk root directory.")
    entries: list[ExtensionTreeEntry] = Field(description="Flat listing of files and dirs.")
    truncated: bool = Field(
        default=False, description="True when the walk was capped at the entry limit."
    )


class ExtensionFileResponse(BaseModel):
    """Raw text content of a single file inside an extension directory."""

    path: str = Field(description="Path relative to the extension root, posix-style.")
    content: str = Field(description="UTF-8 text content; empty string for binaries.")
    truncated: bool = Field(
        default=False, description="True when the file exceeded the read cap."
    )


class CatalogListResponse(BaseModel):
    """Paginated catalog listing response."""

    items: list[dict] = Field(description="Summary-projected extension items.")
    total: int = Field(description="Total matching items.")
    page: int = Field(description="Current page number.")
    per_page: int = Field(description="Items per page.")


class CatalogInstallRequest(BaseModel):
    """Request body for installing from catalog."""

    target_platforms: list[str] = Field(
        min_length=1, description="Target agent platforms for installation."
    )
    overwrite: bool = Field(
        default=False, description="Overwrite existing file if it already exists."
    )


class CatalogInstallResult(BaseModel):
    """Result of installing to a single platform."""

    success: bool = Field(description="Whether installation succeeded.")
    installed_path: str = Field(default="", description="Path where installed.")
    message: str = Field(default="", description="Status message.")


class CatalogInstallResponse(BaseModel):
    """Response after installing from catalog."""

    success: bool = Field(description="Whether all installations succeeded.")
    installed_path: str = Field(default="", description="Path of first successful install.")
    message: str = Field(default="", description="Status message.")
    results: dict[str, CatalogInstallResult] = Field(
        default_factory=dict, description="Per-platform results."
    )


class ExtensionMetaResponse(BaseModel):
    """Catalog metadata for frontend filter/sort options."""

    topics: list[str] = Field(description="Unique topics across the catalog.")
    has_profile: bool = Field(description="Whether a user profile exists for relevance sorting.")


class AgentCapability(BaseModel):
    """Per-agent capability entry."""

    key: str = Field(description="ExtensionSource value, e.g. 'claude'.")
    installed: bool = Field(description="Whether the agent's root directory exists.")
    supported_types: list[str] = Field(description="Extension types this agent can install.")


class AgentCapabilitiesResponse(BaseModel):
    """Response for GET /extensions/agents."""

    agents: list[AgentCapability] = Field(description="All known platforms.")
