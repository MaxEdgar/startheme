"""Validates the actual themes/ and metadata/ directories shipped in
this repository -- not the builtin fallback catalog in theme.py, but
the real files a user would download via `startheme install`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import toml

REPO_ROOT = Path(__file__).resolve().parent.parent
THEMES_DIR = REPO_ROOT / "themes"
METADATA_DIR = REPO_ROOT / "metadata"

EMOJI_PATTERN = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")

KNOWN_MODULES = {
    "os", "username", "hostname", "directory", "git_branch", "git_status",
    "nodejs", "rust", "python", "golang", "cmd_duration", "character",
    "line_break",
}


def theme_files() -> list[Path]:
    return sorted(THEMES_DIR.glob("*.toml"))


def test_at_least_twenty_themes_shipped():
    assert len(theme_files()) >= 20


def test_packaged_copy_matches_repo_root_copy():
    """themes/ and metadata/ at the repo root are what GitHub serves to
    `startheme install`/`browse` (via raw.githubusercontent.com).
    startheme/themes/ and startheme/metadata/ are bundled inside the
    installed package so `startheme list` works offline. The two must
    be kept identical, or `list` and `install` will show different
    catalogs.
    """
    packaged_themes_dir = REPO_ROOT / "startheme" / "themes"
    packaged_metadata_dir = REPO_ROOT / "startheme" / "metadata"

    for root_dir, packaged_dir, label in (
        (THEMES_DIR, packaged_themes_dir, "themes"),
        (METADATA_DIR, packaged_metadata_dir, "metadata"),
    ):
        root_files = {f.name: f.read_text() for f in root_dir.glob("*.toml")}
        packaged_files = {f.name: f.read_text() for f in packaged_dir.glob("*.toml")}
        assert root_files.keys() == packaged_files.keys(), (
            f"{label}/ and startheme/{label}/ have different file sets: "
            f"{set(root_files) ^ set(packaged_files)}"
        )
        mismatched = [
            name for name in root_files if root_files[name] != packaged_files[name]
        ]
        assert not mismatched, (
            f"{label}/ and startheme/{label}/ have diverged for: {mismatched}"
        )


def test_every_theme_has_matching_metadata():
    theme_names = {f.stem for f in THEMES_DIR.glob("*.toml")}
    meta_names = {f.stem for f in METADATA_DIR.glob("*.toml")}
    assert theme_names == meta_names, (
        f"mismatch -- themes only: {theme_names - meta_names}, "
        f"metadata only: {meta_names - theme_names}"
    )


@pytest.mark.parametrize("path", theme_files(), ids=lambda p: p.stem)
def test_theme_file_is_valid_toml_with_required_sections(path):
    data = toml.loads(path.read_text())
    assert "format" in data, f"{path.name} missing top-level 'format'"
    assert "character" in data, f"{path.name} missing [character] section"
    assert "success_symbol" in data["character"]
    assert "error_symbol" in data["character"]


@pytest.mark.parametrize("path", theme_files(), ids=lambda p: p.stem)
def test_theme_format_only_references_known_modules(path):
    text = path.read_text()
    match = re.search(r'^format = """(.*?)"""', text, re.DOTALL | re.MULTILINE)
    data = toml.loads(text)
    body = match.group(1) if match else data.get("format", "")
    used = set(re.findall(r"\$(\w+)", body))
    unknown = used - KNOWN_MODULES
    assert not unknown, f"{path.name} references unknown module(s): {unknown}"


@pytest.mark.parametrize("path", theme_files(), ids=lambda p: p.stem)
def test_theme_has_no_emoji(path):
    matches = EMOJI_PATTERN.findall(path.read_text())
    assert not matches, f"{path.name} contains emoji/dingbat glyphs: {matches}"


@pytest.mark.parametrize(
    "path", sorted(METADATA_DIR.glob("*.toml")), ids=lambda p: p.stem
)
def test_metadata_file_has_required_fields_and_no_emoji(path):
    data = toml.loads(path.read_text())
    for key in ("name", "description", "tags"):
        assert key in data, f"{path.name} missing '{key}'"
    matches = EMOJI_PATTERN.findall(path.read_text())
    assert not matches, f"{path.name} contains emoji/dingbat glyphs: {matches}"
