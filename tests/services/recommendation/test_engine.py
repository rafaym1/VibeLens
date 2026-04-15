"""Tests for the recommendation engine orchestrator."""

import inspect

from vibelens.services.recommendation.engine import (
    RATIONALE_MAX_RESULTS,
    RATIONALE_MAX_RESULTS_LIMIT,
    RATIONALE_MIN_RELEVANCE,
    RECOMMENDATION_OUTPUT_TOKENS,
    RECOMMENDATION_TIMEOUT_SECONDS,
    RETRIEVAL_TOP_K,
    SCORING_TOP_K,
)


def test_engine_constants():
    """Engine constants are defined with expected values."""
    assert RETRIEVAL_TOP_K == 200
    assert SCORING_TOP_K == 100
    assert RATIONALE_MAX_RESULTS == 15
    assert RATIONALE_MAX_RESULTS_LIMIT == 50
    assert RATIONALE_MIN_RELEVANCE == 0.6
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


def test_engine_exports_lightweight_path():
    """Engine accepts empty session_ids for lightweight extraction."""
    from vibelens.services.recommendation.engine import _run_pipeline

    # Verify the function signature accepts empty session_ids
    sig = inspect.signature(_run_pipeline)
    params = list(sig.parameters.keys())
    assert "session_ids" in params


def test_analyze_recommendation_signature():
    """analyze_recommendation accepts optional session_ids and top_n."""
    from vibelens.services.recommendation.engine import analyze_recommendation

    sig = inspect.signature(analyze_recommendation)
    session_ids_param = sig.parameters["session_ids"]
    assert session_ids_param.default is not inspect.Parameter.empty

    top_n_param = sig.parameters["top_n"]
    assert top_n_param.default == RATIONALE_MAX_RESULTS
