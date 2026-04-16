# @chats-lab/vibelens

Agent trajectory analysis and visualization platform. Parses, normalizes, and visualizes conversation histories from Claude Code, Codex, Gemini CLI, and more.

## Install

```bash
npx @chats-lab/vibelens serve
```

Or install globally:

```bash
npm install -g @chats-lab/vibelens
vibelens serve
```

## Requirements

- **Python 3.10+** must be installed on your system
- The `vibelens` Python package: `pip install vibelens`

This npm package is a thin wrapper that detects your Python installation and delegates to the `vibelens` CLI. If Python or the `vibelens` package is missing, it will print install instructions.

If you don't want to manage Python at all, skip the npm wrapper and use [uv](https://docs.astral.sh/uv/): `uvx vibelens serve` handles Python automatically. Full install guide: [docs/INSTALL.md](https://github.com/CHATS-lab/VibeLens/blob/main/docs/INSTALL.md).

## Other install methods

| Method | Command |
|--------|---------|
| uv (no Python needed) | `uvx vibelens serve` |
| pip | `pip install vibelens` |
| pipx (macOS/Debian) | `pipx install vibelens` |
| Developer | `uv pip install -e ".[dev]"` |

## Links

- [Homepage](https://vibelens.chats-lab.org/)
- [GitHub](https://github.com/CHATS-lab/VibeLens)
- [PyPI](https://pypi.org/project/vibelens/)
