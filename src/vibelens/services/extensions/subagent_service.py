"""Subagent management service — orchestrates central + agent stores."""

import time
from dataclasses import dataclass

from vibelens.models.enums import AgentType
from vibelens.models.extension.subagent import VALID_SUBAGENT_NAME, Subagent
from vibelens.storage.extension.subagent_store import SubagentStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 300


@dataclass
class SubagentSyncTarget:
    """An agent platform available for subagent sync."""

    agent: AgentType
    subagent_count: int
    subagents_dir: str


class SubagentService:
    """Orchestrates subagent CRUD across central and agent stores."""

    def __init__(self, central: SubagentStore, agents: dict[AgentType, SubagentStore]) -> None:
        self._central = central
        self._agents = agents
        self._cache: list[Subagent] | None = None
        self._cache_at: float = 0.0

    def install(self, name: str, content: str, sync_to: list[str] | None = None) -> Subagent:
        """Write subagent to central store and optionally sync to agents.

        Args:
            name: Kebab-case subagent name.
            content: Full .md content.
            sync_to: Agent keys to sync to after install.

        Returns:
            Installed Subagent with installed_in populated.

        Raises:
            ValueError: If name invalid or content empty.
            FileExistsError: If subagent already exists.
        """
        if not VALID_SUBAGENT_NAME.match(name):
            raise ValueError(f"Subagent name must be kebab-case: {name!r}")
        if not content.strip():
            raise ValueError("Subagent content must not be empty")
        if self._central.exists(name):
            raise FileExistsError(f"Subagent {name!r} already exists. Use modify() to update.")

        self._central.write(name, content)
        if sync_to:
            self.sync_to_agents(name, sync_to)
        self.invalidate()

        return self._read_with_agents(name)

    def import_from_agent(self, agent: str, name: str) -> Subagent:
        """Copy a subagent from an agent directory into central.

        Args:
            agent: Agent key (e.g. "claude").
            name: Subagent name.

        Returns:
            Imported Subagent.

        Raises:
            KeyError: If agent not found.
            FileNotFoundError: If subagent not in agent dir.
        """
        store = self._resolve_agent(agent)
        if not store.exists(name):
            raise FileNotFoundError(f"Subagent {name!r} not found in agent {agent!r}")

        self._central.copy_from(store, name)
        self.invalidate()
        return self._read_with_agents(name)

    def import_all_from_agent(self, agent: str, overwrite: bool = False) -> list[str]:
        """Import all subagents from an agent directory. Returns imported names.

        Args:
            agent: Agent key.
            overwrite: If True, overwrite existing central subagents.

        Returns:
            List of imported subagent names.

        Raises:
            KeyError: If agent not found.
        """
        store = self._resolve_agent(agent)
        imported: list[str] = []
        for name in store.list_names():
            if not overwrite and self._central.exists(name):
                continue
            self._central.copy_from(store, name)
            imported.append(name)

        if imported:
            self.invalidate()
        return imported

    def uninstall(self, name: str) -> list[str]:
        """Delete from central and all agent stores.

        Args:
            name: Subagent name.

        Returns:
            List of agent keys the subagent was removed from.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Subagent {name!r} not found in central store")

        removed_from: list[str] = []
        for agent_key, store in self._agents.items():
            if store.delete(name):
                removed_from.append(agent_key)

        self._central.delete(name)
        self.invalidate()
        return removed_from

    def uninstall_from_agent(self, name: str, agent: str) -> None:
        """Remove from a single agent store only.

        Args:
            name: Subagent name.
            agent: Agent key.

        Raises:
            KeyError: If agent not found.
            FileNotFoundError: If subagent not in that agent.
        """
        store = self._resolve_agent(agent)
        if not store.exists(name):
            raise FileNotFoundError(f"Subagent {name!r} not in agent {agent!r}")
        store.delete(name)
        self.invalidate()

    def list_subagents(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Subagent], int]:
        """List subagents with pagination and optional search.

        Args:
            page: 1-based page number.
            page_size: Items per page.
            search: Case-insensitive substring match on name/description.

        Returns:
            Tuple of (page items, total matching count).
        """
        all_subagents = self._get_cached()

        if search:
            query = search.lower()
            all_subagents = [
                s
                for s in all_subagents
                if query in s.name.lower() or query in s.description.lower()
            ]

        total = len(all_subagents)
        start = (max(page, 1) - 1) * page_size
        page_items = all_subagents[start : start + page_size]
        return page_items, total

    def get_subagent(self, name: str) -> Subagent:
        """Get a single subagent with installed_in populated.

        Args:
            name: Subagent name.

        Returns:
            Subagent with installed_in set.

        Raises:
            FileNotFoundError: If not found.
        """
        return self._read_with_agents(name)

    def get_subagent_content(self, name: str) -> str:
        """Get raw .md text.

        Args:
            name: Subagent name.

        Returns:
            Raw .md content.

        Raises:
            FileNotFoundError: If not found.
        """
        raw = self._central.read_raw(name)
        if raw is None:
            raise FileNotFoundError(f"Subagent {name!r} not found")
        return raw

    def find_installed_agents(self, name: str) -> list[str]:
        """Return agent keys where this subagent exists on disk."""
        return [key for key, store in self._agents.items() if store.exists(name)]

    def list_sync_targets(self) -> list[SubagentSyncTarget]:
        """List available agent platforms with subagent counts."""
        return [
            SubagentSyncTarget(
                agent=agent,
                subagent_count=len(store.list_names()),
                subagents_dir=str(store.root),
            )
            for agent, store in self._agents.items()
        ]

    def modify(self, name: str, content: str) -> Subagent:
        """Update subagent content. Auto-syncs to agents that already have it.

        Args:
            name: Subagent name.
            content: New .md content.

        Returns:
            Updated Subagent.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Subagent {name!r} not found in central store")

        self._central.write(name, content)

        for agent_key, store in self._agents.items():
            if store.exists(name):
                self._central_to_agent(name, agent_key)

        self.invalidate()
        return self._read_with_agents(name)

    def sync_to_agents(self, name: str, agents: list[str]) -> dict[str, bool]:
        """Copy subagent from central to specified agents.

        Args:
            name: Subagent name.
            agents: Agent keys to sync to.

        Returns:
            Dict mapping agent key to success boolean.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Subagent {name!r} not found in central store")

        results: dict[str, bool] = {}
        for agent_key in agents:
            results[agent_key] = self._central_to_agent(name, agent_key)

        self.invalidate()
        return results

    def invalidate(self) -> None:
        """Clear cached subagent list."""
        self._cache = None
        self._cache_at = 0.0

    def _get_cached(self) -> list[Subagent]:
        """Return cached subagent list, refreshing if stale."""
        now = time.monotonic()
        if self._cache is None or (now - self._cache_at) > CACHE_TTL_SECONDS:
            subagents = []
            for name in self._central.list_names():
                subagent = self._central.read(name)
                if subagent:
                    subagent.installed_in = self.find_installed_agents(name)
                    subagents.append(subagent)
            self._cache = subagents
            self._cache_at = now
        return self._cache

    def _read_with_agents(self, name: str) -> Subagent:
        """Read a subagent from central and populate installed_in."""
        subagent = self._central.read(name)
        if subagent is None:
            raise FileNotFoundError(f"Subagent {name!r} not found")
        subagent.installed_in = self.find_installed_agents(name)
        return subagent

    def _resolve_agent(self, agent: str) -> SubagentStore:
        """Look up an agent store by key."""
        store = self._agents.get(agent)
        if store is None:
            raise KeyError(f"Unknown agent: {agent!r}")
        return store

    def _central_to_agent(self, name: str, agent_key: str) -> bool:
        """Copy subagent from central to one agent. Returns False if agent unknown."""
        store = self._agents.get(agent_key)
        if store is None:
            logger.warning("Unknown agent %r, skipping sync", agent_key)
            return False
        return store.copy_from(self._central, name)
