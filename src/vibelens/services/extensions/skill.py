"""Skill extension handler with GitHub download and agent import logic.

Consolidates skill installation, download from GitHub, and agent-to-central
import into a single module.
"""

from pathlib import Path

import httpx

from vibelens.utils.github import GITHUB_TREE_RE
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

GITHUB_API_BASE = "https://api.github.com"
GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
REQUEST_TIMEOUT_SECONDS = 30


def download_skill_directory(source_url: str, target_dir: Path) -> bool:
    """Download a complete skill directory from a GitHub tree URL.

    Fetches all files recursively from the GitHub Contents API and writes
    them to the local target directory, preserving the directory structure.

    Args:
        source_url: GitHub tree URL (e.g. https://github.com/owner/repo/tree/main/skills/foo).
        target_dir: Local directory to write files into.

    Returns:
        True if at least one file was downloaded successfully.
    """
    match = GITHUB_TREE_RE.match(source_url)
    if not match:
        logger.warning("Cannot parse GitHub URL: %s", source_url)
        return False

    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref")
    path = match.group("path")

    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        downloaded = _fetch_directory_recursive(owner, repo, ref, path, target_dir)
        logger.info(
            "Downloaded %d files from %s/%s/%s to %s", downloaded, owner, repo, path, target_dir
        )
        return downloaded > 0
    except httpx.HTTPError as exc:
        logger.error("GitHub API request failed: %s", exc)
        return False


def _fetch_directory_recursive(owner: str, repo: str, ref: str, path: str, local_dir: Path) -> int:
    """Recursively fetch all files from a GitHub directory via the Contents API.

    Args:
        owner: Repository owner.
        repo: Repository name.
        ref: Git ref (branch/tag).
        path: Directory path within the repo.
        local_dir: Local directory to write into.

    Returns:
        Number of files downloaded.
    """
    api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={ref}"

    with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        response = client.get(api_url)
        response.raise_for_status()
        entries = response.json()

    if not isinstance(entries, list):
        logger.warning("Expected directory listing from %s, got single file", api_url)
        return 0

    downloaded = 0
    for entry in entries:
        entry_name = entry["name"]
        entry_type = entry["type"]

        if entry_type == "file":
            raw_url = entry.get("download_url", "")
            if not raw_url:
                raw_url = f"{GITHUB_RAW_BASE}/{owner}/{repo}/{ref}/{entry['path']}"
            downloaded += _fetch_file(raw_url, local_dir / entry_name)

        elif entry_type == "dir":
            sub_dir = local_dir / entry_name
            sub_dir.mkdir(parents=True, exist_ok=True)
            downloaded += _fetch_directory_recursive(owner, repo, ref, entry["path"], sub_dir)

    return downloaded


def _fetch_file(url: str, local_path: Path) -> int:
    """Download a single file from a URL.

    Args:
        url: Raw file download URL.
        local_path: Local file path to write.

    Returns:
        1 on success, 0 on failure.
    """
    try:
        with httpx.Client(timeout=REQUEST_TIMEOUT_SECONDS) as client:
            response = client.get(url)
            response.raise_for_status()
        local_path.write_bytes(response.content)
        return 1
    except httpx.HTTPError as exc:
        logger.warning("Failed to download %s: %s", url, exc)
        return 0


def import_agent_extensions() -> int:
    """Import extensions from all agent interfaces into the central store."""
    from vibelens.deps import get_skill_service

    service = get_skill_service()
    total_imported = 0
    for agent_key in service._agents:
        try:
            imported = service.import_all_from_agent(agent_key)
            if imported:
                logger.info(
                    "Imported %d skills from %s into central store",
                    len(imported),
                    agent_key,
                )
                total_imported += len(imported)
        except Exception:
            logger.warning("Failed to import from %s", agent_key, exc_info=True)

    if total_imported:
        logger.info("Total skills imported into central store: %d", total_imported)
    return total_imported
