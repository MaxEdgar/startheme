"""Backup and restore of the live starship.toml."""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from .config import Paths


def backup_current(paths: Paths) -> Path | None:
    """Copies the current starship.toml into backups/, timestamped.

    Returns None if there was nothing to back up yet (fresh install).
    """
    if not paths.starship_config.exists():
        return None
    paths.ensure_dirs()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = paths.backups_dir / f"starship.{timestamp}.toml"
    shutil.copy2(paths.starship_config, backup_path)
    return backup_path


def list_backups(paths: Paths) -> list[Path]:
    """Lists backups, most recent first."""
    if not paths.backups_dir.exists():
        return []
    backups = sorted(paths.backups_dir.glob("*.toml"), reverse=True)
    return backups


def restore_latest(paths: Paths) -> Path:
    backups = list_backups(paths)
    if not backups:
        raise FileNotFoundError("no backups exist to restore from")
    latest = backups[0]
    shutil.copy2(latest, paths.starship_config)
    return latest
