# Extension Refactor Design

Unify the catalog/personalization type system under `AgentExtensionType`, rename "catalog" to "extensions", and build full management services for all 5 extension types (skill, subagent, command, hook, repo).

## Reference: Claude Code Extension Types

Per the official Anthropic docs (https://code.claude.com/docs/en/skills.md, https://code.claude.com/docs/en/hooks.md, https://code.claude.com/docs/en/mcp.md):

### Skills (`.claude/skills/<name>/SKILL.md`)

Directory-based. Each skill is a folder with `SKILL.md` (YAML frontmatter + markdown body) plus optional auxiliary files (reference docs, scripts). Installed to `~/.claude/skills/` (personal) or `.claude/skills/` (project). Claude auto-invokes based on `description` matching.

Key frontmatter: `name`, `description`, `when_to_use`, `argument-hint`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `model`, `effort`, `context`, `agent`, `hooks`, `paths`.

### Commands (`.claude/commands/<name>.md`) -- legacy

Single flat `.md` file with the same YAML frontmatter as skills. Functionally identical to skills but without auxiliary file support or auto-invocation. Still fully supported but skills are recommended. If both exist with the same name, the skill wins.

### Subagents -- skills with `context: fork`

A subagent is a skill with `context: fork` and `agent: <type>` in frontmatter. When invoked, it runs in an isolated subagent. Not a fundamentally different file format -- just skills with specific frontmatter fields.

### Hooks (`settings.json` + optional script files)

Defined in `settings.json` under the `hooks` key. Structure: `hooks -> event_name -> [{matcher, hooks: [{type, command}]}]`. Four hook types: `command`, `http`, `prompt`, `agent`. Command hooks can reference external script files (conventionally in `.claude/hooks/`). So a hook installation is hybrid: config entry in `settings.json` + optional script file(s) on disk.

Available events: `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `Stop`, `PreToolUse`, `PostToolUse`, `SubagentStart`, `SubagentStop`, `FileChanged`, and more.

### Repos / MCP Servers

MCP server configs are stored in `~/.claude.json` (local/user scope) or `.mcp.json` (project scope) -- NOT in `settings.json`. Three transport types: `stdio` (local process), `http` (remote, recommended), `sse` (deprecated). Schema: `mcpServers -> {name: {type, command/url, args, env, headers}}`.

Note: The current codebase (`services/catalog/install.py`) incorrectly writes MCP configs to `~/.claude/settings.json`. The RepoHandler must write to `~/.claude.json` instead.

## Motivation

- Two overlapping enums (`ItemType` in catalog, `PersonalizationElementType` in personalization) define the same concept with inconsistent coverage
- "Catalog" is vague -- these are agent extensions that users discover, install, create, and evolve
- Only skills have management logic (`services/skill/`); hooks, subagents, commands, and repos lack import/list/uninstall support
- The storage layer (`storage/skill/`) is skill-specific but the pattern generalizes to all file-based extension types

## 1. Enum Consolidation

**`AgentExtensionType`** replaces both `ItemType` and `PersonalizationElementType`.

Location: `src/vibelens/models/enums.py`

```python
class AgentExtensionType(StrEnum):
    """Types of agent extensions that can be discovered, installed, and managed."""
    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
    REPO = "repo"
```

Deletions:
- `ItemType` from `catalog/catalog.py` (module deleted entirely)
- `PersonalizationElementType` from `models/personalization/enums.py`

All references across the codebase update to `AgentExtensionType`.

## 2. Model: ExtensionItem

**`ExtensionItem`** replaces `CatalogItem`.

Location: `src/vibelens/models/extension.py`

Field renames:
- `item_id` -> `extension_id`
- `item_type: ItemType` -> `extension_type: AgentExtensionType`

Constants co-located in the same file:

```python
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
```

The `is_file_based` computed field remains unchanged in purpose.

## 3. Delete src/vibelens/catalog/

The entire `src/vibelens/catalog/` module is deleted. The builder was already removed. `ExtensionItem` lives in `models/extension.py`. Anything that imported from `vibelens.catalog` updates to import from `vibelens.models.extension`.

## 4. Storage Layer Generalization

Rename `src/vibelens/storage/skill/` -> `src/vibelens/storage/extension/`.

| Before | After |
|--------|-------|
| `BaseSkillStore` | `BaseExtensionStore` |
| `DiskSkillStore` | `DiskExtensionStore` |
| `CentralSkillStore` | `CentralExtensionStore` |
| `AGENT_SKILL_REGISTRY` | `AGENT_EXTENSION_REGISTRY` |
| `SkillSource` | `ExtensionSource` |
| `SkillInfo` | `ExtensionInfo` |

File structure:

```
src/vibelens/storage/extension/
  __init__.py
  base.py       -- BaseExtensionStore ABC
  disk.py       -- DiskExtensionStore (directory-based: skill/subagent; flat-file: command)
  central.py    -- CentralExtensionStore (~/.vibelens/skills/)
  agent.py      -- AGENT_EXTENSION_REGISTRY, create_agent_extension_stores()
  config.py     -- NEW: ConfigExtensionStore (hooks/repos in settings.json)
```

### ConfigExtensionStore (new)

Handles JSON config files for hooks and MCP servers. Two separate config targets:

- **Hooks**: `~/.claude/settings.json` under the `hooks` key
- **MCP servers**: `~/.claude.json` under the `mcpServers` key (NOT settings.json -- this fixes a bug in the current codebase)

```python
class ConfigExtensionStore:
    """Manages config entries in Claude Code JSON config files."""

    # Hooks — in settings.json
    def list_hooks(self, settings_path: Path) -> list[InstalledHook]: ...
    def install_hook(self, hook_data: dict, settings_path: Path) -> None: ...
    def remove_hook(self, hook_id: str, settings_path: Path) -> bool: ...

    # MCP servers — in ~/.claude.json
    def list_repos(self, claude_json_path: Path) -> list[InstalledRepo]: ...
    def install_repo(self, repo_data: dict, claude_json_path: Path) -> None: ...
    def remove_repo(self, server_name: str, claude_json_path: Path) -> bool: ...
```

The existing `_read_settings()` / `_write_settings()` helpers from `services/catalog/install.py` move here and generalize to handle both JSON files.

Note: Hooks are hybrid -- they can include both script files (e.g., `.claude/hooks/my-hook.sh`) AND config entries in `settings.json`. The `ConfigExtensionStore` handles only the JSON config side; file components are handled by the `HookHandler` service which coordinates both.

### Agent Extension Registry

The existing `AGENT_SKILL_REGISTRY` maps agents to their skill directories. This generalizes:

```python
AGENT_EXTENSION_REGISTRY: dict[ExtensionSource, Path] = {
    ExtensionSource.CURSOR: Path.home() / ".cursor" / "skills",
    ExtensionSource.OPENCODE: Path.home() / ".config" / "opencode" / "skills",
    # ... same entries, same directories
}
```

The directories remain `skills/` because that is where agents actually store their files. The registry name changes but the paths stay accurate.

## 5. Extension Management Services

New `src/vibelens/services/extensions/` module with per-type handlers.

```
src/vibelens/services/extensions/
  __init__.py
  base.py          -- FileBasedHandler (shared for skill/subagent/command)
  skill.py         -- SkillHandler(FileBasedHandler)
  subagent.py      -- SubagentHandler(FileBasedHandler)
  command.py       -- CommandHandler(FileBasedHandler)
  hook.py          -- HookHandler(FileBasedHandler) -- hybrid: files + settings.json config
  repo.py          -- RepoHandler (uses ConfigExtensionStore)
  registry.py      -- type -> handler mapping, dispatch functions
  platforms.py     -- platform directory configs (see below)
```

### FileBasedHandler (base.py)

Shared logic for file-based extension types (skill, subagent, command, hook):

```python
class FileBasedHandler:
    """Base handler for file-based extensions (skill, subagent, command).

    Uses DiskExtensionStore/CentralExtensionStore for multi-agent
    import, listing, and installation.
    """

    def install(self, item: ExtensionItem, platform: str, overwrite: bool) -> Path: ...
    def download(self, source_url: str, target_dir: Path) -> bool: ...
    def list_installed(self, platform: str) -> list[ExtensionInfo]: ...
    def uninstall(self, name: str, platform: str) -> bool: ...
    def import_from_agents(self) -> int: ...
```

### Per-type handlers

- **SkillHandler**: Inherits FileBasedHandler. Skills are directories with `SKILL.md` + auxiliary files. Adds skill-specific metadata parsing (YAML frontmatter: name, description, allowed-tools, etc.), central store import with source provenance injection. Absorbs logic from deleted `services/skill/importer.py` and `services/skill/download.py`.
- **SubagentHandler**: Inherits FileBasedHandler. Subagents are structurally skills with `context: fork` and `agent` in frontmatter. SubagentHandler inherits all SkillHandler logic but validates that installed items have the required frontmatter fields.
- **CommandHandler**: Inherits FileBasedHandler. Commands are the legacy flat `.md` file format (no subdirectory). CommandHandler writes single `.md` files to `~/.claude/commands/` rather than directories to `~/.claude/skills/`.
- **HookHandler**: Inherits FileBasedHandler. Hooks are hybrid -- they can include script files (written to `.claude/hooks/`) AND config entries merged into `settings.json` under the `hooks` key. HookHandler overrides `install()` to handle both: write any script files via the base class, then merge the hook config entry into settings.json via ConfigExtensionStore. `list_installed()` reads both the hook files on disk and the settings.json config. `uninstall()` removes both.
- **RepoHandler**: Independent handler. Uses ConfigExtensionStore to merge/list/remove MCP server configs in `~/.claude.json` (NOT settings.json). Supports stdio, http, and sse transport types. May also handle non-MCP repo installs (pip, npm) via `install_command`.

### Registry (registry.py)

```python
def get_handler(extension_type: AgentExtensionType) -> FileBasedHandler | HookHandler | RepoHandler:
    """Get the handler for the given extension type."""
    ...

def install_extension(item: ExtensionItem, platform: str, overwrite: bool) -> Path:
    """Dispatch install to the correct handler."""
    ...

def list_installed(extension_type: AgentExtensionType, platform: str) -> list:
    """List installed extensions of a given type."""
    ...
```

### Platform Configs (platforms.py)

Install targets per extension type for Claude Code:

| Type | Install target |
|------|---------------|
| skill | `~/.claude/skills/<name>/SKILL.md` (directory) |
| subagent | `~/.claude/skills/<name>/SKILL.md` (directory, with `context: fork`) |
| command | `~/.claude/commands/<name>.md` (flat file, legacy) |
| hook | `.claude/hooks/<script>` (files) + `~/.claude/settings.json` (config) |
| repo | `~/.claude.json` under `mcpServers` (config) |

### Deletions

- `services/catalog/install.py` -- logic moves to per-type handlers
- `services/catalog/` -- directory deleted
- `services/skill/importer.py` -- logic moves to SkillHandler
- `services/skill/download.py` -- logic moves to SkillHandler (or shared in FileBasedHandler)
- `services/skill/` -- directory deleted

## 6. API Layer

Rename `src/vibelens/api/catalog.py` -> `src/vibelens/api/extensions.py`.

Router prefix: `/api/extensions` (replaces `/api/catalog`).

Endpoints (same functionality, updated naming):

| Before | After |
|--------|-------|
| `GET /catalog` | `GET /extensions` |
| `GET /catalog/meta` | `GET /extensions/meta` |
| `GET /catalog/{id}/content` | `GET /extensions/{id}/content` |
| `GET /catalog/{id}` | `GET /extensions/{id}` |
| `POST /catalog/{id}/install` | `POST /extensions/{id}/install` |

Query param `item_type` -> `extension_type`.

Schemas: `src/vibelens/schemas/catalog.py` -> `src/vibelens/schemas/extensions.py`:
- `CatalogListResponse` -> `ExtensionListResponse`
- `CatalogMetaResponse` -> `ExtensionMetaResponse`
- `CatalogInstallRequest` -> `ExtensionInstallRequest`
- `CatalogInstallResponse` -> `ExtensionInstallResponse`

The `services/recommendation/catalog.py` file (runtime catalog loader) updates:
- `CatalogSnapshot` -> `ExtensionSnapshot`
- `load_catalog()` -> `load_extensions()`
- Still reads `catalog.json` from disk (data file name unchanged)

## 7. Frontend

### Scope: skill-only for this version

The backend implements all 5 extension types, but the frontend only exposes **skill** in this version. Other types (subagent, command, hook, repo) are fully functional in the backend and API, but the UI filters them out or does not surface them. This keeps the UI focused while the backend is ready for future expansion.

Specifically:
- The explore tab filters to `extension_type=skill` by default (or hides the type filter entirely)
- Creation/evolution modes only target skills (already the case)
- The type badge/filter in the extension list is hidden (only one type visible, no need to filter)
- Backend API still accepts all types for future use

### File renames

| Before | After |
|--------|-------|
| `catalog-card.tsx` | `extension-card.tsx` |
| `catalog-constants.ts` | `extension-constants.ts` |
| `catalog-detail-content.tsx` | `extension-detail-content.tsx` |
| `catalog-detail-view.tsx` | `extension-detail-view.tsx` |
| `catalog-explore-tab.tsx` | `extension-explore-tab.tsx` |

### Type renames in types.ts

- `CatalogItemSummary` -> `ExtensionItemSummary`
- `item_type` -> `extension_type`
- `item_id` -> `extension_id`

### Constants in extension-constants.ts

- `ITEM_TYPE_LABELS` -> `EXTENSION_TYPE_LABELS`
- `ITEM_TYPE_COLORS` -> `EXTENSION_TYPE_COLORS`

### API calls

All fetch URLs from `/api/catalog` -> `/api/extensions`.

## 8. Personalization Impact

The personalization pipeline (creation, evolution, recommendation) references `PersonalizationElementType`. All references update to `AgentExtensionType`.

Affected files:
- `models/personalization/enums.py` -- delete `PersonalizationElementType`
- `models/personalization/creation.py` -- `element_type` field type changes
- `services/creation/creation.py` -- import updates
- `services/evolution/evolution.py` -- import updates
- `services/recommendation/` -- `RecommendationItemType` (if it exists) merges with `AgentExtensionType`
- LLM prompts in `prompts/` -- update any references to element types

`PersonalizationMode` stays unchanged (creation, retrieval, evolution, recommendation are analysis modes, not extension types).

## 9. Test Updates

All test files that reference the renamed types, modules, and API routes need updating:
- `tests/catalog/test_builder.py` -- update imports, delete if builder is fully removed
- `tests/services/catalog/test_install.py` -- move to `tests/services/extensions/`
- Any test importing `ItemType`, `CatalogItem`, `PersonalizationElementType`

## Non-goals

- Changing the `catalog.json` data file name on disk (it is serialized data, rename optional)
- Changing the catalog builder scripts outside `src/`
- Refactoring the personalization analysis pipeline (creation/evolution/recommendation logic stays as-is)
- Adding new extension types beyond the current 5
