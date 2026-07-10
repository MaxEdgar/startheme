# Roadmap

## v0.2 -- Python / TUI rewrite, one-line install, 20 themes (this release)

- [x] Full rewrite from Rust to Python
- [x] Text-based interface (Textual) in addition to the CLI
- [x] Theme source repository fixed to MaxEdgar/startheme, no setup required
- [x] No emoji or decorative unicode anywhere in output
- [x] Core commands: list, search, install, apply, remove, current,
      create, edit, preview, browse, update, export, import, backups, config
- [x] Automatic, timestamped backups on every apply
- [x] Unit, CLI, and theme-catalog test coverage
- [x] One-line install script (`install.sh`) that also offers to
      install Starship itself and wire up shell integration
- [x] 20 distinct, hand-written themes (not palette-swap clones)

## v0.3 -- Polish

- [ ] `--restore <backup-name>` (not just "latest")
- [ ] Live prompt rendering in `preview` when `starship` is on PATH
- [ ] `startheme diff <name>` -- show what would change vs. the live config
- [ ] Shell completions (bash/zsh/fish) for the CLI
- [ ] TUI: color swatches per theme row, not just plain text status
- [ ] `startheme doctor` -- sanity-check the active config before applying

## v0.4 -- Distribution

- [ ] Publish to PyPI (`pip install startheme`)
- [ ] Prebuilt single-file binaries via PyInstaller for users without Python
- [ ] Homebrew tap

## v0.5 -- Catalog growth

- [ ] Grow past the initial 20 themes based on community submissions
- [ ] Theme submission checklist enforced by CI (valid TOML, matching
      metadata, no emoji) -- already partly covered by
      `tests/test_theme_catalog.py`
- [ ] `startheme browse --tag <tag>` filtering

## Later / exploratory

- [ ] Live-render preview inside the TUI using the `starship` binary directly
- [ ] Theme "remix" -- start a new theme from an existing one
- [ ] Multi-profile support (different themes per shell/project)

## Contributing to the roadmap

Have an idea? Open an issue with the `enhancement` label. See
[CONTRIBUTING.md](CONTRIBUTING.md) for how to submit code or a theme.
