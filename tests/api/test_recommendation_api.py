"""Tests for recommendation API endpoints."""


def test_recommendation_schemas_importable():
    """Recommendation schemas are importable."""
    from vibelens.schemas.recommendation import (
        RecommendationAnalyzeRequest,
        RecommendationInstallRequest,
    )
    req = RecommendationAnalyzeRequest(session_ids=["s1", "s2"])
    assert len(req.session_ids) == 2

    install = RecommendationInstallRequest(
        selected_item_ids=["test-runner"],
        target_agent="claude-code",
    )
    assert install.target_agent == "claude-code"


def test_recommendation_router_importable():
    """Recommendation API router is importable."""
    from vibelens.api.recommendation import router
    routes = [r.path for r in router.routes]
    assert "/analyze" in routes or any("/analyze" in r for r in routes)
    print(f"Recommendation routes: {routes}")
