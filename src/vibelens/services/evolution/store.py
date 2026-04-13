"""Evolution analysis result persistence.

Thin subclass of AnalysisStore with evolution-specific meta building.
"""

from pathlib import Path

from vibelens.models.evolution import EvolutionAnalysisResult
from vibelens.schemas.evolution import EvolutionAnalysisMeta
from vibelens.services.analysis_store import AnalysisStore


def _build_meta(analysis_id: str, result: EvolutionAnalysisResult) -> EvolutionAnalysisMeta:
    """Build lightweight metadata from a full evolution analysis result."""
    return EvolutionAnalysisMeta(
        analysis_id=analysis_id,
        title=result.title,
        session_ids=result.session_ids,
        created_at=result.created_at,
        model=result.model,
        cost_usd=result.metrics.cost_usd,
        duration_seconds=result.duration_seconds,
        is_example=result.is_example,
    )


class EvolutionAnalysisStore(AnalysisStore[EvolutionAnalysisResult, EvolutionAnalysisMeta]):
    """Manages persisted evolution analysis results on disk."""

    def __init__(self, store_dir: Path):
        super().__init__(store_dir, EvolutionAnalysisResult, EvolutionAnalysisMeta, _build_meta)
