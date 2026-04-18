"""Plugin stores: one class per agent-native on-disk layout."""

from vibelens.storage.extension.plugin_stores.base import (
    CANONICAL_MANIFEST_DIR,
    CANONICAL_MANIFEST_REL,
    MANIFEST_FILENAME,
    PluginStore,
    parse_plugin_manifest,
)
from vibelens.storage.extension.plugin_stores.canonical_layouts import (
    CodexPluginStore,
    CopilotPluginStore,
    CursorPluginStore,
)
from vibelens.storage.extension.plugin_stores.claude import ClaudePluginStore
from vibelens.storage.extension.plugin_stores.gemini import (
    GEMINI_MANIFEST_FILENAME,
    GeminiPluginStore,
)

__all__ = [
    "CANONICAL_MANIFEST_DIR",
    "CANONICAL_MANIFEST_REL",
    "MANIFEST_FILENAME",
    "GEMINI_MANIFEST_FILENAME",
    "ClaudePluginStore",
    "CodexPluginStore",
    "CopilotPluginStore",
    "CursorPluginStore",
    "GeminiPluginStore",
    "PluginStore",
    "parse_plugin_manifest",
]
