# Installing VibeLens

This guide covers every supported install method, a per-platform walkthrough, and the errors people most often hit. For the short version, see the [README Quick Start](../README.md#quick-start).

## Contents

- [Choosing an install method](#choosing-an-install-method)
- [Per-platform walkthrough](#per-platform-walkthrough)
  - [macOS](#macos)
  - [Windows](#windows)
  - [Linux](#linux)
- [Installing Python](#installing-python)
- [Install methods in detail](#install-methods-in-detail)
- [Troubleshooting](#troubleshooting)
- [Uninstalling](#uninstalling)

## Choosing an install method

| Method | Good for | Prerequisites |
|--------|----------|---------------|
| `install.sh` / `install.ps1` one-liner | First-time users, fresh machines | none (script bootstraps [uv](https://docs.astral.sh/uv/)) |
| `uvx vibelens serve` | One-off runs, ephemeral environments | [uv](https://docs.astral.sh/uv/) on PATH |
| `pip install vibelens` | You already manage Python | Python 3.10+ and `pip` |
| `pipx install vibelens` | Modern macOS/Linux where `pip` is locked | [pipx](https://pipx.pypa.io/) |
| `npx @chats-lab/vibelens serve` | You live in the npm ecosystem already | Node.js 16+ **and** Python 3.10+ with `pip install vibelens` |
| Developer setup (`uv sync`) | Contributing to VibeLens | Git, uv |

If you are not sure, use the one-liner. It handles Python for you and leaves nothing behind in system directories.

## Per-platform walkthrough

### macOS

1. Open **Terminal**: press `Cmd+Space`, type `Terminal`, press Enter.
2. Paste the install command and press Enter:
   ```bash
   curl -LsSf https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.sh | sh
   ```
3. When the script finishes, your default browser should open at `http://localhost:12001`. If it does not, click the link printed in the terminal.

Older macOS (before 11 Big Sur) is not officially supported by uv. See [SSL certificate errors](#ssl-certificate-errors) if the download fails on legacy versions.

### Windows

1. Open **PowerShell**: press the Windows key, type `PowerShell`, press Enter. (PowerShell 5.1 that ships with Windows 10+ is fine; PowerShell 7 also works.)
2. Paste the install command and press Enter:
   ```powershell
   irm https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.ps1 | iex
   ```
3. The script installs uv, runs VibeLens, and opens your browser.

If your organization restricts script execution, see [PowerShell execution policy](#powershell-execution-policy).

### Linux

1. Open a terminal (GNOME / Ubuntu: `Ctrl+Alt+T`).
2. Paste:
   ```bash
   curl -LsSf https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.sh | sh
   ```
3. The script installs uv into `~/.local/bin`, fetches VibeLens, and starts it. If `~/.local/bin` isn't on your shell's `PATH`, open a new terminal or run `source ~/.local/bin/env` (or the equivalent for your uv version).

## Installing Python

You only need this if you want to use `pip` or `pipx` directly. The one-liner does not need Python installed.

### macOS

```bash
# Homebrew (recommended)
brew install python@3.12
```

If `brew` itself is missing, install it first from [brew.sh](https://brew.sh/), or use the one-liner and skip Python altogether.

### Windows

Use the Microsoft Store or winget:

```powershell
winget install Python.Python.3.12
```

Or download an installer from [python.org/downloads](https://www.python.org/downloads/). During install, check **Add python.exe to PATH**.

### Linux

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install python3 python3-pip python3-venv

# Fedora
sudo dnf install python3 python3-pip

# Arch
sudo pacman -S python python-pip
```

## Install methods in detail

### One-liner install script

- `install.sh` (macOS/Linux) and `install.ps1` (Windows) live at the repo root. Both detect an existing `uv`, install it via the official [astral.sh](https://astral.sh/) installer if missing, then run `uvx vibelens serve`.
- Idempotent: re-running skips the uv install step.
- No `sudo`. uv installs to `~/.local/bin` on Unix or `%USERPROFILE%\.local\bin` on Windows.

### uv / uvx

[uv](https://docs.astral.sh/uv/) is a single-binary Python toolchain manager. `uvx` fetches a package into an isolated environment and runs it.

```bash
uvx vibelens serve
```

Upgrade at any time with `uv tool upgrade vibelens` (after `uv tool install vibelens` if you want a persistent install).

### pip

```bash
pip install vibelens
vibelens serve
```

On modern macOS and Debian-derived systems you may hit [`externally-managed-environment`](#externally-managed-environment). Use `pipx` or the one-liner in that case.

### pipx

```bash
pipx install vibelens
vibelens serve
```

pipx installs each CLI into its own venv, which avoids the managed-environment restriction. Install pipx with `brew install pipx` (macOS) or `sudo apt install pipx` (Ubuntu 23.04+).

### npm wrapper

```bash
npx @chats-lab/vibelens serve
```

The npm package is a thin wrapper that shells out to your system Python, which must already have `vibelens` installed. If you prefer npm ergonomics but the wrapper errors out, use `uvx vibelens serve` directly.

### Homebrew

Not yet published. Watch the [repo](https://github.com/CHATS-lab/VibeLens) for updates.

### Docker

Not yet published. If you want a containerized run, use the [developer setup](../README.md#developer-setup) inside a Python base image.

## Troubleshooting

### `command not found: pip`

Python is not installed, or it's installed but not on your `PATH`.

- Easiest fix: use the [one-liner](../README.md#one-liner-recommended); it does not need Python or pip.
- If you want pip: install Python first (see [Installing Python](#installing-python)), then run `python3 -m pip install vibelens`.

### `externally-managed-environment`

Starting with macOS Homebrew Python and Debian 12+, the system Python blocks global `pip install`. The error reads:

```
error: externally-managed-environment
× This environment is externally managed
```

Pick one:

- Use the [one-liner](../README.md#one-liner-recommended).
- Install via pipx: `pipx install vibelens`.
- Create a virtualenv: `python3 -m venv ~/.vibelens-env && ~/.vibelens-env/bin/pip install vibelens && ~/.vibelens-env/bin/vibelens serve`.

### SSL certificate errors

```
SSL: CERTIFICATE_VERIFY_FAILED
```

Most often seen on older macOS. On Python.org installers, run the bundled `Install Certificates.command` once. On Homebrew Python, `brew install ca-certificates` and reinstall Python.

### Corporate proxy / firewall

`pip install` behind a proxy:

```bash
pip install --proxy http://user:pass@proxy.corp:8080 vibelens
```

uv honors `HTTPS_PROXY` and `HTTP_PROXY`. If your proxy intercepts TLS, set `UV_NATIVE_TLS=1` and import your corporate certificate into the system trust store.

### Port already in use

```
OSError: [Errno 48] Address already in use
```

Another process owns port 12001. Start on a different port:

```bash
vibelens serve --port 8080
```

Or stop the conflicting process: `lsof -i :12001` on macOS/Linux, `Get-NetTCPConnection -LocalPort 12001` on Windows.

### `ModuleNotFoundError: No module named 'vibelens'`

You installed into a different Python than the one your shell invokes. Find the interpreter that has it:

```bash
python3 -m pip show vibelens
```

Then run `python3 -m vibelens serve`, or re-install with the interpreter you actually use.

### Windows `py` vs `python`

On Windows, `py` is the launcher that picks the latest installed Python. `python` may point to a Microsoft Store stub that prompts to install Python. Prefer `py -3` or install Python with **Add to PATH** checked.

### `npx` hangs or uses stale cache

`npx` caches packages. Force a fresh fetch:

```bash
npx --ignore-existing @chats-lab/vibelens serve
```

If that still hangs, try the one-liner instead.

### PowerShell execution policy

```
cannot be loaded because running scripts is disabled on this system
```

Temporarily allow the install command in the current session only:

```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
irm https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.ps1 | iex
```

If your organization locks this down entirely, install uv manually from [docs.astral.sh/uv](https://docs.astral.sh/uv/), then run `uvx vibelens serve`.

### Blank page or 404 after the browser opens

- Refresh the tab. The browser sometimes opens before the server is fully ready.
- Check the terminal for errors. Look for a line like `VibeLens running at http://...`.
- Confirm the port. If you passed `--port 8080`, visit that port.

### No sessions found

VibeLens looks here by default:

- `~/.claude/projects/` (Claude Code)
- `~/.codex/sessions/` (Codex CLI)
- `~/.gemini/tmp/` (Gemini CLI)
- `~/.openclaw/agents/` (OpenClaw)

If your logs live elsewhere, either symlink them into one of those paths or use the **Upload** tab in the app to drag in a ZIP.

### LLM-gated features

These features require a language-model API key:

- **Productivity Tips**
- **Personalization** (skill retrieval, creation, evolution)
- `vibelens recommend` CLI

Everything else, including session visualization and dashboard analytics, works without a key. To configure a key, open the app and go to **Settings**, or edit `~/.vibelens/config.yaml`.

## Uninstalling

```bash
# pip
pip uninstall vibelens

# pipx
pipx uninstall vibelens

# uv tool
uv tool uninstall vibelens

# npm (global)
npm uninstall -g @chats-lab/vibelens

# Remove cached state
rm -rf ~/.vibelens/
```

uv itself can be removed by deleting `~/.local/bin/uv` and `~/.local/bin/uvx` on Unix, or `%USERPROFILE%\.local\bin\uv.exe` and `%USERPROFILE%\.local\bin\uvx.exe` on Windows.

Still stuck? Open an issue at [github.com/CHATS-lab/VibeLens/issues](https://github.com/CHATS-lab/VibeLens/issues) with the command you ran and the full error output.
