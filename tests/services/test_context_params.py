"""Tests for context parameter presets."""
from vibelens.services.context_params import (
    PRESET_CONCISE,
    PRESET_RECOMMENDATION,
)


def test_preset_recommendation_exists():
    """PRESET_RECOMMENDATION is importable and has correct values."""
    assert PRESET_RECOMMENDATION.user_prompt_max_chars == 500
    assert PRESET_RECOMMENDATION.agent_message_max_chars == 0
    assert PRESET_RECOMMENDATION.bash_command_max_chars == 0
    assert PRESET_RECOMMENDATION.tool_arg_max_chars == 0
    assert PRESET_RECOMMENDATION.include_non_error_obs is False
    assert PRESET_RECOMMENDATION.observation_max_chars == 0
    assert PRESET_RECOMMENDATION.shorten_home_prefix is True
    assert PRESET_RECOMMENDATION.path_max_segments == 2


def test_preset_recommendation_more_aggressive_than_concise():
    """PRESET_RECOMMENDATION is more aggressive compression than PRESET_CONCISE."""
    assert PRESET_RECOMMENDATION.user_prompt_max_chars < PRESET_CONCISE.user_prompt_max_chars
    assert PRESET_RECOMMENDATION.agent_message_max_chars < PRESET_CONCISE.agent_message_max_chars
