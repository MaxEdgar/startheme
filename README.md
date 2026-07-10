# startheme

A theme manager for the [Starship](https://starship.rs) prompt, with a
text-based interface. 20 themes included, ready to install.

## Install

```
curl -fsSL https://raw.githubusercontent.com/MaxEdgar/startheme/main/install.sh | sh
```

That one command installs startheme, checks whether Starship itself is
installed (and asks before installing it if not), and checks whether
your shell is set up to run it. Nothing happens without your
confirmation except installing the startheme package itself.

Prefer to read the script before running it? It's right here:
[`install.sh`](install.sh).

Once installed:

```
startheme
```

opens the text interface. Or use it as a plain command:

```
startheme list
startheme install cyber
startheme apply cyber
```

No emoji or decorative unicode is used anywhere in this project's
output -- README, CLI, and TUI included -- so it renders correctly in
any terminal, over SSH, in any locale, on any Linux distribution,
without depending on a particular font.

## Why startheme

Starship is good, but hand-editing `starship.toml` and copying config
snippets from blog posts gets tedious. startheme treats prompt themes
the way `oh-my-zsh` treats shell themes: pick one, apply it, switch it
later, without ever risking your own hand-tuned config.

- Browse and install from 20 built-in themes, no configuration needed
- Apply instantly, with an automatic timestamped backup every time
- Create your own theme from a starter template and edit it in `$EDITOR`
- Switch back at any point -- nothing destructive happens without confirmation
- Export or import themes as plain `.toml` files
- A full text-based interface, in addition to the command line

## Themes

| Name | Description |
|---|---|
| `cute` | Soft pastel pink developer theme |
| `cyber` | Dark hacker inspired theme |
| `professional` | Clean enterprise theme |
| `minimal` | No backgrounds or separators, just clean color and spacing |
| `nord` | Arctic, muted Nord color scheme, segmented layout |
| `dracula` | The Dracula palette, two-line layout with language modules |
| `gruvbox` | Warm retro Gruvbox palette, single line, no separators |
| `solarized` | Classic Solarized Dark, low-glare for long sessions |
| `monokai` | Vibrant, high-contrast, editor-inspired single line |
| `catppuccin` | Soft modern Catppuccin Mocha pastel, segmented |
| `tokyonight` | Deep blues and purples with command duration shown |
| `matrix` | Green on black, deliberately sparse terminal-of-old feel |
| `synthwave` | Retro-futuristic magenta, cyan, and purple segments |
| `ocean` | Calm blues and teals, generous spacing |
| `forest` | Earthy greens and browns, warm segmented layout |
| `midnight` | Near-monochrome and understated, almost nothing shown |
| `sunset` | Warm orange to pink gradient across segments |
| `paper` | High contrast for light-background terminals |
| `terminal-classic` | CRT green sparse prompt, closest thing to a retro terminal |
| `powerline-pro` | Every common module wired up for maximum information |

Run `startheme list` to see this from the CLI, or `startheme browse`
to pull descriptions live from this repository. `startheme preview
<name>` shows a theme's structure before you commit to it.

## Text interface

Running `startheme` with no arguments opens a full-screen interface: a
table of themes on the left, current theme and keybindings on the
right.

```
i   install the selected theme
a   apply the selected theme
d   delete the selected theme
n   create a new theme
p   preview the selected theme
b   browse the remote catalog
r   refresh
q   quit
```

Selecting a theme and pressing `i` downloads it; pressing `a` applies
whatever is selected, backing up your current config first, same as
the command-line `apply`. Destructive actions ask for confirmation
before doing anything.

## Command line reference

```
startheme [COMMAND]

Commands:
  list                List installed and available themes
  search <query>      Search installed and remote themes
  browse              Browse the full remote theme catalog
  install <name>      Download a theme from the startheme repository
  apply <name>        Apply an installed theme as your live prompt
  remove <name>       Remove a downloaded theme (asks for confirmation)
  current             Show the currently applied theme
  create <name>       Create a new theme from a starter template
  edit <name>         Open a theme in $EDITOR
  preview <name>      Preview a theme's structure without applying it
  update              Check the repository for newly added themes
  export <name>       Copy an installed theme out to a file
  import <path>       Import a local TOML file as a named theme
  backups             List, or --restore, configuration backups
  config              Show startheme's configuration
  tui                 Launch the text-based interface
  help                Print this message
```

### Creating your own theme

```
startheme create mytheme
startheme edit mytheme      # opens $EDITOR
startheme preview mytheme   # sanity check before going live
startheme apply mytheme
```

`create` generates a working starter `starship.toml` snippet (OS,
username, directory, git branch/status, and a couple of language
modules) so you are editing something real. See
[Starship's configuration docs](https://starship.rs/config/) for the
full module reference.

### Sharing a theme

```
startheme export mytheme --output mytheme.toml
# send the file to someone, or open a pull request against this repo
startheme import mytheme.toml --name mytheme
```

## Manual installation

If you would rather not run the install script:

```
pip install "git+https://github.com/MaxEdgar/startheme.git"
```

You'll still need [Starship](https://starship.rs) installed separately
and initialized in your shell (`eval "$(starship init bash)"` in
`~/.bashrc`, `starship init fish | source` in `~/.config/fish/config.fish`,
etc. -- see [starship.rs/guide](https://starship.rs/guide/#step-2-set-up-your-shell)).

### Requirements

- Python 3.10 or newer
- A terminal that supports basic ANSI colors (the text interface uses
  [Textual](https://github.com/Textualize/textual), which works in
  virtually any modern terminal, including over SSH)

## Configuration

startheme stores its own state under a platform-appropriate config
directory (`~/.config/startheme` on Linux, honoring `XDG_CONFIG_HOME`
if set; `%APPDATA%\startheme` on Windows):

```
~/.config/startheme/
    config.toml       currently active theme
    themes/           downloaded or created themes
    backups/          timestamped starship.toml snapshots
```

The theme source repository (`MaxEdgar/startheme`) is not
configurable. This is intentional -- the tool is meant to work with
zero setup.

Your live Starship config always stays at the standard
`~/.config/starship.toml`. startheme only copies into it after taking
a backup.

## Development

```
git clone https://github.com/MaxEdgar/startheme.git
cd startheme
pip install -e ".[dev]"
pytest                       # unit, CLI, and theme-catalog tests
python -m startheme.cli list # run against your own machine
```

Project layout:

```
startheme/
    cli.py         command-line entry point and subcommands
    tui.py         Textual-based text interface
    config.py      paths, config.toml, fixed repository settings
    theme.py       theme metadata, local install listing, templates
    github.py      GitHub API and raw-content integration
    backup.py      starship.toml snapshotting and restore
    installer.py   install/apply/remove/export/import orchestration
tests/
    test_*.py           unit tests per module
    test_cli.py         end-to-end tests against the CLI entry point
    test_theme_catalog.py   validates every shipped theme + metadata file
themes/            20 theme TOML files
metadata/          matching metadata for each theme
install.sh         one-line installer
```

See [ROADMAP.md](ROADMAP.md) for what is planned next and
[CONTRIBUTING.md](CONTRIBUTING.md) for how to submit a theme or a patch.

## License

[MIT](LICENSE)
