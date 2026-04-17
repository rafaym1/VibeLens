"""Creation models for the proposal and deep-generation pipeline."""

import re

from pydantic import BaseModel, Field, field_validator

from vibelens.models.enums import AgentExtensionType
from vibelens.models.llm.inference import BackendType
from vibelens.models.personalization.constants import (
    DESCRIPTION_CONFIDENCE,
    DESCRIPTION_RATIONALE,
    DESCRIPTION_TITLE,
)
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.trajectories.final_metrics import FinalMetrics
from vibelens.models.trajectories.metrics import Metrics

_NON_KEBAB_RE = re.compile(r"[^a-z0-9-]+")


def _normalize_kebab_name(value: str) -> str:
    """Strip non-ASCII noise from a kebab-case element name.

    LLMs occasionally inject stray Cyrillic or CJK characters at the end of
    otherwise-valid names (e.g. ``ui-refinement-iteratorциклер``). This
    validator lowercases, strips anything outside ``[a-z0-9-]``, then
    collapses consecutive or leading/trailing dashes.
    """
    cleaned = _NON_KEBAB_RE.sub("", value.lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or value


class CreationProposal(BaseModel):
    """A lightweight creation proposal from the proposal pipeline.

    Produced by the proposal LLM step. The user approves proposals
    before the deep-creation step generates full file content.
    """

    element_type: AgentExtensionType = Field(description="Type of element to create.")
    element_name: str = Field(description="Proposed element name in kebab-case.")
    description: str = Field(
        description=(
            "One-line trigger description for the proposed element. "
            "State what the element does AND when it activates. "
            "Include trigger phrases. Max 30 words."
        )
    )
    session_ids: list[str] = Field(
        default_factory=list, description="Session UUIDs where this pattern was observed."
    )
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Titles of workflow patterns this proposal addresses."
    )
    rationale: str = Field(description=DESCRIPTION_RATIONALE)
    confidence: float = Field(default=0.0, description=DESCRIPTION_CONFIDENCE)

    @field_validator("element_name", mode="before")
    @classmethod
    def _kebab_case(cls, value: str) -> str:
        return _normalize_kebab_name(value) if isinstance(value, str) else value


class CreationProposalBatch(BaseModel):
    """LLM output from the proposal generation step.

    Contains lightweight proposals (name + description + rationale) without
    full file content. Deep creation produces the full content per proposal.
    """

    title: str = Field(default="", description=DESCRIPTION_TITLE)
    workflow_patterns: list[WorkflowPattern] = Field(
        default_factory=list, description="Detected workflow patterns from trajectory analysis."
    )
    proposals: list[CreationProposal] = Field(
        default_factory=list, description="Creation proposals."
    )


class CreationProposalResult(BaseModel):
    """Service result wrapping proposals with metadata."""

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
    proposal_batch: CreationProposalBatch = Field(
        description="LLM-generated proposal output with patterns and proposals."
    )


class PersonalizationCreation(BaseModel):
    """A fully generated element from detected workflow patterns.

    Produced by the deep-creation LLM step. Confidence is set by the service
    from the originating proposal's confidence score.
    """

    element_type: AgentExtensionType = Field(description="Type of element to create.")
    element_name: str = Field(description="Element name in kebab-case.")
    description: str = Field(
        description=(
            "Specific trigger description for YAML frontmatter. "
            "State what the element does AND when it activates. "
            "Include trigger phrases. Max 30 words."
        )
    )
    skill_md_content: str = Field(description="Full SKILL.md content including YAML frontmatter.")
    rationale: str = Field(description=DESCRIPTION_RATIONALE)
    tools_used: list[str] = Field(
        default_factory=list,
        description="Tool names referenced in the element (e.g. Read, Edit, Bash).",
    )
    addressed_patterns: list[str] = Field(
        default_factory=list, description="Titles of workflow patterns addressed by this element."
    )
    confidence: float = Field(default=0.0, description=DESCRIPTION_CONFIDENCE)

    @field_validator("element_name", mode="before")
    @classmethod
    def _kebab_case(cls, value: str) -> str:
        return _normalize_kebab_name(value) if isinstance(value, str) else value
