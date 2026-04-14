"""Prompts for element creation: proposals, synthesis, and generation."""

from vibelens.models.llm.prompts import AnalysisPrompt, load_template
from vibelens.models.personalization.creation import CreationProposalBatch, PersonalizationCreation

# Per-batch proposal: detects patterns and proposes new elements
CREATION_PROPOSAL_PROMPT = AnalysisPrompt(
    task_id="creation_proposal",
    system_template=load_template("creation/creation_proposal_system.j2"),
    user_template=load_template("creation/creation_proposal_user.j2"),
    output_model=CreationProposalBatch,
)
# Post-batch synthesis: merges and deduplicates proposals across batches
CREATION_PROPOSAL_SYNTHESIS_PROMPT = AnalysisPrompt(
    task_id="creation_proposal_synthesis",
    system_template=load_template("creation/creation_proposal_synthesis_system.j2"),
    user_template=load_template("creation/creation_proposal_synthesis_user.j2"),
    output_model=CreationProposalBatch,
)
# Generation step: produces full SKILL.md for each approved proposal
CREATION_PROMPT = AnalysisPrompt(
    task_id="creation",
    system_template=load_template("creation/creation_system.j2"),
    user_template=load_template("creation/creation_user.j2"),
    output_model=PersonalizationCreation,
    exclude_fields={"PersonalizationCreation": frozenset({"addressed_patterns"})},
)
