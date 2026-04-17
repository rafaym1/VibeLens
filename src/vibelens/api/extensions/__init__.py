"""Extension API router aggregation."""

from fastapi import APIRouter

from vibelens.api.extensions.catalog import router as catalog_router
from vibelens.api.extensions.factory import build_typed_router
from vibelens.api.extensions.hook import router as hooks_router
from vibelens.deps import get_command_service, get_skill_service, get_subagent_service


def build_extensions_router() -> APIRouter:
    """Aggregate all extension sub-routers under /extensions prefix."""
    extensions_router = APIRouter(prefix="/extensions", tags=["extensions"])
    extensions_router.include_router(catalog_router, prefix="/catalog")
    extensions_router.include_router(build_typed_router(get_skill_service, "skill"))
    extensions_router.include_router(build_typed_router(get_command_service, "command"))
    extensions_router.include_router(build_typed_router(get_subagent_service, "subagent"))
    extensions_router.include_router(hooks_router)
    return extensions_router
