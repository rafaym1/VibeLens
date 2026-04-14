"""Creation pipeline analysis result model."""

from pydantic import BaseModel, Field

from vibelens.models.creation.creation import ElementCreation
from vibelens.models.llm.inference import BackendType
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.trajectories.metrics import Metrics


class CreationAnalysisResult(BaseModel):
    """Complete creation analysis result across all batches.

    Contains detected workflow patterns and the generated elements,
    with session tracking, backend info, and cost metadata.
    """

    analysis_id: str | None = Field(
        default=None, description="Persistence ID. Set when saved to disk."
    )
    session_ids: list[str] = Field(
        description="Session IDs that were successfully loaded and analyzed."
    )
    skipped_session_ids: list[str] = Field(
        default_factory=list, description="Session IDs that could not be loaded."
    )
    title: str = Field(
        default="",
        description=(
            "Self-explanatory title describing the main finding. "
            "Understandable without reading the rest. Max 10 words."
        ),
    )
    workflow_patterns: list[WorkflowPattern] = Field(
        default_factory=list, description="Detected workflow patterns from trajectory analysis."
    )
    creations: list[ElementCreation] = Field(
        default_factory=list, description="Generated elements."
    )
    backend_id: BackendType = Field(description="Inference backend used.")
    model: str = Field(description="Model identifier.")
    created_at: str = Field(description="ISO timestamp of analysis completion.")
    batch_count: int = Field(default=1, description="Number of LLM batches used.")
    metrics: Metrics = Field(
        default_factory=Metrics, description="Token usage and cost from the inference step."
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal issues encountered during analysis."
    )
    duration_seconds: float | None = Field(
        default=None, description="Wall-clock analysis duration in seconds."
    )
    is_example: bool = Field(
        default=False, description="Whether this is a bundled example analysis."
    )
