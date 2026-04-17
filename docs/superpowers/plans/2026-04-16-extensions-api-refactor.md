# Extensions API Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the redundant extensions forwarding layer; reorganize into a read-only catalog API + type-specific CRUD APIs under `/api/extensions/`; extract `BaseExtensionService[T]`; unify the frontend API client and components.

**Architecture:** Backend splits into `api/extensions/{catalog,skill,command,hook,subagent}.py` routers and a `BaseExtensionService[T]` in `services/extensions/base_service.py`. Frontend gets a single `api/extensions.ts` client factory consumed via React context. Existing storage layer is unchanged.

**Tech Stack:** Python/FastAPI, Pydantic, React/TypeScript

---

## File Map

### Backend: New Files
- `src/vibelens/api/extensions/__init__.py` — router aggregator
- `src/vibelens/api/extensions/catalog.py` — read-only catalog + install
- `src/vibelens/api/extensions/skill.py` — skill CRUD
- `src/vibelens/api/extensions/command.py` — command CRUD
- `src/vibelens/api/extensions/hook.py` — hook CRUD (hand-written, not factory)
- `src/vibelens/api/extensions/subagent.py` — subagent CRUD
- `src/vibelens/api/extensions/factory.py` — `build_typed_router()` route factory
- `src/vibelens/services/extensions/base_service.py` — `BaseExtensionService[T]`
- `src/vibelens/services/extensions/catalog_resolver.py` — refactored from `catalog_install.py`

### Backend: Modified Files
- `src/vibelens/api/__init__.py` — remove 5 old routers, add 1 new extensions router
- `src/vibelens/services/extensions/catalog.py` — remove install logic (moved to `catalog_resolver.py`)
- `src/vibelens/services/extensions/skill_service.py` — inherit `BaseExtensionService`
- `src/vibelens/services/extensions/command_service.py` — inherit `BaseExtensionService`
- `src/vibelens/services/extensions/hook_service.py` — inherit `BaseExtensionService`
- `src/vibelens/services/extensions/subagent_service.py` — inherit `BaseExtensionService`
- `src/vibelens/deps.py` — update imports
- `src/vibelens/app.py` — update background startup to use base service

### Backend: Deleted Files
- `src/vibelens/api/extensions.py`
- `src/vibelens/api/skill.py`
- `src/vibelens/api/command.py`
- `src/vibelens/api/hook.py`
- `src/vibelens/api/subagent.py`
- `src/vibelens/services/extensions/catalog_install.py`

### Frontend: New Files
- `frontend/src/api/extensions.ts` — unified API client factory

### Frontend: Modified Files
- `frontend/src/app.tsx` — create and provide extensions client via context
- `frontend/src/types.ts` — add `ExtensionsClient` type
- `frontend/src/components/personalization/extensions/extension-explore-tab.tsx` — use new client
- `frontend/src/components/personalization/extensions/extension-card.tsx` — use new client
- `frontend/src/components/personalization/extensions/extension-detail-view.tsx` — use new client
- `frontend/src/components/personalization/local-extensions-tab.tsx` — rewrite to support all types
- `frontend/src/components/personalization/recommendations-view.tsx` — update install URLs
- `frontend/src/components/personalization/personalization-panel.tsx` — remove `useSyncTargetsByType` usage
- `frontend/src/components/personalization/install-target-dialog.tsx` — use new client

### Frontend: Deleted Files
- `frontend/src/components/personalization/cards.tsx`
- `frontend/src/components/personalization/extensions/extension-endpoints.ts`
- `frontend/src/components/personalization/extensions/use-sync-targets.ts`

### Test Files: Modified
- `tests/api/test_skill_api.py` — update imports and URL paths
- `tests/api/test_command_api.py` — update imports and URL paths
- `tests/api/test_hook_api.py` — update imports and URL paths
- `tests/api/test_subagent_api.py` — update imports and URL paths
- `tests/api/test_extension_api.py` — update imports and URL paths
- `tests/api/test_catalog_api.py` — update imports and URL paths
- `tests/services/extensions/test_skill_service.py` — update imports for base class
- `tests/services/extensions/test_command_service.py` — update imports
- `tests/services/extensions/test_hook_service.py` — update imports
- `tests/services/extensions/test_subagent_service.py` — update imports
- `tests/services/extensions/test_catalog_install.py` — rename to test_catalog_resolver.py, update imports
- `tests/services/extensions/test_catalog_install_service_dispatch.py` — update imports

### Test Files: New
- `tests/services/extensions/test_base_service.py` — test the base class

---

## Task 1: Create `BaseExtensionService[T]`

**Files:**
- Create: `src/vibelens/services/extensions/base_service.py`
- Test: `tests/services/extensions/test_base_service.py`

- [ ] **Step 1: Write the base service test**

```python
# tests/services/extensions/test_base_service.py
"""Tests for BaseExtensionService — shared extension management logic."""

import pytest

from vibelens.models.extension.skill import Skill
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.skill_store import SkillStore

SAMPLE_MD = """\
---
description: A sample skill
tags:
  - testing
---
# Sample

Body.
"""

UPDATED_MD = """\
---
description: Updated
tags:
  - updated
---
# Updated

New body.
"""


@pytest.fixture
def central(tmp_path):
    return SkillStore(root=tmp_path / "central", create=True)


@pytest.fixture
def agents(tmp_path):
    claude = SkillStore(root=tmp_path / "claude", create=True)
    codex = SkillStore(root=tmp_path / "codex", create=True)
    return {"claude": claude, "codex": codex}


@pytest.fixture
def service(central, agents):
    return BaseExtensionService[Skill](
        central_store=central,
        agent_stores=agents,
    )


class TestInstall:
    def test_install_creates_item(self, service):
        item = service.install(name="my-skill", content=SAMPLE_MD)
        assert item.name == "my-skill"
        assert item.description == "A sample skill"

    def test_install_syncs_to_agents(self, service):
        item = service.install(name="my-skill", content=SAMPLE_MD, sync_to=["claude"])
        assert "claude" in item.installed_in

    def test_install_duplicate_raises(self, service):
        service.install(name="my-skill", content=SAMPLE_MD)
        with pytest.raises(FileExistsError):
            service.install(name="my-skill", content=SAMPLE_MD)

    def test_install_bad_name_raises(self, service):
        with pytest.raises(ValueError, match="kebab-case"):
            service.install(name="Bad Name", content=SAMPLE_MD)

    def test_install_empty_content_raises(self, service):
        with pytest.raises(ValueError, match="empty"):
            service.install(name="my-skill", content="   ")


class TestModify:
    def test_modify_updates_content(self, service):
        service.install(name="my-skill", content=SAMPLE_MD)
        updated = service.modify(name="my-skill", content=UPDATED_MD)
        assert updated.description == "Updated"

    def test_modify_auto_syncs(self, service):
        service.install(name="my-skill", content=SAMPLE_MD, sync_to=["claude"])
        updated = service.modify(name="my-skill", content=UPDATED_MD)
        assert "claude" in updated.installed_in

    def test_modify_not_found_raises(self, service):
        with pytest.raises(FileNotFoundError):
            service.modify(name="nope", content=UPDATED_MD)


class TestUninstall:
    def test_uninstall_removes_from_central_and_agents(self, service):
        service.install(name="my-skill", content=SAMPLE_MD, sync_to=["claude"])
        removed = service.uninstall(name="my-skill")
        assert "claude" in removed
        with pytest.raises(FileNotFoundError):
            service.get_item(name="my-skill")

    def test_uninstall_not_found_raises(self, service):
        with pytest.raises(FileNotFoundError):
            service.uninstall(name="nope")


class TestList:
    def test_list_empty(self, service):
        items, total = service.list_items(page=1, page_size=50)
        assert items == []
        assert total == 0

    def test_list_with_pagination(self, service):
        for i in range(5):
            service.install(name=f"skill-{i:02d}", content=SAMPLE_MD)
        items, total = service.list_items(page=1, page_size=2)
        assert len(items) == 2
        assert total == 5

    def test_list_with_search(self, service):
        service.install(name="alpha", content=SAMPLE_MD)
        service.install(name="beta", content=SAMPLE_MD)
        items, total = service.list_items(page=1, page_size=50, search="alpha")
        assert total == 1
        assert items[0].name == "alpha"


class TestSync:
    def test_sync_to_agents(self, service):
        service.install(name="my-skill", content=SAMPLE_MD)
        results = service.sync_to_agents(name="my-skill", agents=["claude", "codex"])
        assert results["claude"] is True
        assert results["codex"] is True

    def test_uninstall_from_agent(self, service):
        service.install(name="my-skill", content=SAMPLE_MD, sync_to=["claude"])
        service.uninstall_from_agent(name="my-skill", agent="claude")
        item = service.get_item(name="my-skill")
        assert "claude" not in item.installed_in


class TestImport:
    def test_import_from_agent(self, service, agents):
        agents["claude"].write("imported-skill", SAMPLE_MD)
        item = service.import_from_agent(agent="claude", name="imported-skill")
        assert item.name == "imported-skill"

    def test_import_all_from_agent(self, service, agents):
        agents["claude"].write("skill-a", SAMPLE_MD)
        agents["claude"].write("skill-b", SAMPLE_MD)
        imported = service.import_all_from_agent(agent="claude")
        assert len(imported) == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_base_service.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'vibelens.services.extensions.base_service'`

- [ ] **Step 3: Implement `BaseExtensionService[T]`**

```python
# src/vibelens/services/extensions/base_service.py
"""Generic base service for extension management (skills, commands, hooks, subagents)."""

import time
from typing import Generic, TypeVar

from vibelens.storage.extension.base_store import VALID_EXTENSION_NAME, BaseExtensionStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

T = TypeVar("T")

CACHE_TTL_SECONDS = 300


class BaseExtensionService(Generic[T]):
    """Orchestrates extension CRUD across a central store and agent stores.

    Subclasses override ``_sync_to_agent`` / ``_unsync_from_agent`` for
    type-specific agent-side behavior (e.g. HookService does JSON merge
    instead of file copy).
    """

    def __init__(
        self,
        central_store: BaseExtensionStore[T],
        agent_stores: dict[str, BaseExtensionStore[T]],
        cache_ttl: int = CACHE_TTL_SECONDS,
    ) -> None:
        self._central = central_store
        self._agents = agent_stores
        self._cache: list[T] | None = None
        self._cache_at: float = 0.0
        self._cache_ttl = cache_ttl

    def install(self, name: str, content: str, sync_to: list[str] | None = None) -> T:
        """Write to central store and optionally sync to agents."""
        if not VALID_EXTENSION_NAME.match(name):
            raise ValueError(f"Extension name must be kebab-case: {name!r}")
        if not content.strip():
            raise ValueError("Extension content must not be empty")
        if self._central.exists(name):
            raise FileExistsError(f"Extension {name!r} already exists. Use modify() to update.")
        self._central.write(name, content)
        self._invalidate_cache()
        if sync_to:
            self.sync_to_agents(name, sync_to)
        return self.get_item(name)

    def modify(self, name: str, content: str) -> T:
        """Update content in central store and auto-sync to agents that have it."""
        if not self._central.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not found in central store")
        self._central.write(name, content)
        self._invalidate_cache()
        installed_in = self._find_installed_agents(name)
        for agent_key in installed_in:
            store = self._agents.get(agent_key)
            if store:
                self._sync_to_agent(name, store)
        return self.get_item(name)

    def uninstall(self, name: str) -> list[str]:
        """Delete from central and all agent stores. Returns list of agents removed from."""
        if not self._central.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not found")
        removed_from: list[str] = []
        for agent_key, store in self._agents.items():
            if store.exists(name):
                self._unsync_from_agent(name, store)
                removed_from.append(agent_key)
        self._central.delete(name)
        self._invalidate_cache()
        return removed_from

    def uninstall_from_agent(self, name: str, agent: str) -> None:
        """Remove from a single agent store."""
        store = self._agents.get(agent)
        if store is None:
            raise KeyError(f"Unknown agent: {agent!r}")
        if not store.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not in agent {agent!r}")
        self._unsync_from_agent(name, store)

    def import_from_agent(self, agent: str, name: str) -> T:
        """Copy an extension from an agent store into central."""
        store = self._agents.get(agent)
        if store is None:
            raise KeyError(f"Unknown agent: {agent!r}")
        if not store.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not in agent {agent!r}")
        content = store.read_raw(name)
        if self._central.exists(name):
            self._central.write(name, content)
        else:
            self._central.write(name, content)
        self._invalidate_cache()
        return self.get_item(name)

    def import_all_from_agent(self, agent: str) -> list[str]:
        """Import all extensions from an agent store. Returns names imported."""
        store = self._agents.get(agent)
        if store is None:
            raise KeyError(f"Unknown agent: {agent!r}")
        imported: list[str] = []
        for name in store.list_names():
            content = store.read_raw(name)
            self._central.write(name, content)
            imported.append(name)
        self._invalidate_cache()
        return imported

    def import_all_agents(self) -> None:
        """Import from all known agent stores."""
        for agent_key in self._agents:
            try:
                self.import_all_from_agent(agent_key)
            except Exception:
                logger.warning("Failed to import from agent %s", agent_key, exc_info=True)

    def list_items(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[T], int]:
        """List extensions with pagination and optional search."""
        all_items = self._get_cached_items()
        if search:
            term = search.lower()
            all_items = [i for i in all_items if self._matches_search(i, term)]
        total = len(all_items)
        start = (page - 1) * page_size
        return all_items[start : start + page_size], total

    def get_item(self, name: str) -> T:
        """Get a single extension by name with installed_in populated."""
        if not self._central.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not found")
        item = self._central.read(name)
        self._populate_installed_in(item, name)
        return item

    def get_item_content(self, name: str) -> str:
        """Get raw content of an extension."""
        if not self._central.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not found")
        return self._central.read_raw(name)

    def get_item_path(self, name: str) -> str:
        """Get the central store path for an extension."""
        return str(self._central._item_path(name))

    def sync_to_agents(self, name: str, agents: list[str]) -> dict[str, bool]:
        """Sync to specified agents. Returns per-agent success map."""
        if not self._central.exists(name):
            raise FileNotFoundError(f"Extension {name!r} not found")
        results: dict[str, bool] = {}
        for agent_key in agents:
            store = self._agents.get(agent_key)
            if store is None:
                results[agent_key] = False
                continue
            try:
                self._sync_to_agent(name, store)
                results[agent_key] = True
            except Exception:
                logger.warning("Failed to sync %s to %s", name, agent_key, exc_info=True)
                results[agent_key] = False
        return results

    def invalidate(self) -> None:
        """Clear the item cache."""
        self._invalidate_cache()

    def list_sync_targets(self) -> list[dict]:
        """Return available agent sync targets with item counts."""
        targets = []
        for agent_key, store in self._agents.items():
            targets.append({
                "agent": agent_key,
                "count": len(store.list_names()),
                "dir": str(store._root),
            })
        return targets

    # --- Hooks for subclass override ---

    def _sync_to_agent(self, name: str, agent_store: BaseExtensionStore[T]) -> None:
        """Copy extension from central to agent store. Override for hooks."""
        content = self._central.read_raw(name)
        agent_store.write(name, content)

    def _unsync_from_agent(self, name: str, agent_store: BaseExtensionStore[T]) -> None:
        """Remove extension from agent store. Override for hooks."""
        agent_store.delete(name)

    # --- Internal helpers ---

    def _find_installed_agents(self, name: str) -> list[str]:
        """Find which agents have this extension installed."""
        return [k for k, s in self._agents.items() if s.exists(name)]

    def _populate_installed_in(self, item: T, name: str) -> None:
        """Set the installed_in field on a model instance."""
        installed = self._find_installed_agents(name)
        if hasattr(item, "installed_in"):
            item.installed_in = installed  # type: ignore[attr-defined]

    def _matches_search(self, item: T, term: str) -> bool:
        """Check if an item matches a search term."""
        name = getattr(item, "name", "")
        desc = getattr(item, "description", "")
        tags = getattr(item, "tags", [])
        return term in name.lower() or term in desc.lower() or any(term in t.lower() for t in tags)

    def _get_cached_items(self) -> list[T]:
        """Return all items, using cache if fresh."""
        now = time.time()
        if self._cache is not None and (now - self._cache_at) < self._cache_ttl:
            return list(self._cache)
        names = sorted(self._central.list_names())
        items = []
        for name in names:
            try:
                item = self._central.read(name)
                self._populate_installed_in(item, name)
                items.append(item)
            except Exception:
                logger.warning("Failed to read extension %s", name, exc_info=True)
        self._cache = items
        self._cache_at = now
        return list(items)

    def _invalidate_cache(self) -> None:
        self._cache = None
        self._cache_at = 0.0
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_base_service.py -v`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/vibelens/services/extensions/base_service.py tests/services/extensions/test_base_service.py
git commit -m "feat(extensions): add BaseExtensionService[T] generic base class"
```

---

## Task 2: Migrate `SkillService` to inherit `BaseExtensionService`

**Files:**
- Modify: `src/vibelens/services/extensions/skill_service.py`
- Test: `tests/services/extensions/test_skill_service.py`

- [ ] **Step 1: Run existing skill service tests to verify baseline**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_skill_service.py -v`
Expected: All PASS

- [ ] **Step 2: Rewrite `SkillService` to inherit `BaseExtensionService`**

Replace the entire file:

```python
# src/vibelens/services/extensions/skill_service.py
"""Skill management service — thin wrapper over BaseExtensionService."""

from dataclasses import dataclass

from vibelens.models.extension.skill import Skill
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.skill_store import SkillStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class SkillSyncTarget:
    """An agent platform available for skill sync."""

    agent: str
    skill_count: int
    skills_dir: str


class SkillService(BaseExtensionService[Skill]):
    """Skill-specific service. Inherits all CRUD from BaseExtensionService."""

    def __init__(self, central: SkillStore, agents: dict[str, SkillStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)

    # --- Skill-specific convenience methods (backward compat for callers) ---

    def list_skills(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Skill], int]:
        """Alias for list_items."""
        return self.list_items(page=page, page_size=page_size, search=search)

    def get_skill(self, name: str) -> Skill:
        """Alias for get_item."""
        return self.get_item(name)

    def get_skill_content(self, name: str) -> str:
        """Alias for get_item_content."""
        return self.get_item_content(name)

    def list_sync_targets(self) -> list[SkillSyncTarget]:
        """Return agent sync targets in skill-specific format."""
        return [
            SkillSyncTarget(
                agent=t["agent"],
                skill_count=t["count"],
                skills_dir=t["dir"],
            )
            for t in super().list_sync_targets()
        ]
```

- [ ] **Step 3: Update test imports for `AgentType` → string keys**

The base service uses string agent keys instead of `AgentType` enum. Update the test fixture:

In `tests/services/extensions/test_skill_service.py`, change the `agents` fixture:
```python
# Old:
@pytest.fixture
def agents(tmp_path):
    claude = SkillStore(root=tmp_path / "claude", create=True)
    codex = SkillStore(root=tmp_path / "codex", create=True)
    return {AgentType.CLAUDE: claude, AgentType.CODEX: codex}

# New:
@pytest.fixture
def agents(tmp_path):
    claude = SkillStore(root=tmp_path / "claude", create=True)
    codex = SkillStore(root=tmp_path / "codex", create=True)
    return {"claude": claude, "codex": codex}
```

Also update any test assertions that reference `AgentType.CLAUDE` as a key to use the string `"claude"`. Update the import line to remove `AgentType` if no longer needed.

- [ ] **Step 4: Run skill service tests**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_skill_service.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add src/vibelens/services/extensions/skill_service.py tests/services/extensions/test_skill_service.py
git commit -m "refactor(extensions): migrate SkillService to inherit BaseExtensionService"
```

---

## Task 3: Migrate `CommandService`, `SubagentService`, `HookService`

**Files:**
- Modify: `src/vibelens/services/extensions/command_service.py`
- Modify: `src/vibelens/services/extensions/subagent_service.py`
- Modify: `src/vibelens/services/extensions/hook_service.py`
- Test: `tests/services/extensions/test_command_service.py`
- Test: `tests/services/extensions/test_subagent_service.py`
- Test: `tests/services/extensions/test_hook_service.py`

- [ ] **Step 1: Run existing tests for all three services**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_command_service.py tests/services/extensions/test_subagent_service.py tests/services/extensions/test_hook_service.py -v`
Expected: All PASS

- [ ] **Step 2: Rewrite `CommandService`**

```python
# src/vibelens/services/extensions/command_service.py
"""Command management service — thin wrapper over BaseExtensionService."""

from dataclasses import dataclass

from vibelens.models.extension.command import Command
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.command_store import CommandStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class CommandSyncTarget:
    """An agent platform available for command sync."""

    agent: str
    command_count: int
    commands_dir: str


class CommandService(BaseExtensionService[Command]):
    """Command-specific service. Inherits all CRUD from BaseExtensionService."""

    def __init__(self, central: CommandStore, agents: dict[str, CommandStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)

    def list_commands(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Command], int]:
        """Alias for list_items."""
        return self.list_items(page=page, page_size=page_size, search=search)

    def get_command(self, name: str) -> Command:
        """Alias for get_item."""
        return self.get_item(name)

    def get_command_content(self, name: str) -> str:
        """Alias for get_item_content."""
        return self.get_item_content(name)

    def list_sync_targets(self) -> list[CommandSyncTarget]:
        """Return agent sync targets in command-specific format."""
        return [
            CommandSyncTarget(
                agent=t["agent"],
                command_count=t["count"],
                commands_dir=t["dir"],
            )
            for t in super().list_sync_targets()
        ]
```

- [ ] **Step 3: Rewrite `SubagentService`**

```python
# src/vibelens/services/extensions/subagent_service.py
"""Subagent management service — thin wrapper over BaseExtensionService."""

from dataclasses import dataclass

from vibelens.models.extension.subagent import Subagent
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.subagent_store import SubagentStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class SubagentSyncTarget:
    """An agent platform available for subagent sync."""

    agent: str
    subagent_count: int
    subagents_dir: str


class SubagentService(BaseExtensionService[Subagent]):
    """Subagent-specific service. Inherits all CRUD from BaseExtensionService."""

    def __init__(self, central: SubagentStore, agents: dict[str, SubagentStore]) -> None:
        super().__init__(central_store=central, agent_stores=agents)

    def list_subagents(
        self, page: int = 1, page_size: int = 50, search: str | None = None
    ) -> tuple[list[Subagent], int]:
        """Alias for list_items."""
        return self.list_items(page=page, page_size=page_size, search=search)

    def get_subagent(self, name: str) -> Subagent:
        """Alias for get_item."""
        return self.get_item(name)

    def get_subagent_content(self, name: str) -> str:
        """Alias for get_item_content."""
        return self.get_item_content(name)

    def list_sync_targets(self) -> list[SubagentSyncTarget]:
        """Return agent sync targets in subagent-specific format."""
        return [
            SubagentSyncTarget(
                agent=t["agent"],
                subagent_count=t["count"],
                subagents_dir=t["dir"],
            )
            for t in super().list_sync_targets()
        ]
```

- [ ] **Step 4: Rewrite `HookService`**

HookService is different — it overrides `_sync_to_agent` and `_unsync_from_agent` for JSON merge, and its `install`/`modify` take structured args instead of raw content. Read the current `hook_service.py` carefully and preserve all JSON merge logic (`_vibelens_managed` tagging, settings.json manipulation). The key overrides:

```python
# src/vibelens/services/extensions/hook_service.py
"""Hook management service — extends BaseExtensionService with JSON merge sync."""

from dataclasses import dataclass

from vibelens.models.extension.hook import Hook
from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.storage.extension.hook_store import HookStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


@dataclass
class HookSyncTarget:
    """An agent platform available for hook sync."""

    agent: str
    hook_count: int
    settings_path: str


class HookService(BaseExtensionService[Hook]):
    """Hook-specific service. Overrides sync for JSON merge into settings.json."""

    def __init__(
        self,
        central: HookStore,
        agents: dict[str, HookStore],
        agent_settings_paths: dict[str, str],
    ) -> None:
        super().__init__(central_store=central, agent_stores=agents)
        self._settings_paths = agent_settings_paths

    def install(  # type: ignore[override]
        self,
        name: str,
        description: str = "",
        tags: list[str] | None = None,
        hook_config: dict[str, list[dict]] | None = None,
        sync_to: list[str] | None = None,
        content: str | None = None,
    ) -> Hook:
        """Install a hook. Accepts structured fields or raw JSON content."""
        if content is None:
            from vibelens.storage.extension.hook_store import serialize_hook

            hook = Hook(
                name=name,
                description=description,
                tags=tags or [],
                hook_config=hook_config or {},
            )
            content = serialize_hook(hook)
        return super().install(name=name, content=content, sync_to=sync_to)

    def modify(  # type: ignore[override]
        self,
        name: str,
        description: str | None = None,
        tags: list[str] | None = None,
        hook_config: dict[str, list[dict]] | None = None,
        content: str | None = None,
    ) -> Hook:
        """Partial update of a hook. None fields are left unchanged."""
        if content is None:
            existing = self.get_item(name)
            from vibelens.storage.extension.hook_store import serialize_hook

            hook = Hook(
                name=name,
                description=description if description is not None else existing.description,
                tags=tags if tags is not None else existing.tags,
                hook_config=hook_config if hook_config is not None else existing.hook_config,
            )
            content = serialize_hook(hook)
        return super().modify(name=name, content=content)

    def import_from_agent(  # type: ignore[override]
        self,
        agent: str,
        name: str,
        event_name: str | None = None,
        matcher: str | None = None,
    ) -> Hook:
        """Import a hook from agent settings.json.

        For hooks, this extracts managed hook groups from the agent's
        settings.json rather than copying a file.
        """
        # Preserve existing hook_service.py import logic — read from settings.json,
        # extract matching hook groups, write to central store.
        # This method must be copied from the current hook_service.py implementation.
        raise NotImplementedError("Copy from current hook_service.py")

    def _sync_to_agent(self, name: str, agent_store: HookStore) -> None:
        """Merge hook config into agent's settings.json with _vibelens_managed tag."""
        # Preserve existing JSON merge logic from current hook_service.py.
        # This reads the agent's settings.json, merges hook groups under the
        # appropriate event names with _vibelens_managed markers, and writes back.
        raise NotImplementedError("Copy from current hook_service.py")

    def _unsync_from_agent(self, name: str, agent_store: HookStore) -> None:
        """Remove managed hook groups from agent's settings.json."""
        # Preserve existing removal logic — scan for _vibelens_managed markers
        # matching this hook name and remove those groups.
        raise NotImplementedError("Copy from current hook_service.py")

    def list_sync_targets(self) -> list[HookSyncTarget]:
        """Return agent sync targets with hook-specific fields."""
        targets = []
        for agent_key, store in self._agents.items():
            settings_path = self._settings_paths.get(agent_key, "")
            targets.append(
                HookSyncTarget(
                    agent=agent_key,
                    hook_count=len(store.list_names()),
                    settings_path=settings_path,
                )
            )
        return targets

    # Alias methods for backward compat
    def list_hooks(self, **kwargs) -> tuple[list[Hook], int]:
        return self.list_items(**kwargs)

    def get_hook(self, name: str) -> Hook:
        return self.get_item(name)

    def get_hook_content(self, name: str) -> str:
        return self.get_item_content(name)
```

**IMPORTANT:** The `_sync_to_agent`, `_unsync_from_agent`, and `import_from_agent` methods marked `NotImplementedError` above must be filled with the actual logic from the current `hook_service.py`. Read the current file and copy the JSON merge logic (settings.json read/write, `_vibelens_managed` tagging, hook group extraction) into these methods.

- [ ] **Step 5: Update test fixtures to use string keys instead of AgentType enum**

For each of the three test files (`test_command_service.py`, `test_subagent_service.py`, `test_hook_service.py`), change agent dict keys from `AgentType.CLAUDE` to `"claude"` and `AgentType.CODEX` to `"codex"`. Remove unused `AgentType` imports.

- [ ] **Step 6: Run all three service tests**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_command_service.py tests/services/extensions/test_subagent_service.py tests/services/extensions/test_hook_service.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/vibelens/services/extensions/command_service.py src/vibelens/services/extensions/subagent_service.py src/vibelens/services/extensions/hook_service.py tests/services/extensions/
git commit -m "refactor(extensions): migrate Command/Subagent/HookService to BaseExtensionService"
```

---

## Task 4: Update `deps.py` for string agent keys

**Files:**
- Modify: `src/vibelens/deps.py`

- [ ] **Step 1: Read current `deps.py` to understand the agent store construction**

Read `src/vibelens/deps.py` and find the `_build_agent_*_stores()` functions. They currently construct `dict[AgentType, Store]` — update to `dict[str, Store]` using the string value of the enum.

- [ ] **Step 2: Update all `_build_agent_*_stores()` functions**

Change each function's return type from `dict[AgentType, ...]` to `dict[str, ...]`. Use `platform.install_key` or the string agent key instead of the `AgentType` enum as the dict key.

Also update the singleton getter functions (`get_skill_service`, `get_command_service`, etc.) if they pass enum keys.

- [ ] **Step 3: Run all extension tests to verify nothing breaks**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/ tests/api/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add src/vibelens/deps.py
git commit -m "refactor(deps): use string agent keys instead of AgentType enum"
```

---

## Task 5: Create `catalog_resolver.py` and update `catalog.py`

**Files:**
- Create: `src/vibelens/services/extensions/catalog_resolver.py`
- Modify: `src/vibelens/services/extensions/catalog.py`
- Delete: `src/vibelens/services/extensions/catalog_install.py`
- Modify: `tests/services/extensions/test_catalog_install.py` → rename to `test_catalog_resolver.py`
- Modify: `tests/services/extensions/test_catalog_install_service_dispatch.py`

- [ ] **Step 1: Run existing catalog tests to verify baseline**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_catalog_install.py tests/services/extensions/test_catalog_install_service_dispatch.py tests/api/test_catalog_api.py -v`
Expected: All PASS

- [ ] **Step 2: Create `catalog_resolver.py`**

Move the install-related functions from `catalog_install.py` into `catalog_resolver.py`. Keep the same function signatures — only the module location changes. The key functions to move:

- `install_extension(item_id, target_platform, overwrite)` — the main dispatcher
- `_install_file()`, `_install_subagent()`, `_install_command()`, `_install_hook_via_service()`, `_install_mcp()` — type-specific installers
- `install_from_source_url()` — GitHub tree download

Read the current `catalog_install.py` and copy all functions into `catalog_resolver.py` with the same implementations.

- [ ] **Step 3: Remove install-related functions from `catalog.py`**

The current `catalog.py` has an `install_extension` function that delegates to `catalog_install.py`. Remove the re-export and update the module's `__all__` or public surface.

- [ ] **Step 4: Delete `catalog_install.py`**

```bash
git rm src/vibelens/services/extensions/catalog_install.py
```

- [ ] **Step 5: Update test imports**

Rename `test_catalog_install.py` to `test_catalog_resolver.py` and update all imports from `vibelens.services.extensions.catalog_install` to `vibelens.services.extensions.catalog_resolver`. Do the same for `test_catalog_install_service_dispatch.py`.

```bash
git mv tests/services/extensions/test_catalog_install.py tests/services/extensions/test_catalog_resolver.py
```

- [ ] **Step 6: Run catalog tests**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/services/extensions/test_catalog_resolver.py tests/services/extensions/test_catalog_install_service_dispatch.py tests/api/test_catalog_api.py -v`
Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add src/vibelens/services/extensions/catalog_resolver.py tests/services/extensions/test_catalog_resolver.py tests/services/extensions/test_catalog_install_service_dispatch.py src/vibelens/services/extensions/catalog.py
git rm src/vibelens/services/extensions/catalog_install.py tests/services/extensions/test_catalog_install.py
git commit -m "refactor(extensions): rename catalog_install to catalog_resolver"
```

---

## Task 6: Create API route factory and `api/extensions/` package

**Files:**
- Create: `src/vibelens/api/extensions/__init__.py`
- Create: `src/vibelens/api/extensions/factory.py`
- Create: `src/vibelens/api/extensions/catalog.py`
- Create: `src/vibelens/api/extensions/skill.py`
- Create: `src/vibelens/api/extensions/command.py`
- Create: `src/vibelens/api/extensions/subagent.py`
- Create: `src/vibelens/api/extensions/hook.py`

- [ ] **Step 1: Create the route factory**

```python
# src/vibelens/api/extensions/factory.py
"""Route factory for extension type CRUD APIs (skill, command, subagent)."""

from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, HTTPException

from vibelens.services.extensions.base_service import BaseExtensionService
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

DEFAULT_PAGE_SIZE = 50


def build_typed_router(
    service_getter: Callable[[], BaseExtensionService[Any]],
    type_name: str,
    type_singular: str,
    tag: str,
    install_request_model: type,
    modify_request_model: type,
    sync_request_model: type,
    list_response_model: type,
    detail_response_model: type,
    sync_target_response_model: type,
    build_list_response: Callable[..., Any],
    build_detail_response: Callable[..., Any],
) -> APIRouter:
    """Generate a standard CRUD router for a file-based extension type.

    Used for skill, command, and subagent (NOT hook — hook has custom routes).
    """
    router = APIRouter(prefix=f"/{type_name}s", tags=[tag])

    @router.post(f"/import/{{agent}}")
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
    ) -> list_response_model:
        service = service_getter()
        if refresh:
            service.invalidate()
        items, total = service.list_items(page=page, page_size=page_size, search=search)
        targets = service.list_sync_targets()
        return build_list_response(
            items=items, total=total, page=page, page_size=page_size, targets=targets
        )

    @router.get(f"/{{name}}")
    def get_item(name: str) -> detail_response_model:
        service = service_getter()
        try:
            item = service.get_item(name)
            content = service.get_item_content(name)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{type_singular} {name!r} not found"
            ) from None
        return build_detail_response(item=item, content=content, path=service.get_item_path(name))

    @router.post("")
    def install_item(req: install_request_model) -> dict:
        service = service_getter()
        try:
            item = service.install(name=req.name, content=req.content, sync_to=req.sync_to)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except FileExistsError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return item.model_dump()

    @router.put(f"/{{name}}")
    def modify_item(name: str, req: modify_request_model) -> dict:
        service = service_getter()
        try:
            item = service.modify(name=name, content=req.content)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{type_singular} {name!r} not found"
            ) from None
        return item.model_dump()

    @router.delete(f"/{{name}}")
    def uninstall_item(name: str) -> dict:
        service = service_getter()
        try:
            removed_from = service.uninstall(name)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{type_singular} {name!r} not found"
            ) from None
        return {"deleted": name, "removed_from": removed_from}

    @router.post(f"/{{name}}/agents")
    def sync_item(name: str, req: sync_request_model) -> dict:
        service = service_getter()
        try:
            results = service.sync_to_agents(name, req.agents)
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{type_singular} {name!r} not found"
            ) from None
        item = service.get_item(name)
        return {"name": name, "results": results, type_singular: item.model_dump()}

    @router.delete(f"/{{name}}/agents/{{agent}}")
    def unsync_item(name: str, agent: str) -> dict:
        service = service_getter()
        try:
            service.uninstall_from_agent(name, agent)
        except KeyError:
            raise HTTPException(status_code=404, detail=f"Unknown agent: {agent!r}") from None
        except FileNotFoundError:
            raise HTTPException(
                status_code=404, detail=f"{type_singular} {name!r} not in agent {agent!r}"
            ) from None
        item = service.get_item(name)
        return {"name": name, "agent": agent, type_singular: item.model_dump()}

    return router
```

- [ ] **Step 2: Create `api/extensions/skill.py` using the factory**

```python
# src/vibelens/api/extensions/skill.py
"""Skill CRUD routes — generated via route factory."""

from vibelens.api.extensions.factory import build_typed_router
from vibelens.deps import get_skill_service
from vibelens.schemas.skills import (
    SkillDetailResponse,
    SkillInstallRequest,
    SkillListResponse,
    SkillModifyRequest,
    SkillSyncRequest,
    SkillSyncTargetResponse,
)


def _build_list_response(items, total, page, page_size, targets):
    return SkillListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        sync_targets=[
            SkillSyncTargetResponse(
                agent=t.agent, skill_count=t.skill_count, skills_dir=t.skills_dir
            )
            for t in targets
        ],
    )


def _build_detail_response(item, content, path):
    return SkillDetailResponse(skill=item, content=content, path=path)


router = build_typed_router(
    service_getter=get_skill_service,
    type_name="skill",
    type_singular="Skill",
    tag="skills",
    install_request_model=SkillInstallRequest,
    modify_request_model=SkillModifyRequest,
    sync_request_model=SkillSyncRequest,
    list_response_model=SkillListResponse,
    detail_response_model=SkillDetailResponse,
    sync_target_response_model=SkillSyncTargetResponse,
    build_list_response=_build_list_response,
    build_detail_response=_build_detail_response,
)
```

- [ ] **Step 3: Create `api/extensions/command.py` and `api/extensions/subagent.py`**

Same pattern as skill.py but with command/subagent-specific schema imports and response builders. Copy the pattern from step 2, substituting:
- `command.py`: `CommandService`, `CommandInstallRequest`, `CommandModifyRequest`, `CommandSyncRequest`, `CommandSyncTargetResponse`, `CommandDetailResponse`, `CommandListResponse`
- `subagent.py`: `SubagentService`, `SubagentInstallRequest`, `SubagentModifyRequest`, `SubagentSyncRequest`, `SubagentSyncTargetResponse`, `SubagentDetailResponse`, `SubagentListResponse`

- [ ] **Step 4: Create `api/extensions/hook.py` (hand-written)**

Copy the current `api/hook.py` contents but change the prefix from `/hooks` to `/hooks` (will be nested under `/extensions` via the parent router). Update the import from `vibelens.deps` and keep all hook-specific routes as-is.

```python
# src/vibelens/api/extensions/hook.py
"""Hook management API routes — hand-written due to structural differences."""

from fastapi import APIRouter, HTTPException

from vibelens.deps import get_hook_service
from vibelens.schemas.hooks import (
    HookDetailResponse,
    HookInstallRequest,
    HookListResponse,
    HookModifyRequest,
    HookSyncRequest,
    HookSyncTargetResponse,
)
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/hooks", tags=["hooks"])

DEFAULT_PAGE_SIZE = 50

# Copy all route handlers from the current api/hook.py verbatim.
# The only change is the file location — the prefix stays "/hooks"
# and will be nested under "/extensions" by the parent router.
```

Fill in all route handlers from the current `api/hook.py`.

- [ ] **Step 5: Create `api/extensions/catalog.py`**

Copy the current `api/extensions.py` contents but change the prefix to `/catalog`. Update the import of `install_extension` to come from `catalog_resolver` instead of `catalog`.

```python
# src/vibelens/api/extensions/catalog.py
"""Extension catalog browsing and install endpoints."""

from fastapi import APIRouter, HTTPException, Query

from vibelens.schemas.extensions import (
    ExtensionInstallRequest,
    ExtensionInstallResponse,
    ExtensionInstallResult,
    ExtensionListResponse,
    ExtensionMetaResponse,
)
from vibelens.services.extensions.catalog import (
    get_extension_by_id,
    get_extension_metadata,
    list_extensions,
    resolve_extension_content,
)
from vibelens.services.extensions.catalog_resolver import install_extension

router = APIRouter(prefix="/catalog", tags=["catalog"])

# Copy all route handlers from the current api/extensions.py verbatim.
# The prefix changes from "/extensions" to "/catalog".
```

Fill in all route handlers from the current `api/extensions.py`.

- [ ] **Step 6: Create `api/extensions/__init__.py`**

```python
# src/vibelens/api/extensions/__init__.py
"""Extension API router aggregation."""

from fastapi import APIRouter

from vibelens.api.extensions.catalog import router as catalog_router
from vibelens.api.extensions.command import router as commands_router
from vibelens.api.extensions.hook import router as hooks_router
from vibelens.api.extensions.skill import router as skills_router
from vibelens.api.extensions.subagent import router as subagents_router


def build_extensions_router() -> APIRouter:
    """Aggregate all extension sub-routers under /extensions prefix."""
    router = APIRouter(prefix="/extensions", tags=["extensions"])
    router.include_router(catalog_router)
    router.include_router(skills_router)
    router.include_router(commands_router)
    router.include_router(hooks_router)
    router.include_router(subagents_router)
    return router
```

- [ ] **Step 7: Commit**

```bash
git add src/vibelens/api/extensions/
git commit -m "feat(api): create api/extensions/ package with factory and type routers"
```

---

## Task 7: Update `api/__init__.py` and delete old routers

**Files:**
- Modify: `src/vibelens/api/__init__.py`
- Delete: `src/vibelens/api/extensions.py`
- Delete: `src/vibelens/api/skill.py`
- Delete: `src/vibelens/api/command.py`
- Delete: `src/vibelens/api/hook.py`
- Delete: `src/vibelens/api/subagent.py`

- [ ] **Step 1: Update `api/__init__.py`**

```python
# src/vibelens/api/__init__.py
"""FastAPI route aggregation."""

from fastapi import APIRouter

from vibelens.api.creation import router as creation_router
from vibelens.api.dashboard import router as dashboard_router
from vibelens.api.donation import router as donation_router
from vibelens.api.evolution import router as evolution_router
from vibelens.api.extensions import build_extensions_router
from vibelens.api.friction import router as friction_router
from vibelens.api.recommendation import router as recommendation_router
from vibelens.api.sessions import router as sessions_router
from vibelens.api.shares import router as shares_router
from vibelens.api.system import router as system_router
from vibelens.api.upload import router as upload_router


def build_router() -> APIRouter:
    """Aggregate all sub-routers into a single API router."""
    router = APIRouter()
    router.include_router(sessions_router)
    router.include_router(donation_router)
    router.include_router(upload_router)
    router.include_router(dashboard_router)
    router.include_router(shares_router)
    router.include_router(system_router)
    router.include_router(friction_router)
    router.include_router(creation_router)
    router.include_router(evolution_router)
    router.include_router(recommendation_router)
    router.include_router(build_extensions_router())
    return router
```

- [ ] **Step 2: Delete old router files**

```bash
git rm src/vibelens/api/extensions.py src/vibelens/api/skill.py src/vibelens/api/command.py src/vibelens/api/hook.py src/vibelens/api/subagent.py
```

- [ ] **Step 3: Update all API tests**

Update test imports and URL paths. For each test file:

`tests/api/test_skill_api.py`:
- Change `from vibelens.api.skill import router` to `from vibelens.api.extensions.skill import router`
- Change monkeypatch target from `vibelens.api.skill` to `vibelens.api.extensions.skill`
- Change URL paths from `/api/skills` to `/api/extensions/skills`
- Update `app.include_router(router, prefix="/api")` to `app.include_router(router, prefix="/api/extensions")`

Apply the same pattern for `test_command_api.py`, `test_hook_api.py`, `test_subagent_api.py`.

For `test_extension_api.py` and `test_catalog_api.py`:
- Change imports from `vibelens.api.extensions` to `vibelens.api.extensions.catalog`
- Change URL paths from `/api/extensions` to `/api/extensions/catalog`

- [ ] **Step 4: Run all API tests**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/api/ -v`
Expected: All PASS

- [ ] **Step 5: Run ruff check**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add src/vibelens/api/__init__.py tests/api/
git commit -m "refactor(api): replace 5 standalone routers with unified extensions package"
```

---

## Task 8: Create frontend API client

**Files:**
- Create: `frontend/src/api/extensions.ts`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Create `api/extensions.ts`**

```typescript
// frontend/src/api/extensions.ts
/**
 * Unified API client for all extension endpoints.
 * Created once via createExtensionsClient(), consumed via useExtensionsClient().
 */

import type {
  ExtensionItemSummary,
  ExtensionListResponse,
  ExtensionMetaResponse,
  ExtensionSyncTarget,
} from "../types";

type FetchFn = (url: string, init?: RequestInit) => Promise<Response>;

const BASE = "/api/extensions";

interface CatalogApi {
  list(params: {
    page?: number;
    perPage?: number;
    sort?: string;
    search?: string;
    extensionType?: string;
    category?: string;
    platform?: string;
  }): Promise<ExtensionListResponse>;
  getMeta(): Promise<ExtensionMetaResponse>;
  getItem(id: string): Promise<ExtensionItemSummary>;
  getContent(id: string): Promise<{ content: string; source: string }>;
  install(
    id: string,
    targets: string[],
    overwrite?: boolean
  ): Promise<{
    success: boolean;
    installed_path: string;
    message: string;
    results: Record<string, { success: boolean; message: string }>;
  }>;
}

interface TypeApi {
  list(params?: {
    page?: number;
    pageSize?: number;
    search?: string;
    refresh?: boolean;
  }): Promise<any>;
  get(name: string): Promise<any>;
  install(name: string, content: string, syncTo?: string[]): Promise<any>;
  modify(name: string, content: string): Promise<any>;
  uninstall(name: string): Promise<any>;
  syncToAgents(name: string, agents: string[]): Promise<any>;
  unsyncFromAgent(name: string, agent: string): Promise<any>;
  importFromAgent(agent: string): Promise<any>;
}

interface SyncTargetsCache {
  get(): Promise<Record<string, ExtensionSyncTarget[]>>;
  invalidate(): void;
}

export interface ExtensionsClient {
  catalog: CatalogApi;
  skills: TypeApi;
  commands: TypeApi;
  hooks: TypeApi;
  subagents: TypeApi;
  syncTargets: SyncTargetsCache;
}

function createTypeApi(fetchFn: FetchFn, typePlural: string): TypeApi {
  const base = `${BASE}/${typePlural}`;

  return {
    async list(params = {}) {
      const qs = new URLSearchParams();
      if (params.page) qs.set("page", String(params.page));
      if (params.pageSize) qs.set("page_size", String(params.pageSize));
      if (params.search) qs.set("search", params.search);
      if (params.refresh) qs.set("refresh", "true");
      const res = await fetchFn(`${base}?${qs}`);
      if (!res.ok) throw new Error(`Failed to list ${typePlural}`);
      return res.json();
    },

    async get(name) {
      const res = await fetchFn(`${base}/${encodeURIComponent(name)}`);
      if (!res.ok) throw new Error(`${typePlural} ${name} not found`);
      return res.json();
    },

    async install(name, content, syncTo) {
      const res = await fetchFn(base, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, content, sync_to: syncTo || [] }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Failed to install ${name}`);
      }
      return res.json();
    },

    async modify(name, content) {
      const res = await fetchFn(`${base}/${encodeURIComponent(name)}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (!res.ok) throw new Error(`Failed to modify ${name}`);
      return res.json();
    },

    async uninstall(name) {
      const res = await fetchFn(`${base}/${encodeURIComponent(name)}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error(`Failed to uninstall ${name}`);
      return res.json();
    },

    async syncToAgents(name, agents) {
      const res = await fetchFn(
        `${base}/${encodeURIComponent(name)}/agents`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ agents }),
        }
      );
      if (!res.ok) throw new Error(`Failed to sync ${name}`);
      return res.json();
    },

    async unsyncFromAgent(name, agent) {
      const res = await fetchFn(
        `${base}/${encodeURIComponent(name)}/agents/${encodeURIComponent(agent)}`,
        { method: "DELETE" }
      );
      if (!res.ok) throw new Error(`Failed to unsync ${name} from ${agent}`);
      return res.json();
    },

    async importFromAgent(agent) {
      const res = await fetchFn(
        `${base}/import/${encodeURIComponent(agent)}`,
        { method: "POST" }
      );
      if (!res.ok) throw new Error(`Failed to import from ${agent}`);
      return res.json();
    },
  };
}

export function createExtensionsClient(fetchFn: FetchFn): ExtensionsClient {
  // Sync targets cache
  let cachedTargets: Record<string, ExtensionSyncTarget[]> | null = null;
  let cachePromise: Promise<Record<string, ExtensionSyncTarget[]>> | null = null;

  const syncTargets: SyncTargetsCache = {
    async get() {
      if (cachedTargets) return cachedTargets;
      if (cachePromise) return cachePromise;
      cachePromise = (async () => {
        const types = ["skills", "commands", "hooks", "subagents"] as const;
        const results: Record<string, ExtensionSyncTarget[]> = {};
        await Promise.all(
          types.map(async (type) => {
            try {
              const res = await fetchFn(`${BASE}/${type}?page_size=1`);
              if (res.ok) {
                const data = await res.json();
                results[type.replace(/s$/, "")] = (data.sync_targets || []).map(
                  (t: any) => ({
                    agent: t.agent,
                    count:
                      t.skill_count ??
                      t.command_count ??
                      t.hook_count ??
                      t.subagent_count ??
                      0,
                    dir:
                      t.skills_dir ??
                      t.commands_dir ??
                      t.settings_path ??
                      t.subagents_dir ??
                      "",
                  })
                );
              }
            } catch {
              results[type.replace(/s$/, "")] = [];
            }
          })
        );
        cachedTargets = results;
        cachePromise = null;
        return results;
      })();
      return cachePromise;
    },
    invalidate() {
      cachedTargets = null;
      cachePromise = null;
    },
  };

  // Catalog API
  const catalog: CatalogApi = {
    async list(params) {
      const qs = new URLSearchParams();
      if (params.page) qs.set("page", String(params.page));
      if (params.perPage) qs.set("per_page", String(params.perPage));
      if (params.sort) qs.set("sort", params.sort);
      if (params.search) qs.set("search", params.search);
      if (params.extensionType) qs.set("extension_type", params.extensionType);
      if (params.category) qs.set("category", params.category);
      if (params.platform) qs.set("platform", params.platform);
      const res = await fetchFn(`${BASE}/catalog?${qs}`);
      if (!res.ok) throw new Error("Failed to list catalog");
      return res.json();
    },

    async getMeta() {
      const res = await fetchFn(`${BASE}/catalog/meta`);
      if (!res.ok) throw new Error("Failed to get catalog meta");
      return res.json();
    },

    async getItem(id) {
      const res = await fetchFn(`${BASE}/catalog/${id}`);
      if (!res.ok) throw new Error(`Catalog item ${id} not found`);
      return res.json();
    },

    async getContent(id) {
      const res = await fetchFn(`${BASE}/catalog/${id}/content`);
      if (!res.ok) throw new Error(`Content for ${id} not found`);
      return res.json();
    },

    async install(id, targets, overwrite = false) {
      const res = await fetchFn(`${BASE}/catalog/${id}/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ target_platforms: targets, overwrite }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || "Install failed");
      }
      return res.json();
    },
  };

  return {
    catalog,
    skills: createTypeApi(fetchFn, "skills"),
    commands: createTypeApi(fetchFn, "commands"),
    hooks: createTypeApi(fetchFn, "hooks"),
    subagents: createTypeApi(fetchFn, "subagents"),
    syncTargets,
  };
}
```

- [ ] **Step 2: Add `ExtensionsClient` to app context**

In `frontend/src/app.tsx`, add:

1. Import `createExtensionsClient` and `ExtensionsClient`
2. Create the client inside the `App` component using `useMemo`:
   ```tsx
   const extensionsClient = useMemo(
     () => createExtensionsClient(fetchWithToken),
     [fetchWithToken]
   );
   ```
3. Add `extensionsClient` to the `AppContext` value
4. Export a `useExtensionsClient()` convenience hook:
   ```tsx
   export function useExtensionsClient() {
     return useAppContext().extensionsClient;
   }
   ```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/api/extensions.ts frontend/src/app.tsx
git commit -m "feat(frontend): add unified extensions API client with context provider"
```

---

## Task 9: Migrate frontend components to new API client

**Files:**
- Modify: `frontend/src/components/personalization/extensions/extension-explore-tab.tsx`
- Modify: `frontend/src/components/personalization/extensions/extension-card.tsx`
- Modify: `frontend/src/components/personalization/extensions/extension-detail-view.tsx`
- Modify: `frontend/src/components/personalization/install-target-dialog.tsx`
- Modify: `frontend/src/components/personalization/recommendations-view.tsx`
- Delete: `frontend/src/components/personalization/extensions/extension-endpoints.ts`
- Delete: `frontend/src/components/personalization/extensions/use-sync-targets.ts`

- [ ] **Step 1: Update `extension-explore-tab.tsx`**

Replace all direct `fetchWithToken` calls with `useExtensionsClient()`:
- `fetchWithToken(\`/api/extensions?...\`)` → `client.catalog.list({...})`
- `fetchWithToken(\`/api/extensions/meta\`)` → `client.catalog.getMeta()`
- Remove `useSyncTargetsByType` import and usage, replace with `client.syncTargets.get()`
- Remove import of `extensionEndpoint` from `extension-endpoints.ts`

- [ ] **Step 2: Update `extension-card.tsx`**

Replace:
- Install calls: `fetchWithToken(\`/api/extensions/${id}/install\`, ...)` → `client.catalog.install(id, targets, overwrite)`
- Uninstall calls: `fetchWithToken(\`/api/${type}s/${name}/agents/${agent}\`, {method: "DELETE"})` → `client[type + 's'].unsyncFromAgent(name, agent)` or use a helper
- Remove `extensionEndpoint` import

- [ ] **Step 3: Update `extension-detail-view.tsx`**

Replace:
- `fetchWithToken(\`/api/extensions/${id}\`)` → `client.catalog.getItem(id)`
- `fetchWithToken(\`/api/extensions/${id}/content\`)` → `client.catalog.getContent(id)`
- Install/uninstall calls → use client methods

- [ ] **Step 4: Update `install-target-dialog.tsx`**

Replace any `fetchWithToken` calls that fetch detail endpoints with client methods. The dialog receives `detailEndpoint` prop — replace this with a function prop or use the client directly.

- [ ] **Step 5: Update `recommendations-view.tsx`**

Replace:
- `fetchWithToken(\`/api/extensions/${id}\`)` → `client.catalog.getItem(id)`
- Install callback: use `client.catalog.install(id, targets)`

- [ ] **Step 6: Update `creations-view.tsx` and `evolutions-view.tsx`**

In `creations-view.tsx`:
- Replace `fetchWithToken(\`/api/skills\`, {method: "POST", ...})` → `client.skills.install(name, content, syncTo)`

In `evolutions-view.tsx`:
- Replace `fetchWithToken(\`/api/skills/${name}\`)` → `client.skills.get(name)`
- Replace `fetchWithToken(\`/api/skills/${name}\`, {method: "PUT", ...})` → `client.skills.modify(name, content)`
- Replace `fetchWithToken(\`/api/skills/${name}/agents\`, {method: "POST", ...})` → `client.skills.syncToAgents(name, agents)`

- [ ] **Step 7: Delete old files**

```bash
rm frontend/src/components/personalization/extensions/extension-endpoints.ts
rm frontend/src/components/personalization/extensions/use-sync-targets.ts
```

- [ ] **Step 8: Verify frontend builds**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens/frontend && npm run build`
Expected: Build succeeds with no errors

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "refactor(frontend): migrate extension components to unified API client"
```

---

## Task 10: Rewrite `local-extensions-tab.tsx` for all types

**Files:**
- Modify: `frontend/src/components/personalization/local-extensions-tab.tsx`
- Delete: `frontend/src/components/personalization/cards.tsx`

- [ ] **Step 1: Rewrite `local-extensions-tab.tsx`**

Rewrite the component to:
1. Use `useExtensionsClient()` for all API calls
2. Support all four extension types via the type API (`client.skills`, `client.commands`, etc.)
3. Add a type filter dropdown at the top (same pattern as `extension-explore-tab.tsx`)
4. **v1: only render the "skill" filter option** — other types exist in code but are hidden:
   ```tsx
   const VISIBLE_TYPES = ["skill"] as const; // Expand later: "command", "hook", "subagent"
   ```
5. Use `ExtensionCard` from `extension-card.tsx` (not the old `cards.tsx` version)
6. Use `ExtensionDetailView` for detail display (not `ExtensionDetailPopup` from `cards.tsx`)

- [ ] **Step 2: Delete `cards.tsx`**

Remove the old `ExtensionCard` and `ExtensionDetailPopup` components. All references should now point to the unified components in `extensions/`.

```bash
rm frontend/src/components/personalization/cards.tsx
```

- [ ] **Step 3: Update any remaining imports of `cards.tsx`**

Search for imports of `cards.tsx` in other files (e.g. `personalization-panel.tsx`, `personalization-view.tsx`) and update them to use the unified components.

- [ ] **Step 4: Verify frontend builds**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "refactor(frontend): rewrite local-extensions-tab for all types, delete cards.tsx"
```

---

## Task 11: Update `personalization-panel.tsx` and remaining wiring

**Files:**
- Modify: `frontend/src/components/personalization/personalization-panel.tsx`
- Modify: `frontend/src/components/personalization/personalization-view.tsx` (if it imports cards.tsx)

- [ ] **Step 1: Update `personalization-panel.tsx`**

- Remove any `useSyncTargetsByType` usage (replaced by client.syncTargets)
- Update the `onInstalled` callback to call `client.syncTargets.invalidate()` after install/uninstall
- Remove unused imports

- [ ] **Step 2: Search for any remaining references to old URLs**

Run a grep across the frontend for old API paths:
```
grep -r '"/api/skills' frontend/src/
grep -r '"/api/commands' frontend/src/
grep -r '"/api/hooks' frontend/src/
grep -r '"/api/subagents' frontend/src/
grep -r '"/api/extensions"' frontend/src/
grep -r 'extension-endpoints' frontend/src/
grep -r 'use-sync-targets' frontend/src/
grep -r 'from.*cards' frontend/src/components/personalization/
```

Fix any remaining references.

- [ ] **Step 3: Verify frontend builds**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Commit**

```bash
git add frontend/src/
git commit -m "refactor(frontend): update personalization panel wiring, remove old references"
```

---

## Task 12: Final verification

**Files:** None (verification only)

- [ ] **Step 1: Run all backend tests**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run pytest tests/ -v`
Expected: All PASS

- [ ] **Step 2: Run ruff check**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run ruff check src/ tests/`
Expected: No errors

- [ ] **Step 3: Build frontend**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens/frontend && npm run build`
Expected: Build succeeds

- [ ] **Step 4: Copy built assets to static dir**

Run: `cp -r frontend/dist/* src/vibelens/static/`

- [ ] **Step 5: Smoke test — start the server**

Run: `cd /Users/JinghengYe/Documents/Projects/Agent-Guideline/VibeLens && uv run vibelens serve`

Verify:
- Server starts without errors
- `GET /api/extensions/catalog` returns catalog items
- `GET /api/extensions/skills` returns skills list
- Frontend loads and the Extensions tab works

- [ ] **Step 6: Final commit**

```bash
git add src/vibelens/static/
git commit -m "build: update static assets after extensions API refactor"
```
