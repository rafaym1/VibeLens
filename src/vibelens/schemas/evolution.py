"""Evolution analysis API schemas — request models and lightweight metadata."""

from pydantic import BaseModel, Field


class EvolutionAnalysisRequest(BaseModel):
    """Request body for running an evolution analysis across sessions."""

    session_ids: list[str] = Field(description="Session IDs to analyze.")
    skill_names: list[str] | None = Field(
        default=None,
        description="Skill names to target for evolution. None means all installed skills.",
    )


class EvolutionAnalysisMeta(BaseModel):
    """Lightweight metadata for a persisted evolution analysis."""

    analysis_id: str = Field(description="Unique ID for this analysis.")
    title: str = Field(default="", description="LLM-generated analysis title.")
    session_ids: list[str] = Field(description="Sessions that were analyzed.")
    created_at: str = Field(description="ISO timestamp of analysis.")
    model: str = Field(description="Model used for analysis.")
    cost_usd: float | None = Field(default=None, description="Inference cost in USD.")
    duration_seconds: float | None = Field(
        default=None, description="Wall-clock analysis duration in seconds."
    )
    is_example: bool = Field(
        default=False, description="Whether this is a bundled example analysis."
    )
