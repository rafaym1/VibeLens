"""Tests for model restructuring — verifies new models and moved imports."""

from vibelens.models.enums import ElementType


class TestElementType:
    """Verify ElementType enum added to enums.py."""

    def test_element_type_values(self):
        assert ElementType.SKILL == "skill"
        assert ElementType.SUBAGENT == "subagent"
        assert ElementType.COMMAND == "command"
        assert ElementType.HOOK == "hook"

    def test_element_type_is_str(self):
        assert isinstance(ElementType.SKILL, str)

    def test_element_type_membership(self):
        assert len(ElementType) == 4
