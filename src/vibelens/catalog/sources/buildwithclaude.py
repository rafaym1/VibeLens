"""Parse buildwithclaude plugins directory and MCP servers JSON."""

import contextlib
import json
from pathlib import Path

from vibelens.catalog.frontmatter import extract_tags, parse_frontmatter
from vibelens.models.recommendation.catalog import CatalogItem, ItemType

SOURCE_PREFIX = "bwc"
DEFAULT_PLATFORMS = ["claude_code"]


def parse_buildwithclaude(hub_dir: Path) -> tuple[list[CatalogItem], dict[str, str]]:
    """Parse all items from a buildwithclaude hub directory.

    Reads plugins/ subdirectories for agents, commands, skills, hooks,
    and mcp-servers.json for MCP server entries.

    Args:
        hub_dir: Path to the buildwithclaude directory.

    Returns:
        Tuple of (items, path_map) where path_map maps item_id to relative
        file path from hub_dir.
    """
    items: list[CatalogItem] = []
    path_map: dict[str, str] = {}
    plugins_dir = hub_dir / "plugins"
    if plugins_dir.is_dir():
        plugin_items, plugin_paths = _parse_plugins(plugins_dir, hub_dir)
        items.extend(plugin_items)
        path_map.update(plugin_paths)
    mcp_path = hub_dir / "mcp-servers.json"
    if mcp_path.is_file():
        items.extend(_parse_mcp_servers(mcp_path))
    return items, path_map


def _parse_plugins(
    plugins_dir: Path, hub_dir: Path
) -> tuple[list[CatalogItem], dict[str, str]]:
    """Parse all plugin packages under plugins/.

    Args:
        plugins_dir: Path to the plugins/ directory.
        hub_dir: Path to the hub root, used to compute relative paths.

    Returns:
        Tuple of (items, path_map) where path_map maps item_id to relative
        file path from hub_dir.
    """
    items: list[CatalogItem] = []
    path_map: dict[str, str] = {}
    for plugin_dir in sorted(plugins_dir.iterdir()):
        if not plugin_dir.is_dir():
            continue
        for item in _parse_agents(plugin_dir):
            items.append(item)
            abs_path = plugin_dir / "agents" / f"{item.name}.md"
            with contextlib.suppress(ValueError):
                path_map[item.item_id] = str(abs_path.relative_to(hub_dir))
        for item in _parse_commands(plugin_dir):
            items.append(item)
            abs_path = plugin_dir / "commands" / f"{item.name}.md"
            with contextlib.suppress(ValueError):
                path_map[item.item_id] = str(abs_path.relative_to(hub_dir))
        for item in _parse_skills(plugin_dir):
            items.append(item)
            abs_path = plugin_dir / "skills" / item.name / "SKILL.md"
            with contextlib.suppress(ValueError):
                path_map[item.item_id] = str(abs_path.relative_to(hub_dir))
        for item in _parse_hooks(plugin_dir):
            items.append(item)
            abs_path = plugin_dir / "hooks" / f"{item.name}.json"
            with contextlib.suppress(ValueError):
                path_map[item.item_id] = str(abs_path.relative_to(hub_dir))
    return items, path_map


def _parse_agents(plugin_dir: Path) -> list[CatalogItem]:
    """Parse agents/*.md files in a plugin directory.

    Args:
        plugin_dir: Path to a single plugin package directory.

    Returns:
        List of CatalogItem instances with ItemType.SUBAGENT.
    """
    agents_dir = plugin_dir / "agents"
    if not agents_dir.is_dir():
        return []
    return [
        item
        for md_file in sorted(agents_dir.glob("*.md"))
        if (item := _md_to_item(md_file, ItemType.SUBAGENT, "agent")) is not None
    ]


def _parse_commands(plugin_dir: Path) -> list[CatalogItem]:
    """Parse commands/*.md files in a plugin directory.

    Args:
        plugin_dir: Path to a single plugin package directory.

    Returns:
        List of CatalogItem instances with ItemType.COMMAND.
    """
    commands_dir = plugin_dir / "commands"
    if not commands_dir.is_dir():
        return []
    return [
        item
        for md_file in sorted(commands_dir.glob("*.md"))
        if (item := _md_to_item(md_file, ItemType.COMMAND, "command")) is not None
    ]


def _parse_skills(plugin_dir: Path) -> list[CatalogItem]:
    """Parse skills/*/SKILL.md files in a plugin directory.

    Args:
        plugin_dir: Path to a single plugin package directory.

    Returns:
        List of CatalogItem instances with ItemType.SKILL.
    """
    skills_dir = plugin_dir / "skills"
    if not skills_dir.is_dir():
        return []
    items: list[CatalogItem] = []
    for skill_md in sorted(skills_dir.glob("*/SKILL.md")):
        item = _md_to_item(skill_md, ItemType.SKILL, "skill")
        if item:
            items.append(item)
    return items


def _parse_hooks(plugin_dir: Path) -> list[CatalogItem]:
    """Parse hooks/*.json files in a plugin directory.

    Args:
        plugin_dir: Path to a single plugin package directory.

    Returns:
        List of CatalogItem instances with ItemType.HOOK.
    """
    hooks_dir = plugin_dir / "hooks"
    if not hooks_dir.is_dir():
        return []
    items: list[CatalogItem] = []
    for json_file in sorted(hooks_dir.glob("*.json")):
        item = _hook_json_to_item(json_file, plugin_dir.name)
        if item:
            items.append(item)
    return items


def _md_to_item(md_path: Path, item_type: ItemType, type_label: str) -> CatalogItem | None:
    """Convert a Markdown file with frontmatter to a CatalogItem.

    Args:
        md_path: Path to the Markdown file.
        item_type: The ItemType to assign.
        type_label: Short label used in the item_id (e.g. "agent", "command").

    Returns:
        CatalogItem if description is present, else None.
    """
    try:
        content = md_path.read_text(encoding="utf-8")
    except OSError:
        return None

    meta, _body = parse_frontmatter(content)
    name = meta.get("name") or md_path.stem
    description = meta.get("description") or ""
    if not description:
        return None

    category = meta.get("category") or "uncategorized"
    item_id = f"{SOURCE_PREFIX}:{type_label}:{name}"

    return CatalogItem(
        item_id=item_id,
        item_type=item_type,
        name=name,
        description=description,
        tags=extract_tags(meta),
        category=category,
        platforms=DEFAULT_PLATFORMS,
        quality_score=0.0,
        popularity=0.0,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="skill_file",
        install_content=content,
    )


def _hook_json_to_item(json_path: Path, plugin_name: str) -> CatalogItem | None:
    """Convert a hook JSON file to a CatalogItem.

    Args:
        json_path: Path to the hook JSON file.
        plugin_name: Name of the parent plugin directory, used as fallback name.

    Returns:
        CatalogItem if description is present, else None.
    """
    try:
        data = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    description = data.get("description") or ""
    if not description:
        return None

    name = json_path.stem if json_path.stem != "hooks" else plugin_name
    item_id = f"{SOURCE_PREFIX}:hook:{name}"

    return CatalogItem(
        item_id=item_id,
        item_type=ItemType.HOOK,
        name=name,
        description=description,
        tags=[],
        category="automation",
        platforms=DEFAULT_PLATFORMS,
        quality_score=0.0,
        popularity=0.0,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="hook_config",
        install_content=json.dumps(data, indent=2),
    )


def _parse_mcp_servers(mcp_path: Path) -> list[CatalogItem]:
    """Parse mcp-servers.json into a list of CatalogItems.

    Args:
        mcp_path: Path to the mcp-servers.json file.

    Returns:
        List of CatalogItem instances with ItemType.REPO.
    """
    try:
        data = json.loads(mcp_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    servers = data.get("mcpServers") or {}
    items: list[CatalogItem] = []
    for server_id, config in servers.items():
        metadata = config.get("_metadata") or {}
        description = metadata.get("description") or ""
        if not description:
            continue

        display_name = metadata.get("displayName") or server_id
        category = metadata.get("category") or "mcp"
        command = config.get("command") or ""
        args = config.get("args") or []
        install_cmd = f"{command} {' '.join(args)}" if command else None
        repository = metadata.get("repository") or ""

        item_id = f"{SOURCE_PREFIX}:mcp:{server_id}"
        config_clean = {k: v for k, v in config.items() if k != "_metadata"}
        install_json = json.dumps({"mcpServers": {server_id: config_clean}}, indent=2)

        items.append(
            CatalogItem(
                item_id=item_id,
                item_type=ItemType.REPO,
                name=display_name,
                description=description,
                tags=[],
                category=category,
                platforms=DEFAULT_PLATFORMS,
                quality_score=0.0,
                popularity=0.0,
                updated_at="",
                source_url=repository,
                repo_full_name="",
                install_method="mcp_config",
                install_command=install_cmd,
                install_content=install_json,
            )
        )
    return items
