# CLAUDE.md — VibeLens

Agent session visualization and personalization platform.

## Key Concepts

- **Trajectory**: Root container for a single agent session — includes steps, agent metadata, final metrics, and cross-references.
- **Step**: One turn in a conversation (user prompt, agent response, or system message) with optional tool calls and observations.

## Frontend Conventions (React + Vite + Tailwind)

Refer to `DESIGN.md`

## Testing

The full suite takes ~2m45s. Run only what you need:

- **Default during edits:** target the test file(s) that exercise the code you changed. `uv run pytest tests/<path>/<file>.py -v -s`.
- **Multi-file change:** run the test directory matching the area, e.g. `uv run pytest tests/storage/ tests/ingest/`.
- **Big change** (touching ≥3 areas, refactoring shared code, or changing public API): run the whole suite once at the end. `uv run pytest tests/`.
- **Always before commit:** `uv run ruff check src/ tests/`. Cheap.

Conventions:

- Tests should log detailed output with `print()` for manual verification, not just assertions.
- Use `-s` to see print output when iterating.

## Release

See [`docs/release.md`](docs/release.md) for the full release flow. Short version:

1. **Version bump**: Update `version` in both `pyproject.toml` and `src/vibelens/__init__.py` (must match).
2. **Changelog**: Move `[Unreleased]` entries into a new `## [x.y.z] - YYYY-MM-DD` section.
3. **Frontend** (if changed): `cd frontend && npm run build && cd ..`.
4. **Verify**: `uv build && uv run ruff check src/ tests/ && uv run pytest tests/ -v`.
5. **Commit, tag, push**: `git commit -am "Release vX.Y.Z" && git tag vX.Y.Z && git push origin main --tags`.
6. **GitHub Release**: `gh release create vX.Y.Z --title "vX.Y.Z" --notes "..."`.
7. **PyPI**: automated by `.github/workflows/publish.yml` on tag push (trusted publishing). No twine, no API token.
