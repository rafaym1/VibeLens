"""Service-layer result models with metadata for personalization analysis."""

from pydantic import BaseModel, Field

from vibelens.models.llm.inference import BackendType
from vibelens.models.personalization.constants import TITLE_DESCRIPTION
from vibelens.models.personalization.creation import PersonalizationCreation
from vibelens.models.personalization.enums import PersonalizationMode
from vibelens.models.personalization.evolution import PersonalizationEvolution
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.skill.retrieval import SkillRecommendation
from vibelens.models.trajectories.final_metrics import FinalMetrics
from vibelens.models.trajectories.metrics import Metrics


class PersonalizationResult(BaseModel):
    """Complete personalization result with service metadata.

    Flattens mode-specific LLM output fields and adds session tracking,
    backend info, and cost metadata from the service layer.
    """

    id: str = Field(description="Persistence ID. Set when saved to disk.")
    mode: PersonalizationMode = Field(description="Which analysis mode was used.")
    session_ids: list[str] = Field(
        description="Session IDs that were successfully loaded and analyzed."
    )
    skipped_session_ids: list[str] = Field(
        default_factory=list, description="Session IDs that could not be loaded."
    )
    title: str = Field(description=TITLE_DESCRIPTION)
    workflow_patterns: list[WorkflowPattern] = Field(
        default_factory=list, description="Detected workflow patterns from trajectory analysis."
    )
    recommendations: list[SkillRecommendation] = Field(
        default_factory=list, description="Recommended skills (retrieval mode)."
    )
    creations: list[PersonalizationCreation] = Field(
        default_factory=list, description="Generated skills (creation mode)."
    )
    evolutions: list[PersonalizationEvolution] = Field(
        default_factory=list, description="Evolution suggestions (evolution mode)."
    )
    backend: BackendType = Field(description="Inference backend used.")
    model: str = Field(description="Model identifier.")
    created_at: str = Field(description="ISO timestamp of analysis completion.")
    batch_count: int = Field(default=1, description="Number of LLM batches used.")
    batch_metrics: list[Metrics] = Field(
        default_factory=list, description="Per-batch token usage and cost entries."
    )
    final_metrics: FinalMetrics = Field(
        default_factory=FinalMetrics, description="Aggregate cost and token totals."
    )
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal issues encountered during analysis."
    )
    is_example: bool = Field(default=False, description="Whether this is an example.")
