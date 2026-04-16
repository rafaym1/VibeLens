"""Command management service — orchestrates central + agent stores."""

import time
from dataclasses import dataclass

from vibelens.models.enums import AgentType
from vibelens.models.extension.command import VALID_COMMAND_NAME, Command
from vibelens.storage.extension.command_store import CommandStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 300


@dataclass
class CommandSyncTarget:
    """An agent platform available for command sync."""

    agent: AgentType
    command_count: int
    commands_dir: str


class CommandService:
    """Orchestrates command CRUD across central and agent stores."""

    def __init__(self, central: CommandStore, agents: dict[AgentType, CommandStore]) -> None:
        self._central = central
        self._agents = agents
        self._cache: list[Command] | None = None
        self._cache_at: float = 0.0

    def install(self, name: str, content: str, sync_to: list[str] | None = None) -> Command:
        """Write command to central store and optionally sync to agents.

        Args:
            name: Kebab-case command name.
            content: Full .md content.
            sync_to: Agent keys to sync to after install.

        Returns:
            Installed Command with installed_in populated.

        Raises:
            ValueError: If name invalid or content empty.
            FileExistsError: If command already exists.
        """
        if not VALID_COMMAND_NAME.match(name):
            raise ValueError(f"Command name must be kebab-case: {name!r}")
        if not content.strip():
            raise ValueError("Command content must not be empty")
        if self._central.exists(name):
            raise FileExistsError(f"Command {name!r} already exists. Use modify() to update.")

        self._central.write(name, content)
        if sync_to:
            self.sync_to_agents(name, sync_to)
        self.invalidate()

        return self._read_with_agents(name)

    def import_from_agent(self, agent: str, name: str) -> Command:
        """Copy a command from an agent directory into central.

        Args:
            agent: Agent key (e.g. "claude").
            name: Command name.

        Returns:
            Imported Command.

        Raises:
            KeyError: If agent not found.
            FileNotFoundError: If command not in agent dir.
        """
        store = self._resolve_agent(agent)
        if not store.exists(name):
            raise FileNotFoundError(f"Command {name!r} not found in agent {agent!r}")

        self._central.copy_from(store, name)
        self.invalidate()
        return self._read_with_agents(name)

    def import_all_from_agent(self, agent: str, overwrite: bool = False) -> list[str]:
        """Import all commands from an agent directory. Returns imported names.

        Args:
            agent: Agent key.
            overwrite: If True, overwrite existing central commands.

        Returns:
            List of imported command names.

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
            name: Command name.

        Returns:
            List of agent keys the command was removed from.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Command {name!r} not found in central store")

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
            name: Command name.
            agent: Agent key.

        Raises:
            KeyError: If agent not found.
            FileNotFoundError: If command not in that agent.
        """
        store = self._resolve_agent(agent)
        if not store.exists(name):
            raise FileNotFoundError(f"Command {name!r} not in agent {agent!r}")
        store.delete(name)
        self.invalidate()

    def list_commands(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Command], int]:
        """List commands with pagination and optional search.

        Args:
            page: 1-based page number.
            page_size: Items per page.
            search: Case-insensitive substring match on name/description.

        Returns:
            Tuple of (page items, total matching count).
        """
        all_commands = self._get_cached()

        if search:
            query = search.lower()
            all_commands = [
                c
                for c in all_commands
                if query in c.name.lower() or query in c.description.lower()
            ]

        total = len(all_commands)
        start = (max(page, 1) - 1) * page_size
        page_items = all_commands[start : start + page_size]
        return page_items, total

    def get_command(self, name: str) -> Command:
        """Get a single command with installed_in populated.

        Args:
            name: Command name.

        Returns:
            Command with installed_in set.

        Raises:
            FileNotFoundError: If not found.
        """
        return self._read_with_agents(name)

    def get_command_content(self, name: str) -> str:
        """Get raw .md text.

        Args:
            name: Command name.

        Returns:
            Raw .md content.

        Raises:
            FileNotFoundError: If not found.
        """
        raw = self._central.read_raw(name)
        if raw is None:
            raise FileNotFoundError(f"Command {name!r} not found")
        return raw

    def find_installed_agents(self, name: str) -> list[str]:
        """Return agent keys where this command exists on disk."""
        return [key for key, store in self._agents.items() if store.exists(name)]

    def list_sync_targets(self) -> list[CommandSyncTarget]:
        """List available agent platforms with command counts."""
        return [
            CommandSyncTarget(
                agent=agent,
                command_count=len(store.list_names()),
                commands_dir=str(store.root),
            )
            for agent, store in self._agents.items()
        ]

    def modify(self, name: str, content: str) -> Command:
        """Update command content. Auto-syncs to agents that already have it.

        Args:
            name: Command name.
            content: New .md content.

        Returns:
            Updated Command.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Command {name!r} not found in central store")

        self._central.write(name, content)

        for agent_key, store in self._agents.items():
            if store.exists(name):
                self._central_to_agent(name, agent_key)

        self.invalidate()
        return self._read_with_agents(name)

    def sync_to_agents(self, name: str, agents: list[str]) -> dict[str, bool]:
        """Copy command from central to specified agents.

        Args:
            name: Command name.
            agents: Agent keys to sync to.

        Returns:
            Dict mapping agent key to success boolean.

        Raises:
            FileNotFoundError: If not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Command {name!r} not found in central store")

        results: dict[str, bool] = {}
        for agent_key in agents:
            results[agent_key] = self._central_to_agent(name, agent_key)

        self.invalidate()
        return results

    def invalidate(self) -> None:
        """Clear cached command list."""
        self._cache = None
        self._cache_at = 0.0

    def _get_cached(self) -> list[Command]:
        """Return cached command list, refreshing if stale."""
        now = time.monotonic()
        if self._cache is None or (now - self._cache_at) > CACHE_TTL_SECONDS:
            commands = []
            for name in self._central.list_names():
                command = self._central.read(name)
                if command:
                    command.installed_in = self.find_installed_agents(name)
                    commands.append(command)
            self._cache = commands
            self._cache_at = now
        return self._cache

    def _read_with_agents(self, name: str) -> Command:
        """Read a command from central and populate installed_in."""
        command = self._central.read(name)
        if command is None:
            raise FileNotFoundError(f"Command {name!r} not found")
        command.installed_in = self.find_installed_agents(name)
        return command

    def _resolve_agent(self, agent: str) -> CommandStore:
        """Look up an agent store by key."""
        store = self._agents.get(agent)
        if store is None:
            raise KeyError(f"Unknown agent: {agent!r}")
        return store

    def _central_to_agent(self, name: str, agent_key: str) -> bool:
        """Copy command from central to one agent. Returns False if agent unknown."""
        store = self._agents.get(agent_key)
        if store is None:
            logger.warning("Unknown agent %r, skipping sync", agent_key)
            return False
        return store.copy_from(self._central, name)
