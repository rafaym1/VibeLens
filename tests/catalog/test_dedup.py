"""Tests for catalog deduplication."""
from vibelens.catalog import CatalogItem, ItemType
from vibelens.catalog.dedup import deduplicate


def _make_item(
    item_id: str,
    name: str,
    description: str = "A tool",
    item_type: ItemType = ItemType.SKILL,
    tags: list[str] | None = None,
    install_content: str | None = None,
) -> CatalogItem:
    return CatalogItem(
        item_id=item_id,
        item_type=item_type,
        name=name,
        description=description,
        tags=tags or [],
        category="testing",
        platforms=["claude_code"],
        quality_score=70.0,
        popularity=0.5,
        updated_at="",
        source_url="",
        repo_full_name="",
        install_method="skill_file",
        install_content=install_content,
    )


def test_no_duplicates_returns_all():
    """Items with unique names pass through unchanged."""
    items = [
        _make_item("bwc:skill:foo", "foo"),
        _make_item("cct:skill:bar", "bar"),
    ]
    result = deduplicate(items)
    assert len(result) == 2
    print(f"No dupes: {[i.item_id for i in result]}")


def test_duplicate_keeps_richer():
    """When names collide, keep the item with install_content."""
    poor = _make_item("featured:skill:memory-bank", "memory-bank", "Short desc")
    rich = _make_item(
        "bwc:skill:memory-bank",
        "memory-bank",
        "Detailed description of memory bank",
        install_content="# Full content",
    )
    result = deduplicate([poor, rich])
    assert len(result) == 1
    assert result[0].item_id == "bwc:skill:memory-bank"
    print(f"Kept richer: {result[0].item_id}")


def test_duplicate_merges_tags():
    """Unique tags from both duplicates are merged."""
    item_a = _make_item("bwc:skill:test", "test", tags=["memory", "context"])
    item_b = _make_item("featured:skill:test", "test", tags=["context", "persistence"])
    result = deduplicate([item_a, item_b])
    assert len(result) == 1
    assert set(result[0].tags) == {"memory", "context", "persistence"}
    print(f"Merged tags: {result[0].tags}")


def test_name_normalization():
    """Names are normalized: lowercase, stripped hyphens, collapsed."""
    item_a = _make_item("bwc:skill:My-Skill", "My-Skill")
    item_b = _make_item("cct:skill:my-skill", "my-skill", install_content="content")
    result = deduplicate([item_a, item_b])
    assert len(result) == 1
    print(f"Normalized: {result[0].item_id}")


def test_different_types_not_deduped():
    """Same name but different types are kept separately."""
    skill = _make_item("bwc:skill:test", "test", item_type=ItemType.SKILL)
    agent = _make_item("cct:agent:test", "test", item_type=ItemType.SUBAGENT)
    result = deduplicate([skill, agent])
    assert len(result) == 2
    print(f"Different types: {[i.item_id for i in result]}")
