"""Agent capabilities endpoint."""

from fastapi import APIRouter

from vibelens.schemas.extensions import AgentCapabilitiesResponse, AgentCapability
from vibelens.services.extensions.platforms import PLATFORMS

router = APIRouter(tags=["agents"])


@router.get("/agents", response_model=AgentCapabilitiesResponse)
def list_agents() -> AgentCapabilitiesResponse:
    """List all known platforms with install state and supported extension types."""
    agents = [
        AgentCapability(
            key=p.source.value,
            installed=p.root.expanduser().is_dir(),
            supported_types=sorted(t.value for t in p.supported_types),
        )
        for p in PLATFORMS.values()
    ]
    return AgentCapabilitiesResponse(agents=agents)
