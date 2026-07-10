from __future__ import annotations

import pytest

from startheme import installer, theme as theme_mod
from startheme.config import Config


def test_apply_fails_when_theme_not_installed(paths, cfg):
    with pytest.raises(FileNotFoundError):
        installer.apply(paths, cfg, "ghost-theme")


def test_apply_backs_up_and_switches_theme(paths, cfg):
    paths.theme_path("cute").write_text('format = "cute"')
    paths.starship_config.write_text('format = "old"')

    backup_path = installer.apply(paths, cfg, "cute")
    assert backup_path is not None
    assert cfg.theme == "cute"
    assert paths.starship_config.read_text() == 'format = "cute"'


def test_apply_with_no_prior_config_returns_none(paths, cfg):
    paths.theme_path("cute").write_text('format = "cute"')
    backup_path = installer.apply(paths, cfg, "cute")
    assert backup_path is None
    assert cfg.theme == "cute"


def test_export_requires_installed_theme(paths, tmp_path):
    dest = tmp_path / "out.toml"
    with pytest.raises(FileNotFoundError):
        installer.export_theme(paths, "missing", dest)


def test_import_then_export_round_trip(paths, tmp_path):
    src = tmp_path / "mytheme.toml"
    src.write_text('format = "imported"')
    installer.import_theme(paths, src, "mytheme")
    assert theme_mod.is_installed(paths, "mytheme")

    out = tmp_path / "exported.toml"
    installer.export_theme(paths, "mytheme", out)
    assert out.read_text() == 'format = "imported"'


def test_import_twice_without_force_raises(paths, tmp_path):
    src = tmp_path / "mytheme.toml"
    src.write_text('format = "v1"')
    installer.import_theme(paths, src, "mytheme")
    with pytest.raises(FileExistsError):
        installer.import_theme(paths, src, "mytheme")


def test_remove_clears_current_theme_if_active(paths, cfg):
    paths.theme_path("cute").write_text('format = "cute"')
    installer.apply(paths, cfg, "cute")
    assert cfg.theme == "cute"
    installer.remove(paths, cfg, "cute")
    assert cfg.theme is None
    assert not theme_mod.is_installed(paths, "cute")
