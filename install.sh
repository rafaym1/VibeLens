#!/usr/bin/env sh
#
# VibeLens installer for macOS and Linux.
#
# What it does:
#   1. Checks whether `uv` is already on PATH.
#   2. If not, installs uv from https://astral.sh/uv/install.sh into ~/.local/bin.
#   3. Sources uv's env file so `uv` is usable in this same shell.
#   4. Runs `uvx vibelens serve`, which fetches VibeLens on first run and starts it.
#
# Safety:
#   - No sudo. uv installs to the user's home directory.
#   - Idempotent. Re-running skips the uv install step when uv is already present.
#   - Fails loudly with a pointer to manual install instructions if any step errors.
#
# Usage:
#   curl -LsSf https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.sh | sh

set -eu

UV_INSTALL_URL="https://astral.sh/uv/install.sh"
INSTALL_DOC_URL="https://github.com/CHATS-lab/VibeLens/blob/main/docs/INSTALL.md"

info() {
  printf '%s\n' "$1"
}

fail() {
  printf 'VibeLens install failed: %s\n' "$1" >&2
  printf 'For manual install steps, see: %s\n' "$INSTALL_DOC_URL" >&2
  exit 1
}

# Try to expose uv installed to ~/.local/bin (or ~/.cargo/bin on older uv versions)
# without requiring the user to open a new shell.
source_uv_env() {
  for candidate in \
    "${HOME}/.local/bin/env" \
    "${HOME}/.cargo/env"
  do
    if [ -f "$candidate" ]; then
      # shellcheck disable=SC1090
      . "$candidate"
      return 0
    fi
  done
  # Fall back to prepending the typical install dir to PATH for this session.
  if [ -d "${HOME}/.local/bin" ]; then
    PATH="${HOME}/.local/bin:${PATH}"
    export PATH
  fi
}

# Step 1: detect existing uv.
info "[1/3] Checking for uv..."
if command -v uv >/dev/null 2>&1; then
  info "      uv is already installed at $(command -v uv)."
  INSTALL_UV=0
else
  info "      uv not found. Will install."
  INSTALL_UV=1
fi

# Step 2: install uv if needed.
if [ "$INSTALL_UV" -eq 1 ]; then
  info "[2/3] Installing uv from ${UV_INSTALL_URL}..."
  if ! command -v curl >/dev/null 2>&1; then
    fail "curl is required but not installed. Install curl, or install uv manually from https://docs.astral.sh/uv/."
  fi
  tmp_installer="$(mktemp)"
  if ! curl -LsSf "$UV_INSTALL_URL" -o "$tmp_installer"; then
    rm -f "$tmp_installer"
    fail "Could not download uv installer from ${UV_INSTALL_URL}. Check your network, or install uv manually."
  fi
  if ! sh "$tmp_installer"; then
    rm -f "$tmp_installer"
    fail "uv installer exited with an error."
  fi
  rm -f "$tmp_installer"
  source_uv_env
  if ! command -v uv >/dev/null 2>&1; then
    fail "uv installed but is not on PATH. Open a new terminal and re-run this command, or add ~/.local/bin to PATH."
  fi
else
  info "[2/3] Skipping uv install."
fi

# Step 3: run VibeLens.
info "[3/3] Starting VibeLens (first run downloads the package; this can take ~30s)..."
exec uvx vibelens serve
