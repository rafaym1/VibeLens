"""Personalization-specific enumerations."""

from vibelens.utils.compat import StrEnum


class PersonalizationMode(StrEnum):
    """Personalization analysis mode."""

    CREATION = "creation"
    RETRIEVAL = "retrieval"
    EVOLUTION = "evolution"
    RECOMMENDATION = "recommendation"


class PersonalizationElementType(StrEnum):
    """File-based element types that can be created or evolved."""

    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
