"""Tests for catalog install service."""
import json
from pathlib import Path
from unittest.mock import patch

from vibelens.catalog import CatalogItem, ItemType
from vibelens.services.catalog.install import install_catalog_item

DEFAULT_SKILL_CONTENT = "# Test Skill\nContent"


def _make_skill_item(
    name: str = "test-skill",
    content: str = DEFAULT_SKILL_CONTENT,
) -> CatalogItem:
    return CatalogItem(
        item_id=f"bwc:skill:{name}",
        item_type=ItemType.SKILL,
        name=name,
        description="A test skill",
        tags=[],
        category="testing",
        platforms=["claude_code"],
        quality_score=80.0,
        popularity=0.5,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="skill_file",
        install_content=content,
    )


def _make_hook_item() -> CatalogItem:
    hook_entries = [{"matcher": "Bash", "hooks": [{"type": "command", "command": "echo test"}]}]
    hook_data = {
        "description": "Test hook",
        "hooks": {"PreToolUse": hook_entries},
    }
    return CatalogItem(
        item_id="bwc:hook:test-hook",
        item_type=ItemType.HOOK,
        name="test-hook",
        description="A test hook",
        tags=[],
        category="automation",
        platforms=["claude_code"],
        quality_score=70.0,
        popularity=0.0,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="hook_config",
        install_content=json.dumps(hook_data),
    )


def _make_mcp_item() -> CatalogItem:
    mcp_data = {"mcpServers": {"test-mcp": {"command": "npx", "args": ["-y", "test-server"]}}}
    return CatalogItem(
        item_id="bwc:mcp:test-mcp",
        item_type=ItemType.REPO,
        name="test-mcp",
        description="A test MCP",
        tags=[],
        category="mcp",
        platforms=["claude_code"],
        quality_score=70.0,
        popularity=0.0,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="mcp_config",
        install_content=json.dumps(mcp_data),
    )


def _make_dirs(tmp_path: Path, claude_dir: Path) -> dict:
    return {
        "claude_code": {
            "commands": claude_dir / "commands",
            "settings": claude_dir / "settings.json",
        }
    }


def test_install_skill_creates_file(tmp_path: Path):
    """Installing a skill writes to commands directory."""
    claude_dir = tmp_path / ".claude"
    dirs = _make_dirs(tmp_path=tmp_path, claude_dir=claude_dir)
    with patch("vibelens.services.catalog.install.PLATFORM_DIRS", dirs):
        item = _make_skill_item()
        installed = install_catalog_item(item=item, target_platform="claude_code")
        assert installed.is_file()
        assert installed.read_text() == DEFAULT_SKILL_CONTENT
        print(f"Installed skill at: {installed}")


def test_install_skill_rejects_overwrite(tmp_path: Path):
    """Installing a skill to existing path raises FileExistsError."""
    claude_dir = tmp_path / ".claude"
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "test-skill.md").write_text("existing")
    dirs = _make_dirs(tmp_path=tmp_path, claude_dir=claude_dir)
    with patch("vibelens.services.catalog.install.PLATFORM_DIRS", dirs):
        item = _make_skill_item()
        try:
            install_catalog_item(item=item, target_platform="claude_code", overwrite=False)
            raise AssertionError("Expected FileExistsError")
        except FileExistsError:
            pass
    print("Correctly rejected overwrite")


def test_install_skill_allows_overwrite(tmp_path: Path):
    """Installing with overwrite=True replaces existing file."""
    claude_dir = tmp_path / ".claude"
    commands_dir = claude_dir / "commands"
    commands_dir.mkdir(parents=True)
    (commands_dir / "test-skill.md").write_text("old content")
    dirs = _make_dirs(tmp_path=tmp_path, claude_dir=claude_dir)
    with patch("vibelens.services.catalog.install.PLATFORM_DIRS", dirs):
        item = _make_skill_item()
        installed = install_catalog_item(item=item, target_platform="claude_code", overwrite=True)
        assert installed.read_text() == DEFAULT_SKILL_CONTENT
    print("Overwrite succeeded")


def test_install_hook_appends_to_settings(tmp_path: Path):
    """Installing a hook appends to settings.json hooks."""
    claude_dir = tmp_path / ".claude"
    settings_path = claude_dir / "settings.json"
    claude_dir.mkdir(parents=True)
    settings_path.write_text(json.dumps({"hooks": {}}))
    dirs = _make_dirs(tmp_path=tmp_path, claude_dir=claude_dir)
    with patch("vibelens.services.catalog.install.PLATFORM_DIRS", dirs):
        item = _make_hook_item()
        install_catalog_item(item=item, target_platform="claude_code")
        settings = json.loads(settings_path.read_text())
        assert "PreToolUse" in settings["hooks"]
        print(f"Hook installed, settings: {json.dumps(settings, indent=2)}")


def test_install_mcp_merges_to_settings(tmp_path: Path):
    """Installing an MCP server merges into settings.json mcpServers."""
    claude_dir = tmp_path / ".claude"
    settings_path = claude_dir / "settings.json"
    claude_dir.mkdir(parents=True)
    settings_path.write_text(json.dumps({"mcpServers": {}}))
    dirs = _make_dirs(tmp_path=tmp_path, claude_dir=claude_dir)
    with patch("vibelens.services.catalog.install.PLATFORM_DIRS", dirs):
        item = _make_mcp_item()
        install_catalog_item(item=item, target_platform="claude_code")
        settings = json.loads(settings_path.read_text())
        assert "test-mcp" in settings["mcpServers"]
        print(f"MCP installed: {list(settings['mcpServers'].keys())}")


def test_install_unknown_platform_raises():
    """Installing to unknown platform raises ValueError."""
    item = _make_skill_item()
    try:
        install_catalog_item(item=item, target_platform="unknown_agent")
        raise AssertionError("Expected ValueError")
    except ValueError as exc:
        assert "unknown_agent" in str(exc)
    print("Correctly rejected unknown platform")
