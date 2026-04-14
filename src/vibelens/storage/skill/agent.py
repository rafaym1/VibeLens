"""Registry of third-party agent skill directories.

All supported agents use the same SKILL.md + YAML frontmatter format
and are instantiated as plain DiskSkillStore instances.

Registry:
    AGENT_SKILL_REGISTRY maps each SkillSourceType to its default
    skills directory path. Use create_agent_skill_stores() to
    instantiate stores for all agents installed on disk.
"""

from pathlib import Path

from vibelens.models.skill import SkillSource
from vibelens.storage.skill.disk import DiskSkillStore

# Maps each third-party agent to its default skills directory on macOS
AGENT_SKILL_REGISTRY: dict[SkillSource, Path] = {
    SkillSource.CURSOR: Path.home() / ".cursor" / "skills",
    SkillSource.OPENCODE: Path.home() / ".config" / "opencode" / "skills",
    SkillSource.ANTIGRAVITY: Path.home() / ".gemini" / "antigravity" / "global_skills",
    SkillSource.KIMI: Path.home() / ".config" / "agents" / "skills",
    SkillSource.OPENCLAW: Path.home() / ".openclaw" / "skills",
    SkillSource.OPENHANDS: Path.home() / ".openhands" / "skills",
    SkillSource.QWEN: Path.home() / ".qwen" / "skills",
    SkillSource.GEMINI: Path.home() / ".gemini" / "skills",
    SkillSource.COPILOT: Path.home() / ".copilot" / "skills",
}


def create_agent_skill_stores() -> list[DiskSkillStore]:
    """Instantiate stores for all registered third-party agents.

    Returns only stores whose skills directories exist on disk,
    so agents the user hasn't installed are silently skipped.
    """
    stores: list[DiskSkillStore] = []
    for source_type, skills_dir in AGENT_SKILL_REGISTRY.items():
        resolved = skills_dir.expanduser().resolve()
        if resolved.is_dir():
            stores.append(DiskSkillStore(resolved, source_type))
    return stores
