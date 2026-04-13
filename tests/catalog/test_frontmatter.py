"""Tests for YAML frontmatter parser."""
from vibelens.catalog.frontmatter import extract_tags, parse_frontmatter


def test_parse_standard_frontmatter():
    """Parse standard YAML frontmatter with body."""
    text = """---
name: test-skill
description: A test skill
category: testing
---
# Test Skill

Body content here.
"""
    meta, body = parse_frontmatter(text)
    assert meta["name"] == "test-skill"
    assert meta["description"] == "A test skill"
    assert meta["category"] == "testing"
    assert "Body content here." in body
    print(f"Parsed meta keys: {list(meta.keys())}, body length: {len(body)}")


def test_parse_no_frontmatter():
    """Return empty dict for files without frontmatter."""
    text = "# Just markdown\n\nNo frontmatter."
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert "Just markdown" in body
    print(f"No frontmatter: meta={meta}, body[:30]={body[:30]}")


def test_parse_empty_frontmatter():
    """Handle empty frontmatter block."""
    text = "---\n---\nBody only."
    meta, body = parse_frontmatter(text)
    assert meta == {}
    assert "Body only." in body
    print(f"Empty frontmatter: meta={meta}")


def test_parse_multiline_description():
    """Handle multi-line description in frontmatter."""
    text = '''---
name: agent-name
description: "Use this agent when you need to design,
  optimize, and test prompts for LLMs."
tools: Read, Write, Edit
model: sonnet
---
Content body.
'''
    meta, body = parse_frontmatter(text)
    assert meta["name"] == "agent-name"
    assert "optimize" in meta["description"]
    assert meta["tools"] == "Read, Write, Edit"
    assert meta["model"] == "sonnet"
    print(f"Multiline desc: {meta['description'][:60]}...")


def test_parse_command_format():
    """Parse command-style frontmatter with allowed-tools."""
    text = """---
allowed-tools: Read, Write, Edit, Bash
argument-hint: [migration-type] | --create
description: Generate database migrations
---
# Command content
"""
    meta, body = parse_frontmatter(text)
    assert meta["allowed-tools"] == "Read, Write, Edit, Bash"
    assert meta["description"] == "Generate database migrations"
    print(f"Command meta: {meta}")


def test_parse_dashes_in_value():
    """Closing delimiter must be on its own line, not inside a value."""
    text = "---\ndescription: Use --- to separate sections\n---\nBody here."
    meta, body = parse_frontmatter(text)
    assert meta["description"] == "Use --- to separate sections"
    assert "Body here." in body
    print(f"Dashes in value: meta={meta}")


def test_extract_tags_with_category():
    """Extract category as a tag."""
    tags = extract_tags({"category": "testing", "name": "foo"})
    assert tags == ["testing"]
    print(f"Category tags: {tags}")


def test_extract_tags_with_list_keywords():
    """Extract list-style keywords with dedup."""
    tags = extract_tags({"category": "dev", "keywords": ["dev", "python", "cli"]})
    assert tags == ["dev", "python", "cli"]
    print(f"List keyword tags: {tags}")


def test_extract_tags_with_comma_string():
    """Extract comma-separated keyword string."""
    tags = extract_tags({"tags": "api, testing, web"})
    assert tags == ["api", "testing", "web"]
    print(f"Comma string tags: {tags}")


def test_extract_tags_empty():
    """Return empty list when no tag fields present."""
    tags = extract_tags({"name": "foo"})
    assert tags == []
    print(f"Empty tags: {tags}")
