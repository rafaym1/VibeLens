"""GitHub URL parsing and download utilities."""

import os
import re
from pathlib import Path

import httpx

from vibelens.utils.log import get_logger

logger = get_logger(__name__)

GITHUB_TREE_RE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/tree/(?P<ref>[^/]+)/(?P<path>.+)"
)

GITHUB_BLOB_RE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<ref>[^/]+)/(?P<path>.+)"
)

GITHUB_RAW_BASE = "https://raw.githubusercontent.com"
GITHUB_API_BASE = "https://api.github.com"
REQUEST_TIMEOUT_SECONDS = 30


def _github_headers() -> dict[str, str]:
    """Build HTTP headers for GitHub API requests.

    Uses GITHUB_TOKEN env var for authentication when available,
    raising the rate limit from 60 to 5000 requests/hour.

    Returns:
        Headers dict with Accept and optional Authorization.
    """
    headers: dict[str, str] = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def github_tree_to_raw_url(tree_url: str, filename: str) -> str | None:
    """Convert a GitHub tree URL to a raw.githubusercontent.com URL for a file.

    Args:
        tree_url: GitHub tree URL like
            https://github.com/{owner}/{repo}/tree/{ref}/{path}
        filename: File name to append (e.g. "SKILL.md").

    Returns:
        Raw content URL, or None if tree_url doesn't match the pattern.
    """
    match = GITHUB_TREE_RE.match(tree_url)
    if not match:
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref")
    path = match.group("path")
    return f"{GITHUB_RAW_BASE}/{owner}/{repo}/{ref}/{path}/{filename}"


def github_blob_to_raw_url(blob_url: str) -> str | None:
    """Convert a GitHub blob URL to a raw.githubusercontent.com URL.

    Args:
        blob_url: GitHub blob URL like
            https://github.com/{owner}/{repo}/blob/{ref}/{path}

    Returns:
        Raw content URL, or None if blob_url doesn't match the pattern.
    """
    match = GITHUB_BLOB_RE.match(blob_url)
    if not match:
        return None
    owner = match.group("owner")
    repo = match.group("repo")
    ref = match.group("ref")
    path = match.group("path")
    return f"{GITHUB_RAW_BASE}/{owner}/{repo}/{ref}/{path}"


def download_directory(source_url: str, target_dir: Path) -> bool:
    """Download a complete directory from a GitHub tree URL.

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
        with httpx.Client(
            timeout=REQUEST_TIMEOUT_SECONDS,
            headers=_github_headers(),
        ) as client:
            downloaded = _fetch_directory_recursive(client, owner, repo, ref, path, target_dir)
        logger.debug(
            "Downloaded %d files from %s/%s/%s to %s", downloaded, owner, repo, path, target_dir
        )
        return downloaded > 0
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 403:
            logger.error(
                "GitHub API rate limit exceeded. Set GITHUB_TOKEN env var to increase limit."
            )
        else:
            logger.error("GitHub API request failed: %s", exc)
        return False
    except httpx.HTTPError as exc:
        logger.error("GitHub API request failed: %s", exc)
        return False


def _fetch_directory_recursive(
    client: httpx.Client, owner: str, repo: str, ref: str, path: str, local_dir: Path
) -> int:
    """Recursively fetch all files from a GitHub directory via the Contents API.

    Args:
        client: Reusable httpx client with auth headers.
        owner: Repository owner.
        repo: Repository name.
        ref: Git ref (branch/tag).
        path: Directory path within the repo.
        local_dir: Local directory to write into.

    Returns:
        Number of files downloaded.
    """
    api_url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}?ref={ref}"

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
            downloaded += _fetch_file(client, raw_url, local_dir / entry_name)

        elif entry_type == "dir":
            sub_dir = local_dir / entry_name
            sub_dir.mkdir(parents=True, exist_ok=True)
            downloaded += _fetch_directory_recursive(
                client, owner, repo, ref, entry["path"], sub_dir
            )

    return downloaded


def _fetch_file(client: httpx.Client, url: str, local_path: Path) -> int:
    """Download a single file from a URL.

    Args:
        client: Reusable httpx client.
        url: Raw file download URL.
        local_path: Local file path to write.

    Returns:
        1 on success, 0 on failure.
    """
    try:
        response = client.get(url)
        response.raise_for_status()
        local_path.write_bytes(response.content)
        return 1
    except httpx.HTTPError as exc:
        logger.warning("Failed to download %s: %s", url, exc)
        return 0
