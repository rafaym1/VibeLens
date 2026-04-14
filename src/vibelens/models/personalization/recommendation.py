"""Recommendation pipeline models — catalog, profile, rationale, and results."""

from pydantic import BaseModel, Field, computed_field

from vibelens.models.llm.inference import BackendType
from vibelens.models.personalization.constants import (
    CONFIDENCE_DESCRIPTION,
    RATIONALE_DESCRIPTION,
    TITLE_DESCRIPTION,
)
from vibelens.models.trajectories.metrics import Metrics
from vibelens.utils.compat import StrEnum


class RecommendationItemType(StrEnum):
    """Recommendation item type classification."""

    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
    REPO = "repo"


FILE_BASED_TYPES: set[RecommendationItemType] = {
    RecommendationItemType.SKILL,
    RecommendationItemType.SUBAGENT,
    RecommendationItemType.COMMAND,
    RecommendationItemType.HOOK,
}

ITEM_TYPE_LABELS: dict[RecommendationItemType, str] = {
    RecommendationItemType.SKILL: "Skill",
    RecommendationItemType.SUBAGENT: "Expert Agent",
    RecommendationItemType.COMMAND: "Slash Command",
    RecommendationItemType.HOOK: "Automation",
    RecommendationItemType.REPO: "Repository",
}


class RecommendationItem(BaseModel):
    """A single item in the recommendation catalog.

    Represents a discoverable AI tool (skill, subagent, command, hook, or repo)
    with quality metrics and installation metadata.
    """

    item_id: str = Field(description="Unique identifier.")
    item_type: RecommendationItemType = Field(description="Classified type.")
    name: str = Field(description="Display name.")
    description: str = Field(description="Plain language, 1-2 sentences.")
    tags: list[str] = Field(description="Searchable tags.")
    category: str = Field(description="Classification category.")
    platforms: list[str] = Field(description="Compatible agent platforms.")
    quality_score: float = Field(description="0-100 composite from crawler scorer.")
    popularity: float = Field(description="Normalized from stars, 0.0-1.0.")
    updated_at: str = Field(description="Last commit ISO timestamp.")
    source_url: str = Field(description="GitHub URL.")
    repo_full_name: str = Field(description="GitHub owner/repo.")
    stars: int = Field(default=0, description="GitHub star count.")
    forks: int = Field(default=0, description="GitHub fork count.")
    language: str = Field(default="", description="Primary repository language.")
    license_name: str = Field(default="", description="Repository license identifier (e.g. MIT).")
    install_method: str = Field(
        description="Installation method: skill_file, pip, npm, mcp_config, etc."
    )
    install_command: str | None = Field(
        default=None, description="CLI install command, e.g. 'pip install foo'."
    )
    install_content: str | None = Field(
        default=None, description="Full file content for direct install."
    )

    @computed_field
    @property
    def is_file_based(self) -> bool:
        """True for file-based types (skill, subagent, command, hook)."""
        return self.item_type in FILE_BASED_TYPES


class UserProfile(BaseModel):
    """Aggregated user profile from L2 profile generation.

    Captures the user's development context, workflow style, and recurring
    friction points. Used by L3 retrieval for scoring and L4 for rationale.
    """

    domains: list[str] = Field(description="Development domains, e.g. web-dev, data-pipeline.")
    languages: list[str] = Field(description="Programming languages, e.g. python, typescript.")
    frameworks: list[str] = Field(description="Frameworks/libraries, e.g. fastapi, react.")
    agent_platforms: list[str] = Field(description="Agent platforms used, e.g. claude-code, codex.")
    bottlenecks: list[str] = Field(
        description="Recurring friction points, e.g. repeated test failures, slow CI."
    )
    workflow_style: str = Field(
        description="Characteristic workflow style, e.g. iterative debugger, prefers small commits."
    )
    search_keywords: list[str] = Field(
        description="20-30 catalog-friendly search terms derived from session content."
    )


class RationaleItem(BaseModel):
    """LLM-generated rationale for a single candidate."""

    item_id: str = Field(description="RecommendationItem reference.")
    rationale: str = Field(description=RATIONALE_DESCRIPTION)
    confidence: float = Field(description=CONFIDENCE_DESCRIPTION)


class RationaleOutput(BaseModel):
    """LLM output for L4 rationale generation."""

    rationales: list[RationaleItem] = Field(description="Per-candidate personalized rationales.")


class CatalogRecommendation(BaseModel):
    """A single catalog item recommended to the user.

    Includes personalized rationale and scoring from the recommendation pipeline.
    """

    item_id: str = Field(description="RecommendationItem reference.")
    item_type: RecommendationItemType = Field(description="Item type.")
    user_label: str = Field(description="User-facing type label.")
    name: str = Field(description="Display name.")
    description: str = Field(description="Plain language description.")
    tags: list[str] = Field(default_factory=list, description="Searchable tags.")
    category: str = Field(default="", description="Classification category.")
    rationale: str = Field(description="Personalized rationale: 1 sentence + 1-2 bullets.")
    confidence: float = Field(description="Match confidence 0.0-1.0.")
    quality_score: float = Field(description="Catalog quality score 0-100.")
    score: float = Field(description="Composite score from scoring pipeline.")
    install_method: str = Field(description="How to install.")
    install_command: str | None = Field(default=None, description="Install command.")
    has_content: bool = Field(description="Whether install_content is bundled.")
    source_url: str = Field(description="GitHub URL.")


class RecommendationResult(BaseModel):
    """Complete recommendation pipeline result.

    Contains the user profile, ranked recommendations, and analysis metadata.
    """

    analysis_id: str | None = Field(default=None, description="Set on persistence.")
    session_ids: list[str] = Field(description="Sessions analyzed.")
    skipped_session_ids: list[str] = Field(default_factory=list, description="Sessions not found.")
    title: str = Field(description=TITLE_DESCRIPTION)
    summary: str = Field(description="1-2 sentence narrative.")
    user_profile: UserProfile = Field(description="Extracted profile from L2.")
    recommendations: list[CatalogRecommendation] = Field(description="Ranked results.")
    backend: BackendType = Field(description="Inference backend.")
    model: str = Field(description="Model identifier.")
    created_at: str = Field(description="ISO timestamp.")
    metrics: Metrics = Field(default_factory=Metrics, description="Token usage and cost.")
    duration_seconds: float | None = Field(default=None, description="Wall-clock time.")
    catalog_version: str = Field(description="Catalog snapshot version used.")
    is_example: bool = Field(default=False, description="Bundled example flag.")
