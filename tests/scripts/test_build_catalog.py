"""End-to-end test for scripts/build_catalog.py against the hub sample fixtures."""

import json
import math
import subprocess
import sys
from pathlib import Path

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "hub_sample"
SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build_catalog.py"


def _run_build(tmp_path: Path) -> Path:
    out = tmp_path / "catalog"
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--hub-output", str(FIXTURE), "--out", str(out)],
        capture_output=True,
        text=True,
        check=False,
    )
    print("stdout:", result.stdout)
    print("stderr:", result.stderr)
    assert result.returncode == 0, f"build failed: {result.stderr}"
    return out


def test_build_produces_all_artifacts(tmp_path: Path):
    out = _run_build(tmp_path)
    for name in (
        "manifest.json",
        "catalog-summary.json",
        "catalog-offsets.json",
        "agent-skill.json",
        "agent-plugin.json",
        "agent-subagent.json",
        "agent-command.json",
        "agent-hook.json",
        "agent-mcp_server.json",
    ):
        assert (out / name).is_file(), f"missing {name}"
    print("all artifacts present")


def test_hub_files_copied_byte_for_byte(tmp_path: Path):
    out = _run_build(tmp_path)
    for src in FIXTURE.glob("agent-*.json"):
        assert (out / src.name).read_bytes() == src.read_bytes(), src.name
    print("byte-for-byte copy verified")


def test_manifest_shape(tmp_path: Path):
    out = _run_build(tmp_path)
    manifest = json.loads((out / "manifest.json").read_text())
    assert manifest["generated_on"] == "2026-04-18"
    assert manifest["hub_source"] == "hub_sample"
    assert manifest["total"] == 7
    assert manifest["item_counts"]["skill"] == 2
    assert manifest["item_counts"]["plugin"] == 1
    for key in (
        "agent-skill.json",
        "agent-plugin.json",
        "agent-subagent.json",
        "agent-command.json",
        "agent-hook.json",
        "agent-mcp_server.json",
    ):
        assert key in manifest["file_sizes"]
    print(f"manifest ok: total={manifest['total']}")


def test_summary_counts_and_detail_fields_omitted(tmp_path: Path):
    out = _run_build(tmp_path)
    summary = json.loads((out / "catalog-summary.json").read_text())
    assert summary["total"] == 7
    assert len(summary["items"]) == 7
    for item in summary["items"]:
        for field in (
            "repo_description",
            "readme_description",
            "author",
            "scores",
            "item_metadata",
            "validation_errors",
            "author_followers",
            "contributors_count",
            "created_at",
            "discovery_origin",
        ):
            assert item.get(field) is None, f"{item['extension_id']} carries {field}"
    print("detail-only fields omitted from summaries")


def test_popularity_derivation(tmp_path: Path):
    out = _run_build(tmp_path)
    summary = json.loads((out / "catalog-summary.json").read_text())
    items = {i["extension_id"]: i for i in summary["items"]}
    max_stars = max(i["stars"] for i in items.values())
    for eid, item in items.items():
        expected = math.log1p(item["stars"]) / math.log1p(max_stars)
        assert abs(item["popularity"] - expected) < 1e-9, eid
    print(f"popularity derivation verified (max_stars={max_stars})")


def test_offsets_round_trip_including_non_ascii(tmp_path: Path):
    out = _run_build(tmp_path)
    offsets = json.loads((out / "catalog-offsets.json").read_text())

    for eid, (type_value, offset, length) in offsets.items():
        path = out / f"agent-{type_value}.json"
        buf = path.read_bytes()
        slice_bytes = buf[offset : offset + length]
        restored = json.loads(slice_bytes)
        assert restored["item_id"] == eid
    beta = offsets["tree:acme/widget:skills/beta"]
    _, offset, length = beta
    beta_bytes = (out / "agent-skill.json").read_bytes()[offset : offset + length]
    restored = json.loads(beta_bytes)
    assert "🙂" in restored["description"]
    assert "漢字" in restored["description"]
    print(f"offsets round-trip ok for {len(offsets)} items (incl. non-ASCII)")
