"""Analysis prompt registry."""

from vibelens.models.llm.prompts import AnalysisPrompt
from vibelens.prompts.evolution import EVOLUTION_PROPOSAL_PROMPT
from vibelens.prompts.friction_analysis import FRICTION_PROMPT
from vibelens.prompts.recommendation import RECOMMENDATION_PROFILE_PROMPT

PROMPT_REGISTRY: dict[str, AnalysisPrompt] = {
    FRICTION_PROMPT.task_id: FRICTION_PROMPT,
    EVOLUTION_PROPOSAL_PROMPT.task_id: EVOLUTION_PROPOSAL_PROMPT,
    RECOMMENDATION_PROFILE_PROMPT.task_id: RECOMMENDATION_PROFILE_PROMPT,
}


def get_prompt(task_id: str) -> AnalysisPrompt | None:
    """Look up a registered analysis prompt by task ID.

    Args:
        task_id: Unique prompt identifier (e.g. 'friction_analysis').

    Returns:
        AnalysisPrompt instance, or None if not found.
    """
    return PROMPT_REGISTRY.get(task_id)
