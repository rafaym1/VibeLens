"""Tests for the single-file tree URL heuristic in utils.github."""

import pytest

from vibelens.utils.github import is_github_single_file_tree


@pytest.mark.parametrize(
    "url,expected",
    [
        # tree URLs pointing at a known-extension file -> True
        (
            "https://github.com/a/b/tree/main/.kiro/agents/security-reviewer.md",
            True,
        ),
        ("https://github.com/a/b/tree/main/skills/demo/SKILL.md", True),
        ("https://github.com/a/b/tree/main/plugins/config.json", True),
        ("https://github.com/a/b/tree/main/scripts/run.sh", True),
        ("https://github.com/a/b/tree/main/pkg/main.py", True),
        # tree URLs pointing at directories -> False
        ("https://github.com/a/b/tree/main/skills/my-skill", False),
        ("https://github.com/a/b/tree/main/plugins/my.plugin", False),
        ("https://github.com/a/b/tree/main/packages/v1.2.3", False),
        ("https://github.com/a/b/tree/main", False),
        # Non-tree URLs -> False
        ("https://github.com/a/b/blob/main/agents/x.md", False),
        ("https://example.com/nope", False),
    ],
)
def test_is_github_single_file_tree(url: str, expected: bool) -> None:
    assert is_github_single_file_tree(url) is expected
