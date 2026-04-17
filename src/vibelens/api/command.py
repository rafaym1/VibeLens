"""Command management API routes."""

from fastapi import APIRouter, HTTPException

from vibelens.deps import get_command_service
from vibelens.schemas.extensions import (
    ExtensionDetailResponse,
    ExtensionInstallRequest,
    ExtensionListResponse,
    ExtensionModifyRequest,
    ExtensionSyncRequest,
    SyncTargetResponse,
)
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/commands", tags=["commands"])

DEFAULT_PAGE_SIZE = 50


@router.post("/import/{agent}")
def import_from_agent(agent: str) -> dict:
    """Import all commands from an agent directory into central store."""
    service = get_command_service()
    try:
        imported = service.import_all_from_agent(agent)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent!r}") from None
    return {"agent": agent, "imported": imported, "count": len(imported)}


@router.get("")
def list_commands(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    search: str | None = None,
    refresh: bool = False,
) -> ExtensionListResponse:
    """List commands with pagination, optional search, and sync targets."""
    service = get_command_service()
    if refresh:
        service.invalidate()
    commands, total = service.list_items(page=page, page_size=page_size, search=search)
    targets = service.list_sync_targets()
    return ExtensionListResponse(
        items=[c.model_dump() for c in commands],
        total=total,
        page=page,
        page_size=page_size,
        sync_targets=[
            SyncTargetResponse(agent=t.agent, count=t.count, dir=t.dir)
            for t in targets
        ],
    )


@router.get("/{name}")
def get_command(name: str) -> ExtensionDetailResponse:
    """Get full command detail with content."""
    service = get_command_service()
    try:
        command = service.get_item(name)
        content = service.get_item_content(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command {name!r} not found") from None
    return ExtensionDetailResponse(
        item=command.model_dump(), content=content, path=service.get_item_path(name)
    )


@router.post("")
def install_command(req: ExtensionInstallRequest) -> dict:
    """Install a new command."""
    service = get_command_service()
    try:
        command = service.install(name=req.name, content=req.content, sync_to=req.sync_to)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileExistsError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return command.model_dump()


@router.put("/{name}")
def modify_command(name: str, req: ExtensionModifyRequest) -> dict:
    """Update an existing command's content."""
    service = get_command_service()
    try:
        command = service.modify(name=name, content=req.content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command {name!r} not found") from None
    return command.model_dump()


@router.delete("/{name}")
def uninstall_command(name: str) -> dict:
    """Delete a command from central and all agent stores."""
    service = get_command_service()
    try:
        removed_from = service.uninstall(name)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command {name!r} not found") from None
    return {"deleted": name, "removed_from": removed_from}


@router.post("/{name}/agents")
def sync_command(name: str, req: ExtensionSyncRequest) -> dict:
    """Sync a command to specified agent platforms."""
    service = get_command_service()
    try:
        results = service.sync_to_agents(name, req.agents)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Command {name!r} not found") from None
    command = service.get_item(name)
    return {"name": name, "results": results, "command": command.model_dump()}


@router.delete("/{name}/agents/{agent}")
def unsync_command(name: str, agent: str) -> dict:
    """Remove a command from a single agent platform."""
    service = get_command_service()
    try:
        service.uninstall_from_agent(name, agent)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent!r}") from None
    except FileNotFoundError:
        raise HTTPException(
            status_code=404, detail=f"Command {name!r} not in agent {agent!r}"
        ) from None
    command = service.get_item(name)
    return {"name": name, "agent": agent, "command": command.model_dump()}
