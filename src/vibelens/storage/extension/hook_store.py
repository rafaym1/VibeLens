"""Hook store — CRUD on a directory of flat .json hook files.

Directory layout:
    <root>/
    ├── safety-guard.json
    ├── log-commands.json
    └── another-hook.json

Each hook is a single ``{name}.json`` file with keys ``name``, ``description``,
``tags``, and ``hook_config``. Unlike commands, hooks are not copied verbatim
to agents; the service merges their ``hook_config`` into each agent's
``settings.json``.
"""

import json
from pathlib import Path

from vibelens.models.extension.hook import Hook
from vibelens.storage.extension.base_store import BaseExtensionStore
from vibelens.utils.content import compute_content_hash
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

HOOK_EXTENSION = ".json"
JSON_INDENT = 2


class HookStore(BaseExtensionStore[Hook]):
    """CRUD on a single directory of flat .json hook files.

    Each hook is a single ``{name}.json`` file containing description, tags,
    and hook_config keyed by event name (e.g. ``PreToolUse``).
    """

    def _item_path(self, name: str) -> Path:
        """Return path to the hook's .json file."""
        return self._root / f"{name}{HOOK_EXTENSION}"

    def _parse(self, name: str, text: str) -> Hook:
        """Parse raw .json text into a Hook."""
        return parse_hook_json(name, text)

    def _iter_candidate_names(self) -> list[str]:
        """Return stems of .json files in the root directory."""
        return [
            entry.stem
            for entry in self._root.iterdir()
            if entry.is_file() and entry.suffix == HOOK_EXTENSION
        ]


def parse_hook_json(name: str, text: str) -> Hook:
    """Parse raw hook .json text into a Hook model.

    Args:
        name: Hook filename stem (used as the canonical name).
        text: Full .json content.

    Returns:
        Parsed Hook with metadata and hook_config.

    Raises:
        ValueError: If text is not valid JSON or not a JSON object.
    """
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON for hook {name!r}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Hook {name!r} JSON must be an object, got {type(data).__name__}")

    description = str(data.get("description", ""))
    raw_tags = data.get("tags", [])
    tags = [str(t).strip() for t in raw_tags if isinstance(t, str) and str(t).strip()]
    hook_config = data.get("hook_config", {})
    if not isinstance(hook_config, dict):
        hook_config = {}

    return Hook(
        name=name,
        description=description,
        topics=tags,
        hook_config=hook_config,
        content_hash=compute_content_hash(text),
    )


def serialize_hook(hook: Hook) -> str:
    """Serialize a Hook to pretty JSON for storage.

    Args:
        hook: Hook model to serialize.

    Returns:
        Indented JSON string (no trailing newline).
    """
    data = {
        "name": hook.name,
        "description": hook.description,
        "tags": hook.topics,
        "hook_config": hook.hook_config,
    }
    return json.dumps(data, indent=JSON_INDENT)
