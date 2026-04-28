# /// script
# dependencies = [
#   "textual",
#   "jstyleson",
#   "pygments",
#   "Pillow",
#   "pathspec",
# ]
# ///

import os
import sys
import jstyleson
from pathlib import Path
from typing import Dict, List, Any, Optional

from rich.syntax import Syntax
from rich.text import Text
from rich.tree import Tree
from PIL import Image
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, ListView, ListItem, Label, Static, DataTable
from textual.containers import Container, Vertical, VerticalScroll
from textual import events
import pathspec

# Add Minify to sys.path to allow imports from core
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))


def format_size(size_bytes: int) -> str:
    if size_bytes == 0:
        return "0B"
    import math

    size_name = ("B", "KB", "MB", "GB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "%s %s" % (s, size_name[i])


def get_loc(path: Path) -> str:
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f"{len(f.readlines())} lines"
    except Exception:
        return "Error"


class ModInfo:
    SCRIPT_HOOKS = [
        "script_initial.py",
        "script_after_decompile.py",
        "script_after_recompile.py",
        "script_after_patch.py",
        "script_uninstall.py",
        "script_utility.py",
        "script.py",
    ]

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.warnings: List[str] = []
        self.recommendations: List[str] = []
        self.errors: List[str] = []
        self.config: Dict[str, Any] = {}
        self.files_count = 0
        self.uncompiled_count = 0
        self.scripts: List[str] = []
        self.has_notes = False
        self.has_preview = False
        self.has_xml = False
        self.has_styling = False
        self.has_blacklist = False
        self.preview_text: Optional[Text] = None
        self.last_preview_width: int = 0
        self.total_size = 0
        self.analyze()

    def analyze(self):
        # Stats
        self.total_size = sum(f.stat().st_size for f in self.path.rglob("*") if f.is_file())

        def check_file(filename, exists_attr, severity=None, msg=None, check_json=False):
            p = self.path / filename
            exists = p.exists()
            if exists_attr:
                setattr(self, exists_attr, exists)
            if not exists:
                if severity == "W":
                    self.warnings.append(msg)
                elif severity == "R":
                    self.recommendations.append(msg)
                return None
            if check_json:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        return jstyleson.load(f)
                except Exception as e:
                    self.errors.append(f"Invalid {filename}: {e}")
            return True

        self.config = check_file("modcfg.json", None, "R", "Missing modcfg.json", True) or {}
        check_file("notes.md", "has_notes", "W", "Missing notes.md")
        check_file("preview.png", "has_preview", "R", "Missing preview.png")
        check_file("xml_mod.json", "has_xml", None, None, True)
        check_file("styling.css", "has_styling")
        check_file("blacklist.txt", "has_blacklist")

        # Directories
        for d, attr in [("files", "files_count"), ("files_uncompiled", "uncompiled_count")]:
            dp = self.path / d
            if dp.exists() and dp.is_dir():
                setattr(self, attr, sum(1 for f in dp.rglob("*") if f.is_file()))

        # Scripts
        self.scripts = [s for s in self.SCRIPT_HOOKS if (self.path / s).exists()]

        # Pre-calculate table rows
        self.active_rows = []
        self.inactive_rows = []

        # settings/presets
        for key, label in [("settings", "Settings Count"), ("presets", "Presets Count")]:
            count = len(self.config.get(key, []))
            if count > 0:
                self.active_rows.append((label, str(count)))
            else:
                self.inactive_rows.append((label, "0"))

        # counts
        for count, label in [(self.files_count, "Compiled Files"), (self.uncompiled_count, "Uncompiled Files")]:
            if count > 0:
                self.active_rows.append((label, str(count)))
            else:
                self.inactive_rows.append((label, "0"))

        # scripts
        if self.scripts:
            self.active_rows.append(("Python Scripts", ", ".join(self.scripts)))
        else:
            self.inactive_rows.append(("Python Scripts", "None"))

        # files
        file_checks = [
            ("modcfg.json", self.path / "modcfg.json", (self.path / "modcfg.json").exists()),
            ("notes.md", self.path / "notes.md", self.has_notes),
            ("xml_mod.json", self.path / "xml_mod.json", self.has_xml),
            ("styling.css", self.path / "styling.css", self.has_styling),
            ("blacklist.txt", self.path / "blacklist.txt", self.has_blacklist),
        ]
        for name, path, exists in file_checks:
            if exists:
                self.active_rows.append((name, get_loc(path)))
            else:
                self.inactive_rows.append((name, "No"))

        if self.has_preview:
            try:
                with Image.open(self.path / "preview.png") as img:
                    self.active_rows.append(("preview.png", f"{img.width}x{img.height} px"))
            except Exception:
                self.active_rows.append(("preview.png", "Yes"))
        else:
            self.inactive_rows.append(("preview.png", "No"))

    @property
    def status_symbol(self) -> str:
        if self.errors:
            return "E"
        if self.warnings:
            return "W"
        if self.recommendations:
            return "R"
        return "✓"


class ModListItem(ListItem):
    def __init__(self, mod: ModInfo):
        super().__init__()
        self.mod = mod

    def compose(self) -> ComposeResult:
        yield Label(f"({self.mod.status_symbol}) {self.mod.name}")


class SummaryItem(ListItem):
    def __init__(self, mods: List[ModInfo]):
        super().__init__()
        self.mods = mods
        self.label = Label("(S) [bold]Project Summary[/bold]")

    def compose(self) -> ComposeResult:
        yield self.label


class ModBrowser(App):
    TITLE = "Dota2 Minify Mod Browser"
    CSS = """
    Screen {
        layout: horizontal;
    }

    #sidebar {
        width: 35%;
        height: 100%;
        border-right: tall $primary;
        background: $surface;
    }

    #main-content {
        width: 65%;
        height: 100%;
        padding: 1;
    }

    .status-ok { color: green; }
    .status-warn { color: yellow; }
    .status-error { color: red; }

    DataTable {
        height: auto;
        max-height: 15;
        margin-top: 1;
        border: solid $accent;
    }

    #analysis-results {
        margin-top: 1;
        padding: 1;
        background: $boost;
        border: round $primary;
        height: 1fr;
    }

    #analysis-results Static {
        height: auto;
    }

    Header {
        background: $primary-darken-2;
        color: white;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("p", "go_to_summary", "Project Summary"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="sidebar"):
            yield Label("Mods List", variant="header")
            yield ListView(id="mod-list")
        with Vertical(id="main-content"):
            yield Label("Select an item to see details", id="mod-title")
            yield DataTable(id="mod-details")
            yield Label("File Preview / Analysis", variant="header")
            with VerticalScroll(id="analysis-results"):
                yield Static(id="analysis-text", expand=True)
        yield Footer()

    def on_mount(self) -> None:
        self.root_dir = Path(__file__).parent.parent
        self.spec = None
        gitignore_path = self.root_dir / ".gitignore"
        if gitignore_path.exists():
            with open(gitignore_path, "r", encoding="utf-8") as f:
                self.spec = pathspec.PathSpec.from_lines("gitwildmatch", f)
        self.last_selected_prop = "Relative Path"
        self.refresh_mods()
        self.query_one("#mod-list", ListView).index = 0
        self.show_summary()

    def action_refresh(self) -> None:
        self.refresh_mods()

    def refresh_mods(self) -> None:
        mod_list = self.query_one("#mod-list", ListView)
        mod_list.clear()

        base_path = Path(__file__).parent.parent / "Minify" / "mods"
        self.mods = []
        for d in base_path.iterdir():
            if d.is_dir() and not d.name.startswith("_"):
                self.mods.append(ModInfo(d))

        # Sort mods: Errors first, then Warnings, then OK
        self.mods.sort(key=lambda m: (len(m.errors) == 0, len(m.warnings) == 0, m.name))

        mod_list.append(SummaryItem(self.mods))
        for mod in self.mods:
            mod_list.append(ModListItem(mod))

    def on_key(self, event: events.Key) -> None:
        focused = self.focused
        if event.key == "right" and focused and focused.id == "mod-list":
            self.query_one("#mod-details").focus()
            event.stop()
        elif event.key == "left" and focused and focused.id == "mod-details":
            table = self.query_one("#mod-details", DataTable)
            if table.cursor_column == 0:
                self.query_one("#mod-list").focus()
                event.stop()
        elif event.key == "left" and focused and focused.id == "analysis-results":
            self.query_one("#mod-details").focus()
            event.stop()

    def on_list_view_highlighted(self, message: ListView.Highlighted) -> None:
        if isinstance(message.item, ModListItem):
            self.show_mod_details(message.item.mod)
        elif isinstance(message.item, SummaryItem):
            self.show_summary()

    def on_list_view_selected(self, message: ListView.Selected) -> None:
        # Same as highlighted to ensure both work
        if isinstance(message.item, ModListItem):
            self.show_mod_details(message.item.mod)
        elif isinstance(message.item, SummaryItem):
            self.show_summary()
        self.query_one("#mod-details").focus()

    def action_go_to_summary(self) -> None:
        mod_list = self.query_one("#mod-list", ListView)
        mod_list.index = 0
        self.show_summary()
        mod_list.focus()

    def get_loc(self, path: Path) -> str:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f"{len(f.readlines())} lines"
        except Exception:
            return "Error"

    def render_file_tree(self, path: Path, label: str = None) -> Tree:
        tree = Tree(f"[bold cyan]{label or path.name}/[/bold cyan]")

        def add_to_tree(target_tree: Tree, current_path: Path):
            items = sorted(list(current_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            for item in items:
                # Explicitly skip unwanted folders in tree
                if item.name == "__pycache__" or item.name.startswith(".") or item.name.startswith("#"):
                    continue

                # Check if ignored - Disable for Minify/mods contents
                if self.spec and "Minify/mods" not in item.as_posix():
                    rel_p = item.relative_to(self.root_dir).as_posix()
                    # pathspec match_file expects the path to be relative to the spec root
                    if self.spec.match_file(rel_p):
                        continue

                if item.is_dir():
                    branch = target_tree.add(f"[bold blue]{item.name}/[/bold blue]")
                    add_to_tree(branch, item)
                else:
                    target_tree.add(item.name)

        add_to_tree(tree, path)
        return tree

    def show_mod_details(self, mod: ModInfo) -> None:
        title = self.query_one("#mod-title", Label)
        title.update(f"Mod: [bold cyan]{mod.name}[/bold cyan]")

        table = self.query_one("#mod-details", DataTable)
        table.clear(columns=True)
        table.add_columns("Property", "Value")

        table.add_row("Relative Path", str(mod.path.relative_to(self.root_dir)))
        table.add_row("Total Size", format_size(mod.total_size))

        for row in mod.active_rows:
            table.add_row(*row)

        if mod.inactive_rows:
            table.add_row("[dim]────────────────────[/dim]", "[dim]──────────[/dim]")
            for row in mod.inactive_rows:
                table.add_row(*row)

        # Restore selection
        if hasattr(self, "last_selected_prop"):
            for i in range(table.row_count):
                if table.get_row_at(i)[0] == self.last_selected_prop:
                    table.move_cursor(row=i)
                    break

        self.current_mod = mod
        self.update_analysis_area(mod)

    def on_data_table_cell_selected(self, message: DataTable.CellSelected) -> None:
        # On Enter/Select, focus the preview area so it can be scrolled
        self.query_one("#analysis-results").focus()

    def on_data_table_cell_highlighted(self, message: DataTable.CellHighlighted) -> None:
        table = self.query_one("#mod-details", DataTable)
        row_index = message.coordinate.row
        row_data = table.get_row_at(row_index)
        prop_name = row_data[0]
        self.last_selected_prop = prop_name

        if not hasattr(self, "current_mod") or not self.current_mod:
            self._handle_summary_preview(prop_name)
            return

        # Mod-specific previews
        if prop_name in ["notes.md", "xml_mod.json", "styling.css", "modcfg.json", "blacklist.txt"]:
            self._handle_file_preview(prop_name)
        elif prop_name in ["Compiled Files", "Uncompiled Files"]:
            self._handle_directory_preview(prop_name)
        elif prop_name == "preview.png":
            self._handle_image_preview()
        elif prop_name == "Python Scripts" and self.current_mod.scripts:
            self._handle_scripts_preview()
        else:
            try:
                self.query_one("#analysis-text", Static).update(self.render_file_tree(self.current_mod.path))
            except Exception:
                self.update_analysis_area(self.current_mod)

    def _handle_summary_preview(self, prop_name: str) -> None:
        try:
            output = []
            if prop_name == "Total Mods Scanned":
                output.append("[bold cyan]All Mods:[/bold cyan]")
                for m in sorted(self.mods, key=lambda x: x.name):
                    output.append(f" - {m.name}")
            elif prop_name == "Total Size of All Mods":
                output.append("[bold cyan]Mods by Size (Descending):[/bold cyan]")
                for m in sorted(self.mods, key=lambda x: x.total_size, reverse=True):
                    output.append(f" - {m.name}: {format_size(m.total_size)}")
            elif prop_name == "Mods with Errors":
                output.append("[bold red]Mods with Errors:[/bold red]")
                for m in sorted([m for m in self.mods if m.errors], key=lambda x: x.name):
                    errs_str = ", ".join(m.errors)
                    output.append(f" - {m.name} ({errs_str})")
            elif prop_name == "Mods with Warnings":
                output.append("[bold yellow]Mods with Warnings:[/bold yellow]")
                for m in sorted([m for m in self.mods if m.warnings], key=lambda x: x.name):
                    warns_str = ", ".join(m.warnings)
                    output.append(f" - {m.name} ({warns_str})")
            elif prop_name == "Mods with Recommendations":
                output.append("[bold cyan]Mods with Recommendations:[/bold cyan]")
                for m in sorted([m for m in self.mods if m.recommendations], key=lambda x: x.name):
                    recs_str = ", ".join(m.recommendations)
                    output.append(f" - {m.name} ({recs_str})")
            elif prop_name == "Mods Perfect (OK)":
                output.append("[bold green]Perfect Mods:[/bold green]")
                for m in sorted(
                    [m for m in self.mods if not (m.errors or m.warnings or m.recommendations)], key=lambda x: x.name
                ):
                    output.append(f" - {m.name}")
            elif prop_name == "Total Script Files":
                output.append("[bold cyan]Mods by Script Count (Descending):[/bold cyan]")
                for m in sorted([m for m in self.mods if m.scripts], key=lambda x: len(x.scripts), reverse=True):
                    output.append(f" - {m.name}: {len(m.scripts)} scripts")

            if output:
                self.query_one("#analysis-text", Static).update("\n".join(output))
        except Exception as e:
            self.query_one("#analysis-text", Static).update(f"[red]Summary Preview Error: {e}[/red]")

    def _handle_file_preview(self, prop_name: str) -> None:
        file_path = self.current_mod.path / prop_name
        if not file_path.exists():
            self.query_one("#analysis-text", Static).update("")
            return

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(10000)
                lexer = {".md": "markdown", ".json": "jsonc", ".css": "css", ".py": "python"}.get(
                    file_path.suffix, "text"
                )
                syntax = Syntax(content, lexer, theme="monokai", line_numbers=True, word_wrap=True)
                self.query_one("#analysis-text", Static).update(syntax)
        except Exception as e:
            self.query_one("#analysis-text", Static).update(f"[red]Error reading file: {e}[/red]")

    def _handle_directory_preview(self, prop_name: str) -> None:
        dir_name = "files" if prop_name == "Compiled Files" else "files_uncompiled"
        dir_path = self.current_mod.path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            try:
                self.query_one("#analysis-text", Static).update(self.render_file_tree(dir_path, f"{dir_name}/"))
            except Exception as e:
                self.query_one("#analysis-text", Static).update(f"[red]Error generating tree: {e}[/red]")
        else:
            self.query_one("#analysis-text", Static).update("")

    def _handle_image_preview(self) -> None:
        file_path = self.current_mod.path / "preview.png"
        if not file_path.exists():
            self.query_one("#analysis-text", Static).update("")
            return

        try:
            container = self.query_one("#analysis-results")
            width = (container.content_size.width - 2) if container.content_size.width > 10 else 40

            # Use cached preview if width hasn't changed
            if self.current_mod.preview_text and self.current_mod.last_preview_width == width:
                self.query_one("#analysis-text", Static).update(self.current_mod.preview_text)
                return

            img = Image.open(file_path).convert("RGB")
            aspect = img.height / img.width
            new_h = int(width * aspect * 0.5)
            img = img.resize((width, new_h), Image.Resampling.LANCZOS)

            text = Text()
            for y in range(new_h):
                for x in range(width):
                    r, g, b = img.getpixel((x, y))
                    text.append("█", style=f"rgb({r},{g},{b})")
                if y < new_h - 1:
                    text.append("\n")

            self.current_mod.preview_text = text
            self.current_mod.last_preview_width = width
            self.query_one("#analysis-text", Static).update(text)
        except Exception as e:
            self.query_one("#analysis-text", Static).update(f"[red]Error rendering image: {e}[/red]")

    def _handle_scripts_preview(self) -> None:
        all_content = []
        for script in self.current_mod.scripts:
            try:
                with open(self.current_mod.path / script, "r", encoding="utf-8") as f:
                    all_content.append(f"# --- {script} ---\n{f.read(5000)}\n")
            except Exception as e:
                all_content.append(f"# Error reading {script}: {e}\n")

        syntax = Syntax("\n".join(all_content), "python", theme="monokai", line_numbers=True, word_wrap=True)
        self.query_one("#analysis-text", Static).update(syntax)

    def update_analysis_area(self, mod: ModInfo) -> None:
        results = self.query_one("#analysis-text", Static)
        output = []
        if mod.errors:
            output.append("[bold red]Critical Errors:[/bold red]")
            for err in mod.errors:
                output.append(f" [ERR] {err}")

        if mod.warnings:
            if output:
                output.append("")
            output.append("[bold yellow]Mandatory Warnings (Should be fixed):[/bold yellow]")
            for warn in mod.warnings:
                output.append(f" [WRN] {warn}")

        if mod.recommendations:
            if output:
                output.append("")
            output.append("[bold cyan]Recommendations:[/bold cyan]")
            for rec in mod.recommendations:
                output.append(f" [R] {rec}")

        if not mod.errors and not mod.warnings and not mod.recommendations:
            output.append("[bold green]OK: This mod looks perfect for release![/bold green]")
        elif not mod.errors and not mod.warnings:
            output.append("")
            output.append("[bold green]OK: No mandatory issues found.[/bold green]")

        results.update("\n".join(output))

    def show_summary(self) -> None:
        title = self.query_one("#mod-title", Label)
        title.update("[bold magenta]Project-wide Summary[/bold magenta]")

        total_mods = len(self.mods)
        total_size = sum(m.total_size for m in self.mods)
        mods_with_errors = sum(1 for m in self.mods if m.errors)
        mods_with_warnings = sum(1 for m in self.mods if m.warnings and not m.errors)
        mods_with_recs = sum(1 for m in self.mods if m.recommendations and not m.errors and not m.warnings)
        mods_ok = sum(1 for m in self.mods if not m.errors and not m.warnings and not m.recommendations)

        table = self.query_one("#mod-details", DataTable)
        table.clear(columns=True)
        table.add_columns("Metric", "Value")
        table.add_row("Total Mods Scanned", str(total_mods))
        table.add_row("Total Size of All Mods", format_size(total_size))
        table.add_row("Mods with Errors", f"[red]{mods_with_errors}[/red]")
        table.add_row("Mods with Warnings", f"[yellow]{mods_with_warnings}[/yellow]")
        table.add_row("Mods with Recommendations", f"[cyan]{mods_with_recs}[/cyan]")
        table.add_row("Mods Perfect (OK)", f"[green]{mods_ok}[/green]")
        table.add_row("Total Script Files", str(sum(len(m.scripts) for m in self.mods)))

        results = self.query_one("#analysis-text", Static)
        output = [
            f"[bold]Overall Status:[/bold]",
            f" - Critical errors (E) in {mods_with_errors} mods.",
            f" - Mandatory warnings (W) in {mods_with_warnings} mods.",
            f" - Recommendations (I) in {mods_with_recs} mods.",
            "",
            "[bold cyan]Action Items:[/bold cyan]",
            " 1. Fix all [red](E)[/red] (Invalid JSON etc.)",
            " 2. Address [yellow](W)[/yellow] (Missing notes.md)",
            " 3. Review [cyan](I)[/cyan] (Missing modcfg/previews)",
            " 4. Run precommit.sh before pushing",
        ]
        results.update("\n".join(output))
        self.current_mod = None


if __name__ == "__main__":
    app = ModBrowser()
    app.run()
