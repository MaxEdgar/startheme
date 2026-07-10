"""Install / apply / remove / export / import orchestration."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import backup as backup_mod
from . import github
from . import theme as theme_mod
from .config import Config, Paths, assert_valid_name


def install(paths: Paths, name: str, force: bool = False) -> None:
    """Downloads a theme from the startheme repository into
    <config>/themes/<name>.toml.
    """
    assert_valid_name(name)
    paths.ensure_dirs()

    dest = paths.theme_path(name)
    if dest.exists() and not force:
        raise FileExistsError(
            f"theme '{name}' is already installed (use --force to re-download)"
        )

    contents = github.download_theme(name)
    dest.write_text(contents)


def apply(paths: Paths, cfg: Config, name: str) -> Path | None:
    """Backs up the live starship.toml, copies the installed theme
    over it, and records it as the current theme.

    Returns the backup path, or None if there was nothing to back up.
    """
    assert_valid_name(name)
    theme_path = paths.theme_path(name)
    if not theme_path.exists():
        raise FileNotFoundError(
            f"theme '{name}' is not installed yet. "
            f"Try `startheme install {name}` first."
        )

    backup_path = backup_mod.backup_current(paths)
    shutil.copy2(theme_path, paths.starship_config)

    cfg.theme = name
    cfg.save(paths)
    return backup_path


def remove(paths: Paths, cfg: Config, name: str) -> None:
    """Removes an installed theme file. Never touches the live
    starship.toml.
    """
    theme_mod.remove_theme_file(paths, name)
    if cfg.theme == name:
        cfg.theme = None
        cfg.save(paths)


def export_theme(paths: Paths, name: str, dest: Path) -> None:
    src = paths.theme_path(name)
    if not src.exists():
        raise FileNotFoundError(f"theme '{name}' is not installed")
    shutil.copy2(src, dest)


def import_theme(paths: Paths, src: Path, name: str, force: bool = False) -> None:
    assert_valid_name(name)
    if not src.exists():
        raise FileNotFoundError(f"file not found: {src}")
    dest = paths.theme_path(name)
    if dest.exists() and not force:
        raise FileExistsError(
            f"theme '{name}' already exists (use --force to overwrite)"
        )
    paths.ensure_dirs()
    shutil.copy2(src, dest)
