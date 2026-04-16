# VibeLens installer for Windows (PowerShell 5.1+ / PowerShell 7+).
#
# What it does:
#   1. Checks whether `uv` is already on PATH.
#   2. If not, installs uv from https://astral.sh/uv/install.ps1 into the user's profile.
#   3. Refreshes PATH so `uv` is usable in this same PowerShell session.
#   4. Runs `uvx vibelens serve`, which fetches VibeLens on first run and starts it.
#
# Safety:
#   - No admin rights required. uv installs to $HOME\.local\bin.
#   - Idempotent. Re-running skips the uv install step when uv is already present.
#   - Fails loudly with a pointer to manual install instructions on any error.
#
# Usage:
#   irm https://raw.githubusercontent.com/CHATS-lab/VibeLens/main/install.ps1 | iex

$ErrorActionPreference = 'Stop'

$UvInstallUrl  = 'https://astral.sh/uv/install.ps1'
$InstallDocUrl = 'https://github.com/CHATS-lab/VibeLens/blob/main/docs/INSTALL.md'

function Write-Info([string]$Message) {
  Write-Host $Message
}

function Invoke-Fail([string]$Message) {
  Write-Host "VibeLens install failed: $Message" -ForegroundColor Red
  Write-Host "For manual install steps, see: $InstallDocUrl" -ForegroundColor Red
  exit 1
}

function Update-SessionPath {
  # uv installs to $HOME\.local\bin by default. Make sure that's on PATH for this session.
  $uvBin = Join-Path $HOME '.local\bin'
  if ((Test-Path $uvBin) -and ($env:Path -notlike "*$uvBin*")) {
    $env:Path = "$uvBin;$env:Path"
  }
}

# Step 1: detect existing uv.
Write-Info '[1/3] Checking for uv...'
$installUv = $true
if (Get-Command uv -ErrorAction SilentlyContinue) {
  $uvPath = (Get-Command uv).Source
  Write-Info "      uv is already installed at $uvPath."
  $installUv = $false
} else {
  Write-Info '      uv not found. Will install.'
}

# Step 2: install uv if needed.
if ($installUv) {
  Write-Info "[2/3] Installing uv from $UvInstallUrl..."
  try {
    $installer = Invoke-RestMethod -Uri $UvInstallUrl -UseBasicParsing
  } catch {
    Invoke-Fail "Could not download uv installer from $UvInstallUrl. Check your network, or install uv manually."
  }
  try {
    Invoke-Expression $installer
  } catch {
    Invoke-Fail "uv installer raised an error: $($_.Exception.Message)"
  }
  Update-SessionPath
  if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Invoke-Fail 'uv installed but is not on PATH. Open a new PowerShell window and re-run this command.'
  }
} else {
  Write-Info '[2/3] Skipping uv install.'
}

# Step 3: run VibeLens.
Write-Info '[3/3] Starting VibeLens (first run downloads the package; this can take ~30s)...'
& uvx vibelens serve
exit $LASTEXITCODE
