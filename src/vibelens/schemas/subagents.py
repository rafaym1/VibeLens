"""Subagent API schemas — request and response models."""

from pydantic import BaseModel, Field

from vibelens.models.extension.subagent import Subagent


class SubagentInstallRequest(BaseModel):
    """Create a new subagent."""

    name: str = Field(description="Kebab-case subagent name.")
    content: str = Field(description="Full .md content.")
    sync_to: list[str] = Field(
        default_factory=list, description="Agent keys to sync to after install."
    )


class SubagentModifyRequest(BaseModel):
    """Update subagent content."""

    content: str = Field(description="New .md content.")


class SubagentSyncRequest(BaseModel):
    """Sync subagent to specific agents."""

    agents: list[str] = Field(description="Agent keys to sync to.")


class SubagentSyncTargetResponse(BaseModel):
    """An agent platform available for subagent sync."""

    agent: str = Field(description="Agent identifier (e.g. 'claude').")
    subagent_count: int = Field(description="Number of subagents in agent dir.")
    subagents_dir: str = Field(description="Agent subagents directory path.")


class SubagentDetailResponse(BaseModel):
    """Full subagent detail including content."""

    subagent: Subagent = Field(description="Subagent metadata with install status.")
    content: str = Field(description="Raw .md text.")
    path: str = Field(description="Central store path.")


class SubagentListResponse(BaseModel):
    """Paginated subagent listing with available sync targets."""

    items: list[Subagent] = Field(description="Page of subagents with install status.")
    total: int = Field(description="Total matching subagents.")
    page: int = Field(description="Current page number.")
    page_size: int = Field(description="Items per page.")
    sync_targets: list[SubagentSyncTargetResponse] = Field(
        description="Agent platforms available for sync."
    )
