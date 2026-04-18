"""Tests for HookStore — flat-file I/O wrapper for hook .json files."""

import json

import pytest

from vibelens.models.extension.hook import Hook
from vibelens.storage.extension.hook_store import (
    HookStore,
    parse_hook_json,
    serialize_hook,
)

SAMPLE_HOOK_DATA = {
    "name": "safety-guard",
    "description": "A sample hook",
    "tags": ["safety"],
    "hook_config": {
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [{"type": "command", "command": "/bin/echo"}],
            }
        ]
    },
}
SAMPLE_HOOK_JSON = json.dumps(SAMPLE_HOOK_DATA, indent=2)

MINIMAL_HOOK_JSON = json.dumps({"name": "minimal", "description": "Minimal"}, indent=2)


class TestParseHookJson:
    def test_parses_full_hook(self):
        hook = parse_hook_json("safety-guard", SAMPLE_HOOK_JSON)
        assert hook.name == "safety-guard"
        assert hook.description == "A sample hook"
        assert hook.topics == ["safety"]
        assert "PreToolUse" in hook.hook_config
        assert hook.content_hash != ""

    def test_parses_minimal(self):
        hook = parse_hook_json("minimal", MINIMAL_HOOK_JSON)
        assert hook.description == "Minimal"
        assert hook.topics == []
        assert hook.hook_config == {}

    def test_uses_filename_as_name(self):
        """The name argument overrides any ``name`` in the JSON body."""
        hook = parse_hook_json("on-disk-name", SAMPLE_HOOK_JSON)
        assert hook.name == "on-disk-name"

    def test_rejects_invalid_json(self):
        with pytest.raises(ValueError, match="Invalid JSON"):
            parse_hook_json("bad", "not json at all")

    def test_rejects_non_object(self):
        with pytest.raises(ValueError, match="must be an object"):
            parse_hook_json("arr", "[1, 2, 3]")


class TestSerializeHook:
    def test_round_trip(self):
        hook = Hook(
            name="my-hook",
            description="round trip",
            tags=["a"],
            hook_config={"PreToolUse": [{"matcher": "Bash", "hooks": []}]},
        )
        text = serialize_hook(hook)
        parsed = json.loads(text)
        assert parsed["name"] == "my-hook"
        assert parsed["description"] == "round trip"
        assert parsed["tags"] == ["a"]
        assert parsed["hook_config"]["PreToolUse"][0]["matcher"] == "Bash"


class TestHookStore:
    @pytest.fixture
    def store(self, tmp_path):
        return HookStore(root=tmp_path, create=True)

    @pytest.fixture
    def populated_store(self, store):
        store.write("alpha", SAMPLE_HOOK_JSON)
        store.write("beta", MINIMAL_HOOK_JSON)
        return store

    def test_write_and_read(self, store):
        store.write("my-hook", SAMPLE_HOOK_JSON)
        hook = store.read("my-hook")
        assert hook is not None
        assert hook.name == "my-hook"
        assert hook.description == "A sample hook"
        assert hook.hook_config["PreToolUse"][0]["matcher"] == "Bash"

    def test_write_creates_json_file(self, store):
        path = store.write("new-hook", SAMPLE_HOOK_JSON)
        assert path.exists()
        assert path.name == "new-hook.json"

    def test_read_nonexistent_returns_none(self, store):
        assert store.read("nonexistent") is None

    def test_read_raw(self, store):
        store.write("my-hook", SAMPLE_HOOK_JSON)
        raw = store.read_raw("my-hook")
        assert raw is not None
        assert "A sample hook" in raw

    def test_list_names(self, populated_store):
        assert sorted(populated_store.list_names()) == ["alpha", "beta"]

    def test_list_names_empty(self, store):
        assert store.list_names() == []

    def test_list_names_ignores_non_json_files(self, store):
        store.write("real-hook", SAMPLE_HOOK_JSON)
        (store.root / "ignored.txt").write_text("nope", encoding="utf-8")
        assert "real-hook" in store.list_names()
        assert "ignored" not in store.list_names()

    def test_exists(self, populated_store):
        assert populated_store.exists("alpha")
        assert not populated_store.exists("nonexistent")

    def test_delete(self, populated_store):
        assert populated_store.delete("alpha")
        assert not populated_store.exists("alpha")

    def test_delete_nonexistent(self, store):
        assert not store.delete("nope")

    def test_write_rejects_invalid_name(self, store):
        with pytest.raises(ValueError, match="kebab-case"):
            store.write("Not Valid", SAMPLE_HOOK_JSON)

    def test_root_property(self, tmp_path):
        store = HookStore(root=tmp_path / "hooks", create=True)
        assert store.root == (tmp_path / "hooks")

    def test_create_false_does_not_create_dir(self, tmp_path):
        root = tmp_path / "does-not-exist"
        store = HookStore(root=root)
        assert not root.exists()
        assert store.list_names() == []
