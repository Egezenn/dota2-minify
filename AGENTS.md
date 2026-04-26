# Dota2 Minify

`dota2-minify` is a modding tool and manager for Dota 2, designed to streamline the modification of game files, UI configurations, styling, and application of specific game patches.

## Tech Stack

- **Language**: Python 3.13
- **Package Manager**: `uv`
- **GUI Framework**: DearPyGui (DPG)

## Core Directory Structure

- `Minify/`: The main application package.
  - `__main__.py`: The entry point for the DearPyGui application.
  - `build.py`: Handles compiling, extracting, and patching Mod files into Dota 2 VPK format.
  - `conditions.py`: System conditionals (verifying paths, workshop tools status).
  - `helper.py`: Provides utility functions to compile images, execute mod scripts dynamically, etc.

  - `bin/`: Contains static utility files such as `localization.json` and `gamepakcontents.txt` (a complete list of files inside the game pak, created once a patch is ran).

  - `core/`: Contains fundamental backend modules:
    - `base.py`: Unchanging static variables, paths, and OS-level info.
    - `config.py`: Utilities for reading and writing JSON config files (`minify_config.json`, `mods.json`).
    - `constants.py`: Important static paths and pre-calculated lists for the patching pipeline.
    - `fs.py`: File system utilities, path manipulation, reading/writing/copying files.
    - `log.py`: Handles unhandled exceptions and writes warnings/crashes to log files.
    - `mods_shared.py`: Shared capabilities specific to handling mods logic.
    - `steam.py`: Functions to detect Steam directories, game paths, and modify launch options.
    - `utils.py`: Shared utilities

  - `ui/`: Contains the DearPyGui interface logic:
    - `announcements.py`: Fetches and displays global announcements to users on app start.
    - `checkboxes.py`: Logic for rendering and managing the state of mod enablement checkboxes.
    - `details.py`: Renders the detailed view of an individual mod (parsing `notes.md` and preview image).
    - `dev_tools.py`: Helper GUI functionalities intended for developers or advanced debugging.
    - `fonts.py`: Registers and initializes different custom fonts for DearPyGui.
    - `gui.py`: Manages the overall layout logic, viewport scaling, and rendering routines.
    - `localization.py`: Multi-language dynamic text localization support.
    - `markdown.py`: Custom parser to render markdown files (`notes.md`) using DPG items.
    - `modal_shared.py`: Base components for pop-up dialogs and modals.
    - `modals.py`: Implementations of specific modals (Uninstall, Announcements, Update dialogs).
    - `settings.py`: The powerhouse for rendering the global settings menu, including the dynamic generation of mod-specific configuration options.
    - `shared.py`: Stores minimal state shared across UI modules.
    - `terminal.py`: Draws the "terminal" window in the UI that logs the patching progress in real-time.
    - `theme.py`: Configures the DearPyGui color maps, styles, and dark-theme configurations.
    - `window.py`: Window focus logic and drag/drop/resize helper implementations.
  - `mods/`: The root directory for all available mods native to Minify. Each subdirectory represents a standalone mod.

### Third-Party Dependencies

The application uses external executables downloaded at runtime into the `Minify/` directory:

- **Ripgrep (`rg.exe`)**: Utilized for extremely fast, pattern-based text searching and filtering during the compilation and patching processes. May use it from system if existent.
- **Source2Viewer (`Source2Viewer-CLI.exe`)**: Used to parse, decompile, or convert proprietary Source 2 engine assets into usable formats. Downloaded only if Workshop Tools are available.

Additionally, it interacts with Dota 2 Workshop Tools if the DLC is installed:

- **ResourceCompiler (`resourcecompiler.exe`)**: Invoked by Minify to compile raw assets (XML, CSS etc.) into their Source 2 binary equivalents (`_c`).
- **Note:** Minify provides `helper.compile_assets()`, a convenient wrapper function that automatically handles compiling images and other assets using this tool. It can also generate a pak from the compiled assets.

## The Modding System

Mods in Minify are robust and programmatically driven.

### `modcfg.json`

Mods can optionally include a `modcfg.json` file. It dictates how the mod interacts with the Minify system and how it is exposed in the Settings UI.
Key objects in the `modcfg.json` settings array include:

- **Input Types**: `checkbox`, `combo`, `number` (`int`/`float`), `slider`, `color`, `list`, `button`.
- Settings are rendered dynamically by `Minify/ui/settings.py` based on exactly what is defined in `modcfg.json`.
- **Presets**: The `presets` list allows developers to provide predefined combinations of setting values.

### Mod Scripts

Mods can execute custom Python behavior via standardized script hooks:

- `script_initial.py`, `script_after_decompile.py`, `script_after_patch.py`, `script_uninstall.py`, etc.
When writing custom logic for a mod, hook into these files.

### XML & CSS Injection

Mods dynamically patch Dota 2's UI layout (`xml_mod.json`) and styling (`styling.css`). The build engine compiles and merges these changes alongside base VPK content.

## General Advice for Agents

- Always reference `docs/wiki/development/mod-structure.md`, `docs/wiki/development/scripting.md`, and `docs/wiki/development/ui-modding.md` if you are modifying or debugging how mod folders are structured, what files they support, and how the `__main__.py` patching loop reads them.
- DearPyGui (`dpg`) has strict state requirements. Do not delete items that are still referenced elsewhere in the DPG registry without proper cleanup.
- Keep UI operations on the main thread and respect `gui.lock_interaction()` when heavy I/O operations (like extracting/packing VPKs) are running.
- If the user is experiencing issues, the tracebacks and other info are located in `Minify/logs`.
- If a mod requires something really specific or complex, it should be decoupled into its own script.
- Any features or scripts that require internet connectivity **MUST** be able to fail silently without crashing the application.
- **Filesystem Operations**: Prefer using the `os` module (and `os.path`) over `pathlib`. Some project dependencies are older and expect string-based paths; using `pathlib` can lead to subtle bugs or type errors in these contexts.
- When running or creating standalone scripts in subdirectories (like `tests/` or `scripts/`), always ensure the `Minify/` directory is added to `sys.path` to allow proper imports of `core` and `ui` packages:
- Always run `scripts/precommit.sh` to check for and resolve any linting or test errors before committing your changes.

  ```python
  import os
  import sys
  sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../Minify")))
  ```

- All structural or build-related changes must maintain compatibility with the automated release process defined in `.github/workflows/release.yml`.
- **Dependencies**: If you add any new dependencies (production or dev), you MUST add them to the `README.md` dependencies section.

## Development Guidelines

- **Line Length**: 120 (Configured in `pyproject.toml`).
- **Formatting**: We use `black` and any other formatter that conforms to its logic (`ruff format`).
- **Linting & Imports**:
  - We use `ruff check` as our primary linter.
  - To organize and sort imports, use: `ruff check . --select I --fix`.
  - Avoid using function top imports (local imports) unless absolutely necessary. While cyclic imports are common in this project, analyze the dependency chain thoroughly before resorting to them.
- **PR Naming**:
  - Use the format `<category>: concise title`.
  - Categories: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`.
  - No flavor, no emojis, straight to the point.
- **Pylint**: Seldomly used to scour for anything missed by Ruff. Ignore rules are in `pyproject.toml`.
- **VSCode Extensions**: Recommended extensions can be found in `.vscode/extensions.json`.

## Testing Guidelines

Following these guidelines ensures that our tests are reliable, readable, and maintainable.

### 1. Core Principles

- **Isolation**: Each test should be independent. Side effects from one test must not affect another.
- **Speed**: Tests should be fast. Use mocking for heavy I/O operations (network, disk, subprocesses).
- **Correctness**: Tests should verify both happy paths and edge cases (errors, empty inputs, invalid types).
- **Surgical Mocking**: Only mock what is necessary. Prefer mocking the `core` modules rather than standard library functions.

### 2. Environment Setup

- **sys.path**: Ensure the `Minify/` directory is in `sys.path`.
- **Mocking core.config**: Most modules depend on `core.config`. Mock it early to avoid hitting the real config file:

  ```python
  from unittest.mock import MagicMock
  import core.config
  core.config.get = MagicMock(side_effect=lambda key, default=None: default)
  core.config.set = MagicMock()
  ```

### 3. Recommended Tools

- **Framework**: `pytest`
- **Mocking**: `unittest.mock` (`patch`, `MagicMock`, `call`)
- **Assertions**: Standard `assert` statements.

### 4. Test Structure

- **File Naming**: Located in `tests/`, following `test_<module_name>.py`.
- **Function Naming**: Start with `test_`, use descriptive names: `test_<function_name>_<scenario>_<expected_result>`.
- **Parametrization**: Use `@pytest.mark.parametrize` for multiple inputs.

### 5. Handling the Filesystem

- **tmp_path**: Always use the `tmp_path` fixture for real filesystem interaction.
- **Mocking os.path.exists**: Use `@patch("os.path.exists", return_value=True)` when a real filesystem isn't needed.

### 6. Common Patterns

- **Mocking core.utils.open_utf8R**: Mock internal file utilities to control content.
- **monkeypatch**: Use in fixtures for reusable mocked environments.

## Debugging & Developer Tools

The application includes a specialized developer toolbox accessible via the **Hammer Icon** in the UI.

- Use **Create debug zip** to gather logs and configurations for bug reports.
- Use **Dev Tools** to access utilities (e.g., file openers, path openers, and compilation). (Note: Advanced debugging features like inspecting the DearPyGui item registry, managing window states, and debugging UI layouts in real-time are only available when running **unfrozen** with the `debug_env` key set to `True`).
