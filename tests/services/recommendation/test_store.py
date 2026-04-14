"""Tests for recommendation store."""

import tempfile
from datetime import datetime, timezone
from pathlib import Path

from vibelens.models.llm.inference import BackendType
from vibelens.models.recommendation.catalog import ITEM_TYPE_LABELS, ItemType
from vibelens.models.recommendation.profile import UserProfile
from vibelens.models.recommendation.results import (
    CatalogRecommendation,
    RecommendationResult,
)
from vibelens.models.trajectories.metrics import Metrics
from vibelens.services.recommendation.store import RecommendationStore


def _build_test_result(session_ids: list[str]) -> RecommendationResult:
    """Build a minimal RecommendationResult for tests."""
    return RecommendationResult(
        analysis_id="test-rec-001",
        session_ids=session_ids,
        skipped_session_ids=[],
        title="Test recommendations",
        summary="Test summary.",
        user_profile=UserProfile(
            domains=["web-dev"],
            languages=["python"],
            frameworks=["fastapi"],
            agent_platforms=["claude-code"],
            bottlenecks=["slow tests"],
            workflow_style="iterative",
            search_keywords=["testing", "python"],
        ),
        recommendations=[
            CatalogRecommendation(
                item_id="test/skill",
                item_type=ItemType.SKILL,
                user_label=ITEM_TYPE_LABELS[ItemType.SKILL],
                name="test-skill",
                description="A test skill.",
                rationale="Matches test patterns.",
                confidence=0.9,
                quality_score=80.0,
                score=0.85,
                install_method="skill_file",
                install_command=None,
                has_content=True,
                source_url="https://example.com",
            ),
        ],
        backend_id=BackendType.MOCK,
        model="mock-model",
        created_at=datetime.now(timezone.utc).isoformat(),
        metrics=Metrics(cost_usd=0.01),
        duration_seconds=1.0,
        catalog_version="test",
    )


def test_recommendation_store_save_and_load():
    """RecommendationStore saves and loads results."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = RecommendationStore(Path(tmpdir))
        result = _build_test_result(["session-1", "session-2"])
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
        result = _build_test_result(["s1"])
        store.save(result, "test-001")
        analyses = store.list_analyses()
        assert len(analyses) == 1
        assert analyses[0].analysis_id == "test-001"
