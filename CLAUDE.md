# CLAUDE.md — VibeLens

Agent session visualization and personalization platform.

## Key Concepts

- **Trajectory**: Root container for a single agent session — includes steps, agent metadata, final metrics, and cross-references.
- **Step**: One turn in a conversation (user prompt, agent response, or system message) with optional tool calls and observations.

## Frontend Conventions (React + Vite + Tailwind)

Refer to `DESIGN.md`

## Testing

- Ruff: `ruff check src/ tests/`
- Run: `pytest tests/ -v -s` (use `-s` to see print output).
- Tests should log detailed output with `print()` for manual verification, not just assertions.

## Release

1. **Version bump**: Update `version` in both `pyproject.toml` and `src/vibelens/__init__.py`.
2. **Changelog**: Add entry to `CHANGELOG.md` under `## [x.y.z] - YYYY-MM-DD`.
3. **Commit & push**: `git commit` then `git push origin main`.
4. **Tag**: `git tag v{version} {commit_sha}` then `git push origin v{version}`.
5. **GitHub Release**: `gh release create v{version} --title "v{version}" --latest --notes "..."`.
6. **PyPI**: `rm -rf dist/ && python -m build && twine upload dist/*`.
