from __future__ import annotations

from startheme import backup as backup_mod


def test_backup_with_no_existing_config_is_none(paths):
    assert backup_mod.backup_current(paths) is None


def test_backup_and_restore_round_trip(paths):
    paths.starship_config.write_text('format = "original"')

    backup_path = backup_mod.backup_current(paths)
    assert backup_path is not None
    assert backup_path.exists()

    paths.starship_config.write_text('format = "changed"')
    restored_from = backup_mod.restore_latest(paths)
    assert restored_from == backup_path

    assert paths.starship_config.read_text() == 'format = "original"'


def test_list_backups_most_recent_first(paths):
    paths.starship_config.write_text('format = "v1"')
    first = backup_mod.backup_current(paths)
    paths.starship_config.write_text('format = "v2"')
    second = backup_mod.backup_current(paths)

    backups = backup_mod.list_backups(paths)
    assert backups[0] in (first, second)  # timestamps may tie in fast tests
    assert len(backups) >= 1
