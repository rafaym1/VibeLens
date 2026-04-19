"""Tests for the partial-rebuild path in LocalTrajectoryStore.

The partial path lets startup re-parse only changed/new/removed files
instead of rebuilding the entire index. These tests cover the partition
logic and the dropped_paths memo that prevents retrying empty files.
"""

import json
from pathlib import Path

import pytest

from vibelens.ingest import index_cache
from vibelens.models.enums import AgentType
from vibelens.storage.trajectory.local import LocalTrajectoryStore, _partition_files


@pytest.fixture
def isolated_cache(tmp_path, monkeypatch) -> Path:
    """Redirect index_cache.DEFAULT_CACHE_PATH to a tmp file per test."""
    cache_file = tmp_path / "session_index.json"
    monkeypatch.setattr(index_cache, "DEFAULT_CACHE_PATH", cache_file)
    return cache_file


@pytest.fixture
def claude_data_dirs(tmp_path) -> dict[AgentType, Path]:
    """Build a minimal claude data dir with two valid session files + history.jsonl."""
    claude_dir = tmp_path / ".claude"
    projects_dir = claude_dir / "projects" / "-Users-Test-Project"
    projects_dir.mkdir(parents=True)

    history_file = claude_dir / "history.jsonl"
    history_entries = [
        {
            "display": "First message",
            "pastedContents": {},
            "timestamp": 1707734674932,
            "project": "/Users/Test/Project",
            "sessionId": "session-A",
        },
        {
            "display": "Second message",
            "pastedContents": {},
            "timestamp": 1707734680000,
            "project": "/Users/Test/Project",
            "sessionId": "session-B",
        },
    ]
    with history_file.open("w") as f:
        for e in history_entries:
            f.write(json.dumps(e) + "\n")

    for sid in ("session-A", "session-B"):
        session_file = projects_dir / f"{sid}.jsonl"
        with session_file.open("w") as f:
            f.write(
                json.dumps(
                    {
                        "type": "user",
                        "uuid": f"u-{sid}",
                        "sessionId": sid,
                        "timestamp": 1707734674932,
                        "message": {"role": "user", "content": f"prompt for {sid}"},
                    }
                )
                + "\n"
            )

    return {AgentType.CLAUDE: claude_dir}


def _read_cache(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_warm_restart_unchanged_takes_fast_path(
    isolated_cache, claude_data_dirs, caplog
):
    """When no file mtimes change between two starts, the fast cache-hit path runs."""
    store1 = LocalTrajectoryStore(data_dirs=claude_data_dirs)
    store1.list_metadata()  # warm
    assert isolated_cache.exists()

    caplog.clear()
    store2 = LocalTrajectoryStore(data_dirs=claude_data_dirs)
    store2.list_metadata()  # should hit fast path
    messages = [r.getMessage() for r in caplog.records]
    assert any("Loaded 2 sessions from index cache" in m for m in messages)
    # Fast-path log line lacks the "(N unchanged...)" suffix.
    assert not any("unchanged," in m for m in messages)


def test_one_changed_file_runs_partial_rebuild(
    isolated_cache, claude_data_dirs, caplog
):
    """Touching one session file triggers the partial path; the other survives from cache."""
    store1 = LocalTrajectoryStore(data_dirs=claude_data_dirs)
    store1.list_metadata()

    # Touch session-A's file to bump its mtime.
    session_a = (
        claude_data_dirs[AgentType.CLAUDE]
        / "projects"
        / "-Users-Test-Project"
        / "session-A.jsonl"
    )
    text = session_a.read_text()
    session_a.write_text(text + "\n")

    caplog.clear()
    store2 = LocalTrajectoryStore(data_dirs=claude_data_dirs)
    store2.list_metadata()
    messages = [r.getMessage() for r in caplog.records]
    partial_lines = [m for m in messages if "1 unchanged" in m and "1 re-parsed" in m]
    assert partial_lines, f"expected partial-rebuild log, got: {messages}"
    assert "session-A" in store2._metadata_cache
    assert "session-B" in store2._metadata_cache


def test_dropped_path_not_retried_on_warm_restart(isolated_cache, tmp_path, caplog):
    """A file that yields no parseable trajectory is recorded in dropped_paths
    and skipped on the next startup as long as its mtime is unchanged."""
    # Build a claude dir where session-bad.jsonl has only a snapshot entry
    # (no user/assistant messages → first_message empty → dropped).
    claude_dir = tmp_path / ".claude"
    projects = claude_dir / "projects" / "-Users-Test-Project"
    projects.mkdir(parents=True)
    bad_file = projects / "session-bad.jsonl"
    bad_file.write_text(
        json.dumps(
            {
                "type": "file-history-snapshot",
                "messageId": "snap-1",
                "snapshot": {"messageId": "snap-1", "trackedFileBackups": {}},
            }
        )
        + "\n"
    )

    data_dirs = {AgentType.CLAUDE: claude_dir}
    store1 = LocalTrajectoryStore(data_dirs=data_dirs)
    store1.list_metadata()

    cache = _read_cache(isolated_cache)
    assert str(bad_file) in cache["dropped_paths"], (
        f"dropped_paths should contain bad file, got {cache['dropped_paths']}"
    )

    # Second startup: file mtime unchanged → bad file not retried.
    caplog.clear()
    store2 = LocalTrajectoryStore(data_dirs=data_dirs)
    store2.list_metadata()
    # No "session-bad" should appear in metadata_cache.
    assert "session-bad" not in store2._metadata_cache
    # The cache should still record the dropped path.
    cache2 = _read_cache(isolated_cache)
    assert str(bad_file) in cache2["dropped_paths"]


def test_partition_files_classifies_correctly(tmp_path):
    """_partition_files separates unchanged / changed / new / removed correctly."""
    file_a = tmp_path / "a.jsonl"
    file_a.write_text("a")
    file_b = tmp_path / "b.jsonl"
    file_b.write_text("b")

    file_index = {
        "a": (file_a, object()),
        "b": (file_b, object()),
    }

    # cached_mtimes records a's old mtime + a third file 'c' that no longer exists.
    cached_mtimes = {
        str(file_a): file_a.stat().st_mtime_ns - 1,  # different → changed
        str(tmp_path / "c.jsonl"): 999_999,  # gone → removed
    }
    dropped_paths: dict[str, int] = {}

    partition, fresh_dropped = _partition_files(file_index, cached_mtimes, dropped_paths)

    assert "a" in partition.changed
    assert "b" in partition.new
    assert partition.unchanged == {}
    assert str(tmp_path / "c.jsonl") in partition.removed_paths
    assert fresh_dropped == {}


def test_partition_files_skips_dropped_with_unchanged_mtime(tmp_path):
    """Files in dropped_paths with matching mtimes are excluded from all sets."""
    bad = tmp_path / "bad.jsonl"
    bad.write_text("x")
    bad_mtime = bad.stat().st_mtime_ns

    file_index = {"bad": (bad, object())}
    cached_mtimes: dict[str, int] = {}
    dropped_paths = {str(bad): bad_mtime}

    partition, fresh_dropped = _partition_files(file_index, cached_mtimes, dropped_paths)

    assert partition.new == {}
    assert partition.unchanged == {}
    assert partition.changed == {}
    assert fresh_dropped == {str(bad): bad_mtime}
