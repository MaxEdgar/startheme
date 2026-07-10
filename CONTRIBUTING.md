# Contributing to startheme

Thanks for considering a contribution. There are two kinds of
contribution here, and they go through different paths.

## Contributing code

1. Fork and clone the repo.
2. Set up a dev environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```
3. Make your change. Keep functions small and add a unit test next to
   the code you touched (see `tests/test_*.py` for the existing pattern).
4. Run the test suite before opening a PR:
   ```bash
   pytest
   ```
5. Open a PR describing why, not just what. If it changes CLI or TUI
   output, paste a before/after in the description.

### Code style

- No emoji or decorative unicode in any user-facing output (CLI, TUI, or
  README). Status markers are plain text: `[OK]`, `[INFO]`, `[ERROR]`.
  This is intentional -- see the README for why.
- Raise real exceptions (`ValueError`, `FileNotFoundError`,
  `FileExistsError`) from the `theme`, `backup`, `installer`, and
  `github` modules; catch and translate them into a message in
  `cli.py`/`tui.py`, not the other way around.
- Keep `cli.py` and `tui.py` thin: they should orchestrate and format
  output, not contain business logic. New behavior usually belongs in
  `theme.py`, `github.py`, `backup.py`, or `installer.py`.
- Type hints throughout; this codebase targets Python 3.10+, so
  `X | None` is fine, `Optional[X]` is not required.

### Adding a new CLI subcommand

1. Add a `cmd_<name>` function in `cli.py` that takes
   `(paths, cfg, args)` and returns an exit code.
2. Register it in `build_parser()`.
3. Put any real logic in the relevant module, not inline in `cli.py`.
4. Add at least one test in `tests/test_cli.py`.

### Adding a TUI feature

- New keybindings go in `StarthemeApp.BINDINGS` in `tui.py`, with a
  matching `action_<name>` method.
- Modal dialogs (confirmations, prompts) are `ModalScreen` subclasses;
  see `ConfirmScreen` and `CreateThemeScreen` for the pattern.
- Long-running work (network calls) should use `@work(thread=True)` so
  the interface does not freeze; see `_install_worker` for an example.

## Contributing a theme

Themes live in this repository's own `themes/` and `metadata/`
directories -- `startheme` is fixed to download from here, so a theme
only becomes installable once it is merged.

1. Add `themes/<name>.toml` -- a valid Starship configuration. Test it
   locally first:
   ```bash
   starship prompt --config themes/<name>.toml
   ```
2. Add a matching `metadata/<name>.toml`:
   ```toml
   name = "<name>"
   author = "your name or handle"
   description = "One line, under about 60 characters"
   tags = ["a-few", "lowercase", "tags"]
   ```
3. Do not use emoji in the theme's `format` string, the metadata, or any
   symbol/glyph field. Plain characters or Nerd Font powerline glyphs
   only -- see `themes/professional.toml` for a plain example and
   `themes/cyber.toml` for a Nerd-Font-glyph example.
4. Test end-to-end against your own fork before opening a PR:
   ```bash
   git clone https://github.com/<you>/startheme.git
   cd startheme && pip install -e .
   # temporarily point GITHUB_OWNER/GITHUB_REPO in config.py at your fork
   startheme install <name>
   startheme apply <name>
   ```

### Theme quality guidelines

- Keep it to styling only -- no secrets or machine-specific paths.
- Note in your PR description if a theme requires a
  [Nerd Font](https://www.nerdfonts.com/) for its glyphs to render.
- Prefer `truncate_to_repo = true` for `[directory]` so long paths do
  not dominate the prompt.
- Give `[character]` both `success_symbol` and `error_symbol` -- a
  theme that does not visibly change on a failed command is a paper cut.

## Reporting bugs

Open an issue with:
- `startheme --version`
- OS, terminal emulator, and Python version
- The exact command you ran and its full output

## Code of conduct

Be kind. Assume good faith. Disagree about code, not about people.
