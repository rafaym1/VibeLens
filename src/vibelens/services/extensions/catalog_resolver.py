"""Install and uninstall catalog extension items to agent platform directories."""

import shutil
import tempfile
from pathlib import Path

from vibelens.deps import get_plugin_service, get_skill_service
from vibelens.models.enums import AgentExtensionType, ExtensionSource
from vibelens.models.extension import AgentExtensionItem
from vibelens.services.extensions.platforms import AgentPlatform, get_platform
from vibelens.utils.github import GITHUB_TREE_RE, download_directory
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


def _resolve_platform(target_platform: str) -> AgentPlatform:
    """Look up a platform by ExtensionSource value and verify it is installed."""
    platform = get_platform(target_platform)
    if not platform.root.expanduser().is_dir():
        raise ValueError(f"Agent {target_platform!r} not installed")
    return platform


def install_catalog_item(
    item: AgentExtensionItem, target_platform: str, overwrite: bool = False
) -> Path:
    """Install a catalog item to the target agent platform.

    Dispatches by extension_type. The service layer (``services/extensions/
    catalog.py::install_extension``) gates HOOK / MCP_SERVER / REPO before
    this resolver is called, so we only handle SKILL / SUBAGENT / COMMAND /
    PLUGIN here.
    """
    platform = _resolve_platform(target_platform)
    if item.extension_type not in platform.supported_types:
        raise ValueError(
            f"Agent {target_platform!r} does not support {item.extension_type.value}"
        )

    if item.extension_type == AgentExtensionType.PLUGIN:
        return _install_plugin(
            item=item, target_platform=target_platform, platform=platform, overwrite=overwrite
        )

    return install_from_source_url(
        item=item, target_platform=target_platform, overwrite=overwrite
    )


def install_from_source_url(
    item: AgentExtensionItem, target_platform: str, overwrite: bool = False
) -> Path:
    """Download the item's GitHub tree into the target agent directory.

    Used for SKILL (directory), SUBAGENT (single file), COMMAND (single file).
    ``download_directory`` handles both tree URLs and single-file blob paths.
    """
    platform = _resolve_platform(target_platform)

    if not item.source_url or not GITHUB_TREE_RE.match(item.source_url):
        raise ValueError(
            f"Item {item.extension_id} has no installable content or valid source URL"
        )

    target_dir = _target_dir_for(item=item, platform=platform)
    if target_dir is None:
        raise ValueError(
            f"Platform {target_platform!r} has no directory for {item.extension_type.value}"
        )

    if target_dir.exists() and not overwrite:
        raise FileExistsError(
            f"Directory already exists: {target_dir}. Use overwrite=true to replace."
        )

    logger.debug(
        "Downloading %s from %s to %s", item.extension_id, item.source_url, target_dir
    )

    success = download_directory(source_url=item.source_url, target_dir=target_dir)
    if not success:
        raise ValueError(f"Failed to download {item.extension_type.value} from {item.source_url}")

    if item.extension_type == AgentExtensionType.SKILL:
        _mirror_skill_to_central(name=item.name, target_dir=target_dir)

    logger.debug("Installed %s to %s", item.extension_id, target_dir)
    return target_dir


def _target_dir_for(item: AgentExtensionItem, platform: AgentPlatform) -> Path | None:
    """Return the on-agent install path for the item's type, or None if unsupported."""
    if item.extension_type == AgentExtensionType.SKILL and platform.skills_dir:
        return platform.skills_dir / item.name
    if item.extension_type == AgentExtensionType.SUBAGENT and platform.subagents_dir:
        return platform.subagents_dir / item.name
    if item.extension_type == AgentExtensionType.COMMAND and platform.commands_dir:
        return platform.commands_dir / item.name
    return None


def _mirror_skill_to_central(name: str, target_dir: Path) -> None:
    """Copy an installed skill dir into the VibeLens central skill store."""
    try:
        service = get_skill_service()
        central_dir = Path(service.get_item_path(name)).parent
        logger.debug("Copying %s to central at %s", name, central_dir)
        if central_dir.exists():
            shutil.rmtree(central_dir)
        shutil.copytree(target_dir, central_dir)
        service.invalidate()
    except OSError as exc:
        logger.warning("Failed to mirror %s to central store: %s", name, exc)


def _install_plugin(
    item: AgentExtensionItem,
    target_platform: str,
    platform: AgentPlatform,
    overwrite: bool,
) -> Path:
    """Install a PLUGIN extension via PluginService.

    Downloads the plugin tree into the central plugin dir, then syncs to
    the target agent. Claude agent stores drive the 4-file marketplace
    merge under the hood; other agents perform a plain directory drop.
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
    """Download the tree and read ``.claude-plugin/plugin.json`` from it."""
    if not item.source_url:
        raise ValueError(f"Plugin {item.name}: no source_url")

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
    """Download plugin assets (skills, commands, agents) into the central plugin dir."""
    if not item.source_url:
        return
    central_plugin_dir = Path(service.get_item_path(item.name)).parent.parent
    central_plugin_dir.parent.mkdir(parents=True, exist_ok=True)
    download_directory(source_url=item.source_url, target_dir=central_plugin_dir)


def uninstall_extension(item: AgentExtensionItem, target_platform: str) -> Path:
    """Remove an installed extension from the target platform."""
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

    if platform.skills_dir:
        skill_dir = platform.skills_dir / item.name
        if skill_dir.is_dir():
            shutil.rmtree(skill_dir)
            logger.info("Uninstalled %s from %s", item.extension_id, skill_dir)
            return skill_dir

    if platform.subagents_dir:
        subagent_file = platform.subagents_dir / f"{item.name}.md"
        if subagent_file.is_file():
            subagent_file.unlink()
            logger.info("Uninstalled %s from %s", item.extension_id, subagent_file)
            return subagent_file

    if platform.commands_dir:
        command_file = platform.commands_dir / f"{item.name}.md"
        if command_file.is_file():
            command_file.unlink()
            logger.info("Uninstalled %s from %s", item.extension_id, command_file)
            return command_file

    raise FileNotFoundError(f"Extension {item.name} not found on platform {target_platform}")


def _plugin_installed_path(platform: AgentPlatform, name: str, target_platform: str) -> Path:
    """Return the on-agent installed path for a plugin (for reporting)."""
    if platform.source == ExtensionSource.CLAUDE:
        return platform.root.expanduser() / "plugins" / "cache" / "vibelens" / name
    if platform.plugins_dir is None:
        raise ValueError(f"Platform {target_platform} has no plugins directory")
    return platform.plugins_dir.expanduser() / name
