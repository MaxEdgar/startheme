"""GitHub integration for the fixed startheme theme repository.

Every function here talks to the same, hardcoded repository -
see startheme.config.GITHUB_OWNER / GITHUB_REPO. There is no
per-user configuration of the theme source; this keeps the tool
zero-setup.
"""

from __future__ import annotations

import requests

from . import __version__
from .config import GITHUB_OWNER, GITHUB_REF, GITHUB_REPO
from .theme import ThemeMetadata

USER_AGENT = f"startheme/{__version__}"
TIMEOUT = 20


class GitHubError(RuntimeError):
    """Raised for any network or API failure talking to GitHub."""


def _headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT}


def list_remote_themes() -> list[str]:
    """Lists theme names (without .toml) in themes/ via the GitHub
    Contents API.
    """
    url = (
        f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/contents/themes?ref={GITHUB_REF}"
    )
    try:
        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise GitHubError(f"could not reach GitHub: {exc}") from exc

    if resp.status_code == 404:
        raise GitHubError(
            f"{GITHUB_OWNER}/{GITHUB_REPO} has no themes/ directory on "
            f"ref '{GITHUB_REF}'"
        )
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise GitHubError(
            "GitHub API rate limit exceeded for this network. "
            "This happens on shared/unauthenticated connections; wait a "
            "bit and try again, or use `startheme install <name>` "
            "directly, which does not use the rate-limited API."
        )
    if not resp.ok:
        raise GitHubError(f"GitHub API returned {resp.status_code} for {url}")

    entries = resp.json()
    names = [
        entry["name"][: -len(".toml")]
        for entry in entries
        if entry.get("type") == "file" and entry.get("name", "").endswith(".toml")
    ]
    return sorted(names)


def download_theme(name: str) -> str:
    """Downloads the raw contents of themes/<name>.toml."""
    url = (
        f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/{GITHUB_REF}/themes/{name}.toml"
    )
    try:
        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise GitHubError(f"could not reach GitHub: {exc}") from exc

    if resp.status_code == 404:
        raise GitHubError(f"theme '{name}' was not found in {GITHUB_OWNER}/{GITHUB_REPO}")
    if not resp.ok:
        raise GitHubError(f"download failed with HTTP {resp.status_code}")
    return resp.text


def fetch_metadata(name: str) -> ThemeMetadata:
    """Fetches metadata/<name>.toml; raises GitHubError if absent."""
    url = (
        f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}"
        f"/{GITHUB_REF}/metadata/{name}.toml"
    )
    try:
        resp = requests.get(url, headers=_headers(), timeout=TIMEOUT)
    except requests.RequestException as exc:
        raise GitHubError(f"could not reach GitHub: {exc}") from exc

    if not resp.ok:
        raise GitHubError(f"no metadata found for '{name}'")
    return ThemeMetadata.from_toml_text(resp.text, fallback_name=name)
