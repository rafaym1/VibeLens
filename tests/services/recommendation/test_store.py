"""Tests for recommendation store and mock data."""
import tempfile
from pathlib import Path

from vibelens.services.recommendation.mock import build_mock_recommendation_result
from vibelens.services.recommendation.store import RecommendationStore


def test_recommendation_store_save_and_load():
    """RecommendationStore saves and loads results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RecommendationStore(Path(tmpdir))
        result = build_mock_recommendation_result(["session-1", "session-2"])
        store.save(result, "test-analysis-001")
        loaded = store.load("test-analysis-001")
        assert loaded is not None
        assert loaded.analysis_id == "test-analysis-001"
        assert len(loaded.recommendations) > 0
        print(f"Saved and loaded {len(loaded.recommendations)} recommendations")


def test_recommendation_store_list():
    """RecommendationStore lists analyses."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RecommendationStore(Path(tmpdir))
        result = build_mock_recommendation_result(["s1"])
        store.save(result, "test-001")
        analyses = store.list_analyses()
        assert len(analyses) == 1
        assert analyses[0].analysis_id == "test-001"


def test_mock_recommendation_result():
    """build_mock_recommendation_result produces valid result."""
    result = build_mock_recommendation_result(["s1", "s2", "s3"])
    assert len(result.recommendations) > 0
    assert result.user_profile is not None
    assert len(result.user_profile.search_keywords) > 0
    print(f"Mock: {len(result.recommendations)} recs, {len(result.user_profile.domains)} domains")
