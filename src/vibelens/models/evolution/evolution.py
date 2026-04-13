"""Element evolution models for any file-based element type."""

from pydantic import BaseModel, Field

from vibelens.models.enums import ElementType
from vibelens.models.llm.inference import BackendType
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.trajectories.metrics import Metrics


class ElementEdit(BaseModel):
    """A single edit to an existing element file.

    Uses old_string/new_string like the Edit tool:
    - Replace: old_string="original text", new_string="new text"
    - Delete: old_string="text to remove", new_string=""
    - Append: old_string="" (empty), new_string="text to add"
    """

    old_string: str = Field(description="Text to find in the element file. Empty for append.")
    new_string: str = Field(description="Replacement text. Empty for deletion.")
    replace_all: bool = Field(default=False, description="Replace all occurrences if True.")


class ElementEvolutionProposal(BaseModel):
    """A lightweight evolution proposal before deep editing.

    Produced by the proposal LLM step. The user approves proposals
    before the deep-edit step generates granular edits.
    """

    element_type: ElementType = Field(description="Type of element to evolve.")
    element_name: str = Field(description="Name of the existing element to modify.")
    description: str = Field(description="Proposed improvement. Max 30 words.")
    rationale: str = Field(
        description=(
            "One sentence (15 words), then 1-2 bullets starting with '\\n- ' (10 words each)."
        )
    )
    suggested_changes: str = Field(
        default="", description="High-level change description for deep-edit LLM call."
    )
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Workflow pattern titles this proposal addresses."
    )
    relevant_session_indices: list[int] = Field(
        default_factory=list, description="0-indexed session indices relevant to this proposal."
    )
    confidence: float = Field(
        default=0.0, description="Confidence this evolution is needed. 0.0-1.0."
    )


class ElementEvolutionProposalOutput(BaseModel):
    """LLM output from the evolution proposal step."""

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
    proposals: list[ElementEvolutionProposal] = Field(
        default_factory=list, description="Evolution proposals for existing elements."
    )


class ElementEvolutionProposalResult(BaseModel):
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
    backend_id: BackendType = Field(description="Inference backend used.")
    created_at: str = Field(description="ISO timestamp of analysis completion.")
    model: str = Field(description="Model identifier.")
    metrics: Metrics = Field(
        default_factory=Metrics, description="Token usage and cost from the inference step."
    )
    duration_seconds: float | None = Field(
        default=None, description="Wall-clock analysis duration in seconds."
    )
    batch_count: int = Field(default=1, description="Number of LLM batches used.")
    warnings: list[str] = Field(
        default_factory=list, description="Non-fatal issues encountered during analysis."
    )
    proposal_output: ElementEvolutionProposalOutput = Field(
        description="LLM-generated proposal output with patterns and proposals."
    )


class ElementEvolution(BaseModel):
    """A suggested improvement to an existing installed element.

    Produced by the deep-edit LLM step. Contains granular edits
    to apply to the element's source file.
    """

    element_type: ElementType = Field(description="Type of element being evolved.")
    element_name: str = Field(description="Name of the existing element to evolve.")
    description: str = Field(description="What the evolution does. Max 30 words.")
    edits: list[ElementEdit] = Field(description="Ordered list of granular edits to apply.")
    rationale: str = Field(
        description=(
            "One sentence (15 words), then 1-2 bullets starting with '\\n- ' (10 words each)."
        )
    )
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Workflow pattern titles addressed."
    )
    confidence: float = Field(default=0.0, description="Confidence score 0.0-1.0.")
