"""Skill management service — extends BaseExtensionService for future specialization."""

from vibelens.models.extension.skill import Skill
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.skill_store import SkillStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class SkillService(BaseExtensionService[Skill]):
    """Skill-specific service. Currently inherits everything from base."""

    def __init__(self, central: SkillStore, agents: dict[str, SkillStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)
