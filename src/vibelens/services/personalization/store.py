"""Personalization result persistence.

Thin subclass of AnalysisStore with personalization-specific meta building.
"""

from pathlib import Path

from vibelens.models.skill import PersonalizationResult
from vibelens.schemas.skills import PersonalizationMeta
from vibelens.services.analysis_store import AnalysisStore


def _build_meta(analysis_id: str, result: PersonalizationResult) -> PersonalizationMeta:
    """Build lightweight metadata from a full personalization result."""
    return PersonalizationMeta(
        analysis_id=analysis_id,
        mode=result.mode,
        title=result.title,
        session_ids=result.session_ids,
        created_at=result.created_at,
        model=result.model,
        cost_usd=result.metrics.cost_usd,
        duration_seconds=result.duration_seconds,
    )


class PersonalizationStore(AnalysisStore[PersonalizationResult, PersonalizationMeta]):
    """Manages persisted personalization results on disk."""

    def __init__(self, store_dir: Path):
        super().__init__(store_dir, PersonalizationResult, PersonalizationMeta, _build_meta)
