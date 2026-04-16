"""Central catalog of agent-CLI backend models.

Single source of truth for which model names each CLI backend supports
and which one to default to when the user has not configured one. The
per-backend modules (claude, codex, gemini, ...) all look up their lists
here instead of duplicating constants.

This intentionally answers a different question than ``llm/pricing.py``:
catalog = "which models does this CLI support?", pricing = "how much
does each model cost?".

Lists were verified against each tool's official docs and GitHub repo as
of April 2026; bump them whenever a vendor ships a new generation.
"""

from vibelens.models.llm.inference import BackendType

# Per-backend (available models, default model) pairs.
# Models are ordered cheapest-first; ``default`` is the cheapest model
# the catalog recommends when no model is explicitly configured.
AGENT_MODEL_CATALOG: dict[BackendType, tuple[list[str], str | None]] = {
    BackendType.CLAUDE_CODE: (
        [
            "claude-haiku-4-5",
            "claude-sonnet-4-5",
            "claude-sonnet-4-6",
            "claude-opus-4-5",
            "claude-opus-4-6",
            "claude-opus-4-7",
        ],
        "claude-haiku-4-5",
    ),
    BackendType.CODEX: (
        [
            "gpt-5.4-mini",
            "gpt-5.3-codex",
            "gpt-5.2",
            "gpt-5.4",
        ],
        "gpt-5.4-mini",
    ),
    BackendType.GEMINI: (
        [
            "gemini-2.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-3-flash-preview",
            "gemini-3.1-pro-preview",
        ],
        "gemini-2.5-flash-lite",
    ),
    BackendType.CURSOR: (
        [
            "auto",
            "composer-2",
            "composer-1.5",
            "sonnet-4.6",
            "sonnet-4.6-thinking",
            "opus-4.6",
            "gpt-5.3-codex",
            "gemini-3-flash",
            "gemini-3-pro",
            "grok",
        ],
        "auto",
    ),
    BackendType.AIDER: (
        [
            "gemini/gemini-2.5-flash-lite",
            "gemini/gemini-flash-latest",
            "deepseek/deepseek-chat",
            "deepseek/deepseek-reasoner",
            "gpt-5-mini",
            "claude-haiku-4-5",
            "claude-sonnet-4-6",
            "openai/gpt-5",
            "claude-opus-4-6",
            "gemini/gemini-3.1-pro-preview",
        ],
        "gemini/gemini-2.5-flash-lite",
    ),
    BackendType.OPENCODE: (
        [
            "google/gemini-2.5-flash",
            "deepseek/deepseek-v3.2",
            "xai/grok-4-fast-non-reasoning",
            "openai/gpt-5-mini",
            "anthropic/claude-haiku-4-5-20251001",
            "google/gemini-2.5-pro",
            "openai/gpt-5",
            "anthropic/claude-sonnet-4-5-20250929",
            "anthropic/claude-opus-4-5-20251101",
            "google/gemini-3-pro-preview",
        ],
        "google/gemini-2.5-flash",
    ),
    BackendType.OPENCLAW: (
        [
            "openai/gpt-4o-mini",
            "anthropic/claude-haiku-4-5",
            "moonshot/kimi-k2.5",
            "google/gemini-3-flash-preview",
            "anthropic/claude-sonnet-4-6",
            "openai/gpt-5.4",
            "google/gemini-3.1-pro-preview",
            "anthropic/claude-opus-4-6",
            "xai/grok-4",
        ],
        "openai/gpt-4o-mini",
    ),
    BackendType.KIMI: (
        [
            "kimi-k2.5",
            "kimi-k2-0905-preview",
            "kimi-k2-thinking",
            "kimi-k2-turbo-preview",
            "kimi-k2-thinking-turbo",
        ],
        "kimi-k2.5",
    ),
    # Amp routes between frontier models internally based on its three
    # modes (smart / rush / deep) and exposes no --model flag.
    BackendType.AMP: ([], None),
}


def available_models(backend: BackendType) -> list[str]:
    """Return the list of model names supported by ``backend``.

    Args:
        backend: Backend identifier to look up.

    Returns:
        Model names in cheapest-first order, or an empty list if the
        backend is not in the catalog.
    """
    entry = AGENT_MODEL_CATALOG.get(backend)
    return entry[0] if entry else []


def default_model(backend: BackendType) -> str | None:
    """Return the default (cheapest recommended) model for ``backend``.

    Args:
        backend: Backend identifier to look up.

    Returns:
        Default model name, or None if the backend has no recommended
        default (e.g. Amp exposes no published model list).
    """
    entry = AGENT_MODEL_CATALOG.get(backend)
    return entry[1] if entry else None
