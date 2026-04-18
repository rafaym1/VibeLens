"""Verify per-agent plugin stores write the correct on-disk manifest path."""

import json
from pathlib import Path

import pytest

from vibelens.storage.extension.plugin_stores import (
    CodexPluginStore,
    CopilotPluginStore,
    CursorPluginStore,
    GeminiPluginStore,
    PluginStore,
)


def _seed_central(root: Path, name: str = "my-plugin") -> PluginStore:
    central = PluginStore(root, create=True)
    manifest = json.dumps(
        {
            "name": name,
            "version": "1.0.0",
            "description": "Example plugin.",
            "keywords": ["testing"],
        },
        indent=2,
    )
    central.write(name, manifest)
    # Add a fake asset so we can verify directory copy carries non-manifest files.
    (root / name / "scripts").mkdir()
    (root / name / "scripts" / "helper.sh").write_text("#!/bin/sh\necho hi\n")
    return central


@pytest.mark.parametrize(
    ("store_class", "expected_rel"),
    [
        (CodexPluginStore, Path(".codex-plugin") / "plugin.json"),
        (CursorPluginStore, Path(".cursor-plugin") / "plugin.json"),
        (CopilotPluginStore, Path("plugin.json")),
    ],
)
def test_canonical_layout_stores_write_correct_manifest_path(
    tmp_path: Path, store_class, expected_rel
):
    central = _seed_central(tmp_path / "central")
    agent_root = tmp_path / "agent"
    store = store_class(agent_root, create=True)

    assert store.copy_from(central, "my-plugin") is True

    expected_manifest = agent_root / "my-plugin" / expected_rel
    assert expected_manifest.is_file()
    data = json.loads(expected_manifest.read_text())
    assert data["name"] == "my-plugin"
    assert data["version"] == "1.0.0"
    # Asset carried along
    assert (agent_root / "my-plugin" / "scripts" / "helper.sh").is_file()
    # Source manifest dir not left behind (for subdir layouts)
    if expected_rel.parent != Path("."):
        stale = agent_root / "my-plugin" / ".claude-plugin"
        assert not stale.exists()


def test_canonical_layout_store_round_trips(tmp_path: Path):
    """Central → agent → central round-trip preserves name, version, tags."""
    central_a = _seed_central(tmp_path / "central-a")
    cursor_root = tmp_path / "cursor"
    cursor_store = CursorPluginStore(cursor_root, create=True)
    cursor_store.copy_from(central_a, "my-plugin")

    central_b = PluginStore(tmp_path / "central-b", create=True)
    central_b.copy_from(cursor_store, "my-plugin")

    round_tripped = central_b.read("my-plugin")
    assert round_tripped is not None
    assert round_tripped.name == "my-plugin"
    assert round_tripped.version == "1.0.0"
    assert round_tripped.tags == ["testing"]


def test_gemini_store_writes_flat_manifest(tmp_path: Path):
    central = _seed_central(tmp_path / "central")
    gemini_root = tmp_path / "gemini"
    store = GeminiPluginStore(gemini_root, create=True)

    assert store.copy_from(central, "my-plugin") is True

    manifest_path = gemini_root / "my-plugin" / "gemini-extension.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text())
    assert data["name"] == "my-plugin"
    assert data["version"] == "1.0.0"
    assert data["description"] == "Example plugin."
    # Tags preserved under vibelens namespace for round-trip.
    assert data["vibelens"]["keywords"] == ["testing"]
    # Claude-style manifest dir not present
    assert not (gemini_root / "my-plugin" / ".claude-plugin").exists()


def test_gemini_store_round_trips_tags(tmp_path: Path):
    central_a = _seed_central(tmp_path / "central-a")
    gemini_root = tmp_path / "gemini"
    gemini_store = GeminiPluginStore(gemini_root, create=True)
    gemini_store.copy_from(central_a, "my-plugin")

    # Read the gemini manifest through the store's parser.
    plugin = gemini_store.read("my-plugin")
    assert plugin is not None
    assert plugin.tags == ["testing"]
    assert plugin.version == "1.0.0"
