"""Heuristic quality scoring for bulk catalog items."""

import math
from datetime import datetime, timezone

from vibelens.models.recommendation.catalog import CatalogItem

WEIGHT_DESCRIPTION = 0.30
WEIGHT_SOURCE = 0.25
WEIGHT_STARS = 0.20
WEIGHT_RECENCY = 0.15
WEIGHT_DIVERSITY = 0.10

DESCRIPTION_NORM_CHARS = 200

SOURCE_QUALITY: dict[str, float] = {
    "featured": 0.7,
    "bwc": 0.5,
    "cct": 0.3,
}

DIVERSITY_THRESHOLD = 5
DIVERSITY_BOOST = 0.2


def score_items(items: list[CatalogItem]) -> list[CatalogItem]:
    """Assign quality_score to each item using weighted heuristic signals.

    Each signal produces a 0.0-1.0 value. The weighted sum is mapped to
    the 50-100 range via: final = 50 + weighted_sum * 50.

    Args:
        items: Items with quality_score=0.0 (to be filled).

    Returns:
        Same items with quality_score populated.
    """
    category_counts = _count_categories(items)

    for item in items:
        desc_signal = _score_description(item.description)
        source_signal = _score_source(item.item_id)
        stars_signal = item.popularity
        recency_signal = _score_recency(item.updated_at)
        diversity_signal = _score_diversity(item.category, category_counts)

        weighted_sum = (
            WEIGHT_DESCRIPTION * desc_signal
            + WEIGHT_SOURCE * source_signal
            + WEIGHT_STARS * stars_signal
            + WEIGHT_RECENCY * recency_signal
            + WEIGHT_DIVERSITY * diversity_signal
        )
        item.quality_score = round(50.0 + weighted_sum * 50.0, 1)

    return items


def _score_description(description: str) -> float:
    """Score description richness: longer, more specific descriptions score higher."""
    return min(len(description) / DESCRIPTION_NORM_CHARS, 1.0)


def _score_source(item_id: str) -> float:
    """Score source quality from item_id prefix."""
    prefix = item_id.split(":")[0] if ":" in item_id else ""
    return SOURCE_QUALITY.get(prefix, 0.0)


def _score_recency(updated_at: str) -> float:
    """Score recency from updated_at timestamp.

    Uses exponential decay: e^(-0.01 * days). Returns 0.5 default if no date.
    """
    if not updated_at:
        return 0.5

    try:
        dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        now = datetime.now(tz=timezone.utc)
        days = max((now - dt).days, 0)
        return math.exp(-0.01 * days)
    except (ValueError, TypeError):
        return 0.5


def _score_diversity(category: str, category_counts: dict[str, int]) -> float:
    """Boost items in sparse categories to prevent empty categories."""
    count = category_counts.get(category, 0)
    if count < DIVERSITY_THRESHOLD:
        return DIVERSITY_BOOST
    return 0.0


def _count_categories(items: list[CatalogItem]) -> dict[str, int]:
    """Count items per category."""
    counts: dict[str, int] = {}
    for item in items:
        counts[item.category] = counts.get(item.category, 0) + 1
    return counts
