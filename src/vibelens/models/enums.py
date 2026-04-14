"""Enumeration types for VibeLens domain models."""

from vibelens.utils.compat import StrEnum


class AgentType(StrEnum):
    """Known agent CLI types.

    Includes both trajectory-parsed agents (claude_code, codex, gemini, dataclaw)
    and skill-only agents (cursor, opencode, etc.) that we scan for installed skills.
    """

    AIDER = "aider"
    ANTIGRAVITY = "antigravity"
    CLAUDE_CODE = "claude_code"
    CLAUDE_CODE_WEB = "claude_code_web"
    CODEX = "codex"
    COPILOT = "copilot"
    CURSOR = "cursor"
    DATACLAW = "dataclaw"
    GEMINI = "gemini"
    KIMI = "kimi"
    OPENCODE = "opencode"
    OPENCLAW = "openclaw"
    OPENHANDS = "openhands"
    PARSED = "parsed"
    QWEN_CODE = "qwen_code"


class StepSource(StrEnum):
    """Originator of a trajectory step (ATIF v1.6)."""

    SYSTEM = "system"
    USER = "user"
    AGENT = "agent"


class ContentType(StrEnum):
    """Content part type within a multimodal message (ATIF v1.6)."""

    TEXT = "text"
    IMAGE = "image"
    PDF = "pdf"


class AppMode(StrEnum):
    """Application operating mode."""

    SELF = "self"
    DEMO = "demo"
    TEST = "test"


class SessionPhase(StrEnum):
    """Semantic phase of a coding agent session."""

    EXPLORATION = "exploration"
    PLANNING = "planning"
    IMPLEMENTATION = "implementation"
    VERIFICATION = "verification"
    DEBUGGING = "debugging"
    MIXED = "mixed"


class ElementType(StrEnum):
    """File-based element types that can be created or evolved."""

    SKILL = "skill"
    SUBAGENT = "subagent"
    COMMAND = "command"
    HOOK = "hook"
