"""LLM provider URL registry and utility functions.

Provider-specific helpers that don't belong in the config model itself.
The config model (InferenceConfig) lives in settings.py.
"""

from vibelens.config.settings import InferenceConfig

# Provider prefix → default base URL
PROVIDER_BASE_URLS: dict[str, str] = {
    "anthropic": "https://api.anthropic.com",
    "openai": "https://api.openai.com/v1",
    "google": "https://generativelanguage.googleapis.com/v1beta",
    "gemini": "https://generativelanguage.googleapis.com/v1beta",
    "openrouter": "https://openrouter.ai/api/v1",
    "mistral": "https://api.mistral.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com",
    "minimax": "https://api.minimax.chat/v1",
    "qwen": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "together": "https://api.together.xyz/v1",
    "fireworks": "https://api.fireworks.ai/inference/v1",
}

# Number of trailing characters shown when masking an API key for display
API_KEY_MASK_SUFFIX_LEN = 4
# Characters replacing the hidden portion of an API key
API_KEY_MASK = "***"


def resolve_base_url(config: InferenceConfig) -> str | None:
    """Resolve base URL from config or provider registry.

    If ``config.base_url`` is set, returns it. Otherwise extracts the
    provider prefix from the model name and looks up PROVIDER_BASE_URLS.

    Args:
        config: Inference configuration.

    Returns:
        Resolved base URL, or None if provider is unknown.
    """
    if config.base_url:
        return config.base_url

    provider = _extract_provider(config.model)
    if not provider:
        return None
    return PROVIDER_BASE_URLS.get(provider)


def mask_api_key(api_key: str) -> str:
    """Mask an API key for display, preserving the last 4 chars."""
    if not api_key or len(api_key) <= API_KEY_MASK_SUFFIX_LEN:
        return API_KEY_MASK
    return f"{API_KEY_MASK}{api_key[-API_KEY_MASK_SUFFIX_LEN:]}"


def _extract_provider(model: str) -> str | None:
    """Extract provider prefix from a litellm model name (e.g. 'anthropic/...' -> 'anthropic')."""
    if "/" not in model:
        return None
    return model.split("/", 1)[0].lower()
