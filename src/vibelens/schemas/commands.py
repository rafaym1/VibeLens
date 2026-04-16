"""Command API schemas — request and response models."""

from pydantic import BaseModel, Field

from vibelens.models.extension.command import Command


class CommandInstallRequest(BaseModel):
    """Create a new command."""

    name: str = Field(description="Kebab-case command name.")
    content: str = Field(description="Full .md content.")
    sync_to: list[str] = Field(
        default_factory=list, description="Agent keys to sync to after install."
    )


class CommandModifyRequest(BaseModel):
    """Update command content."""

    content: str = Field(description="New .md content.")


class CommandSyncRequest(BaseModel):
    """Sync command to specific agents."""

    agents: list[str] = Field(description="Agent keys to sync to.")


class CommandSyncTargetResponse(BaseModel):
    """An agent platform available for command sync."""

    agent: str = Field(description="Agent identifier (e.g. 'claude').")
    command_count: int = Field(description="Number of commands in agent dir.")
    commands_dir: str = Field(description="Agent commands directory path.")


class CommandDetailResponse(BaseModel):
    """Full command detail including content."""

    command: Command = Field(description="Command metadata with install status.")
    content: str = Field(description="Raw .md text.")
    path: str = Field(description="Central store path.")


class CommandListResponse(BaseModel):
    """Paginated command listing with available sync targets."""

    items: list[Command] = Field(description="Page of commands with install status.")
    total: int = Field(description="Total matching commands.")
    page: int = Field(description="Current page number.")
    page_size: int = Field(description="Items per page.")
    sync_targets: list[CommandSyncTargetResponse] = Field(
        description="Agent platforms available for sync."
    )
