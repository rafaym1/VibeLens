"""Command management service — extends BaseExtensionService for future specialization."""

from vibelens.models.extension.command import Command
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.command_store import CommandStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class CommandService(BaseExtensionService[Command]):
    """Command-specific service. Currently inherits everything from base."""

    def __init__(self, central: CommandStore, agents: dict[str, CommandStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)
