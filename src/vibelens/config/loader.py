"""YAML config file auto-discovery."""

import os
from pathlib import Path

from vibelens.utils.log import get_logger

logger = get_logger(__name__)

# Env var pointing to the YAML config file path
CONFIG_ENV_VAR = "VIBELENS_CONFIG"
# Config file names auto-discovered in the working directory
DEFAULT_CONFIG_NAMES = ["vibelens.yaml", "vibelens.yml"]


def discover_config_path() -> Path | None:
    """Auto-discover a YAML config file.

    Checks (in order):
        1. ``VIBELENS_CONFIG`` environment variable
        2. ``vibelens.yaml`` or ``vibelens.yml`` in the current directory

    Returns:
        Path to the config file, or None if not found.
    """
    env_value = os.environ.get(CONFIG_ENV_VAR)
    if env_value:
        path = Path(env_value)
        if path.exists():
            return path
        logger.warning("%s points to missing file: %s", CONFIG_ENV_VAR, path)
        return None

    for name in DEFAULT_CONFIG_NAMES:
        path = Path(name)
        if path.exists():
            return path

    return None
