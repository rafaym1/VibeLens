"""Tests for the recommendation engine orchestrator."""
from vibelens.services.recommendation.engine import (
    RECOMMENDATION_OUTPUT_TOKENS,
    RECOMMENDATION_TIMEOUT_SECONDS,
    RETRIEVAL_TOP_K,
    SCORING_TOP_K,
)


def test_engine_constants():
    """Engine constants are defined with expected values."""
    assert RETRIEVAL_TOP_K == 30
    assert SCORING_TOP_K == 15
    assert RECOMMENDATION_OUTPUT_TOKENS > 0
    assert RECOMMENDATION_TIMEOUT_SECONDS > 0


def test_engine_importable():
    """Engine entry points are importable."""
    from vibelens.services.recommendation.engine import (
        analyze_recommendation,
        estimate_recommendation,
    )
    assert callable(analyze_recommendation)
    assert callable(estimate_recommendation)
