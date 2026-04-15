"""Tests for catalog quality scoring."""
from vibelens.catalog import CatalogItem, ItemType
from vibelens.catalog.scoring import score_items


def _make_item(
    item_id: str = "test:skill:foo",
    description: str = "A useful tool for testing",
    popularity: float = 0.0,
    updated_at: str = "",
    category: str = "testing",
) -> CatalogItem:
    return CatalogItem(
        item_id=item_id,
        item_type=ItemType.SKILL,
        name="foo",
        description=description,
        tags=[],
        category=category,
        platforms=["claude_code"],
        quality_score=0.0,
        popularity=popularity,
        updated_at=updated_at,
        source_url="",
        repo_full_name="",
        install_method="skill_file",
    )


def test_score_items_assigns_scores():
    """All items get quality_score in 50-100 range."""
    items = [_make_item(item_id=f"test:skill:item-{i}") for i in range(5)]
    scored = score_items(items)
    for item in scored:
        assert 50.0 <= item.quality_score <= 100.0
    print(f"Scores: {[round(i.quality_score, 1) for i in scored]}")


def test_longer_description_scores_higher():
    """Items with richer descriptions score higher."""
    short = _make_item(item_id="test:skill:short", description="Short")
    long_desc = (
        "A comprehensive tool that provides extensive functionality for automated testing, "
        "including " * 3
    )
    long = _make_item(item_id="test:skill:long", description=long_desc)
    scored = score_items([short, long])
    long_score = next(i for i in scored if i.item_id == "test:skill:long").quality_score
    short_score = next(i for i in scored if i.item_id == "test:skill:short").quality_score
    assert long_score > short_score
    print(f"Short={short_score:.1f}, Long={long_score:.1f}")


def test_source_quality_bonus():
    """Items from higher-quality sources get boosted."""
    bwc = _make_item(item_id="bwc:skill:foo")
    cct = _make_item(item_id="cct:skill:bar")
    featured = _make_item(item_id="featured:skill:baz")
    scored = score_items([bwc, cct, featured])
    bwc_score = next(i for i in scored if "bwc" in i.item_id).quality_score
    cct_score = next(i for i in scored if "cct" in i.item_id).quality_score
    assert bwc_score >= cct_score
    print(f"BWC={bwc_score:.1f}, CCT={cct_score:.1f}")


def test_popularity_affects_score():
    """Items with higher popularity score higher."""
    unpopular = _make_item(item_id="test:skill:unpop", popularity=0.0)
    popular = _make_item(item_id="test:skill:pop", popularity=0.9)
    scored = score_items([unpopular, popular])
    pop_score = next(i for i in scored if i.item_id.split(":")[-1] == "pop").quality_score
    unpop_score = next(i for i in scored if "unpop" in i.item_id).quality_score
    assert pop_score > unpop_score
    print(f"Unpopular={unpop_score:.1f}, Popular={pop_score:.1f}")


def test_rare_category_gets_diversity_boost():
    """Items in sparse categories get a diversity boost."""
    common_items = [
        _make_item(item_id=f"test:skill:common-{i}", category="testing") for i in range(10)
    ]
    rare = _make_item(item_id="test:skill:rare", category="rare-niche")
    scored = score_items(common_items + [rare])
    rare_score = next(i for i in scored if "rare" in i.item_id).quality_score
    common_score = next(i for i in scored if "common-0" in i.item_id).quality_score
    assert rare_score > common_score
    print(f"Common={common_score:.1f}, Rare={rare_score:.1f}")
