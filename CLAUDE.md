# CLAUDE.md — VibeLens

Agent session visualization and personalization platform.

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

Canonical flow: [`docs/release.md`](docs/release.md). User-facing entry points: [`README.md`](README.md) (PyPI badge, [CHANGELOG](CHANGELOG.md) link).

Quick-reference for executing a release:

1. **Version bump** — update `version` in `pyproject.toml` and `__version__` in `src/vibelens/__init__.py`. They must match.
2. **CHANGELOG** — promote `[Unreleased]` entries into a new `## [X.Y.Z] - YYYY-MM-DD` section. Keep the `[Unreleased]` heading empty for the next cycle.
3. **Catalog** (only if `agent-tool-hub` output is newer): `uv run python scripts/build_catalog.py --hub-output <path> --out src/vibelens/data/catalog`. Commit the regenerated `src/vibelens/data/catalog/`.
4. **Frontend** (only if `frontend/src/` changed): `cd frontend && npm run build && cd ..`. Commit `src/vibelens/static/`.
5. **Verify**: `uv run ruff check src/ tests/ && uv run pytest tests/ && uv build`.
6. **Tag and push**: `git commit -am "Release vX.Y.Z" && git tag vX.Y.Z && git push origin main --tags`. Trusted publishing on PyPI (`.github/workflows/publish.yml`) takes over from the tag push — no token, no `twine`.
7. **GitHub Release** (use the CHANGELOG entry as the body): `gh release create vX.Y.Z --title "vX.Y.Z" --notes "$(...)"`.
