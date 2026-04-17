"""Subagent management service — extends BaseExtensionService for future specialization."""

from vibelens.models.extension.subagent import Subagent
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.subagent_store import SubagentStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class SubagentService(BaseExtensionService[Subagent]):
    """Subagent-specific service. Currently inherits everything from base."""

    def __init__(self, central: SubagentStore, agents: dict[str, SubagentStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)
