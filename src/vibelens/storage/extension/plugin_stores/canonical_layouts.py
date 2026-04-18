"""Per-agent plugin stores that share the canonical manifest schema.

Codex, Cursor, and Copilot all use the same Claude-compatible plugin
manifest shape (same fields, different file locations). Each is a thin
subclass of :class:`PluginStore` that declares its native manifest path.
"""

from pathlib import Path

from vibelens.storage.extension.plugin_stores.base import MANIFEST_FILENAME, PluginStore


class CodexPluginStore(PluginStore):
    """Codex plugins: manifest at ``.codex-plugin/plugin.json``."""

    _manifest_rel_path = Path(".codex-plugin") / MANIFEST_FILENAME


class CursorPluginStore(PluginStore):
    """Cursor plugins: manifest at ``.cursor-plugin/plugin.json``."""

    _manifest_rel_path = Path(".cursor-plugin") / MANIFEST_FILENAME


class CopilotPluginStore(PluginStore):
    """Copilot plugins: manifest at ``plugin.json`` (plugin root, no subdir)."""

    _manifest_rel_path = Path(MANIFEST_FILENAME)
