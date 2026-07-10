"""Command-line interface for startheme.

Plain-text output only: no emoji, no non-ASCII symbols, so this
reads correctly in any terminal and any locale. Status markers are
plain words ([OK], [ERROR], [INFO]) instead of icons.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from . import __version__, backup as backup_mod
from . import github
from . import installer
from . import theme as theme_mod
from .config import Config, GITHUB_OWNER, GITHUB_REPO, Paths, assert_valid_name

OK = "[OK]"
ERR = "[ERROR]"
INFO = "[INFO]"


def _print_theme_line(meta: theme_mod.ThemeMetadata, installed: bool, current: bool) -> None:
    marker = ""
    if current:
        marker = " (current)"
    elif installed:
        marker = " (installed)"
    print(f"  {meta.name}{marker}")
    if meta.description:
        print(f"      {meta.description}")


def cmd_list(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    installed = theme_mod.list_installed(paths)
    catalog = theme_mod.builtin_catalog()

    print("Available themes:")
    print()
    for meta in catalog:
        _print_theme_line(meta, meta.name in installed, cfg.theme == meta.name)

    for name in installed:
        if not any(m.name == name for m in catalog):
            meta = theme_mod.ThemeMetadata(name=name, description="Custom theme")
            _print_theme_line(meta, True, cfg.theme == name)

    print()
    print("Tip: startheme install <name>, then startheme apply <name>")
    return 0


def cmd_search(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    query = args.query.lower()
    installed = theme_mod.list_installed(paths)
    catalog = theme_mod.builtin_catalog()

    try:
        remote_names = github.list_remote_themes()
        for name in remote_names:
            if not any(m.name == name for m in catalog):
                catalog.append(theme_mod.ThemeMetadata(name=name))
    except github.GitHubError:
        pass  # fall back to the local/builtin catalog silently

    matches = [
        m
        for m in catalog
        if query in m.name.lower()
        or query in m.description.lower()
        or any(query in tag.lower() for tag in m.tags)
    ]

    if not matches:
        print(f"{INFO} No themes matched '{args.query}'")
        return 0

    print(f"Themes matching '{args.query}':")
    print()
    for meta in matches:
        _print_theme_line(meta, meta.name in installed, cfg.theme == meta.name)
    return 0


def cmd_browse(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    print(f"Fetching the theme catalog from {GITHUB_OWNER}/{GITHUB_REPO}...")
    try:
        remote = github.list_remote_themes()
    except github.GitHubError as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1

    if not remote:
        print(f"{INFO} No themes published yet.")
        return 0

    print()
    print("Theme catalog:")
    print()
    for name in remote:
        try:
            meta = github.fetch_metadata(name)
        except github.GitHubError:
            meta = theme_mod.ThemeMetadata(name=name)
        _print_theme_line(meta, theme_mod.is_installed(paths, name), cfg.theme == name)
    print()
    print("Install any of these with: startheme install <name>")
    return 0


def cmd_install(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    try:
        print(f"Downloading {args.name}.toml ...")
        installer.install(paths, args.name, force=args.force)
    except (ValueError, FileExistsError, github.GitHubError) as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Installed {args.name}")
    return 0


def cmd_apply(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    try:
        backup_path = installer.apply(paths, cfg, args.name)
    except (ValueError, FileNotFoundError) as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Applied {args.name} theme")
    if backup_path:
        print(f"{OK} Backup created at {backup_path}")
    else:
        print(f"{INFO} No previous config found, nothing to back up")
    print("Restart your terminal to see the changes.")
    return 0


def cmd_remove(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    if not theme_mod.is_installed(paths, args.name):
        print(f"{ERR} theme '{args.name}' is not installed", file=sys.stderr)
        return 1

    if not args.yes:
        answer = input(f"Remove theme '{args.name}'? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print(f"{INFO} Cancelled")
            return 0

    try:
        installer.remove(paths, cfg, args.name)
    except FileNotFoundError as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Removed {args.name}")
    print("Your live starship.toml was not touched.")
    return 0


def cmd_current(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    if cfg.theme:
        print("Current theme:")
        print(f"  {cfg.theme}")
    else:
        print(f"{INFO} No theme applied yet.")
        print("Run: startheme apply <name>")
    return 0


def cmd_create(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    author = args.author or os.environ.get("USER") or os.environ.get("USERNAME") or "anonymous"
    try:
        theme_mod.create_theme(paths, args.name, author, force=args.force)
    except (ValueError, FileExistsError) as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Created {args.name}")
    print(f"  {paths.theme_path(args.name)}")
    print(f"Run: startheme edit {args.name}")
    return 0


def cmd_edit(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    if not theme_mod.is_installed(paths, args.name):
        print(
            f"{ERR} theme '{args.name}' is not installed. "
            f"Try `startheme create {args.name}` first.",
            file=sys.stderr,
        )
        return 1
    editor = os.environ.get("EDITOR", "vi")
    path = paths.theme_path(args.name)
    try:
        result = subprocess.run([editor, str(path)])
    except OSError as exc:
        print(f"{ERR} failed to launch '{editor}': {exc}", file=sys.stderr)
        return 1
    if result.returncode != 0:
        print(f"{ERR} {editor} exited with a non-zero status", file=sys.stderr)
        return 1
    print(f"{OK} Saved {args.name}")
    return 0


def cmd_preview(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    try:
        contents = theme_mod.read_theme_contents(paths, args.name)
    except FileNotFoundError as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1

    print(f"Preview of '{args.name}':")
    print("-" * 40)
    format_line = next(
        (l for l in contents.splitlines() if l.strip().startswith("format")),
        "(no top-level format found)",
    )
    print(format_line)
    module_count = sum(
        1
        for l in contents.splitlines()
        if l.strip().startswith("[") and l.strip().endswith("]")
    )
    print()
    print(f"{module_count} module section(s) configured")
    print("-" * 40)
    print("This is a static preview. For a live render, run:")
    print(f"  starship prompt --config {paths.theme_path(args.name)}")
    return 0


def cmd_update(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    print("Checking for new themes...")
    try:
        remote = github.list_remote_themes()
    except github.GitHubError as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} {len(remote)} theme(s) available upstream")
    for name in remote:
        print(f"  - {name}")
    return 0


def cmd_export(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    dest = Path(args.output) if args.output else Path(f"{args.name}.toml")
    try:
        installer.export_theme(paths, args.name, dest)
    except FileNotFoundError as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Exported {args.name} to {dest}")
    return 0


def cmd_import(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    src = Path(args.path)
    name = args.name or src.stem
    try:
        installer.import_theme(paths, src, name, force=args.force)
    except (ValueError, FileNotFoundError, FileExistsError) as exc:
        print(f"{ERR} {exc}", file=sys.stderr)
        return 1
    print(f"{OK} Imported as {name}")
    return 0


def cmd_backups(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    if args.restore:
        try:
            restored_from = backup_mod.restore_latest(paths)
        except FileNotFoundError as exc:
            print(f"{ERR} {exc}", file=sys.stderr)
            return 1
        print(f"{OK} Restored {restored_from}")
        return 0

    backups = backup_mod.list_backups(paths)
    if not backups:
        print(f"{INFO} No backups yet.")
        return 0
    print("Backups (most recent first):")
    for path in backups:
        print(f"  - {path}")
    print()
    print("Run with --restore to restore the latest one.")
    return 0


def cmd_config(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    print("startheme configuration:")
    print(f"  theme        {cfg.theme or '(none)'}")
    print(f"  repository   {GITHUB_OWNER}/{GITHUB_REPO} (fixed)")
    print(f"  config file  {paths.config_file}")
    return 0


def cmd_tui(paths: Paths, cfg: Config, args: argparse.Namespace) -> int:
    from .tui import StarthemeApp

    StarthemeApp(paths=paths, cfg=cfg).run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="startheme",
        description="A theme manager for the Starship prompt.",
    )
    parser.add_argument(
        "--version", action="version", version=f"startheme {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List installed and available themes")
    p_list.set_defaults(func=cmd_list)

    p_search = sub.add_parser("search", help="Search installed and remote themes")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_browse = sub.add_parser("browse", help="Browse the full remote theme catalog")
    p_browse.set_defaults(func=cmd_browse)

    p_install = sub.add_parser("install", help="Download a theme from the startheme repository")
    p_install.add_argument("name")
    p_install.add_argument("-f", "--force", action="store_true")
    p_install.set_defaults(func=cmd_install)

    p_apply = sub.add_parser("apply", help="Apply an installed theme as your live prompt")
    p_apply.add_argument("name")
    p_apply.set_defaults(func=cmd_apply)

    p_remove = sub.add_parser("remove", help="Remove a downloaded theme")
    p_remove.add_argument("name")
    p_remove.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")
    p_remove.set_defaults(func=cmd_remove)

    p_current = sub.add_parser("current", help="Show the currently applied theme")
    p_current.set_defaults(func=cmd_current)

    p_create = sub.add_parser("create", help="Create a new theme from a starter template")
    p_create.add_argument("name")
    p_create.add_argument("-f", "--force", action="store_true")
    p_create.add_argument("-a", "--author")
    p_create.set_defaults(func=cmd_create)

    p_edit = sub.add_parser("edit", help="Open a theme in $EDITOR")
    p_edit.add_argument("name")
    p_edit.set_defaults(func=cmd_edit)

    p_preview = sub.add_parser("preview", help="Preview a theme's structure")
    p_preview.add_argument("name")
    p_preview.set_defaults(func=cmd_preview)

    p_update = sub.add_parser("update", help="Check the repository for new themes")
    p_update.set_defaults(func=cmd_update)

    p_export = sub.add_parser("export", help="Copy an installed theme out to a file")
    p_export.add_argument("name")
    p_export.add_argument("-o", "--output")
    p_export.set_defaults(func=cmd_export)

    p_import = sub.add_parser("import", help="Import a local TOML file as a named theme")
    p_import.add_argument("path")
    p_import.add_argument("-n", "--name")
    p_import.add_argument("-f", "--force", action="store_true")
    p_import.set_defaults(func=cmd_import)

    p_backups = sub.add_parser("backups", help="List or restore configuration backups")
    p_backups.add_argument("-r", "--restore", action="store_true")
    p_backups.set_defaults(func=cmd_backups)

    p_config = sub.add_parser("config", help="Show startheme configuration")
    p_config.set_defaults(func=cmd_config)

    p_tui = sub.add_parser("tui", help="Launch the interactive text interface")
    p_tui.set_defaults(func=cmd_tui)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    paths = Paths.resolve()
    paths.ensure_dirs()
    cfg = Config.load(paths)

    if not getattr(args, "command", None):
        # No subcommand: launch the TUI, same as running `startheme`
        # with nothing else.
        from .tui import StarthemeApp

        StarthemeApp(paths=paths, cfg=cfg).run()
        return 0

    try:
        return args.func(paths, cfg, args)
    except KeyboardInterrupt:
        print()
        return 130


if __name__ == "__main__":
    sys.exit(main())
