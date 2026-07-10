"""Interactive text interface for startheme, built with Textual.

Launched by running `startheme` with no arguments, or `startheme tui`
explicitly. No emoji or decorative unicode is used anywhere in this
module so it renders correctly in any terminal.
"""

from __future__ import annotations

from dataclasses import dataclass

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    TextArea,
)

from . import backup as backup_mod
from . import github
from . import installer
from . import theme as theme_mod
from .config import Config, GITHUB_OWNER, GITHUB_REPO, Paths


@dataclass
class ThemeRow:
    name: str
    description: str
    installed: bool
    current: bool


class ConfirmScreen(ModalScreen[bool]):
    """A small yes/no modal, used for destructive actions."""

    CSS = """
    ConfirmScreen {
        align: center middle;
    }
    #dialog {
        width: 50;
        height: auto;
        border: round $warning;
        padding: 1 2;
        background: $surface;
    }
    #buttons {
        height: auto;
        align: right middle;
        padding-top: 1;
    }
    """

    def __init__(self, message: str) -> None:
        super().__init__()
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.message)
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Confirm", id="confirm", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm")


class MessageScreen(ModalScreen[None]):
    """A simple dismissible message modal for status/errors."""

    CSS = """
    MessageScreen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        border: round $primary;
        padding: 1 2;
        background: $surface;
    }
    """

    def __init__(self, title: str, message: str) -> None:
        super().__init__()
        self.title_text = title
        self.message = message

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label(self.title_text, classes="title")
            yield Static(self.message)
            yield Button("OK", id="ok")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(None)


class CreateThemeScreen(ModalScreen[str | None]):
    """Prompts for a new theme name."""

    CSS = """
    CreateThemeScreen {
        align: center middle;
    }
    #dialog {
        width: 50;
        height: auto;
        border: round $primary;
        padding: 1 2;
        background: $surface;
    }
    #buttons {
        height: auto;
        align: right middle;
        padding-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("New theme name")
            yield Input(placeholder="my-theme", id="name-input")
            with Horizontal(id="buttons"):
                yield Button("Cancel", id="cancel")
                yield Button("Create", id="create", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "create":
            value = self.query_one("#name-input", Input).value.strip()
            self.dismiss(value or None)
        else:
            self.dismiss(None)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip() or None)


class StarthemeApp(App):
    """Main Textual application."""

    TITLE = "startheme"
    SUB_TITLE = f"theme manager for Starship  -  source: {GITHUB_OWNER}/{GITHUB_REPO}"

    CSS = """
    Screen {
        layout: vertical;
    }
    #body {
        layout: horizontal;
        height: 1fr;
    }
    #theme-table {
        width: 2fr;
        border: round $primary;
    }
    #sidebar {
        width: 1fr;
        border: round $primary;
        padding: 1 2;
    }
    #sidebar Label {
        margin-bottom: 1;
    }
    #status {
        height: 3;
        border: round $secondary;
        padding: 0 1;
    }
    .title {
        text-style: bold;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("i", "install_selected", "Install"),
        Binding("a", "apply_selected", "Apply"),
        Binding("d", "remove_selected", "Delete"),
        Binding("n", "create_theme", "New"),
        Binding("p", "preview_selected", "Preview"),
        Binding("b", "browse_remote", "Browse remote"),
    ]

    status_text = reactive("Ready.")

    def __init__(self, paths: Paths, cfg: Config) -> None:
        super().__init__()
        self.paths = paths
        self.cfg = cfg
        self.rows: list[ThemeRow] = []

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="body"):
            yield DataTable(id="theme-table", cursor_type="row", zebra_stripes=True)
            with Vertical(id="sidebar"):
                yield Label("Current theme", classes="title")
                yield Static(self.cfg.theme or "(none)", id="current-theme")
                yield Label("")
                yield Label("Keys", classes="title")
                yield Static(
                    "i  install\n"
                    "a  apply\n"
                    "d  delete\n"
                    "n  new theme\n"
                    "p  preview\n"
                    "b  browse remote\n"
                    "r  refresh\n"
                    "q  quit"
                )
        yield Static(self.status_text, id="status")
        yield Footer()

    def on_mount(self) -> None:
        table = self.query_one("#theme-table", DataTable)
        table.add_columns("Name", "Status", "Description")
        self.refresh_table(remote=False)

    def set_status(self, text: str) -> None:
        self.status_text = text
        self.query_one("#status", Static).update(text)

    def refresh_table(self, remote: bool = False) -> None:
        table = self.query_one("#theme-table", DataTable)
        table.clear()

        installed = theme_mod.list_installed(self.paths)
        catalog = {m.name: m for m in theme_mod.builtin_catalog()}

        if remote:
            try:
                for name in github.list_remote_themes():
                    if name not in catalog:
                        catalog[name] = theme_mod.ThemeMetadata(name=name)
                self.set_status(f"Loaded remote catalog from {GITHUB_OWNER}/{GITHUB_REPO}.")
            except github.GitHubError as exc:
                self.set_status(f"Could not reach GitHub: {exc}")

        for name in installed:
            if name not in catalog:
                catalog[name] = theme_mod.ThemeMetadata(name=name, description="Custom theme")

        self.rows = []
        for meta in sorted(catalog.values(), key=lambda m: m.name):
            is_installed = meta.name in installed
            is_current = self.cfg.theme == meta.name
            status = "current" if is_current else ("installed" if is_installed else "remote")
            self.rows.append(ThemeRow(meta.name, meta.description, is_installed, is_current))
            table.add_row(meta.name, status, meta.description, key=meta.name)

        self.query_one("#current-theme", Static).update(self.cfg.theme or "(none)")

    def _selected_name(self) -> str | None:
        table = self.query_one("#theme-table", DataTable)
        if table.row_count == 0:
            return None
        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key
        return str(row_key.value) if row_key.value is not None else None

    def action_refresh(self) -> None:
        self.refresh_table(remote=False)
        self.set_status("Refreshed local state.")

    def action_browse_remote(self) -> None:
        self.set_status(f"Contacting {GITHUB_OWNER}/{GITHUB_REPO} ...")
        self.refresh_table(remote=True)

    @work(exclusive=True, thread=True)
    def _install_worker(self, name: str) -> None:
        try:
            installer.install(self.paths, name, force=True)
            self.call_from_thread(self.set_status, f"Installed {name}.")
        except Exception as exc:  # noqa: BLE001 - surfaced to the user
            self.call_from_thread(self.set_status, f"Install failed: {exc}")
        finally:
            self.call_from_thread(self.refresh_table, False)

    def action_install_selected(self) -> None:
        name = self._selected_name()
        if not name:
            return
        self.set_status(f"Downloading {name} ...")
        self._install_worker(name)

    def action_apply_selected(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if not theme_mod.is_installed(self.paths, name):
            self.set_status(f"'{name}' is not installed yet. Press i to install it first.")
            return
        try:
            backup_path = installer.apply(self.paths, self.cfg, name)
        except Exception as exc:  # noqa: BLE001
            self.set_status(f"Apply failed: {exc}")
            return
        msg = f"Applied {name}."
        msg += f" Backup saved to {backup_path}." if backup_path else " No prior config to back up."
        self.set_status(msg)
        self.refresh_table(remote=False)

    def action_remove_selected(self) -> None:
        name = self._selected_name()
        if not name or not theme_mod.is_installed(self.paths, name):
            self.set_status("Nothing installed to remove for this selection.")
            return

        def handle_confirm(confirmed: bool | None) -> None:
            if not confirmed:
                return
            try:
                installer.remove(self.paths, self.cfg, name)
                self.set_status(f"Removed {name}.")
            except Exception as exc:  # noqa: BLE001
                self.set_status(f"Remove failed: {exc}")
            self.refresh_table(remote=False)

        self.push_screen(ConfirmScreen(f"Remove theme '{name}'?"), handle_confirm)

    def action_create_theme(self) -> None:
        def handle_name(name: str | None) -> None:
            if not name:
                return
            try:
                theme_mod.create_theme(self.paths, name, author="you", force=False)
                self.set_status(f"Created {name}. Edit it with: startheme edit {name}")
            except Exception as exc:  # noqa: BLE001
                self.set_status(f"Create failed: {exc}")
            self.refresh_table(remote=False)

        self.push_screen(CreateThemeScreen(), handle_name)

    def action_preview_selected(self) -> None:
        name = self._selected_name()
        if not name:
            return
        if not theme_mod.is_installed(self.paths, name):
            self.set_status(f"'{name}' is not installed yet. Press i to install it first.")
            return
        contents = theme_mod.read_theme_contents(self.paths, name)
        preview = "\n".join(contents.splitlines()[:25])
        self.push_screen(MessageScreen(f"Preview: {name}", preview))
