"""Application configuration package.

Provides YAML/JSON configuration with environment variable overrides.
Priority (highest to lowest): env vars > .env file > YAML > settings.json > defaults.
"""

from vibelens.config.loader import discover_config_path
from vibelens.config.settings import (
    SETTINGS_JSON_PATH,
    InferenceConfig,
    Settings,
    load_settings,
    save_inference_config,
)
from vibelens.llm.providers import mask_api_key, resolve_base_url

__all__ = [
    "InferenceConfig",
    "SETTINGS_JSON_PATH",
    "Settings",
    "discover_config_path",
    "load_settings",
    "mask_api_key",
    "resolve_base_url",
    "save_inference_config",
]
