from __future__ import annotations

import io
import contextlib

import pytest

from startheme import cli
from startheme.config import Paths, Config


def run_cli(monkeypatch, home, args):
    """Runs the CLI with HOME/XDG_CONFIG_HOME pointed at an isolated
    tmp directory, capturing stdout/stderr and the exit code.
    """
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.delenv("EDITOR", raising=False)

    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = cli.main(args)
    return code, out.getvalue(), err.getvalue()


def test_list_runs_without_error_on_fresh_install(monkeypatch, tmp_path):
    code, out, _ = run_cli(monkeypatch, tmp_path, ["list"])
    assert code == 0
    assert "Available themes" in out


def test_current_reports_none_on_fresh_install(monkeypatch, tmp_path):
    code, out, _ = run_cli(monkeypatch, tmp_path, ["current"])
    assert code == 0
    assert "No theme applied yet" in out


def test_create_then_reports_created(monkeypatch, tmp_path):
    code, out, _ = run_cli(
        monkeypatch, tmp_path, ["create", "mytheme", "--author", "tester"]
    )
    assert code == 0
    assert "Created mytheme" in out

    theme_path = tmp_path / ".config" / "startheme" / "themes" / "mytheme.toml"
    assert theme_path.exists()
    assert "tester" in theme_path.read_text()


def test_create_twice_without_force_fails(monkeypatch, tmp_path):
    run_cli(monkeypatch, tmp_path, ["create", "dup"])
    code, _, err = run_cli(monkeypatch, tmp_path, ["create", "dup"])
    assert code == 1
    assert "already exists" in err


def test_apply_without_install_fails_with_helpful_message(monkeypatch, tmp_path):
    code, _, err = run_cli(monkeypatch, tmp_path, ["apply", "nonexistent"])
    assert code == 1
    assert "not installed" in err


def test_create_then_apply_switches_active_theme_and_backs_up(monkeypatch, tmp_path):
    config_dir = tmp_path / ".config"
    config_dir.mkdir(parents=True)
    (config_dir / "starship.toml").write_text('format = "old"')

    run_cli(monkeypatch, tmp_path, ["create", "mine"])
    code, out, _ = run_cli(monkeypatch, tmp_path, ["apply", "mine"])
    assert code == 0
    assert "Applied mine theme" in out
    assert "Backup created" in out

    code, out, _ = run_cli(monkeypatch, tmp_path, ["current"])
    assert "mine" in out

    backups_dir = config_dir / "startheme" / "backups"
    assert len(list(backups_dir.iterdir())) == 1


def test_remove_with_yes_flag_skips_prompt(monkeypatch, tmp_path):
    run_cli(monkeypatch, tmp_path, ["create", "throwaway"])
    code, out, _ = run_cli(monkeypatch, tmp_path, ["remove", "throwaway", "--yes"])
    assert code == 0
    assert "Removed throwaway" in out


def test_invalid_theme_name_is_rejected(monkeypatch, tmp_path):
    code, _, err = run_cli(monkeypatch, tmp_path, ["create", "../evil"])
    assert code == 1
    assert "not a valid theme name" in err


def test_export_requires_existing_theme(monkeypatch, tmp_path):
    code, _, err = run_cli(monkeypatch, tmp_path, ["export", "nope"])
    assert code == 1
    assert "not installed" in err


def test_config_shows_fixed_repository(monkeypatch, tmp_path):
    code, out, _ = run_cli(monkeypatch, tmp_path, ["config"])
    assert code == 0
    assert "MaxEdgar/startheme" in out


def test_no_emoji_anywhere_in_list_output(monkeypatch, tmp_path):
    import re

    code, out, _ = run_cli(monkeypatch, tmp_path, ["list"])
    assert code == 0
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\u2600-\u27BF]"
    )
    assert not emoji_pattern.search(out)
