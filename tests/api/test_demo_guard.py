"""Tests for the centralized demo-mode guard middleware."""

import pytest

from vibelens.api.demo_guard import (
    _BLOCKED_ROUTES,
    DEMO_RESTRICTED_DETAIL,
    _is_blocked,
)


class TestBlocklistMatching:
    """Verify _is_blocked correctly matches routes."""

    @pytest.mark.parametrize(
        "method, path",
        [
            ("POST", "/api/extensions/skills"),
            ("PUT", "/api/extensions/skills/my-skill"),
            ("DELETE", "/api/extensions/commands/cmd-name"),
            ("POST", "/api/extensions/hooks/import/claude"),
            ("POST", "/api/extensions/subagents/sub-name/agents"),
            ("DELETE", "/api/extensions/hooks/hook-name/agents/codex"),
            ("POST", "/api/extensions/catalog/item-123/install"),
            ("POST", "/api/llm/configure"),
            ("POST", "/api/shares"),
            ("DELETE", "/api/shares/session-abc"),
            ("POST", "/api/analysis/friction"),
            ("POST", "/api/creation"),
            ("POST", "/api/evolution"),
            ("POST", "/api/recommendation"),
            ("DELETE", "/api/analysis/friction/analysis-1"),
            ("DELETE", "/api/creation/analysis-2"),
            ("DELETE", "/api/evolution/analysis-3"),
            ("DELETE", "/api/recommendation/analysis-4"),
            ("POST", "/api/analysis/friction/jobs/job-1/cancel"),
            ("POST", "/api/creation/jobs/job-2/cancel"),
        ],
    )
    def test_blocked_routes(self, method: str, path: str):
        assert _is_blocked(method, path), f"{method} {path} should be blocked"

    @pytest.mark.parametrize(
        "method, path",
        [
            # GET requests always pass
            ("GET", "/api/extensions/skills"),
            ("GET", "/api/sessions"),
            ("GET", "/api/shares"),
            ("GET", "/api/analysis/dashboard"),
            ("GET", "/api/creation/some-id"),
            # Allowed POST operations
            ("POST", "/api/upload/zip"),
            ("POST", "/api/sessions/donate"),
            ("POST", "/api/donation/receive"),
            ("POST", "/api/sessions/download"),
            ("POST", "/api/analysis/friction/estimate"),
            ("POST", "/api/creation/estimate"),
            ("POST", "/api/evolution/estimate"),
            ("POST", "/api/recommendation/estimate"),
            # Polling job status (GET)
            ("GET", "/api/analysis/friction/jobs/job-1"),
            ("GET", "/api/creation/jobs/job-2"),
        ],
    )
    def test_allowed_routes(self, method: str, path: str):
        assert not _is_blocked(method, path), f"{method} {path} should be allowed"


class TestBlocklistCompleteness:
    """Ensure all four extension types have matching CRUD patterns."""

    EXTENSION_TYPES = ["skills", "commands", "subagents", "hooks"]

    def _routes_for_type(self, ext_type: str) -> set[tuple[str, str]]:
        return {(m, p) for m, p in _BLOCKED_ROUTES if f"/{ext_type}" in p}

    @pytest.mark.parametrize("ext_type", EXTENSION_TYPES)
    def test_crud_routes_present(self, ext_type: str):
        routes = self._routes_for_type(ext_type)
        methods_present = {m for m, _ in routes}
        assert "POST" in methods_present, f"Missing POST for {ext_type}"
        assert "PUT" in methods_present, f"Missing PUT for {ext_type}"
        assert "DELETE" in methods_present, f"Missing DELETE for {ext_type}"

    @pytest.mark.parametrize("ext_type", EXTENSION_TYPES)
    def test_import_route_present(self, ext_type: str):
        routes = self._routes_for_type(ext_type)
        import_routes = {(m, p) for m, p in routes if "/import/" in p}
        assert len(import_routes) >= 1, f"Missing import route for {ext_type}"

    @pytest.mark.parametrize("ext_type", EXTENSION_TYPES)
    def test_sync_routes_present(self, ext_type: str):
        routes = self._routes_for_type(ext_type)
        sync_routes = {(m, p) for m, p in routes if "/agents" in p and "/import/" not in p}
        assert len(sync_routes) >= 2, f"Missing sync/unsync routes for {ext_type}"


class TestResponseFormat:
    """Verify the 403 response detail is the expected stable code."""

    def test_detail_is_stable_string(self):
        assert DEMO_RESTRICTED_DETAIL == "demo_mode_restricted"
