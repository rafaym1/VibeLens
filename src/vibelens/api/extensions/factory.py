"""Lightweight route factory for file-based extension CRUD (skill, command, subagent)."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from vibelens.schemas.extensions import (
    ExtensionDetailResponse,
    ExtensionInstallRequest,
    ExtensionListResponse,
    ExtensionModifyRequest,
    ExtensionSyncRequest,
    SyncTargetResponse,
)
from vibelens.services.extensions.base_service import BaseExtensionService

DEFAULT_PAGE_SIZE = 50


def build_typed_router(
    service_getter: Callable[[], BaseExtensionService[Any]], type_name: str
) -> APIRouter:
    """Generate CRUD router for a file-based extension type.

    Used for skill, command, subagent. Hook has a hand-written router.
    """
    plural = f"{type_name}s"
    label = type_name.capitalize()
    router = APIRouter(prefix=f"/{plural}", tags=[plural])

    @router.post("/import/{agent}")
    def import_from_agent(agent: str) -> dict:
        service = service_getter()
        try:
            imported = service.import_all_from_agent(agent)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {agent!r}") from None
        return {"agent": agent, "imported": imported, "count": len(imported)}

    @router.get("")
    def list_items(
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        search: str | None = None,
        refresh: bool = False,
    ) -> ExtensionListResponse:
        service = service_getter()
        if refresh:
            service.invalidate()
        items, total = service.list_items(page=page, page_size=page_size, search=search)
        targets = service.list_sync_targets()
        return ExtensionListResponse(
            items=[i.model_dump() for i in items],
            total=total,
            page=page,
            page_size=page_size,
            sync_targets=[
                SyncTargetResponse(agent=t.agent, count=t.count, dir=t.dir) for t in targets
            ],
        )

    @router.get("/{name}")
    def get_item(name: str) -> ExtensionDetailResponse:
        service = service_getter()
        try:
            item = service.get_item(name)
            content = service.get_item_content(name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"{label} {name!r} not found") from None
        return ExtensionDetailResponse(
            item=item.model_dump(), content=content, path=service.get_item_path(name)
        )

    @router.post("")
    def install_item(req: ExtensionInstallRequest) -> dict:
        service = service_getter()
        try:
            item = service.install(name=req.name, content=req.content, sync_to=req.sync_to)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return item.model_dump()

    @router.put("/{name}")
    def modify_item(name: str, req: ExtensionModifyRequest) -> dict:
        service = service_getter()
        try:
            item = service.modify(name=name, content=req.content)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"{label} {name!r} not found") from None
        return item.model_dump()

    @router.delete("/{name}")
    def uninstall_item(name: str) -> dict:
        service = service_getter()
        try:
            removed_from = service.uninstall(name)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"{label} {name!r} not found") from None
        return {"deleted": name, "removed_from": removed_from}

    @router.post("/{name}/agents")
    def sync_item(name: str, req: ExtensionSyncRequest) -> dict:
        service = service_getter()
        try:
            results = service.sync_to_agents(name, req.agents)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail=f"{label} {name!r} not found") from None
        item = service.get_item(name)
        return {"name": name, "results": results, type_name: item.model_dump()}

    @router.delete("/{name}/agents/{agent}")
    def unsync_item(name: str, agent: str) -> dict:
        service = service_getter()
        try:
            service.uninstall_from_agent(name, agent)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {agent!r}") from None
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{label} {name!r} not in agent {agent!r}"
            ) from None
        item = service.get_item(name)
        return {"name": name, "agent": agent, type_name: item.model_dump()}

    return router
