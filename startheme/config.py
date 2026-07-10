"""Configuration and filesystem paths for startheme.

The theme source repository is fixed to the official startheme repo.
This is intentional: startheme is meant to work out of the box with
zero setup, and the whole point of hardcoding this is that `install`,
`browse`, and `update` just work the first time you run them.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

# Hardcoded upstream theme repository. Do not make this configurable;
# see the module docstring above.
GITHUB_OWNER = "MaxEdgar"
GITHUB_REPO = "startheme"
GITHUB_REF = "main"

APP_NAME = "startheme"

_VALID_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def is_valid_theme_name(name: str) -> bool:
    """True if `name` is a safe, simple identifier.

    Restricting to letters, numbers, dash, and underscore prevents
    path traversal via crafted theme names (e.g. "../../etc/passwd").
    """
    return bool(name) and bool(_VALID_NAME_RE.match(name))


def assert_valid_name(name: str) -> None:
    if not is_valid_theme_name(name):
        raise ValueError(
            f"'{name}' is not a valid theme name "
            "(use letters, numbers, - and _ only)"
        )


def _xdg_config_home() -> Path:
    """Resolve the config root the same way most Linux tools do,
    while still being reasonable on macOS and Windows.
    """
    env = os.environ.get("XDG_CONFIG_HOME")
    if env:
        return Path(env)
    if os.name == "nt":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata)
    return Path.home() / ".config"


@dataclass
class Paths:
    """Resolves all on-disk locations startheme cares about."""

    config_dir: Path
    themes_dir: Path
    backups_dir: Path
    config_file: Path
    starship_config: Path

    @classmethod
    def resolve(cls) -> "Paths":
        config_dir = _xdg_config_home() / APP_NAME
        return cls(
            config_dir=config_dir,
            themes_dir=config_dir / "themes",
            backups_dir=config_dir / "backups",
            config_file=config_dir / "config.toml",
            starship_config=Path.home() / ".config" / "starship.toml",
        )

    def ensure_dirs(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.themes_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.starship_config.parent.mkdir(parents=True, exist_ok=True)

    def theme_path(self, name: str) -> Path:
        return self.themes_dir / f"{name}.toml"


@dataclass
class Config:
    """Persistent, user-editable state (currently just the active
    theme name). The theme source repo is intentionally not part of
    this -- see GITHUB_OWNER / GITHUB_REPO above.
    """

    theme: str | None = None

    @staticmethod
    def load(paths: Paths) -> "Config":
        if not paths.config_file.exists():
            cfg = Config()
            cfg.save(paths)
            return cfg
        theme = None
        for line in paths.config_file.read_text().splitlines():
            line = line.strip()
            if line.startswith("theme"):
                _, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                theme = value or None
        return Config(theme=theme)

    def save(self, paths: Paths) -> None:
        paths.ensure_dirs()
        theme_value = f'"{self.theme}"' if self.theme else '""'
        contents = (
            "# startheme configuration\n"
            "# The theme source repository is fixed; see startheme.config\n"
            f"theme = {theme_value}\n"
            f'github_owner = "{GITHUB_OWNER}"\n'
            f'github_repo = "{GITHUB_REPO}"\n'
            f'github_ref = "{GITHUB_REF}"\n'
        )
        paths.config_file.write_text(contents)
