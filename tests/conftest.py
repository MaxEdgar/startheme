from __future__ import annotations

import pytest

from startheme.config import Config, Paths


@pytest.fixture()
def paths(tmp_path) -> Paths:
    root = tmp_path
    p = Paths(
        config_dir=root / "config",
        themes_dir=root / "config" / "themes",
        backups_dir=root / "config" / "backups",
        config_file=root / "config" / "config.toml",
        starship_config=root / "starship.toml",
    )
    p.ensure_dirs()
    return p


@pytest.fixture()
def cfg() -> Config:
    return Config()
