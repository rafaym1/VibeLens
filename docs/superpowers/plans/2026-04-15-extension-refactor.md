# Extension Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unify the catalog/personalization type system under `AgentExtensionType`, rename "catalog" to "extensions" throughout, and build management services for all 5 extension types.

**Architecture:** Single `AgentExtensionType` enum replaces three overlapping enums. `ExtensionItem` model replaces `CatalogItem`. Storage layer generalizes from skill-only to all file-based types + config-based types. Per-type service handlers provide install/list/uninstall for each extension type. Frontend shows skills only for this version.

**Tech Stack:** Python 3.12, Pydantic v2, FastAPI, React + TypeScript + Vite

**Spec:** `docs/superpowers/specs/2026-04-15-extension-refactor-design.md`

---

### Task 1: Add AgentExtensionType Enum and ExtensionItem Model

**Files:**
- Modify: `src/vibelens/models/enums.py`
- Create: `src/vibelens/models/extension.py`
- Modify: `src/vibelens/models/__init__.py`
- Test: `tests/models/test_extension.py`

- [ ] **Step 1: Write tests for AgentExtensionType and ExtensionItem**

Create `tests/models/test_extension.py`:

```python
"""Tests for the AgentExtensionType enum and ExtensionItem model."""

from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import (
    EXTENSION_TYPE_LABELS,
    FILE_BASED_TYPES,
    ExtensionItem,
)


def test_agent_extension_type_values():
    """All 5 extension types are present."""
    assert AgentExtensionType.SKILL == "skill"
    assert AgentExtensionType.SUBAGENT == "subagent"
    assert AgentExtensionType.COMMAND == "command"
    assert AgentExtensionType.HOOK == "hook"
    assert AgentExtensionType.REPO == "repo"
    assert len(AgentExtensionType) == 5
    print(f"All 5 extension types: {list(AgentExtensionType)}")


def test_file_based_types():
    """FILE_BASED_TYPES includes skill, subagent, command, hook but not repo."""
    assert AgentExtensionType.SKILL in FILE_BASED_TYPES
    assert AgentExtensionType.SUBAGENT in FILE_BASED_TYPES
    assert AgentExtensionType.COMMAND in FILE_BASED_TYPES
    assert AgentExtensionType.HOOK in FILE_BASED_TYPES
    assert AgentExtensionType.REPO not in FILE_BASED_TYPES
    print(f"FILE_BASED_TYPES: {FILE_BASED_TYPES}")


def test_extension_type_labels():
    """All 5 types have human-readable labels."""
    assert len(EXTENSION_TYPE_LABELS) == 5
    assert EXTENSION_TYPE_LABELS[AgentExtensionType.SKILL] == "Skill"
    assert EXTENSION_TYPE_LABELS[AgentExtensionType.REPO] == "Repository"
    print(f"Labels: {EXTENSION_TYPE_LABELS}")


def test_extension_item_is_file_based():
    """is_file_based computed field works for all types."""
    base_kwargs = dict(
        extension_id="test:1",
        name="test-item",
        description="Test",
        tags=["test"],
        category="test",
        platforms=["claude_code"],
        quality_score=50.0,
        popularity=0.5,
        updated_at="2026-01-01T00:00:00Z",
        source_url="https://github.com/test/repo",
        repo_full_name="test/repo",
        install_method="skill_file",
    )
    skill_item = ExtensionItem(extension_type=AgentExtensionType.SKILL, **base_kwargs)
    repo_item = ExtensionItem(extension_type=AgentExtensionType.REPO, **base_kwargs)

    assert skill_item.is_file_based is True
    assert repo_item.is_file_based is False
    print(f"skill.is_file_based={skill_item.is_file_based}, repo.is_file_based={repo_item.is_file_based}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/models/test_extension.py -v -s`
Expected: FAIL with `ModuleNotFoundError` (enum and model don't exist yet)

- [ ] **Step 3: Add AgentExtensionType to models/enums.py**

Add to `src/vibelens/models/enums.py` after the `SessionPhase` class:

```python
class AgentExtensionType(StrEnum):
    """Types of agent extensions that can be discovered, installed, and managed."""

    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
    REPO = "repo"
```

- [ ] **Step 4: Create models/extension.py**

Create `src/vibelens/models/extension.py`:

```python
"""Agent extension model and type constants."""

from pydantic import BaseModel, Field, computed_field

from vibelens.models.enums import AgentExtensionType

FILE_BASED_TYPES: set[AgentExtensionType] = {
    AgentExtensionType.SKILL,
    AgentExtensionType.SUBAGENT,
    AgentExtensionType.COMMAND,
    AgentExtensionType.HOOK,
}

EXTENSION_TYPE_LABELS: dict[AgentExtensionType, str] = {
    AgentExtensionType.SKILL: "Skill",
    AgentExtensionType.SUBAGENT: "Expert Agent",
    AgentExtensionType.COMMAND: "Slash Command",
    AgentExtensionType.HOOK: "Automation",
    AgentExtensionType.REPO: "Repository",
}


class ExtensionItem(BaseModel):
    """A discoverable agent extension with quality metrics and installation metadata.

    Represents a skill, subagent, command, hook, or repo that users can
    browse, install, create, or evolve.
    """

    extension_id: str = Field(description="Unique identifier.")
    extension_type: AgentExtensionType = Field(description="Classified type.")
    name: str = Field(description="Display name.")
    description: str = Field(description="Plain language, 1-2 sentences.")
    tags: list[str] = Field(description="Searchable tags.")
    category: str = Field(description="Classification category.")
    platforms: list[str] = Field(description="Compatible agent platforms.")
    quality_score: float = Field(description="0-100 composite from crawler scorer.")
    popularity: float = Field(description="Normalized from stars, 0.0-1.0.")
    updated_at: str = Field(description="Last commit ISO timestamp.")
    source_url: str = Field(description="GitHub URL.")
    repo_full_name: str = Field(description="GitHub owner/repo.")
    stars: int = Field(default=0, description="GitHub star count.")
    forks: int = Field(default=0, description="GitHub fork count.")
    language: str = Field(default="", description="Primary repository language.")
    license_name: str = Field(default="", description="Repository license identifier (e.g. MIT).")
    install_method: str = Field(
        description="Installation method: skill_file, hook_config, mcp_config, pip, npm, etc."
    )
    install_command: str | None = Field(
        default=None, description="CLI install command, e.g. 'pip install foo'."
    )
    install_content: str | None = Field(
        default=None, description="Full file content for direct install."
    )

    @computed_field
    @property
    def is_file_based(self) -> bool:
        """True for file-based types (skill, subagent, command, hook)."""
        return self.extension_type in FILE_BASED_TYPES
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/models/test_extension.py -v -s`
Expected: All 4 tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/vibelens/models/enums.py src/vibelens/models/extension.py tests/models/test_extension.py
git commit -m "feat: add AgentExtensionType enum and ExtensionItem model"
```

---

### Task 2: Update Personalization Models to Use AgentExtensionType

**Files:**
- Modify: `src/vibelens/models/personalization/enums.py`
- Modify: `src/vibelens/models/personalization/__init__.py`
- Modify: `src/vibelens/models/personalization/creation.py`
- Modify: `src/vibelens/models/personalization/recommendation.py`
- Test: `tests/models/test_extension.py` (add tests)

- [ ] **Step 1: Write tests for the model migration**

Append to `tests/models/test_extension.py`:

```python
def test_creation_proposal_uses_agent_extension_type():
    """CreationProposal.element_type accepts AgentExtensionType."""
    from vibelens.models.personalization.creation import CreationProposal

    proposal = CreationProposal(
        element_type=AgentExtensionType.SKILL,
        element_name="test-skill",
        rationale="Test rationale",
    )
    assert proposal.element_type == AgentExtensionType.SKILL
    print(f"CreationProposal.element_type = {proposal.element_type}")


def test_recommendation_item_uses_agent_extension_type():
    """RecommendationItem uses AgentExtensionType instead of RecommendationItemType."""
    from vibelens.models.personalization.recommendation import RecommendationItem

    item = RecommendationItem(
        item_id="test:1",
        extension_type=AgentExtensionType.SKILL,
        name="test",
        repo_name="test/repo",
        source_url="https://github.com/test/repo",
        updated_at="2026-01-01",
        description="Test",
        tags=["test"],
    )
    assert item.extension_type == AgentExtensionType.SKILL
    print(f"RecommendationItem.extension_type = {item.extension_type}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/models/test_extension.py::test_creation_proposal_uses_agent_extension_type tests/models/test_extension.py::test_recommendation_item_uses_agent_extension_type -v -s`
Expected: FAIL (old enum types still in use)

- [ ] **Step 3: Delete PersonalizationElementType, update creation.py**

In `src/vibelens/models/personalization/enums.py`, delete the `PersonalizationElementType` class entirely. Keep `PersonalizationMode`.

In `src/vibelens/models/personalization/creation.py`:
- Change import from `from vibelens.models.personalization.enums import PersonalizationElementType` to `from vibelens.models.enums import AgentExtensionType`
- Change both `element_type: PersonalizationElementType` fields to `element_type: AgentExtensionType`

In `src/vibelens/models/personalization/__init__.py`:
- Remove `PersonalizationElementType` from imports and `__all__`

- [ ] **Step 4: Update recommendation.py — delete RecommendationItemType**

In `src/vibelens/models/personalization/recommendation.py`:
- Delete the `RecommendationItemType` class
- Add import: `from vibelens.models.enums import AgentExtensionType`
- In `RecommendationItem`: rename `item_type` → `extension_type`, change type to `AgentExtensionType`
- Rename `item_id` → `extension_id` in `RecommendationItem`

- [ ] **Step 5: Fix downstream imports of the deleted enums**

Search for all imports of `PersonalizationElementType` and `RecommendationItemType` and update them. Key files:
- `src/vibelens/services/creation/creation.py` — update import path
- `src/vibelens/services/evolution/evolution.py` — update import path
- `src/vibelens/services/recommendation/engine.py` — update `RecommendationItemType` references
- `src/vibelens/services/recommendation/scoring.py` — update if referenced
- `src/vibelens/prompts/` — search and update any template references

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/models/test_extension.py -v -s`
Expected: All 6 tests PASS

Run: `ruff check src/vibelens/models/`
Expected: No errors

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: replace PersonalizationElementType and RecommendationItemType with AgentExtensionType"
```

---

### Task 3: Rename models/skill/ — SkillSource → ExtensionSource, SkillInfo → ExtensionInfo

**Files:**
- Modify: `src/vibelens/models/enums.py` — rename `SkillSource` → `ExtensionSource`
- Modify: `src/vibelens/models/skill/source.py` — rename `SkillSourceInfo` → `ExtensionSourceInfo`
- Modify: `src/vibelens/models/skill/info.py` — rename `SkillInfo` → `ExtensionInfo`
- Modify: `src/vibelens/models/skill/__init__.py` — update exports
- Modify: `src/vibelens/models/__init__.py` — update exports
- All downstream consumers (storage, services, api, deps, frontend types)

- [ ] **Step 1: Rename SkillSource → ExtensionSource in models/enums.py**

In `src/vibelens/models/enums.py`:
- Rename `class SkillSource` → `class ExtensionSource`
- Update all member references: `SkillSource.AIDER` → `ExtensionSource.AIDER`, etc.
- Keep the `AgentType` cross-references intact

- [ ] **Step 2: Rename SkillSourceInfo → ExtensionSourceInfo in models/skill/source.py**

In `src/vibelens/models/skill/source.py`:
- Update import: `SkillSource` → `ExtensionSource`
- Rename class: `SkillSourceInfo` → `ExtensionSourceInfo`
- Update `source_type` field type to `ExtensionSource`

- [ ] **Step 3: Rename SkillInfo → ExtensionInfo in models/skill/info.py**

In `src/vibelens/models/skill/info.py`:
- Update import: `SkillSourceInfo` → `ExtensionSourceInfo`
- Rename `VALID_SKILL_NAME` → `VALID_EXTENSION_NAME`
- Rename class: `SkillInfo` → `ExtensionInfo`
- Update validator method name: `validate_kebab_case` (keep same)
- Update `hash_content` classmethod (keep same)

- [ ] **Step 4: Update models/skill/__init__.py exports**

```python
"""Extension domain models (skill, subagent, command, hook, repo)."""

from vibelens.models.enums import ExtensionSource
from vibelens.models.skill.info import VALID_EXTENSION_NAME, ExtensionInfo
from vibelens.models.skill.retrieval import SkillRecommendation, SkillRetrievalOutput
from vibelens.models.skill.source import ExtensionSourceInfo

__all__ = [
    "ExtensionInfo",
    "ExtensionSource",
    "ExtensionSourceInfo",
    "SkillRecommendation",
    "SkillRetrievalOutput",
    "VALID_EXTENSION_NAME",
]
```

- [ ] **Step 5: Update models/__init__.py**

Replace `SkillInfo` with `ExtensionInfo` in the imports and `__all__`.

- [ ] **Step 6: Update all downstream consumers**

Use find-and-replace across the codebase for these renames:
- `SkillSource` → `ExtensionSource` (in all `.py` files)
- `SkillSourceInfo` → `ExtensionSourceInfo` (in all `.py` files)
- `SkillInfo` → `ExtensionInfo` (in all `.py` files, except `SkillInfo` in frontend `types.ts` which renames separately)
- `VALID_SKILL_NAME` → `VALID_EXTENSION_NAME` (in all `.py` files)
- `from vibelens.models.skill import SkillSource` → `from vibelens.models.skill import ExtensionSource`

Key files to update:
- `src/vibelens/storage/skill/base.py` — `SkillInfo`, `SkillSource` in signatures
- `src/vibelens/storage/skill/disk.py` — `SkillInfo`, `SkillSource`, `SkillSourceInfo`
- `src/vibelens/storage/skill/central.py` — `SkillInfo`, `SkillSource`, `SkillSourceInfo`
- `src/vibelens/storage/skill/agent.py` — `SkillSource`
- `src/vibelens/storage/skill/__init__.py` — exports
- `src/vibelens/deps.py` — `SkillSource` references
- `src/vibelens/api/skill.py` — `SkillInfo`, `AGENT_SKILL_REGISTRY`
- `src/vibelens/services/personalization/shared.py` — if references `SkillInfo`

- [ ] **Step 7: Run full test suite**

Run: `pytest tests/ -v -s --tb=short 2>&1 | head -100`
Expected: Existing tests still pass (some may need import updates — fix them)

Run: `ruff check src/ tests/`
Expected: No errors

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: rename SkillSource/SkillInfo/SkillSourceInfo to ExtensionSource/ExtensionInfo/ExtensionSourceInfo"
```

---

### Task 4: Rename storage/skill/ → storage/extension/

**Files:**
- Rename: `src/vibelens/storage/skill/` → `src/vibelens/storage/extension/`
- Rename classes: `BaseSkillStore` → `BaseExtensionStore`, `DiskSkillStore` → `DiskExtensionStore`, `CentralSkillStore` → `CentralExtensionStore`
- Rename: `AGENT_SKILL_REGISTRY` → `AGENT_EXTENSION_REGISTRY`, `create_agent_skill_stores` → `create_agent_extension_stores`
- Update all imports across codebase

- [ ] **Step 1: Rename the directory**

```bash
git mv src/vibelens/storage/skill src/vibelens/storage/extension
```

- [ ] **Step 2: Rename classes in storage/extension/base.py**

- `BaseSkillStore` → `BaseExtensionStore`
- Update all docstrings and type annotations referencing the old name

- [ ] **Step 3: Rename classes in storage/extension/disk.py**

- `DiskSkillStore` → `DiskExtensionStore`
- Update import: `from vibelens.storage.extension.base import BaseExtensionStore`

- [ ] **Step 4: Rename classes in storage/extension/central.py**

- `CentralSkillStore` → `CentralExtensionStore`
- Update imports from `.base` and `.disk`

- [ ] **Step 5: Rename in storage/extension/agent.py**

- `AGENT_SKILL_REGISTRY` → `AGENT_EXTENSION_REGISTRY`
- `create_agent_skill_stores` → `create_agent_extension_stores`
- Update class references: `DiskExtensionStore`

- [ ] **Step 6: Update storage/extension/__init__.py**

```python
"""Extension storage backends for agent-specific extension management."""

from vibelens.models.skill import ExtensionInfo
from vibelens.storage.extension.agent import create_agent_extension_stores
from vibelens.storage.extension.base import BaseExtensionStore
from vibelens.storage.extension.central import CentralExtensionStore
from vibelens.storage.extension.disk import DiskExtensionStore

__all__ = [
    "BaseExtensionStore",
    "CentralExtensionStore",
    "DiskExtensionStore",
    "ExtensionInfo",
    "create_agent_extension_stores",
]
```

- [ ] **Step 7: Update all imports referencing storage/skill/**

Find-and-replace across all `.py` files:
- `from vibelens.storage.skill` → `from vibelens.storage.extension`
- `BaseSkillStore` → `BaseExtensionStore`
- `DiskSkillStore` → `DiskExtensionStore`
- `CentralSkillStore` → `CentralExtensionStore`
- `AGENT_SKILL_REGISTRY` → `AGENT_EXTENSION_REGISTRY`
- `create_agent_skill_stores` → `create_agent_extension_stores`

Key files:
- `src/vibelens/deps.py` — 4 import blocks + class references
- `src/vibelens/api/skill.py` — imports + references
- `src/vibelens/services/skill/importer.py` — will be deleted later, but update for now
- `src/vibelens/services/personalization/shared.py` — if references storage

- [ ] **Step 8: Run full test suite and linter**

Run: `pytest tests/ -v -s --tb=short 2>&1 | head -100`
Run: `ruff check src/ tests/`
Expected: All pass

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: rename storage/skill/ to storage/extension/, rename all store classes"
```

---

### Task 5: Delete src/vibelens/catalog/ and Update Imports

**Files:**
- Delete: `src/vibelens/catalog/` (entire directory)
- Modify: all files that imported from `vibelens.catalog`

- [ ] **Step 1: Update all imports from vibelens.catalog**

Every file that does `from vibelens.catalog import CatalogItem, ItemType` needs to change to `from vibelens.models.extension import ExtensionItem` and `from vibelens.models.enums import AgentExtensionType`.

Files to update (source):
- `src/vibelens/services/catalog/install.py` — `CatalogItem, ItemType` → `ExtensionItem, AgentExtensionType`
- `src/vibelens/api/catalog.py` — `CatalogItem` → `ExtensionItem`
- `src/vibelens/services/recommendation/catalog.py` — `CatalogItem` → `ExtensionItem`
- `src/vibelens/services/recommendation/retrieval.py` — `CatalogItem` → `ExtensionItem`
- `src/vibelens/services/recommendation/engine.py` — `CatalogItem` → `ExtensionItem`
- `src/vibelens/services/recommendation/scoring.py` — `CatalogItem` → `ExtensionItem`

In each file, also rename field accesses:
- `item.item_type` → `item.extension_type`
- `item.item_id` → `item.extension_id`
- `ItemType.SKILL` → `AgentExtensionType.SKILL`
- `ItemType.HOOK` → `AgentExtensionType.HOOK`
- etc.

Files to update (tests):
- `tests/catalog/test_builder.py`
- `tests/catalog/test_sources.py`
- `tests/catalog/test_enricher.py`
- `tests/catalog/test_dedup.py`
- `tests/catalog/test_scoring.py`
- `tests/services/catalog/test_install.py`
- `tests/api/test_catalog_api.py`
- `tests/services/recommendation/test_scoring.py`
- `tests/services/recommendation/test_catalog.py`
- `tests/services/recommendation/test_retrieval.py`

- [ ] **Step 2: Delete src/vibelens/catalog/**

```bash
rm -rf src/vibelens/catalog/
```

- [ ] **Step 3: Run linter and test suite**

Run: `ruff check src/ tests/`
Run: `pytest tests/ -v -s --tb=short 2>&1 | head -100`
Expected: Pass (some catalog builder tests may fail if they reference deleted builder code — delete those tests too)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "refactor: delete catalog/ module, update all imports to use ExtensionItem"
```

---

### Task 6: Add ConfigExtensionStore for Hook/Repo Configs

**Files:**
- Create: `src/vibelens/storage/extension/config.py`
- Test: `tests/storage/extension/test_config.py`

- [ ] **Step 1: Write tests for ConfigExtensionStore**

Create `tests/storage/extension/__init__.py` (empty) and `tests/storage/extension/test_config.py`:

```python
"""Tests for ConfigExtensionStore — hooks and MCP configs in JSON files."""

import json
from pathlib import Path

from vibelens.storage.extension.config import ConfigExtensionStore


def test_install_hook(tmp_path: Path):
    """install_hook merges hook entries into settings.json."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{}", encoding="utf-8")

    store = ConfigExtensionStore()
    hook_data = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo test"}]}
            ]
        }
    }
    store.install_hook(hook_data=hook_data, settings_path=settings_path)

    result = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "hooks" in result
    assert "PreToolUse" in result["hooks"]
    assert len(result["hooks"]["PreToolUse"]) == 1
    print(f"Installed hook config: {json.dumps(result, indent=2)}")


def test_install_hook_appends_to_existing(tmp_path: Path):
    """install_hook appends to existing hook entries, does not overwrite."""
    settings_path = tmp_path / "settings.json"
    existing = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "echo existing"}]}
            ]
        }
    }
    settings_path.write_text(json.dumps(existing), encoding="utf-8")

    store = ConfigExtensionStore()
    new_hook = {
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo new"}]}
            ]
        }
    }
    store.install_hook(hook_data=new_hook, settings_path=settings_path)

    result = json.loads(settings_path.read_text(encoding="utf-8"))
    assert len(result["hooks"]["PreToolUse"]) == 2
    print(f"Hook entries after append: {len(result['hooks']['PreToolUse'])}")


def test_list_hooks(tmp_path: Path):
    """list_hooks returns all hook event entries from settings.json."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo a"}]}
            ],
            "PostToolUse": [
                {"matcher": "", "hooks": [{"type": "command", "command": "echo b"}]}
            ],
        }
    }), encoding="utf-8")

    store = ConfigExtensionStore()
    hooks = store.list_hooks(settings_path=settings_path)
    assert len(hooks) == 2
    print(f"Listed {len(hooks)} hook groups")


def test_remove_hook(tmp_path: Path):
    """remove_hook removes a hook group by event + matcher."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text(json.dumps({
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo a"}]},
                {"matcher": "Edit", "hooks": [{"type": "command", "command": "echo b"}]},
            ]
        }
    }), encoding="utf-8")

    store = ConfigExtensionStore()
    removed = store.remove_hook(event_name="PreToolUse", matcher="Bash", settings_path=settings_path)
    assert removed is True

    result = json.loads(settings_path.read_text(encoding="utf-8"))
    assert len(result["hooks"]["PreToolUse"]) == 1
    assert result["hooks"]["PreToolUse"][0]["matcher"] == "Edit"
    print(f"Remaining hooks after removal: {result['hooks']['PreToolUse']}")


def test_install_repo(tmp_path: Path):
    """install_repo merges MCP server config into claude.json."""
    claude_json_path = tmp_path / ".claude.json"
    claude_json_path.write_text("{}", encoding="utf-8")

    store = ConfigExtensionStore()
    repo_data = {
        "mcpServers": {
            "my-server": {
                "type": "stdio",
                "command": "/usr/bin/my-server",
                "args": [],
            }
        }
    }
    store.install_repo(repo_data=repo_data, config_path=claude_json_path)

    result = json.loads(claude_json_path.read_text(encoding="utf-8"))
    assert "mcpServers" in result
    assert "my-server" in result["mcpServers"]
    print(f"Installed MCP config: {json.dumps(result, indent=2)}")


def test_list_repos(tmp_path: Path):
    """list_repos returns all MCP server entries from claude.json."""
    claude_json_path = tmp_path / ".claude.json"
    claude_json_path.write_text(json.dumps({
        "mcpServers": {
            "server-a": {"type": "stdio", "command": "a"},
            "server-b": {"type": "http", "url": "https://b.com"},
        }
    }), encoding="utf-8")

    store = ConfigExtensionStore()
    repos = store.list_repos(config_path=claude_json_path)
    assert len(repos) == 2
    print(f"Listed {len(repos)} MCP servers")


def test_remove_repo(tmp_path: Path):
    """remove_repo removes an MCP server entry by name."""
    claude_json_path = tmp_path / ".claude.json"
    claude_json_path.write_text(json.dumps({
        "mcpServers": {
            "server-a": {"type": "stdio", "command": "a"},
            "server-b": {"type": "http", "url": "https://b.com"},
        }
    }), encoding="utf-8")

    store = ConfigExtensionStore()
    removed = store.remove_repo(server_name="server-a", config_path=claude_json_path)
    assert removed is True

    result = json.loads(claude_json_path.read_text(encoding="utf-8"))
    assert "server-a" not in result["mcpServers"]
    assert "server-b" in result["mcpServers"]
    print(f"Remaining servers: {list(result['mcpServers'].keys())}")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/storage/extension/test_config.py -v -s`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Implement ConfigExtensionStore**

Create `src/vibelens/storage/extension/config.py`:

```python
"""Config-based extension store for hooks and MCP servers.

Manages extensions stored in JSON config files rather than on-disk
directories. Hooks live in settings.json; MCP servers live in ~/.claude.json.
"""

import json
from pathlib import Path

from pydantic import BaseModel, Field

from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class InstalledHook(BaseModel):
    """A hook group installed in settings.json."""

    event_name: str = Field(description="Hook event (e.g. PreToolUse, SessionStart).")
    matcher: str = Field(default="", description="Matcher pattern for filtering.")
    hooks: list[dict] = Field(description="Hook handler entries.")


class InstalledRepo(BaseModel):
    """An MCP server installed in claude.json."""

    server_name: str = Field(description="MCP server name.")
    config: dict = Field(description="Server config (type, command/url, args, env, etc.).")


class ConfigExtensionStore:
    """Manages config entries in Claude Code JSON config files.

    Hooks are stored in settings.json under the 'hooks' key.
    MCP servers are stored in ~/.claude.json under the 'mcpServers' key.
    """

    def list_hooks(self, settings_path: Path) -> list[InstalledHook]:
        """List all hook groups from settings.json.

        Args:
            settings_path: Path to settings.json.

        Returns:
            List of installed hook groups.
        """
        settings = _read_json(settings_path)
        hooks_config = settings.get("hooks", {})
        result: list[InstalledHook] = []
        for event_name, groups in hooks_config.items():
            if not isinstance(groups, list):
                continue
            for group in groups:
                result.append(InstalledHook(
                    event_name=event_name,
                    matcher=group.get("matcher", ""),
                    hooks=group.get("hooks", []),
                ))
        return result

    def install_hook(self, hook_data: dict, settings_path: Path) -> None:
        """Merge hook entries into settings.json.

        Args:
            hook_data: Dict with 'hooks' key mapping event names to hook groups.
            settings_path: Path to settings.json.
        """
        settings = _read_json(settings_path)
        hooks_to_add = hook_data.get("hooks", {})
        existing_hooks = settings.setdefault("hooks", {})

        for event_name, entries in hooks_to_add.items():
            existing_entries = existing_hooks.setdefault(event_name, [])
            existing_entries.extend(entries)

        _write_json(settings_path, settings)
        logger.info("Installed hook config to %s", settings_path)

    def remove_hook(
        self, event_name: str, matcher: str, settings_path: Path
    ) -> bool:
        """Remove a hook group by event name and matcher.

        Args:
            event_name: Hook event (e.g. PreToolUse).
            matcher: Matcher pattern to identify the hook group.
            settings_path: Path to settings.json.

        Returns:
            True if a hook group was removed.
        """
        settings = _read_json(settings_path)
        hooks_config = settings.get("hooks", {})
        groups = hooks_config.get(event_name, [])

        original_count = len(groups)
        groups = [g for g in groups if g.get("matcher", "") != matcher]

        if len(groups) == original_count:
            return False

        hooks_config[event_name] = groups
        _write_json(settings_path, settings)
        logger.info("Removed hook %s/%s from %s", event_name, matcher, settings_path)
        return True

    def list_repos(self, config_path: Path) -> list[InstalledRepo]:
        """List all MCP server entries from claude.json.

        Args:
            config_path: Path to ~/.claude.json.

        Returns:
            List of installed MCP servers.
        """
        config = _read_json(config_path)
        servers = config.get("mcpServers", {})
        return [
            InstalledRepo(server_name=name, config=cfg)
            for name, cfg in servers.items()
            if isinstance(cfg, dict)
        ]

    def install_repo(self, repo_data: dict, config_path: Path) -> None:
        """Merge MCP server config into claude.json.

        Args:
            repo_data: Dict with 'mcpServers' key mapping names to configs.
            config_path: Path to ~/.claude.json.
        """
        config = _read_json(config_path)
        servers = repo_data.get("mcpServers", {})
        existing_servers = config.setdefault("mcpServers", {})
        existing_servers.update(servers)

        _write_json(config_path, config)
        logger.info("Installed MCP config to %s", config_path)

    def remove_repo(self, server_name: str, config_path: Path) -> bool:
        """Remove an MCP server entry by name.

        Args:
            server_name: Server name to remove.
            config_path: Path to ~/.claude.json.

        Returns:
            True if a server was removed.
        """
        config = _read_json(config_path)
        servers = config.get("mcpServers", {})
        if server_name not in servers:
            return False

        del servers[server_name]
        _write_json(config_path, config)
        logger.info("Removed MCP server %s from %s", server_name, config_path)
        return True


def _read_json(path: Path) -> dict:
    """Read a JSON file, returning empty dict if missing or invalid.

    Args:
        path: Path to the JSON file.

    Returns:
        Parsed dict, or empty dict on missing/invalid file.
    """
    if path.is_file():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_json(path: Path, data: dict) -> None:
    """Write a dict to a JSON file.

    Args:
        path: Path to the JSON file.
        data: Dict to serialize.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/storage/extension/test_config.py -v -s`
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/vibelens/storage/extension/config.py tests/storage/extension/
git commit -m "feat: add ConfigExtensionStore for hooks and MCP server configs"
```

---

### Task 7: Create Extension Service Handlers

**Files:**
- Create: `src/vibelens/services/extensions/__init__.py`
- Create: `src/vibelens/services/extensions/platforms.py`
- Create: `src/vibelens/services/extensions/base.py`
- Create: `src/vibelens/services/extensions/skill.py`
- Create: `src/vibelens/services/extensions/subagent.py`
- Create: `src/vibelens/services/extensions/command.py`
- Create: `src/vibelens/services/extensions/hook.py`
- Create: `src/vibelens/services/extensions/repo.py`
- Create: `src/vibelens/services/extensions/registry.py`
- Test: `tests/services/extensions/test_handlers.py`

- [ ] **Step 1: Write tests for extension handlers**

Create `tests/services/extensions/__init__.py` (empty) and `tests/services/extensions/test_handlers.py`:

```python
"""Tests for extension service handlers — install, list, uninstall."""

import json
from pathlib import Path

from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import ExtensionItem
from vibelens.services.extensions.registry import get_handler, install_extension


def _make_extension(
    extension_type: AgentExtensionType = AgentExtensionType.SKILL,
    name: str = "test-skill",
    install_content: str | None = "---\nname: test-skill\ndescription: Test\n---\nTest content",
    install_method: str = "skill_file",
) -> ExtensionItem:
    return ExtensionItem(
        extension_id=f"test:{name}",
        extension_type=extension_type,
        name=name,
        description="Test extension",
        tags=["test"],
        category="test",
        platforms=["claude_code"],
        quality_score=50.0,
        popularity=0.5,
        updated_at="2026-01-01T00:00:00Z",
        source_url="https://github.com/test/repo/tree/main/skills/test",
        repo_full_name="test/repo",
        install_method=install_method,
        install_content=install_content,
    )


def test_get_handler_returns_correct_type():
    """get_handler returns the correct handler for each extension type."""
    from vibelens.services.extensions.skill import SkillHandler
    from vibelens.services.extensions.hook import HookHandler
    from vibelens.services.extensions.repo import RepoHandler

    assert isinstance(get_handler(AgentExtensionType.SKILL), SkillHandler)
    assert isinstance(get_handler(AgentExtensionType.HOOK), HookHandler)
    assert isinstance(get_handler(AgentExtensionType.REPO), RepoHandler)
    print("All handlers resolve correctly")


def test_install_skill(tmp_path: Path):
    """SkillHandler installs a skill as a directory with SKILL.md."""
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()

    item = _make_extension()
    handler = get_handler(AgentExtensionType.SKILL)
    path = handler.install(item=item, target_dir=skills_dir, overwrite=False)

    assert (skills_dir / "test-skill" / "SKILL.md").is_file()
    content = (skills_dir / "test-skill" / "SKILL.md").read_text()
    assert "Test content" in content
    print(f"Installed skill to {path}")


def test_install_command(tmp_path: Path):
    """CommandHandler installs a command as a flat .md file."""
    commands_dir = tmp_path / "commands"
    commands_dir.mkdir()

    item = _make_extension(
        extension_type=AgentExtensionType.COMMAND,
        name="test-cmd",
    )
    handler = get_handler(AgentExtensionType.COMMAND)
    path = handler.install(item=item, target_dir=commands_dir, overwrite=False)

    assert (commands_dir / "test-cmd.md").is_file()
    print(f"Installed command to {path}")


def test_install_hook(tmp_path: Path):
    """HookHandler installs hook config to settings.json."""
    settings_path = tmp_path / "settings.json"
    settings_path.write_text("{}", encoding="utf-8")

    hook_content = json.dumps({
        "hooks": {
            "PreToolUse": [
                {"matcher": "Bash", "hooks": [{"type": "command", "command": "echo test"}]}
            ]
        }
    })
    item = _make_extension(
        extension_type=AgentExtensionType.HOOK,
        name="test-hook",
        install_content=hook_content,
        install_method="hook_config",
    )
    handler = get_handler(AgentExtensionType.HOOK)
    path = handler.install(item=item, settings_path=settings_path, overwrite=False)

    result = json.loads(settings_path.read_text())
    assert "hooks" in result
    assert "PreToolUse" in result["hooks"]
    print(f"Installed hook config to {path}")


def test_install_repo(tmp_path: Path):
    """RepoHandler installs MCP config to claude.json."""
    claude_json = tmp_path / ".claude.json"
    claude_json.write_text("{}", encoding="utf-8")

    mcp_content = json.dumps({
        "mcpServers": {
            "my-server": {"type": "stdio", "command": "/usr/bin/server"}
        }
    })
    item = _make_extension(
        extension_type=AgentExtensionType.REPO,
        name="my-server",
        install_content=mcp_content,
        install_method="mcp_config",
    )
    handler = get_handler(AgentExtensionType.REPO)
    path = handler.install(item=item, config_path=claude_json, overwrite=False)

    result = json.loads(claude_json.read_text())
    assert "my-server" in result.get("mcpServers", {})
    print(f"Installed MCP config to {path}")


def test_install_skill_raises_on_existing(tmp_path: Path):
    """SkillHandler raises FileExistsError when target exists and overwrite=False."""
    skills_dir = tmp_path / "skills"
    (skills_dir / "test-skill").mkdir(parents=True)
    (skills_dir / "test-skill" / "SKILL.md").write_text("existing")

    item = _make_extension()
    handler = get_handler(AgentExtensionType.SKILL)
    try:
        handler.install(item=item, target_dir=skills_dir, overwrite=False)
        assert False, "Should have raised FileExistsError"
    except FileExistsError:
        print("Correctly raised FileExistsError")


def test_install_skill_overwrites(tmp_path: Path):
    """SkillHandler overwrites when overwrite=True."""
    skills_dir = tmp_path / "skills"
    (skills_dir / "test-skill").mkdir(parents=True)
    (skills_dir / "test-skill" / "SKILL.md").write_text("old content")

    item = _make_extension()
    handler = get_handler(AgentExtensionType.SKILL)
    handler.install(item=item, target_dir=skills_dir, overwrite=True)

    content = (skills_dir / "test-skill" / "SKILL.md").read_text()
    assert "Test content" in content
    print(f"Overwrote skill content successfully")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/services/extensions/test_handlers.py -v -s`
Expected: FAIL with `ImportError`

- [ ] **Step 3: Create platforms.py**

Create `src/vibelens/services/extensions/platforms.py`:

```python
"""Platform directory configurations for extension installation."""

from pathlib import Path

from vibelens.models.enums import AgentExtensionType

# Install target paths per extension type for Claude Code
CLAUDE_CODE_PATHS: dict[str, Path] = {
    "skills": Path.home() / ".claude" / "skills",
    "commands": Path.home() / ".claude" / "commands",
    "hooks": Path.home() / ".claude" / "hooks",
    "settings": Path.home() / ".claude" / "settings.json",
    "claude_json": Path.home() / ".claude.json",
}

# Maps extension types to their install target key in CLAUDE_CODE_PATHS
EXTENSION_INSTALL_TARGETS: dict[AgentExtensionType, str] = {
    AgentExtensionType.SKILL: "skills",
    AgentExtensionType.SUBAGENT: "skills",
    AgentExtensionType.COMMAND: "commands",
    AgentExtensionType.HOOK: "settings",
    AgentExtensionType.REPO: "claude_json",
}
```

- [ ] **Step 4: Create base.py — FileBasedHandler**

Create `src/vibelens/services/extensions/base.py`:

```python
"""Base handler for file-based extensions (skill, subagent, command, hook)."""

import shutil
from pathlib import Path

from vibelens.models.extension import ExtensionItem
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class FileBasedHandler:
    """Shared install/uninstall logic for file-based extension types.

    Skills and subagents install as directories (name/SKILL.md).
    Commands install as flat files (name.md).
    Subclasses override to customize behavior.
    """

    def install(self, item: ExtensionItem, target_dir: Path, overwrite: bool = False) -> Path:
        """Write install_content to the target directory.

        Args:
            item: ExtensionItem with install_content populated.
            target_dir: Parent directory for installation.
            overwrite: If True, overwrite existing files.

        Returns:
            Path where the item was installed.

        Raises:
            FileExistsError: If target exists and overwrite is False.
        """
        target = self._resolve_target(item=item, target_dir=target_dir)
        if target.exists() and not overwrite:
            raise FileExistsError(
                f"Already exists: {target}. Use overwrite=true to replace."
            )
        self._write_content(item=item, target=target)
        logger.info("Installed %s to %s", item.extension_id, target)
        return target

    def uninstall(self, name: str, target_dir: Path) -> bool:
        """Remove an installed extension.

        Args:
            name: Extension name.
            target_dir: Parent directory to remove from.

        Returns:
            True if removed, False if not found.
        """
        target = target_dir / name
        if target.is_dir():
            shutil.rmtree(target)
            return True
        target_md = target_dir / f"{name}.md"
        if target_md.is_file():
            target_md.unlink()
            return True
        return False

    def _resolve_target(self, item: ExtensionItem, target_dir: Path) -> Path:
        """Resolve the install target path. Override in subclasses.

        Args:
            item: Extension item being installed.
            target_dir: Parent directory.

        Returns:
            Target path (directory for skills/subagents, file for commands).
        """
        return target_dir / item.name

    def _write_content(self, item: ExtensionItem, target: Path) -> None:
        """Write the extension content to disk. Override in subclasses.

        Args:
            item: Extension item with install_content.
            target: Resolved target path.
        """
        target.mkdir(parents=True, exist_ok=True)
        skill_md = target / "SKILL.md"
        skill_md.write_text(item.install_content or "", encoding="utf-8")
```

- [ ] **Step 5: Create per-type handlers**

Create `src/vibelens/services/extensions/skill.py`:

```python
"""Skill extension handler."""

from vibelens.services.extensions.base import FileBasedHandler


class SkillHandler(FileBasedHandler):
    """Handler for skill extensions.

    Skills install as directories with SKILL.md inside ~/.claude/skills/.
    """
    pass
```

Create `src/vibelens/services/extensions/subagent.py`:

```python
"""Subagent extension handler."""

from vibelens.services.extensions.base import FileBasedHandler


class SubagentHandler(FileBasedHandler):
    """Handler for subagent extensions.

    Subagents are skills with context: fork in frontmatter.
    Install as directories with SKILL.md inside ~/.claude/skills/.
    """
    pass
```

Create `src/vibelens/services/extensions/command.py`:

```python
"""Command extension handler (legacy flat .md format)."""

from pathlib import Path

from vibelens.models.extension import ExtensionItem
from vibelens.services.extensions.base import FileBasedHandler


class CommandHandler(FileBasedHandler):
    """Handler for command extensions (legacy format).

    Commands install as flat .md files in ~/.claude/commands/.
    """

    def _resolve_target(self, item: ExtensionItem, target_dir: Path) -> Path:
        """Commands are flat files, not directories."""
        return target_dir / f"{item.name}.md"

    def _write_content(self, item: ExtensionItem, target: Path) -> None:
        """Write command content as a single .md file."""
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(item.install_content or "", encoding="utf-8")
```

Create `src/vibelens/services/extensions/hook.py`:

```python
"""Hook extension handler — hybrid: script files + settings.json config."""

import json
from pathlib import Path

from vibelens.models.extension import ExtensionItem
from vibelens.services.extensions.base import FileBasedHandler
from vibelens.storage.extension.config import ConfigExtensionStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class HookHandler(FileBasedHandler):
    """Handler for hook extensions.

    Hooks are hybrid: they can include script files on disk AND config
    entries in settings.json. install() merges the hook config into
    settings.json. If the hook also includes script files, those are
    written to the hooks directory.
    """

    def __init__(self) -> None:
        self._config_store = ConfigExtensionStore()

    def install(
        self,
        item: ExtensionItem,
        settings_path: Path,
        hooks_dir: Path | None = None,
        overwrite: bool = False,
    ) -> Path:
        """Install hook config to settings.json and optional script files.

        Args:
            item: ExtensionItem with hook JSON in install_content.
            settings_path: Path to settings.json.
            hooks_dir: Optional directory for script files.
            overwrite: If True, overwrite existing entries.

        Returns:
            Path to the settings file.
        """
        hook_data = json.loads(item.install_content or "{}")
        self._config_store.install_hook(hook_data=hook_data, settings_path=settings_path)
        logger.info("Installed hook %s to %s", item.extension_id, settings_path)
        return settings_path
```

Create `src/vibelens/services/extensions/repo.py`:

```python
"""Repo extension handler — MCP server configs in ~/.claude.json."""

import json
from pathlib import Path

from vibelens.models.extension import ExtensionItem
from vibelens.storage.extension.config import ConfigExtensionStore
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class RepoHandler:
    """Handler for repo extensions (MCP servers, CLI tools).

    MCP server configs are merged into ~/.claude.json under mcpServers.
    """

    def __init__(self) -> None:
        self._config_store = ConfigExtensionStore()

    def install(
        self,
        item: ExtensionItem,
        config_path: Path,
        overwrite: bool = False,
    ) -> Path:
        """Install MCP server config to claude.json.

        Args:
            item: ExtensionItem with MCP JSON in install_content.
            config_path: Path to ~/.claude.json.
            overwrite: If True, overwrite existing entries.

        Returns:
            Path to the config file.
        """
        mcp_data = json.loads(item.install_content or "{}")
        self._config_store.install_repo(repo_data=mcp_data, config_path=config_path)
        logger.info("Installed repo %s to %s", item.extension_id, config_path)
        return config_path
```

- [ ] **Step 6: Create registry.py**

Create `src/vibelens/services/extensions/registry.py`:

```python
"""Extension handler registry — maps AgentExtensionType to handlers."""

from vibelens.models.enums import AgentExtensionType
from vibelens.services.extensions.command import CommandHandler
from vibelens.services.extensions.hook import HookHandler
from vibelens.services.extensions.repo import RepoHandler
from vibelens.services.extensions.skill import SkillHandler
from vibelens.services.extensions.subagent import SubagentHandler

_HANDLERS = {
    AgentExtensionType.SKILL: SkillHandler,
    AgentExtensionType.SUBAGENT: SubagentHandler,
    AgentExtensionType.COMMAND: CommandHandler,
    AgentExtensionType.HOOK: HookHandler,
    AgentExtensionType.REPO: RepoHandler,
}

_instances: dict[AgentExtensionType, object] = {}


def get_handler(extension_type: AgentExtensionType):
    """Get the handler instance for the given extension type.

    Args:
        extension_type: The type of extension.

    Returns:
        Handler instance (SkillHandler, HookHandler, RepoHandler, etc.)

    Raises:
        ValueError: If no handler is registered for the type.
    """
    if extension_type not in _instances:
        handler_cls = _HANDLERS.get(extension_type)
        if handler_cls is None:
            raise ValueError(f"No handler registered for {extension_type}")
        _instances[extension_type] = handler_cls()
    return _instances[extension_type]
```

Create `src/vibelens/services/extensions/__init__.py`:

```python
"""Extension management services."""
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `pytest tests/services/extensions/test_handlers.py -v -s`
Expected: All 7 tests PASS

- [ ] **Step 8: Commit**

```bash
git add src/vibelens/services/extensions/ tests/services/extensions/
git commit -m "feat: add extension service handlers with per-type install logic"
```

---

### Task 8: Rename API Layer — catalog → extensions

**Files:**
- Rename: `src/vibelens/schemas/catalog.py` → `src/vibelens/schemas/extensions.py`
- Rename: `src/vibelens/api/catalog.py` → `src/vibelens/api/extensions.py`
- Modify: `src/vibelens/services/recommendation/catalog.py` — rename classes
- Modify: `src/vibelens/app.py` — update router import
- Update all references

- [ ] **Step 1: Rename schemas**

```bash
git mv src/vibelens/schemas/catalog.py src/vibelens/schemas/extensions.py
```

In `src/vibelens/schemas/extensions.py`, rename:
- `CatalogListResponse` → `ExtensionListResponse`
- `CatalogInstallRequest` → `ExtensionInstallRequest`
- `CatalogInstallResponse` → `ExtensionInstallResponse`
- `CatalogMetaResponse` → `ExtensionMetaResponse`
- Update all docstrings

- [ ] **Step 2: Rename API route file**

```bash
git mv src/vibelens/api/catalog.py src/vibelens/api/extensions.py
```

In `src/vibelens/api/extensions.py`:
- Update router prefix: `APIRouter(prefix="/extensions", tags=["extensions"])`
- Update all imports: schemas from `vibelens.schemas.extensions`, model from `vibelens.models.extension`
- Replace `CatalogItem` → `ExtensionItem` in type annotations
- Replace `item.item_type` → `item.extension_type`, `item.item_id` → `item.extension_id`
- Replace `item_type` query param → `extension_type`
- Replace `install_catalog_item` → use `services.extensions.registry.install_extension` (or wire in directly for now)
- Update all function names and docstrings

- [ ] **Step 3: Update recommendation/catalog.py**

In `src/vibelens/services/recommendation/catalog.py`:
- `CatalogSnapshot` → `ExtensionSnapshot`
- `load_catalog()` → `load_extensions()`
- `load_catalog_from_path()` → `load_extensions_from_path()`
- Update imports: `from vibelens.models.extension import ExtensionItem`
- Update all `CatalogItem` references → `ExtensionItem`

- [ ] **Step 4: Update api/__init__.py router registration**

In `src/vibelens/api/__init__.py`:
- Change `from vibelens.api.catalog import router as catalog_router` → `from vibelens.api.extensions import router as extensions_router`
- Change `routers.include_router(catalog_router)` → `routers.include_router(extensions_router)`

This is critical — without this update the app will fail to start after the file rename.

- [ ] **Step 5: Update app.py if it references catalog imports**

In `src/vibelens/app.py`:
- Update `import_agent_skills` import from `vibelens.services.skill.importer` (this will be updated or kept temporarily)

- [ ] **Step 6: Update all downstream imports**

Files referencing `from vibelens.services.recommendation.catalog import`:
- `src/vibelens/api/extensions.py` — update to `load_extensions`, `ExtensionSnapshot`
- `src/vibelens/services/recommendation/engine.py` — update references
- `src/vibelens/services/recommendation/retrieval.py` — update references

- [ ] **Step 7: Delete old services/catalog/**

```bash
rm -rf src/vibelens/services/catalog/
```

- [ ] **Step 8: Run linter and test suite**

Run: `ruff check src/ tests/`
Run: `pytest tests/ -v -s --tb=short 2>&1 | head -100`
Expected: Pass (fix any remaining import errors)

- [ ] **Step 9: Commit**

```bash
git add -A
git commit -m "refactor: rename API catalog -> extensions, update schemas and routes"
```

---

### Task 9: Update deps.py and Delete services/skill/

**Files:**
- Modify: `src/vibelens/deps.py`
- Modify: `src/vibelens/app.py`
- Delete: `src/vibelens/services/skill/`

- [ ] **Step 1: Update deps.py singleton names and imports**

In `src/vibelens/deps.py`:
- Update all `from vibelens.models.skill import SkillSource` → `from vibelens.models.skill import ExtensionSource`
- Update all `from vibelens.storage.skill.*` → `from vibelens.storage.extension.*`
- Rename `SkillSource.CLAUDE` → `ExtensionSource.CLAUDE`
- Rename `DiskSkillStore` → `DiskExtensionStore`
- Rename `CentralSkillStore` → `CentralExtensionStore`
- Rename `create_agent_skill_stores` → `create_agent_extension_stores`
- Rename function names:
  - `get_claude_skill_store` → `get_claude_extension_store`
  - `get_codex_skill_store` → `get_codex_extension_store`
  - `get_central_skill_store` → `get_central_extension_store`
  - `get_agent_skill_stores` → `get_agent_extension_stores`

- [ ] **Step 2: Update app.py startup**

In `src/vibelens/app.py`:
- If it still imports `from vibelens.services.skill.importer import import_agent_skills`, move that logic to `services/extensions/skill.py` or inline it

- [ ] **Step 3: Update api/skill.py imports**

In `src/vibelens/api/skill.py`:
- Update all `from vibelens.storage.skill.*` → `from vibelens.storage.extension.*`
- Update all class names: `DiskSkillStore` → `DiskExtensionStore`, `AGENT_SKILL_REGISTRY` → `AGENT_EXTENSION_REGISTRY`

- [ ] **Step 4: Update services/personalization/shared.py**

If it references the old skill store DI functions, update to new names.

- [ ] **Step 5: Delete services/skill/**

```bash
rm -rf src/vibelens/services/skill/
```

The download logic from `services/skill/download.py` can be moved to `services/extensions/skill.py` if needed by the skill handler's download method. For now, move the `download_skill_directory` function and its constants to `services/extensions/skill.py`:

Add to `src/vibelens/services/extensions/skill.py`:

```python
"""Skill extension handler."""

import re
from pathlib import Path

import httpx

from vibelens.services.extensions.base import FileBasedHandler
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_TREE_PATTERN = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<ref>[^/]+)/(?P<path>.+)"
)
REQUEST_TIMEOUT_SECONDS = 30


class SkillHandler(FileBasedHandler):
    """Handler for skill extensions.

    Skills install as directories with SKILL.md inside ~/.claude/skills/.
    Supports downloading from GitHub tree URLs.
    """

    def download(self, source_url: str, target_dir: Path) -> bool:
        """Download a skill directory from a GitHub tree URL.

        Args:
            source_url: GitHub tree URL.
            target_dir: Local directory to write files into.

        Returns:
            True if at least one file was downloaded.
        """
        match = GITHUB_TREE_PATTERN.match(source_url)
        if not match:
            logger.warning("Cannot parse GitHub URL: %s", source_url)
            return False

        owner = match.group("owner")
        repo = match.group("repo")
        ref = match.group("ref")
        path = match.group("path")

        target_dir.mkdir(parents=True, exist_ok=True)
        try:
            downloaded = _fetch_directory_recursive(owner, repo, ref, path, target_dir)
            logger.info("Downloaded %d files from %s/%s/%s", downloaded, owner, repo, path)
            return downloaded > 0
        except httpx.HTTPError as exc:
            logger.error("GitHub API request failed: %s", exc)
            return False


def _fetch_directory_recursive(
    owner: str, repo: str, ref: str, path: str, local_dir: Path
) -> int:
    """Recursively fetch all files from a GitHub directory.

    Args:
        owner: Repository owner.
        repo: Repository name.
        ref: Git ref (branch/tag).
        path: Directory path within the repo.
        local_dir: Local directory to write into.

    Returns:
        Number of files downloaded.
    """
    api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.get(api_url)
        response.raise_for_status()
        entries = response.json()

    if not isinstance(entries, list):
        return 0

    downloaded = 0
    for entry in entries:
        if entry["type"] == "file":
            raw_url = entry.get("download_url") or f"{GITHUB_RAW_BASE}/{owner}/{repo}/{ref}/{entry['path']}"
            downloaded += _fetch_file(raw_url, local_dir / entry["name"])
        elif entry["type"] == "dir":
            sub_dir = local_dir / entry["name"]
            sub_dir.mkdir(parents=True, exist_ok=True)
            downloaded += _fetch_directory_recursive(owner, repo, ref, entry["path"], sub_dir)
    return downloaded


def _fetch_file(url: str, local_path: Path) -> int:
    """Download a single file.

    Args:
        url: Raw file URL.
        local_path: Local file path.

    Returns:
        1 on success, 0 on failure.
    """
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.get(url)
            response.raise_for_status()
        local_path.write_bytes(response.content)
        return 1
    except httpx.HTTPError as exc:
        logger.warning("Failed to download %s: %s", url, exc)
        return 0
```

- [ ] **Step 6: Run full test suite and linter**

Run: `ruff check src/ tests/`
Run: `pytest tests/ -v -s --tb=short 2>&1 | head -100`
Expected: Pass

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "refactor: update deps.py, move download logic, delete services/skill/"
```

---

### Task 10: Frontend Renames

**Files:**
- Rename: `frontend/src/components/personalization/catalog-*.tsx` → `extension-*.tsx`
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/personalization/personalization-panel.tsx`
- Modify: `frontend/src/components/personalization/recommendation-constants.ts`
- Modify: `frontend/src/components/personalization/recommendation-card.tsx`

- [ ] **Step 1: Rename frontend files**

```bash
cd frontend/src/components/personalization
git mv catalog-card.tsx extension-card.tsx
git mv catalog-constants.ts extension-constants.ts
git mv catalog-detail-content.tsx extension-detail-content.tsx
git mv catalog-detail-view.tsx extension-detail-view.tsx
git mv catalog-explore-tab.tsx extension-explore-tab.tsx
git mv catalog-format.ts extension-format.ts
git mv catalog-pagination.tsx extension-pagination.tsx
```

- [ ] **Step 2: Update types.ts**

In `frontend/src/types.ts`:
- Rename `CatalogItemSummary` → `ExtensionItemSummary`
- Rename `CatalogListResponse` → `ExtensionListResponse`
- Rename `CatalogMetaResponse` → `ExtensionMetaResponse`
- Rename `CatalogInstallResponse` → `ExtensionInstallResponse`
- Rename `CatalogRecommendation` → `ExtensionRecommendation`
- In `RecommendationResult`: rename `catalog_version` → `extension_catalog_version`, update `recommendations: ExtensionRecommendation[]`
- In `ExtensionItemSummary`: rename `item_id` → `extension_id`, `item_type` → `extension_type`
- In `RecommendationItem`: rename `item_id` → `extension_id`, `item_type` → `extension_type`
- Rename `SkillInfo` → `ExtensionInfo`, `SkillSourceInfo` → `ExtensionSourceInfo`, `SkillSource` → `ExtensionSource` (frontend interfaces)

- [ ] **Step 3: Update extension-constants.ts**

Rename exports:
- `ITEM_TYPE_COLORS` → `EXTENSION_TYPE_COLORS`
- `ITEM_TYPE_LABELS` → `EXTENSION_TYPE_LABELS`
- `ITEM_TYPE_ICON_COLORS` → `EXTENSION_TYPE_ICON_COLORS`

- [ ] **Step 4: Update recommendation-constants.ts**

Rename exports (deduplicate if possible — import from extension-constants instead):
- `ITEM_TYPE_COLORS` → `EXTENSION_TYPE_COLORS`
- `ITEM_TYPE_LABELS` → `EXTENSION_TYPE_LABELS`

Better: delete duplicates and import from `./extension-constants`.

- [ ] **Step 5: Update all internal imports in renamed files**

Each `extension-*.tsx` file needs its imports updated:
- `./catalog-constants` → `./extension-constants`
- `./catalog-format` → `./extension-format`
- `./catalog-card` → `./extension-card`
- `./catalog-detail-content` → `./extension-detail-content`
- `./catalog-detail-view` → `./extension-detail-view`
- `./catalog-pagination` → `./extension-pagination`
- `CatalogItemSummary` → `ExtensionItemSummary`
- `ITEM_TYPE_LABELS` → `EXTENSION_TYPE_LABELS`
- `ITEM_TYPE_COLORS` → `EXTENSION_TYPE_COLORS`

- [ ] **Step 6: Update API fetch URLs**

In `extension-explore-tab.tsx`:
- `/api/catalog/meta` → `/api/extensions/meta`
- `/api/catalog?${params}` → `/api/extensions?${params}`
- `item_type` query param → `extension_type`

In `extension-card.tsx`:
- `/api/catalog/${...}/install` → `/api/extensions/${...}/install`

In `extension-detail-view.tsx`:
- `/api/catalog/${...}` → `/api/extensions/${...}`
- `/api/catalog/${...}/content` → `/api/extensions/${...}/content`
- `/api/catalog/${...}/install` → `/api/extensions/${...}/install`

- [ ] **Step 7: Update field accesses**

Throughout all extension-*.tsx files:
- `item.item_id` → `item.extension_id`
- `item.item_type` → `item.extension_type`

In `recommendation-card.tsx`:
- `rec.item_type` → `rec.extension_type`
- `rec.item_id` → `rec.extension_id`

In `recommendation-results-view.tsx`:
- `key={rec.item_id}` → `key={rec.extension_id}`

- [ ] **Step 8: Update personalization-panel.tsx**

Update import: `CatalogExploreTab` → `ExtensionExploreTab` from `./extension-explore-tab`

- [ ] **Step 9: Update personalization-panel.tsx and local-skills-tab.tsx**

Replace `SkillInfo` → `ExtensionInfo` and `SkillSourceInfo` → `ExtensionSourceInfo` in imports and type annotations.

- [ ] **Step 10: Build frontend to verify**

Run: `cd frontend && npm run build`
Expected: Build succeeds with zero TypeScript errors

- [ ] **Step 11: Commit**

```bash
git add -A
git commit -m "refactor: rename frontend catalog -> extension, update types and API URLs"
```

---

### Task 11: Update Tests

**Files:**
- Move/update: `tests/catalog/` — update imports, delete builder tests if builder is gone
- Move: `tests/services/catalog/` → `tests/services/extensions/` (merge with existing)
- Update: `tests/api/test_catalog_api.py`
- Update: `tests/services/recommendation/test_*.py`

- [ ] **Step 1: Update tests/catalog/ imports**

In all `tests/catalog/*.py` files:
- `from vibelens.catalog import CatalogItem, ItemType` → `from vibelens.models.extension import ExtensionItem` + `from vibelens.models.enums import AgentExtensionType`
- `ItemType.SKILL` → `AgentExtensionType.SKILL`
- `CatalogItem(item_type=..., item_id=...)` → `ExtensionItem(extension_type=..., extension_id=...)`
- `item.item_type` → `item.extension_type`

If `tests/catalog/test_builder.py` references deleted builder code, delete the test file.

- [ ] **Step 2: Update tests/services/catalog/test_install.py**

Move to `tests/services/extensions/test_install.py` and update:
- Imports to use `ExtensionItem`, `AgentExtensionType`
- `install_catalog_item` → use handler registry or update function name
- All `item_type=` → `extension_type=`, `item_id=` → `extension_id=`

- [ ] **Step 3: Update tests/api/test_catalog_api.py**

Rename to `tests/api/test_extensions_api.py` and update:
- Route URLs: `/api/catalog` → `/api/extensions`
- Model imports and field names

- [ ] **Step 4: Update tests/services/recommendation/test_*.py**

In `test_scoring.py`, `test_catalog.py`, `test_retrieval.py`:
- Update imports: `CatalogItem` → `ExtensionItem`, `ItemType` → `AgentExtensionType`
- Update field names

- [ ] **Step 5: Run full test suite**

Run: `pytest tests/ -v -s --tb=short`
Expected: All tests pass

Run: `ruff check src/ tests/`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "test: update all tests for extension refactor renames"
```

---

### Task 12: Final Verification and Cleanup

**Files:**
- Modify: `CLAUDE.md` — update project structure docs
- Verify: no stale references remain

- [ ] **Step 1: Search for any remaining stale references**

```bash
# These should all return zero results
rg "ItemType" src/ tests/ --type py
rg "CatalogItem" src/ tests/ --type py
rg "PersonalizationElementType" src/ tests/ --type py
rg "RecommendationItemType" src/ tests/ --type py
rg "from vibelens.catalog" src/ tests/ --type py
rg "from vibelens.services.catalog" src/ tests/ --type py
rg "from vibelens.services.skill" src/ tests/ --type py
rg "from vibelens.storage.skill" src/ tests/ --type py
rg "SkillSource" src/ tests/ --type py
rg "BaseSkillStore\|DiskSkillStore\|CentralSkillStore" src/ tests/ --type py
rg "AGENT_SKILL_REGISTRY" src/ tests/ --type py
rg "/api/catalog" frontend/src/ --type ts --type tsx
rg "item_type\|item_id" frontend/src/types.ts
rg "CatalogItemSummary\|CatalogRecommendation\|CatalogListResponse\|CatalogMetaResponse\|CatalogInstallResponse" frontend/src/ --type ts --type tsx
rg "ITEM_TYPE_LABELS\|ITEM_TYPE_COLORS" frontend/src/ --type ts --type tsx
rg "catalog_router" src/vibelens/api/ --type py
```

Fix any remaining references found.

- [ ] **Step 2: Run full backend test suite**

Run: `pytest tests/ -v -s`
Expected: All tests pass

- [ ] **Step 3: Run linter**

Run: `ruff check src/ tests/`
Expected: No errors

- [ ] **Step 4: Build frontend**

Run: `cd frontend && npm run build`
Expected: Build succeeds with zero TypeScript errors

- [ ] **Step 5: Update cli.py catalog commands**

In `src/vibelens/cli.py`:
- Rename `update_catalog()` → `update_extensions()` (or keep as placeholder if not fully implemented)
- Rename `build_catalog()` → `build_extensions()` (or keep as placeholder if not fully implemented)
- Update any imports of `CatalogItem`, `ItemType`, or catalog-related modules
- Update command names in the Typer app if they reference "catalog"

- [ ] **Step 6: Update CLAUDE.md project structure**

Update the project structure section to reflect:
- `models/extension.py` — ExtensionItem model
- `models/enums.py` — includes AgentExtensionType, ExtensionSource
- `storage/extension/` — replaces storage/skill/
- `services/extensions/` — per-type handlers
- `api/extensions.py` — replaces api/catalog.py
- Delete references to `catalog/`, `services/catalog/`, `services/skill/`, `storage/skill/`

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: final cleanup and docs update for extension refactor"
```
