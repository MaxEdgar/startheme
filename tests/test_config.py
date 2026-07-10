from __future__ import annotations

import pytest

from startheme.config import Config, is_valid_theme_name, assert_valid_name


def test_valid_names():
    assert is_valid_theme_name("cute")
    assert is_valid_theme_name("cyber-punk_2")
    assert not is_valid_theme_name("../etc/passwd")
    assert not is_valid_theme_name("")
    assert not is_valid_theme_name("has space")


def test_assert_valid_name_raises():
    with pytest.raises(ValueError):
        assert_valid_name("../evil")


def test_config_round_trip(paths):
    cfg = Config(theme="cute")
    cfg.save(paths)
    reloaded = Config.load(paths)
    assert reloaded.theme == "cute"


def test_config_defaults_to_no_theme(paths):
    cfg = Config.load(paths)
    assert cfg.theme is None
