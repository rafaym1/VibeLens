"""Friction analysis API schemas — request models and lightweight metadata."""

from pydantic import BaseModel, Field

from vibelens.models.llm.inference import BackendType
from vibelens.models.trajectories.final_metrics import FinalMetrics


class FrictionAnalysisRequest(BaseModel):
    """Request for LLM-powered friction analysis across sessions."""

    session_ids: list[str] = Field(description="Session IDs to analyze for friction events.")


class FrictionMeta(BaseModel):
    """Lightweight metadata for a persisted friction analysis."""

    id: str = Field(description="Unique analysis ID.")
    title: str | None = Field(default=None, description="Short title from synthesis.")
    session_count: int = Field(description="Number of sessions analyzed.")
    batch_count: int = Field(default=1, description="Number of LLM batches used.")
    item_count: int = Field(default=0, description="Number of friction types detected.")
    backend: BackendType = Field(description="Inference backend used.")
    model: str = Field(description="Model used for analysis.")
    created_at: str = Field(description="ISO timestamp of analysis.")
    final_metrics: FinalMetrics = Field(
        default_factory=FinalMetrics, description="Aggregate cost and token totals."
    )
    is_example: bool = Field(
        default=False, description="Whether this is a bundled example analysis."
    )
