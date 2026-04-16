"""Skill store — CRUD on a directory of SKILL.md folders.

Directory layout:
    <root>/
    ├── my-skill/
    │   ├── SKILL.md         (YAML frontmatter + markdown body)
    │   ├── scripts/         (optional)
    │   └── references/      (optional)
    └── another-skill/
        └── SKILL.md
"""

import hashlib
import shutil
from pathlib import Path

import yaml

from vibelens.models.extension.skill import VALID_SKILL_NAME, Skill
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

SKILL_FILENAME = "SKILL.md"
FRONTMATTER_DELIMITER = "---"


class SkillStore:
    """CRUD on a single directory of skill subdirectories.

    Each skill lives in a subdirectory named after the skill (kebab-case)
    and contains a SKILL.md file with YAML frontmatter.
    """

    def __init__(self, root: Path, *, create: bool = False) -> None:
        """Initialize a skill store.

        Args:
            root: Directory containing skill subdirectories.
            create: If True, create root dir on init (for central store).
        """
        self._root = root.expanduser().resolve()
        if create:
            self._root.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        """Root directory for this store."""
        return self._root

    def list_names(self) -> list[str]:
        """Return sorted list of valid skill directory names."""
        if not self._root.is_dir():
            return []
        return sorted(
            entry.name
            for entry in self._root.iterdir()
            if entry.is_dir()
            and VALID_SKILL_NAME.match(entry.name)
            and (entry / SKILL_FILENAME).is_file()
        )

    def exists(self, name: str) -> bool:
        """Check if a skill exists in this store."""
        return (self._root / name / SKILL_FILENAME).is_file()

    def read(self, name: str) -> Skill | None:
        """Read and parse a skill. Returns None if not found."""
        raw = self.read_raw(name)
        if raw is None:
            return None
        return parse_skill_md(name, raw)

    def read_raw(self, name: str) -> str | None:
        """Read raw SKILL.md text. Returns None if not found."""
        skill_file = self._root / name / SKILL_FILENAME
        if not skill_file.is_file():
            return None
        try:
            return skill_file.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", skill_file, exc)
            return None

    def write(self, name: str, content: str) -> Path:
        """Write skill content to {name}/SKILL.md.

        Args:
            name: Kebab-case skill name.
            content: Full SKILL.md content.

        Returns:
            Path to the written SKILL.md file.

        Raises:
            ValueError: If name is not valid kebab-case.
        """
        if not VALID_SKILL_NAME.match(name):
            raise ValueError(f"Skill name must be kebab-case: {name!r}")

        skill_dir = self._root / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / SKILL_FILENAME
        skill_file.write_text(content.rstrip() + "\n", encoding="utf-8")
        return skill_file

    def delete(self, name: str) -> bool:
        """Remove a skill directory entirely. Returns True if deleted."""
        skill_dir = self._root / name
        if not skill_dir.is_dir():
            return False
        shutil.rmtree(skill_dir)
        return True

    def copy_from(self, source: "SkillStore", name: str) -> bool:
        """Copy a skill directory from another store.

        Args:
            source: Store to copy from.
            name: Skill name to copy.

        Returns:
            True if copied, False if source skill not found.
        """
        source_dir = source.root / name
        if not (source_dir / SKILL_FILENAME).is_file():
            return False

        target_dir = self._root / name
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(source_dir, target_dir)
        return True


def parse_frontmatter(text: str) -> dict:
    """Extract YAML frontmatter from SKILL.md text.

    Returns empty dict if no valid frontmatter found.
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != FRONTMATTER_DELIMITER:
        return {}

    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == FRONTMATTER_DELIMITER:
            end_idx = i
            break

    if end_idx is None:
        return {}

    yaml_text = "\n".join(lines[1:end_idx])
    try:
        parsed = yaml.safe_load(yaml_text)
        return parsed if isinstance(parsed, dict) else {}
    except yaml.YAMLError as exc:
        logger.warning("Failed to parse YAML frontmatter: %s", exc)
        return {}


def extract_body(text: str) -> str:
    """Extract markdown body after YAML frontmatter."""
    if not text.startswith(FRONTMATTER_DELIMITER):
        return text
    end_idx = text.find(FRONTMATTER_DELIMITER, len(FRONTMATTER_DELIMITER))
    if end_idx < 0:
        return text
    return text[end_idx + len(FRONTMATTER_DELIMITER) :].lstrip("\n")


def parse_skill_md(name: str, text: str) -> Skill:
    """Parse raw SKILL.md text into a Skill model.

    Args:
        name: Skill directory name.
        text: Full SKILL.md content.

    Returns:
        Parsed Skill with metadata from frontmatter.
    """
    frontmatter = parse_frontmatter(text)
    description = str(frontmatter.pop("description", ""))
    tags = frontmatter.pop("tags", [])
    if not isinstance(tags, list):
        tags = []
    tags = [str(t).strip() for t in tags if str(t).strip()]

    raw_tools = frontmatter.pop("allowed-tools", None)
    allowed_tools = _parse_allowed_tools(raw_tools)

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    return Skill(
        name=name,
        description=description,
        tags=tags,
        allowed_tools=allowed_tools,
        content_hash=content_hash,
    )


def _parse_allowed_tools(raw: str | list | None) -> list[str]:
    """Normalize allowed-tools from frontmatter into a list."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(t).strip() for t in raw if str(t).strip()]
    return [t.strip() for t in str(raw).split(",") if t.strip()]
