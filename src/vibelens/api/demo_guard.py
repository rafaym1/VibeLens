"""Centralized demo-mode guard middleware.

Blocks state-mutating API routes when the server runs in demo mode,
returning 403 with a stable ``demo_mode_restricted`` detail code.
The frontend can match on this code to show the "Install VibeLens
Locally" dialog.

Only attached to the app when ``is_demo_mode()`` is true at startup,
so there is zero overhead in self-use mode.
"""

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

DEMO_RESTRICTED_DETAIL = "demo_mode_restricted"

_PARAM_RE = re.compile(r"\{[^}]+\}")

# Route patterns blocked in demo mode.
# Path parameters like {name} become single-segment regex wildcards.
# Paths are relative to the /api prefix (added by _compile_blocklist).
_BLOCKED_ROUTES: list[tuple[str, str]] = [
    # Extension CRUD (skills, commands, subagents, hooks)
    ("POST", "/extensions/skills"),
    ("POST", "/extensions/commands"),
    ("POST", "/extensions/subagents"),
    ("POST", "/extensions/hooks"),
    ("PUT", "/extensions/skills/{name}"),
    ("PUT", "/extensions/commands/{name}"),
    ("PUT", "/extensions/subagents/{name}"),
    ("PUT", "/extensions/hooks/{name}"),
    ("DELETE", "/extensions/skills/{name}"),
    ("DELETE", "/extensions/commands/{name}"),
    ("DELETE", "/extensions/subagents/{name}"),
    ("DELETE", "/extensions/hooks/{name}"),
    # Import from agent
    ("POST", "/extensions/skills/import/{agent}"),
    ("POST", "/extensions/commands/import/{agent}"),
    ("POST", "/extensions/subagents/import/{agent}"),
    ("POST", "/extensions/hooks/import/{agent}"),
    # Sync / unsync to agent platforms
    ("POST", "/extensions/skills/{name}/agents"),
    ("POST", "/extensions/commands/{name}/agents"),
    ("POST", "/extensions/subagents/{name}/agents"),
    ("POST", "/extensions/hooks/{name}/agents"),
    ("DELETE", "/extensions/skills/{name}/agents/{agent}"),
    ("DELETE", "/extensions/commands/{name}/agents/{agent}"),
    ("DELETE", "/extensions/subagents/{name}/agents/{agent}"),
    ("DELETE", "/extensions/hooks/{name}/agents/{agent}"),
    # Catalog install
    ("POST", "/extensions/catalog/{item_id}/install"),
    # LLM config
    ("POST", "/llm/configure"),
    # Shares
    ("POST", "/shares"),
    ("DELETE", "/shares/{session_id}"),
    # Analysis run
    ("POST", "/analysis/friction"),
    ("POST", "/creation"),
    ("POST", "/evolution"),
    ("POST", "/recommendation"),
    # Analysis delete
    ("DELETE", "/analysis/friction/{analysis_id}"),
    ("DELETE", "/creation/{analysis_id}"),
    ("DELETE", "/evolution/{analysis_id}"),
    ("DELETE", "/recommendation/{analysis_id}"),
    # Job cancel
    ("POST", "/analysis/friction/jobs/{job_id}/cancel"),
    ("POST", "/creation/jobs/{job_id}/cancel"),
    ("POST", "/evolution/jobs/{job_id}/cancel"),
    ("POST", "/recommendation/jobs/{job_id}/cancel"),
]


def _compile_blocklist(
    routes: list[tuple[str, str]], prefix: str = "/api"
) -> list[tuple[str, re.Pattern[str]]]:
    """Compile route patterns into (method, regex) pairs.

    Replaces ``{param}`` placeholders with a single-segment wildcard
    BEFORE escaping literal characters, so braces are not escaped.

    Args:
        routes: List of (HTTP_METHOD, path_pattern) tuples.
        prefix: URL prefix prepended to each pattern.

    Returns:
        Compiled list of (method, regex) pairs for matching.
    """
    compiled: list[tuple[str, re.Pattern[str]]] = []
    for method, path in routes:
        full = prefix + path
        # Split on {param}, escape literal segments, rejoin with wildcard
        parts = _PARAM_RE.split(full)
        param_count = len(_PARAM_RE.findall(full))
        escaped = [re.escape(p) for p in parts]
        regex_str = "[^/]+".join(escaped) if param_count else re.escape(full)
        compiled.append((method, re.compile(f"^{regex_str}$")))
    return compiled


_COMPILED_BLOCKLIST = _compile_blocklist(_BLOCKED_ROUTES)


def _is_blocked(method: str, path: str) -> bool:
    """Check if a request method+path matches any blocked route.

    Args:
        method: HTTP method (uppercase).
        path: Request URL path.

    Returns:
        True if the route is blocked in demo mode.
    """
    for blocked_method, pattern in _COMPILED_BLOCKLIST:
        if method == blocked_method and pattern.match(path):
            return True
    return False


class DemoGuardMiddleware(BaseHTTPMiddleware):
    """Middleware that blocks state-mutating routes in demo mode."""

    async def dispatch(self, request: Request, call_next):
        """Intercept blocked routes and return 403."""
        if _is_blocked(request.method, request.url.path):
            return JSONResponse(status_code=403, content={"detail": DEMO_RESTRICTED_DETAIL})
        return await call_next(request)
