"""Plugin management service — mirrors SkillService over plugin directories.

Plugins have the same lifecycle shape as skills (central store +
per-agent stores), but individual agents have different on-disk
mechanics. Non-Claude agents use ``PluginStore`` (plain directory drops);
Claude uses ``ClaudePluginStore`` which drives the 4-file marketplace
merge. Both satisfy ``BaseExtensionStore`` so the service itself is
identical to skills.
"""

from vibelens.models.extension.plugin import Plugin
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.base_store import BaseExtensionStore
from vibelens.storage.extension.plugin_stores import PluginStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class PluginService(BaseExtensionService[Plugin]):
    """Plugin-specific service. Inherits every method from BaseExtensionService."""

    def __init__(self, central: PluginStore, agents: dict[str, BaseExtensionStore[Plugin]]) -> None:
        super().__init__(central_store=central, agent_stores=agents)
