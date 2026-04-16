"""Prompts for element evolution: proposals, synthesis, and editing."""

from vibelens.models.llm.prompts import AnalysisPrompt, load_template
from vibelens.models.personalization.evolution import (
    EvolutionProposalBatch,
    PersonalizationEvolution,
)

# Per-batch proposal: detects patterns and proposes improvements to existing elements
EVOLUTION_PROPOSAL_PROMPT = AnalysisPrompt(
    task_id="evolution_proposal",
    system_template=load_template("evolution/evolution_proposal_system.j2"),
    user_template=load_template("evolution/evolution_proposal_user.j2"),
    output_model=EvolutionProposalBatch,
)
# Post-batch synthesis: merges and deduplicates evolution proposals across batches
EVOLUTION_PROPOSAL_SYNTHESIS_PROMPT = AnalysisPrompt(
    task_id="evolution_proposal_synthesis",
    system_template=load_template("evolution/evolution_proposal_synthesis_system.j2"),
    user_template=load_template("evolution/evolution_proposal_synthesis_user.j2"),
    output_model=EvolutionProposalBatch,
)
# Edit step: generates granular old_string/new_string edits for each proposal
EVOLUTION_PROMPT = AnalysisPrompt(
    task_id="evolution",
    system_template=load_template("evolution/evolution_system.j2"),
    user_template=load_template("evolution/evolution_user.j2"),
    output_model=PersonalizationEvolution,
    exclude_fields={"PersonalizationEvolution": frozenset({"addressed_patterns", "element_type"})},
)
