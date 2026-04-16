"""Hook management service — orchestrates central store + agent settings.json files.

Unlike commands/subagents (where agent-side storage is a directory of .md files),
hooks live inside each agent's ``settings.json`` under the top-level ``hooks`` key.
Sync merges each event/group from the central hook into the agent's settings.json,
tagging every inserted group with ``_vibelens_managed: {hook_name}`` so the group
can be located for later unsync/modify operations without touching unmanaged entries.
"""

import copy
import json
import time
from dataclasses import dataclass
from pathlib import Path

from vibelens.models.enums import AgentType
from vibelens.models.extension.hook import Hook
from vibelens.storage.extension.base_store import VALID_EXTENSION_NAME
from vibelens.storage.extension.hook_store import HookStore, serialize_hook
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

CACHE_TTL_SECONDS = 300
VIBELENS_MARKER_KEY = "_vibelens_managed"
HOOKS_ROOT_KEY = "hooks"
JSON_INDENT = 2


@dataclass
class HookSyncTarget:
    """An agent platform available for hook sync."""

    agent: AgentType
    hook_count: int
    settings_path: str


class HookService:
    """Orchestrates hook CRUD across central store and agent settings.json files."""

    def __init__(
        self,
        central: HookStore,
        agent_settings: dict[AgentType, Path],
    ) -> None:
        """Create a HookService.

        Args:
            central: Central HookStore under ``~/.vibelens/hooks/``.
            agent_settings: Map of AgentType to each agent's ``settings.json`` path.
        """
        self._central = central
        self._agent_settings = agent_settings
        self._cache: list[Hook] | None = None
        self._cache_at: float = 0.0

    def install(
        self,
        name: str,
        description: str,
        tags: list[str],
        hook_config: dict[str, list[dict]],
        sync_to: list[str] | None = None,
    ) -> Hook:
        """Write hook JSON to central store and optionally sync to agents.

        Args:
            name: Kebab-case hook name.
            description: Human description.
            tags: Tags for discovery.
            hook_config: Event-name to list-of-hook-groups mapping.
            sync_to: Agent keys to sync to after install.

        Returns:
            Installed Hook with installed_in populated.

        Raises:
            ValueError: If name is not valid kebab-case.
            FileExistsError: If hook already exists.
        """
        if not VALID_EXTENSION_NAME.match(name):
            raise ValueError(f"Hook name must be kebab-case: {name!r}")
        if self._central.exists(name):
            raise FileExistsError(f"Hook {name!r} already exists. Use modify() to update.")

        hook = Hook(
            name=name, description=description, tags=tags, hook_config=hook_config
        )
        self._central.write(name, serialize_hook(hook))
        if sync_to:
            self.sync_to_agents(name, sync_to)
        self.invalidate()
        return self._read_with_agents(name)

    def modify(
        self,
        name: str,
        description: str | None = None,
        tags: list[str] | None = None,
        hook_config: dict[str, list[dict]] | None = None,
    ) -> Hook:
        """Update hook content. Auto-syncs to agents where already installed.

        Args:
            name: Hook name.
            description: New description, or None to keep current.
            tags: New tags, or None to keep current.
            hook_config: New hook_config, or None to keep current.

        Returns:
            Updated Hook.

        Raises:
            FileNotFoundError: If hook not in central.
        """
        current = self._central.read(name)
        if current is None:
            raise FileNotFoundError(f"Hook {name!r} not found in central store")

        updated = Hook(
            name=name,
            description=current.description if description is None else description,
            tags=current.tags if tags is None else tags,
            hook_config=current.hook_config if hook_config is None else hook_config,
        )
        self._central.write(name, serialize_hook(updated))

        for agent_key in self.find_installed_agents(name):
            self._central_to_agent(name, agent_key)

        self.invalidate()
        return self._read_with_agents(name)

    def uninstall(self, name: str) -> list[str]:
        """Delete from central and remove from every agent settings.json.

        Args:
            name: Hook name.

        Returns:
            List of agent keys the hook was removed from.

        Raises:
            FileNotFoundError: If hook not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Hook {name!r} not found in central store")

        removed_from = self.find_installed_agents(name)
        for agent_key in removed_from:
            self._remove_marker_from_settings(name, agent_key)

        self._central.delete(name)
        self.invalidate()
        return removed_from

    def uninstall_from_agent(self, name: str, agent: str) -> None:
        """Remove the hook from a single agent's settings.json only.

        Args:
            name: Hook name.
            agent: Agent key.

        Raises:
            KeyError: If agent not found.
            FileNotFoundError: If hook not installed in that agent.
        """
        agent_key = self._resolve_agent_key(agent)
        if not self._agent_has_marker(name, agent_key):
            raise FileNotFoundError(f"Hook {name!r} not in agent {agent!r}")
        self._remove_marker_from_settings(name, agent_key)
        self.invalidate()

    def sync_to_agents(self, name: str, agents: list[str]) -> dict[str, bool]:
        """Merge central hook into each listed agent's settings.json.

        Args:
            name: Hook name.
            agents: Agent keys to sync to.

        Returns:
            Dict mapping agent key to success boolean (False if agent unknown).

        Raises:
            FileNotFoundError: If hook not in central.
        """
        if not self._central.exists(name):
            raise FileNotFoundError(f"Hook {name!r} not found in central store")

        results: dict[str, bool] = {}
        for agent_key_raw in agents:
            results[agent_key_raw] = self._central_to_agent(name, agent_key_raw)

        self.invalidate()
        return results

    def import_from_agent(
        self, agent: str, name: str, event_name: str, matcher: str
    ) -> Hook:
        """Extract a hook group from an agent's settings.json into central.

        Args:
            agent: Agent key (e.g. "claude").
            name: Name for the new central hook.
            event_name: Event name to look up (e.g. "PreToolUse").
            matcher: Matcher field on the group to locate.

        Returns:
            Created Hook stored in central.

        Raises:
            ValueError: If name is not valid kebab-case.
            KeyError: If agent not found.
            FileNotFoundError: If no matching hook group found.
            FileExistsError: If a central hook with this name already exists.
        """
        if not VALID_EXTENSION_NAME.match(name):
            raise ValueError(f"Hook name must be kebab-case: {name!r}")
        if self._central.exists(name):
            raise FileExistsError(f"Hook {name!r} already exists in central store")

        agent_key = self._resolve_agent_key(agent)
        settings = self._read_settings(self._agent_settings[agent_key])
        groups = settings.get(HOOKS_ROOT_KEY, {}).get(event_name, [])
        matching = [g for g in groups if g.get("matcher") == matcher]
        if not matching:
            raise FileNotFoundError(
                f"No hook group for event={event_name!r} matcher={matcher!r} in agent {agent!r}"
            )

        stripped = [_strip_marker(g) for g in matching]
        hook = Hook(name=name, hook_config={event_name: stripped})
        self._central.write(name, serialize_hook(hook))
        self.invalidate()
        return self._read_with_agents(name)

    def list_hooks(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Hook], int]:
        """List hooks with pagination and optional search.

        Args:
            page: 1-based page number.
            page_size: Items per page.
            search: Case-insensitive substring match on name/description.

        Returns:
            Tuple of (page items, total matching count).
        """
        all_hooks = self._get_cached()
        if search:
            query = search.lower()
            all_hooks = [
                h for h in all_hooks
                if query in h.name.lower() or query in h.description.lower()
            ]
        total = len(all_hooks)
        start = (max(page, 1) - 1) * page_size
        return all_hooks[start : start + page_size], total

    def get_hook(self, name: str) -> Hook:
        """Get a single hook with installed_in populated.

        Args:
            name: Hook name.

        Returns:
            Hook with installed_in set.

        Raises:
            FileNotFoundError: If not found.
        """
        return self._read_with_agents(name)

    def get_hook_content(self, name: str) -> str:
        """Return raw JSON text of the central hook.

        Args:
            name: Hook name.

        Returns:
            Raw JSON content.

        Raises:
            FileNotFoundError: If not found.
        """
        raw = self._central.read_raw(name)
        if raw is None:
            raise FileNotFoundError(f"Hook {name!r} not found")
        return raw

    def find_installed_agents(self, name: str) -> list[str]:
        """Return agent keys whose settings.json has any group marked with this hook."""
        return [key for key in self._agent_settings if self._agent_has_marker(name, key)]

    def get_item_path(self, name: str) -> str:
        """Return the central-store file path for a hook."""
        return str(self._central.path_for(name))

    def list_sync_targets(self) -> list[HookSyncTarget]:
        """List available agent platforms with counts of managed hooks."""
        targets: list[HookSyncTarget] = []
        for agent_key, path in self._agent_settings.items():
            targets.append(
                HookSyncTarget(
                    agent=agent_key,
                    hook_count=self._count_managed_hooks(path),
                    settings_path=str(path),
                )
            )
        return targets

    def invalidate(self) -> None:
        """Clear cached hook list."""
        self._cache = None
        self._cache_at = 0.0

    def _get_cached(self) -> list[Hook]:
        """Return cached hook list, refreshing if stale."""
        now = time.monotonic()
        if self._cache is None or (now - self._cache_at) > CACHE_TTL_SECONDS:
            hooks: list[Hook] = []
            for name in self._central.list_names():
                hook = self._central.read(name)
                if hook:
                    hook.installed_in = self.find_installed_agents(name)
                    hooks.append(hook)
            self._cache = hooks
            self._cache_at = now
        return self._cache

    def _read_with_agents(self, name: str) -> Hook:
        """Read a hook from central and populate installed_in."""
        hook = self._central.read(name)
        if hook is None:
            raise FileNotFoundError(f"Hook {name!r} not found")
        hook.installed_in = self.find_installed_agents(name)
        return hook

    def _resolve_agent_key(self, agent: str) -> AgentType:
        """Look up an AgentType from a string key."""
        for key in self._agent_settings:
            if str(key) == agent:
                return key
        raise KeyError(f"Unknown agent: {agent!r}")

    def _central_to_agent(self, name: str, agent_key_raw: str) -> bool:
        """Merge central hook into one agent's settings.json. False if unknown agent."""
        try:
            agent_key = self._resolve_agent_key(agent_key_raw)
        except KeyError:
            logger.warning("Unknown agent %r, skipping sync", agent_key_raw)
            return False

        hook = self._central.read(name)
        if hook is None:
            return False

        path = self._agent_settings[agent_key]
        settings = self._read_settings(path)
        hooks_root = settings.setdefault(HOOKS_ROOT_KEY, {})

        for event_name, groups in hook.hook_config.items():
            existing = hooks_root.get(event_name, [])
            cleaned = [g for g in existing if g.get(VIBELENS_MARKER_KEY) != name]
            for group in groups:
                tagged = {**copy.deepcopy(group), VIBELENS_MARKER_KEY: name}
                cleaned.append(tagged)
            hooks_root[event_name] = cleaned

        self._write_settings(path, settings)
        return True

    def _remove_marker_from_settings(self, name: str, agent_key: AgentType) -> None:
        """Remove every hook group tagged with ``name`` from this agent's settings."""
        path = self._agent_settings[agent_key]
        settings = self._read_settings(path)
        hooks_root = settings.get(HOOKS_ROOT_KEY, {})
        if not hooks_root:
            return

        cleaned_root: dict[str, list[dict]] = {}
        for event_name, groups in hooks_root.items():
            kept = [g for g in groups if g.get(VIBELENS_MARKER_KEY) != name]
            if kept:
                cleaned_root[event_name] = kept

        if cleaned_root:
            settings[HOOKS_ROOT_KEY] = cleaned_root
        else:
            settings.pop(HOOKS_ROOT_KEY, None)
        self._write_settings(path, settings)

    def _agent_has_marker(self, name: str, agent_key: AgentType) -> bool:
        """Return True if the agent's settings.json contains any group marked with this hook."""
        path = self._agent_settings[agent_key]
        settings = self._read_settings(path)
        hooks_root = settings.get(HOOKS_ROOT_KEY, {})
        for groups in hooks_root.values():
            if any(g.get(VIBELENS_MARKER_KEY) == name for g in groups):
                return True
        return False

    def _count_managed_hooks(self, path: Path) -> int:
        """Count unique managed hook names across all event groups in an agent settings.json."""
        settings = self._read_settings(path)
        hooks_root = settings.get(HOOKS_ROOT_KEY, {})
        names: set[str] = set()
        for groups in hooks_root.values():
            for group in groups:
                marker = group.get(VIBELENS_MARKER_KEY)
                if isinstance(marker, str):
                    names.add(marker)
        return len(names)

    def _read_settings(self, path: Path) -> dict:
        """Read settings.json. Returns empty dict if missing or invalid."""
        if not path.is_file():
            return {}
        try:
            text = path.read_text(encoding="utf-8")
            data = json.loads(text)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Cannot read settings.json at %s: %s", path, exc)
            return {}
        return data if isinstance(data, dict) else {}

    def _write_settings(self, path: Path, data: dict) -> None:
        """Write settings.json atomically (tmp file + rename)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        tmp_path.write_text(json.dumps(data, indent=JSON_INDENT), encoding="utf-8")
        tmp_path.replace(path)


def _strip_marker(group: dict) -> dict:
    """Return a deep copy of a hook group with the VibeLens marker removed."""
    stripped = copy.deepcopy(group)
    stripped.pop(VIBELENS_MARKER_KEY, None)
    return stripped
