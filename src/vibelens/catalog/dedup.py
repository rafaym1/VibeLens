"""Deduplication logic for catalog items from multiple sources."""

import re

from vibelens.models.recommendation.catalog import CatalogItem


def deduplicate(items: list[CatalogItem]) -> list[CatalogItem]:
    """Deduplicate items by normalized (name, item_type) pairs.

    When duplicates are found, keeps the item with richer metadata
    (prefers install_content > no content, longer description > shorter).
    Merges unique tags from all duplicates.

    Args:
        items: Raw items from all sources (may contain duplicates).

    Returns:
        Deduplicated list of CatalogItem instances.
    """
    groups: dict[tuple[str, str], list[CatalogItem]] = {}
    for item in items:
        key = (_normalize_name(item.name), item.item_type.value)
        groups.setdefault(key, []).append(item)

    result: list[CatalogItem] = []
    for _key, group in groups.items():
        if len(group) == 1:
            result.append(group[0])
            continue
        best = _pick_best(group)
        merged_tags = _merge_tags(group)
        best.tags = merged_tags
        result.append(best)

    return result


def _normalize_name(name: str) -> str:
    """Normalize a name for dedup comparison.

    Lowercases, strips leading/trailing hyphens, collapses multiple hyphens.
    """
    normalized = name.lower().strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized


def _pick_best(group: list[CatalogItem]) -> CatalogItem:
    """Pick the item with richest metadata from a duplicate group."""
    return max(
        group,
        key=lambda item: (
            1 if item.install_content else 0,
            len(item.description),
            item.quality_score,
        ),
    )


def _merge_tags(group: list[CatalogItem]) -> list[str]:
    """Merge unique tags from all items in a group, preserving order."""
    seen: dict[str, None] = {}
    for item in group:
        for tag in item.tags:
            seen.setdefault(tag, None)
    return list(seen.keys())
