"""Install and uninstall catalog extension items to agent platform directories."""

import json
import shutil
from pathlib import Path

from vibelens.deps import (
    get_command_service,
    get_hook_service,
    get_plugin_service,
    get_skill_service,
    get_subagent_service,
)
from vibelens.models.enums import AgentExtensionType
from vibelens.models.extension import AgentExtensionItem
from vibelens.services.extensions.platforms import AgentPlatform, get_platform
from vibelens.utils.github import GITHUB_TREE_RE, download_directory
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


def _resolve_platform(target_platform: str) -> AgentPlatform:
    """Look up a platform by ExtensionSource value and verify it is installed.

    Args:
        target_platform: Platform key (e.g. 'claude', 'codex').

    Returns:
        Matching AgentPlatform.

    Raises:
        ValueError: If target_platform is unknown or its root does not exist.
    """
    platform = get_platform(target_platform)
    if not platform.root.expanduser().is_dir():
        raise ValueError(f"Agent {target_platform!r} not installed")
    return platform


def install_catalog_item(
    item: AgentExtensionItem, target_platform: str, overwrite: bool = False
) -> Path:
    """Install a catalog item to the target agent platform.

    Routes to the correct installer based on extension type:
    - SKILL → SkillService.install (central + agent sync)
    - SUBAGENT → SubagentService.install (central + agent sync)
    - COMMAND → CommandService.install (central + agent sync)
    - HOOK → HookService.install (central + tagged merge into settings.json)
    - MCP (install_method="mcp_config") → merges into settings.json mcpServers

    Args:
        item: ExtensionItem with install_content populated.
        target_platform: Platform install key (e.g. 'claude_code').
        overwrite: If True, overwrite existing files.

    Returns:
        Path where the item was installed on the agent side.

    Raises:
        ValueError: If platform is unknown or item type is not installable.
        FileExistsError: If target file exists and overwrite is False.
    """
    platform = _resolve_platform(target_platform)

    if item.extension_type not in platform.supported_types and item.install_method != "mcp_config":
        raise ValueError(f"Agent {target_platform!r} does not support {item.extension_type.value}")

    if item.extension_type == AgentExtensionType.PLUGIN:
        return _install_plugin(
            item=item, target_platform=target_platform, platform=platform, overwrite=overwrite
        )
    if item.extension_type == AgentExtensionType.SUBAGENT:
        if not platform.subagents_dir:
            raise ValueError(f"Platform {target_platform} has no subagents directory")
        return _install_subagent(
            item=item,
            target_platform=target_platform,
            agent_dir=platform.subagents_dir,
            overwrite=overwrite,
        )
    elif item.extension_type == AgentExtensionType.COMMAND:
        if not platform.commands_dir:
            raise ValueError(f"Platform {target_platform} has no commands directory")
        return _install_command(
            item=item,
            target_platform=target_platform,
            agent_dir=platform.commands_dir,
            overwrite=overwrite,
        )
    elif item.extension_type == AgentExtensionType.SKILL:
        if not platform.skills_dir:
            raise ValueError(f"Platform {target_platform} has no skills directory")
        return _install_skill(
            item=item,
            target_platform=target_platform,
            agent_dir=platform.skills_dir,
            overwrite=overwrite,
        )
    elif item.extension_type == AgentExtensionType.HOOK:
        if not platform.hook_config_path:
            raise ValueError(f"Platform {target_platform} has no hook config path")
        return _install_hook(
            item=item,
            target_platform=target_platform,
            settings_path=platform.hook_config_path,
            overwrite=overwrite,
        )
    elif item.install_method == "mcp_config":
        if not platform.hook_config_path:
            raise ValueError(f"Platform {target_platform} has no config path for MCP")
        return _install_mcp(item=item, settings_path=platform.hook_config_path)
    else:
        raise ValueError(
            f"Cannot auto-install item type {item.extension_type} with method {item.install_method}"
        )


def install_from_source_url(
    item: AgentExtensionItem, target_platform: str, overwrite: bool = False
) -> Path:
    """Install a catalog item by downloading its skill directory from GitHub.

    Used when install_content is None but source_url points to a GitHub tree URL.

    Args:
        item: ExtensionItem with a GitHub tree source_url.
        target_platform: Platform install key (e.g. 'claude_code').
        overwrite: If True, overwrite existing directory.

    Returns:
        Path where the skill directory was installed.

    Raises:
        ValueError: If platform is unknown, source_url is missing, or download fails.
        FileExistsError: If target directory exists and overwrite is False.
    """
    platform = _resolve_platform(target_platform)

    if not item.source_url or not GITHUB_TREE_RE.match(item.source_url):
        raise ValueError(f"Item {item.extension_id} has no installable content or valid source URL")

    logger.debug(
        "Downloading %s from %s to %s",
        item.extension_id,
        item.source_url,
        platform.skills_dir / item.name,
    )

    target_dir = platform.skills_dir / item.name
    if target_dir.exists() and not overwrite:
        raise FileExistsError(
            f"Directory already exists: {target_dir}. Use overwrite=true to replace."
        )

    success = download_directory(source_url=item.source_url, target_dir=target_dir)
    if not success:
        raise ValueError(f"Failed to download skill from {item.source_url}")

    logger.debug("Installed %s from source URL to %s", item.extension_id, target_dir)

    if item.extension_type == AgentExtensionType.SKILL:
        try:
            service = get_skill_service()
            central_dir = Path(service.get_item_path(item.name)).parent
            logger.debug("Copying %s to central at %s", item.name, central_dir)
            if central_dir.exists():
                shutil.rmtree(central_dir)
            shutil.copytree(target_dir, central_dir)
            service.invalidate()
        except OSError as exc:
            logger.warning("Failed to copy %s to central: %s", item.name, exc)

    return target_dir


def uninstall_extension(item: AgentExtensionItem, target_platform: str) -> Path:
    """Remove an installed extension from the target platform.

    Args:
        item: ExtensionItem to uninstall.
        target_platform: Platform install key (e.g. 'claude_code').

    Returns:
        Path that was removed.

    Raises:
        ValueError: If platform is unknown.
        FileNotFoundError: If the extension is not installed.
    """
    platform = _resolve_platform(target_platform)

    if item.extension_type == AgentExtensionType.PLUGIN:
        service = get_plugin_service()
        try:
            service.uninstall_from_agent(item.name, target_platform)
        except KeyError as exc:
            raise FileNotFoundError(str(exc)) from exc
        installed_path = _plugin_installed_path(
            platform=platform, name=item.name, target_platform=target_platform
        )
        logger.info("Uninstalled plugin %s from %s", item.extension_id, installed_path)
        return installed_path

    # Check skills dir first (directory-based installs)
    skill_dir = platform.skills_dir / item.name
    if skill_dir.is_dir():
        shutil.rmtree(skill_dir)
        logger.info("Uninstalled %s from %s", item.extension_id, skill_dir)
        return skill_dir

    # Check subagents dir (single-file subagent installs)
    if platform.subagents_dir:
        subagent_file = platform.subagents_dir / f"{item.name}.md"
        if subagent_file.is_file():
            subagent_file.unlink()
            logger.info("Uninstalled %s from %s", item.extension_id, subagent_file)
            return subagent_file

    # Check commands dir (single-file installs)
    if platform.commands_dir:
        command_file = platform.commands_dir / f"{item.name}.md"
        if command_file.is_file():
            command_file.unlink()
            logger.info("Uninstalled %s from %s", item.extension_id, command_file)
            return command_file

    raise FileNotFoundError(f"Extension {item.name} not found on platform {target_platform}")


def _install_file(item: AgentExtensionItem, target_dir: Path, overwrite: bool) -> Path:
    """Write install_content to target directory as {name}.md.

    Args:
        item: ExtensionItem with install_content.
        target_dir: Target directory for the .md file.
        overwrite: If True, replace existing file.

    Returns:
        Path to the written file.

    Raises:
        FileExistsError: If file exists and overwrite is False.
    """
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{item.name}.md"

    if target.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {target}. Use overwrite=true to replace.")

    target.write_text(item.install_content or "", encoding="utf-8")
    logger.debug("Installed %s to %s", item.extension_id, target)
    return target


def _install_skill(
    item: AgentExtensionItem, target_platform: str, agent_dir: Path, overwrite: bool
) -> Path:
    """Install a SKILL via SkillService; populate central + agent dir.

    Args:
        item: ExtensionItem with install_content.
        target_platform: Platform install key used as the service agent key.
        agent_dir: Platform's skills directory (used for the return path).
        overwrite: If True, overwrite existing central content.

    Returns:
        Path to the agent-side skill directory.
    """
    service = get_skill_service()
    content = item.install_content or ""
    logger.debug(
        "Installing skill %s via SkillService (content_len=%d, target=%s)",
        item.name,
        len(content),
        target_platform,
    )
    try:
        service.install(name=item.name, content=content, sync_to=[target_platform])
    except FileExistsError:
        if not overwrite:
            raise
        logger.debug("Skill %s exists in central, modifying + re-syncing", item.name)
        service.modify(name=item.name, content=content)
        service.sync_to_agents(name=item.name, agents=[target_platform])

    installed = agent_dir / item.name
    logger.debug("Installed skill %s to %s", item.extension_id, installed)
    return installed


def _install_subagent(
    item: AgentExtensionItem, target_platform: str, agent_dir: Path, overwrite: bool
) -> Path:
    """Install a SUBAGENT via SubagentService; populate central + agent dir.

    Args:
        item: ExtensionItem with install_content.
        target_platform: Platform install key used as the service agent key.
        agent_dir: Platform's subagents directory (used for the return path).
        overwrite: If True, overwrite existing central content.

    Returns:
        Path to the agent-side .md file.
    """
    service = get_subagent_service()
    content = item.install_content or ""
    try:
        service.install(name=item.name, content=content, sync_to=[target_platform])
    except FileExistsError:
        if overwrite:
            service.modify(name=item.name, content=content)
        service.sync_to_agents(name=item.name, agents=[target_platform])

    installed = agent_dir / f"{item.name}.md"
    logger.debug("Installed subagent %s to %s", item.extension_id, installed)
    return installed


def _install_command(
    item: AgentExtensionItem, target_platform: str, agent_dir: Path, overwrite: bool
) -> Path:
    """Install a COMMAND via CommandService; populate central + agent dir.

    Args:
        item: ExtensionItem with install_content.
        target_platform: Platform install key used as the service agent key.
        agent_dir: Platform's commands directory (used for the return path).
        overwrite: If True, overwrite existing central content.

    Returns:
        Path to the agent-side .md file.
    """
    service = get_command_service()
    content = item.install_content or ""
    try:
        service.install(name=item.name, content=content, sync_to=[target_platform])
    except FileExistsError:
        if overwrite:
            service.modify(name=item.name, content=content)
        service.sync_to_agents(name=item.name, agents=[target_platform])

    installed = agent_dir / f"{item.name}.md"
    logger.debug("Installed command %s to %s", item.extension_id, installed)
    return installed


def _install_hook(
    item: AgentExtensionItem, target_platform: str, settings_path: Path, overwrite: bool
) -> Path:
    """Install a HOOK via HookService; populate central + tagged merge into settings.

    Args:
        item: ExtensionItem with hook JSON in install_content.
        target_platform: Platform install key used as the service agent key.
        settings_path: Path to the agent settings.json (used for the return path).
        overwrite: If True, overwrite existing central hook config.

    Returns:
        Path to the agent settings.json.
    """
    service = get_hook_service()
    blob = json.loads(item.install_content or "{}")
    hook_config = blob.get("hooks", blob)
    if not isinstance(hook_config, dict):
        raise ValueError(f"Hook {item.name!r} install_content has no hook groups")

    try:
        service.install(
            name=item.name,
            description=item.description or "",
            tags=list(item.tags or []),
            hook_config=hook_config,
            sync_to=[target_platform],
        )
    except FileExistsError:
        if overwrite:
            service.modify(name=item.name, hook_config=hook_config)
        service.sync_to_agents(name=item.name, agents=[target_platform])

    logger.debug("Installed hook %s to %s", item.extension_id, settings_path)
    return settings_path


def _install_mcp(item: AgentExtensionItem, settings_path: Path) -> Path:
    """Merge MCP server config into settings.json mcpServers.

    Args:
        item: ExtensionItem with MCP JSON in install_content.
        settings_path: Path to settings.json.

    Returns:
        Path to the settings file.
    """
    settings = _read_settings(settings_path=settings_path)
    mcp_data = json.loads(item.install_content or "{}")
    servers = mcp_data.get("mcpServers") or {}

    existing_servers = settings.setdefault("mcpServers", {})
    existing_servers.update(servers)

    _write_settings(settings_path=settings_path, settings=settings)
    logger.debug("Installed MCP %s to %s", item.extension_id, settings_path)
    return settings_path


def _read_settings(settings_path: Path) -> dict:
    """Read settings.json, returning empty dict if missing or invalid.

    Args:
        settings_path: Path to the settings JSON file.

    Returns:
        Parsed settings dict, or empty dict on missing/invalid file.
    """
    if settings_path.is_file():
        try:
            return json.loads(settings_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _write_settings(settings_path: Path, settings: dict) -> None:
    """Write settings dict back to settings.json.

    Args:
        settings_path: Path to write the settings JSON file.
        settings: Settings dict to serialize.
    """
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def _install_plugin(
    item: AgentExtensionItem, target_platform: str, platform: AgentPlatform, overwrite: bool
) -> Path:
    """Install a PLUGIN extension via PluginService.

    The service writes the plugin manifest to the VibeLens central plugin
    store and syncs the full plugin directory to the target agent's store.
    Claude agent stores drive the 4-file marketplace merge under the hood;
    other agents perform a plain directory drop into ``plugins_dir``.
    """
    manifest_text = _fetch_plugin_manifest(item=item)
    service = get_plugin_service()

    try:
        service.install(name=item.name, content=manifest_text, sync_to=[target_platform])
    except FileExistsError:
        if not overwrite:
            raise
        service.modify(name=item.name, content=manifest_text)
        service.sync_to_agents(name=item.name, agents=[target_platform])

    _populate_plugin_assets(item=item, service=service)
    service.sync_to_agents(name=item.name, agents=[target_platform])

    installed_path = _plugin_installed_path(
        platform=platform, name=item.name, target_platform=target_platform
    )
    logger.info("Installed plugin %s to %s", item.extension_id, installed_path)
    return installed_path


def _fetch_plugin_manifest(item: AgentExtensionItem) -> str:
    """Extract plugin.json text from install_content or download from source_url."""
    if item.install_content:
        payload = json.loads(item.install_content)
        if not isinstance(payload, dict) or "plugin.json" not in payload:
            raise ValueError(f"Plugin {item.name}: install_content must include 'plugin.json'")
        return json.dumps(payload["plugin.json"], indent=2)

    if not item.source_url:
        raise ValueError(f"Plugin {item.name}: no install_content or source_url")

    import tempfile

    with tempfile.TemporaryDirectory() as scratch:
        scratch_dir = Path(scratch) / item.name
        scratch_dir.mkdir(parents=True)
        if not download_directory(source_url=item.source_url, target_dir=scratch_dir):
            raise ValueError(f"Failed to download plugin from {item.source_url}")
        manifest_path = scratch_dir / ".claude-plugin" / "plugin.json"
        if not manifest_path.is_file():
            raise ValueError(
                f"Plugin {item.name}: downloaded tree missing .claude-plugin/plugin.json"
            )
        return manifest_path.read_text(encoding="utf-8")


def _populate_plugin_assets(item: AgentExtensionItem, service) -> None:
    """Download plugin assets (skills, commands, agents) into the central plugin dir.

    For plugins sourced from GitHub, copy the full tree alongside the
    manifest so that ``sync_to_agents`` carries all files. Plugins with
    only ``install_content`` contribute just the manifest.
    """
    if not item.source_url:
        return
    central_plugin_dir = Path(service.get_item_path(item.name)).parent.parent
    central_plugin_dir.parent.mkdir(parents=True, exist_ok=True)
    download_directory(source_url=item.source_url, target_dir=central_plugin_dir)


def _plugin_installed_path(platform: AgentPlatform, name: str, target_platform: str) -> Path:
    """Return the on-agent installed path for a plugin (for reporting)."""
    from vibelens.models.enums import ExtensionSource

    if platform.source == ExtensionSource.CLAUDE:
        return platform.root.expanduser() / "plugins" / "cache" / "vibelens" / name
    if platform.plugins_dir is None:
        raise ValueError(f"Platform {target_platform} has no plugins directory")
    return platform.plugins_dir.expanduser() / name
