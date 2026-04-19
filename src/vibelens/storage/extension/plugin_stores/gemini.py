"""Gemini plugin store — handles Gemini's ``gemini-extension.json`` layout.

Gemini CLI calls its plugin-equivalent an "extension" and ships it with a
flat manifest named ``gemini-extension.json`` at the plugin root (no
``.claude-plugin`` subdirectory). Inside VibeLens we keep using the
"plugin" vocabulary across the code, and translate to Gemini's native
layout only at the disk boundary in this store. The manifest's core
fields (``name``, ``version``, ``description``) match our canonical
Plugin schema; the ``keywords`` tag field is a VibeLens-specific
addition we preserve so we can round-trip it. Gemini's native-only
fields (``mcpServers``, ``contextFileName``, ``settings``, ``themes``)
pass through untouched because we rewrite the manifest without touching
them.
"""

import json
import shutil
from pathlib import Path

from vibelens.models.extension.plugin import Plugin
from vibelens.storage.extension.base_store import BaseExtensionStore
from vibelens.storage.extension.plugin_stores.base import (
    CANONICAL_MANIFEST_REL,
    PluginStore,
    _remove_empty_ancestors,
    parse_plugin_manifest,
)
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

GEMINI_MANIFEST_FILENAME = "gemini-extension.json"


class GeminiPluginStore(PluginStore):
    """Gemini extensions: manifest at ``gemini-extension.json`` in root.

    Schema fields that overlap with Claude's manifest are translated on
    copy; fields unique to one side are preserved (central side) or
    passed through untouched (Gemini side).
    """

    _manifest_rel_path = Path(GEMINI_MANIFEST_FILENAME)

    def _copy_impl(self, source: BaseExtensionStore[Plugin], name: str) -> bool:
        """Copy the plugin tree and translate manifest from Claude format to Gemini."""
        source_dir = source.root / name
        source_manifest_rel = getattr(source, "_manifest_rel_path", CANONICAL_MANIFEST_REL)
        source_manifest_path = source_dir / source_manifest_rel
        if not source_manifest_path.is_file():
            return False
        target_dir = self._root / name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_dir)

        # Drop the copied source manifest directory; we'll write the Gemini one.
        copied_source_manifest = target_dir / source_manifest_rel
        if copied_source_manifest.is_file():
            copied_source_manifest.unlink()
            _remove_empty_ancestors(root=target_dir, leaf=copied_source_manifest.parent)

        canonical_text = source_manifest_path.read_text(encoding="utf-8")
        gemini_manifest = _canonical_to_gemini(canonical_text=canonical_text)
        (target_dir / GEMINI_MANIFEST_FILENAME).write_text(
            json.dumps(gemini_manifest, indent=2), encoding="utf-8"
        )
        return True

    def _parse(self, name: str, text: str) -> Plugin:
        """Parse a Gemini-style manifest into the common Plugin model."""
        canonical_text = _gemini_to_canonical_text(gemini_text=text)
        return parse_plugin_manifest(name=name, text=canonical_text)


def _canonical_to_gemini(canonical_text: str) -> dict:
    """Translate Claude-style plugin.json to Gemini extension manifest.

    Preserves ``keywords`` in a ``vibelens`` namespace so importing the
    extension back into the central store round-trips tags. Gemini itself
    ignores unknown keys.
    """
    try:
        canonical = json.loads(canonical_text)
    except json.JSONDecodeError:
        canonical = {}
    if not isinstance(canonical, dict):
        canonical = {}

    manifest: dict = {
        "name": canonical.get("name", ""),
        "version": canonical.get("version", "0.0.0"),
        "description": canonical.get("description", ""),
    }
    keywords = canonical.get("keywords") or []
    if isinstance(keywords, list) and keywords:
        manifest.setdefault("vibelens", {})["keywords"] = keywords
    return manifest


def _gemini_to_canonical_text(gemini_text: str) -> str:
    """Translate Gemini manifest back into Claude-style JSON text."""
    try:
        gemini_manifest = json.loads(gemini_text)
    except json.JSONDecodeError:
        gemini_manifest = {}
    if not isinstance(gemini_manifest, dict):
        gemini_manifest = {}

    canonical: dict = {
        "name": gemini_manifest.get("name", ""),
        "version": gemini_manifest.get("version", "0.0.0"),
        "description": gemini_manifest.get("description", ""),
    }
    vibelens_block = gemini_manifest.get("vibelens")
    if isinstance(vibelens_block, dict):
        keywords = vibelens_block.get("keywords") or []
        if isinstance(keywords, list) and keywords:
            canonical["keywords"] = keywords
    return json.dumps(canonical, indent=2)
