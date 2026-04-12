"""Recommendation analysis result persistence.

Thin subclass of AnalysisStore with recommendation-specific meta building.
"""

from pathlib import Path

from pydantic import BaseModel, Field

from vibelens.models.recommendation.results import RecommendationResult
from vibelens.services.analysis_store import AnalysisStore


class RecommendationMeta(BaseModel):
    """Lightweight metadata for a persisted recommendation analysis."""

    analysis_id: str = Field(description="Unique analysis ID.")
    title: str = Field(default="", description="Main finding.")
    session_ids: list[str] = Field(description="Sessions analyzed.")
    created_at: str = Field(description="ISO timestamp.")
    model: str = Field(description="Model used.")
    cost_usd: float | None = Field(default=None, description="Inference cost.")
    duration_seconds: float | None = Field(default=None, description="Wall-clock duration.")
    recommendation_count: int = Field(default=0, description="Number of recommendations.")
    is_example: bool = Field(default=False, description="Bundled example flag.")


def _build_meta(analysis_id: str, result: RecommendationResult) -> RecommendationMeta:
    """Build lightweight metadata from a full recommendation result."""
    return RecommendationMeta(
        analysis_id=analysis_id,
        title=result.title,
        session_ids=result.session_ids,
        created_at=result.created_at,
        model=result.model,
        cost_usd=result.metrics.cost_usd if result.metrics else None,
        duration_seconds=result.duration_seconds,
        recommendation_count=len(result.recommendations),
        is_example=result.is_example,
    )


class RecommendationStore(AnalysisStore[RecommendationResult, RecommendationMeta]):
    """Manages persisted recommendation analysis results on disk."""

    def __init__(self, store_dir: Path):
        super().__init__(store_dir, RecommendationResult, RecommendationMeta, _build_meta)
