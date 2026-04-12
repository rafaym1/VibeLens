"""Skill retrieval mode — deprecated, replaced by recommendation pipeline."""

from vibelens.llm.cost_estimator import CostEstimate
from vibelens.models.skill import SkillAnalysisResult


def estimate_skill_retrieval(
    session_ids: list[str], session_token: str | None = None
) -> CostEstimate:
    """Pre-flight cost estimate for skill retrieval analysis.

    Args:
        session_ids: Sessions to analyze.
        session_token: Browser tab token for upload scoping.

    Raises:
        NotImplementedError: Retrieval is replaced by the recommendation pipeline.
    """
    raise NotImplementedError("Retrieval replaced by recommendation pipeline")


async def analyze_skill_retrieval(
    session_ids: list[str], session_token: str | None = None
) -> SkillAnalysisResult:
    """Run retrieval-mode skill analysis.

    Args:
        session_ids: Sessions to analyze.
        session_token: Browser tab token for upload scoping.

    Raises:
        NotImplementedError: Retrieval is replaced by the recommendation pipeline.
    """
    raise NotImplementedError("Retrieval replaced by recommendation pipeline")
