"""Prompts for element creation: proposals, synthesis, and generation."""

from vibelens.models.llm.prompts import AnalysisPrompt, load_template
from vibelens.models.skill import SkillCreation, SkillCreationProposalOutput

# Per-batch proposal: detects patterns and proposes new skills
SKILL_CREATION_PROPOSAL_PROMPT = AnalysisPrompt(
    task_id="skill_creation_proposal",
    system_template=load_template("creation/creation_proposal_system.j2"),
    user_template=load_template("creation/creation_proposal_user.j2"),
    output_model=SkillCreationProposalOutput,
)
# Post-batch synthesis: merges and deduplicates proposals across batches
SKILL_CREATION_PROPOSAL_SYNTHESIS_PROMPT = AnalysisPrompt(
    task_id="skill_creation_proposal_synthesis",
    system_template=load_template("creation/creation_proposal_synthesis_system.j2"),
    user_template=load_template("creation/creation_proposal_synthesis_user.j2"),
    output_model=SkillCreationProposalOutput,
)
# Generation step: produces full SKILL.md for each approved proposal
SKILL_CREATION_GENERATE_PROMPT = AnalysisPrompt(
    task_id="skill_creation_generate",
    system_template=load_template("creation/creation_system.j2"),
    user_template=load_template("creation/creation_user.j2"),
    output_model=SkillCreation,
    exclude_fields={"SkillCreation": frozenset({"addressed_patterns"})},
)
