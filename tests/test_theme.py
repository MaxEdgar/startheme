from __future__ import annotations

import pytest

from startheme import theme as theme_mod


def test_builtin_catalog_has_at_least_twenty_themes():
    catalog = theme_mod.builtin_catalog()
    assert len(catalog) >= 20
    assert any(t.name == "cute" for t in catalog)


def test_starter_template_contains_name_and_author():
    tpl = theme_mod.starter_template("mytheme", "alice")
    assert "mytheme" in tpl
    assert "alice" in tpl
    assert "[character]" in tpl


def test_create_and_list_installed(paths):
    theme_mod.create_theme(paths, "mine", "tester")
    assert theme_mod.is_installed(paths, "mine")
    assert "mine" in theme_mod.list_installed(paths)


def test_create_twice_without_force_raises(paths):
    theme_mod.create_theme(paths, "dup", "tester")
    with pytest.raises(FileExistsError):
        theme_mod.create_theme(paths, "dup", "tester")


def test_create_twice_with_force_overwrites(paths):
    theme_mod.create_theme(paths, "dup", "first")
    theme_mod.create_theme(paths, "dup", "second", force=True)
    contents = theme_mod.read_theme_contents(paths, "dup")
    assert "second" in contents


def test_remove_theme_file(paths):
    theme_mod.create_theme(paths, "throwaway", "tester")
    theme_mod.remove_theme_file(paths, "throwaway")
    assert not theme_mod.is_installed(paths, "throwaway")


def test_remove_missing_theme_raises(paths):
    with pytest.raises(FileNotFoundError):
        theme_mod.remove_theme_file(paths, "ghost")


def test_metadata_from_toml_text():
    text = (
        'name = "cute"\n'
        'author = "startheme"\n'
        'description = "Soft pastel pink developer theme"\n'
        'tags = ["pink", "cute", "minimal"]\n'
    )
    meta = theme_mod.ThemeMetadata.from_toml_text(text, fallback_name="cute")
    assert meta.name == "cute"
    assert meta.author == "startheme"
    assert meta.tags == ["pink", "cute", "minimal"]
