"""Evolution models for any file-based element type."""

from pydantic import BaseModel, Field

from vibelens.models.llm.inference import BackendType
from vibelens.models.personalization.constants import (
    CONFIDENCE_DESCRIPTION,
    RATIONALE_DESCRIPTION,
    TITLE_DESCRIPTION,
)
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.trajectories.final_metrics import FinalMetrics
from vibelens.models.trajectories.metrics import Metrics


class PersonalizationEdit(BaseModel):
    """A single edit to an existing element file.

    Uses old_string/new_string like the Edit tool:
    - Replace: old_string="original text", new_string="new text"
    - Delete: old_string="text to remove", new_string=""
    - Append: old_string="" (empty), new_string="text to add"
    """

    old_string: str = Field(description="Text to find in the element file. Empty for append.")
    new_string: str = Field(description="Replacement text. Empty for deletion.")
    replace_all: bool = Field(default=False, description="Replace all occurrences if True.")


class EvolutionProposal(BaseModel):
    """A lightweight evolution proposal before deep editing.

    Produced by the proposal LLM step. The user approves proposals
    before the deep-edit step generates granular edits.
    """

    element_name: str = Field(description="Name of the existing element to modify.")
    session_indices: list[int] = Field(
        default_factory=list, description="0-indexed session indices relevant to this proposal."
    )
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Workflow pattern titles this proposal addresses."
    )
    rationale: str = Field(description=RATIONALE_DESCRIPTION)
    confidence: float = Field(
        default=0.0, description="Confidence this evolution is needed. 0.0-1.0."
    )


class EvolutionProposalBatch(BaseModel):
    """LLM output from the evolution proposal step."""

    title: str = Field(description=TITLE_DESCRIPTION)
    workflow_patterns: list[WorkflowPattern] = Field(
        default_factory=list, description="Detected workflow patterns from trajectory analysis."
    )
    proposals: list[EvolutionProposal] = Field(
        default_factory=list, description="Evolution proposals."
    )


class EvolutionProposalResult(BaseModel):
    """Service result wrapping evolution proposals with metadata."""

    proposal_id: str | None = Field(
        default=None, description="Persistence ID. Set when saved to disk."
    )
    session_ids: list[str] = Field(
        description="Session IDs that were successfully loaded and analyzed."
    )
    skipped_session_ids: list[str] = Field(
        default_factory=list, description="Session IDs that could not be loaded."
    )
    created_at: str = Field(description="ISO timestamp of analysis completion.")
    backend: BackendType = Field(description="Inference backend used.")
    model: str = Field(description="Model identifier.")
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
    proposal_batch: EvolutionProposalBatch = Field(
        description="LLM-generated proposal output with patterns and proposals."
    )


class PersonalizationEvolution(BaseModel):
    """A suggested improvement to an existing installed element.

    Produced by the deep-edit LLM step. Contains granular edits
    to apply to the element's source file.
    """

    element_name: str = Field(description="Name of the existing element to evolve.")
    edits: list[PersonalizationEdit] = Field(description="Ordered list of granular edits to apply.")
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Workflow pattern titles addressed."
    )
    rationale: str = Field(description=RATIONALE_DESCRIPTION)
    confidence: float = Field(default=0.0, description=CONFIDENCE_DESCRIPTION)
