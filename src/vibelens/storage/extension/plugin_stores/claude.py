"""Claude-specific plugin store backed by the VibeLens marketplace merge.

Installing a plugin on Claude requires touching four files plus a cache copy
of the plugin tree. This store presents a BaseExtensionStore interface over
that flow so PluginService can treat Claude uniformly with other agents.

Reads are sourced from ``~/.claude/plugins/cache/vibelens/{name}/{version}/``
(the cache directory Claude reads at session start). Writes route through
``claude_installer`` to keep all four registry files in sync.
"""

import json
from pathlib import Path

from vibelens.models.extension.plugin import Plugin
from vibelens.storage.extension.base_store import BaseExtensionStore
from vibelens.storage.extension.plugin_stores.base import (
    CANONICAL_MANIFEST_DIR,
    MANIFEST_FILENAME,
    parse_plugin_manifest,
)
from vibelens.storage.extension.plugin_stores.claude_installer import (
    ClaudePluginInstallRequest,
    install_claude_plugin,
    uninstall_claude_plugin,
)
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


class ClaudePluginStore(BaseExtensionStore[Plugin]):
    """BaseExtensionStore facade over the Claude plugin cache + registry files.

    The underlying directory is ``~/.claude/plugins/cache/vibelens/`` —
    Claude's own cache root for plugins we install. Plugin files live one
    level deeper (under a version dir); ``_item_path`` resolves to the
    manifest of whichever version is currently recorded.
    """

    _manifest_rel_path: Path = Path(CANONICAL_MANIFEST_DIR) / MANIFEST_FILENAME

    def _version_dir(self, name: str) -> Path | None:
        """Return the installed version directory for this plugin, or None."""
        plugin_root = self._root / name
        if not plugin_root.is_dir():
            return None
        versions = [entry for entry in plugin_root.iterdir() if entry.is_dir()]
        if not versions:
            return None
        versions.sort(key=lambda p: p.name)
        return versions[-1]

    def _item_path(self, name: str) -> Path:
        """Return the plugin.json path for the currently installed version.

        When no version is on disk yet, returns a nonexistent-but-honest
        path under the plugin root so ``read_raw`` naturally reports
        missing — callers should not treat the returned path as writable.
        """
        version_dir = self._version_dir(name)
        if version_dir is None:
            return self._root / name / CANONICAL_MANIFEST_DIR / MANIFEST_FILENAME
        return version_dir / CANONICAL_MANIFEST_DIR / MANIFEST_FILENAME

    def _parse(self, name: str, text: str) -> Plugin:
        return parse_plugin_manifest(name=name, text=text)

    def _iter_candidate_names(self) -> list[str]:
        if not self._root.is_dir():
            return []
        return [entry.name for entry in self._root.iterdir() if entry.is_dir()]

    def _delete_impl(self, name: str) -> bool:
        """Uninstall via the 4-file merge driver."""
        try:
            uninstall_claude_plugin(name=name)
        except FileNotFoundError:
            return False
        return True

    def _copy_impl(self, source: BaseExtensionStore[Plugin], name: str) -> bool:
        """Install via the 4-file merge driver from a source plugin directory."""
        source_manifest = source.root / name / CANONICAL_MANIFEST_DIR / MANIFEST_FILENAME
        if not source_manifest.is_file():
            return False
        manifest_text = source_manifest.read_text(encoding="utf-8")
        plugin = parse_plugin_manifest(name=name, text=manifest_text)
        request = _build_install_request(plugin=plugin, manifest_text=manifest_text)
        install_claude_plugin(request=request, overwrite=True)
        return True


def _build_install_request(plugin: Plugin, manifest_text: str) -> ClaudePluginInstallRequest:
    """Wrap a Plugin + raw manifest into the installer's typed input."""
    manifest_data = json.loads(manifest_text) if manifest_text.strip() else {}
    content_payload = json.dumps({"plugin.json": manifest_data})
    return ClaudePluginInstallRequest(
        name=plugin.name,
        description=plugin.description,
        install_content=content_payload,
        source_url="",
        log_id=f"local/{plugin.name}",
    )
