## Python API Reference

Extensive symbol dump that lists docstrings, source codes is available [here](/development/symbols/).

> [!NOTE]
> The API might change, however with 1.13.1's base, you'll have compatibility until the next major release.
>
> Not all variables are dumped in the symbol index; only [core.base](/development/symbols/core.base) and [core.constants](/development/symbols/core.constants) include them to keep the documentation focused.

Following are necesities for modders, briefly explained:

### `script.py` template

If and when there is a specific behavior to be automated you can include a python script along with your mod. You can find the template below.

Appending `_initial, _after_decompile, _after_recompile, _after_patch, _uninstall` to your script's name will adjust when it'll be executed. Thus giving you the full control of how your mod can be handled. By default it executes while iterating over each mod when you are patching.

```python
# This script template can be run both manually and from minify.
# You are able to use packages and modules from minify (you need an activated environment from the minify root or running with the tool `uv` can automatically handle this.)
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
minify_root = os.path.abspath(os.path.join(current_dir, os.pardir, os.pardir))
os.chdir(minify_root)

if minify_root not in sys.path:
    sys.path.insert(0, minify_root)

# isort: split

# Any package or module native to minify can be imported here
# import requests
#
# import fs
# ...


def main():
    pass
    # Code specific to your mod goes here, minify will try to execute this block.
    # If any exceptions occur, it'll be written to `logs` directory


if __name__ == "__main__":
    main()
```

### Platform & Version Utilities

When writing scripts, you often need to handle platform differences or check for app compatibility. The [Minify/core/base.py](/development/symbols/core.base) module provides several pre-calculated variables for this:

- **[`VERSION`](/development/symbols/core.base#version)**: The current Minify version string. Use it for compatibility checks.
- **[`OS`](/development/symbols/core.base#os)**: The current operating system name.
- **[`WIN`](/development/symbols/core.base#win)**, **[`LINUX`](/development/symbols/core.base#linux)**, **[`MAC`](/development/symbols/core.base#mac)**: Constants for comparison.
  - `base.WIN` is `"Windows"`
  - `base.LINUX` is `"Linux"`
  - `base.MAC` is `"Darwin"`
- **[`MACHINE`](/development/symbols/core.base#machine)**: The hardware architecture (e.g., `x86_64`, `arm64`).
- **[`ARCHITECTURE`](/development/symbols/core.base#architecture)**: Either `64bit` or `32bit`.

#### Example: Platform & Version checks

```python
from core import base, utils

# Compatibility check (Robust comparison)
if not utils.is_version_at_least(base.VERSION, "1.13.1"):
    print("This script requires Minify 1.13.1 or newer.")
    return

# Platform-specific logic
if base.OS == base.WIN:
    # Windows specific code
    pass
elif base.OS == base.LINUX:
    # Linux specific code
    pass

# Handling ARM devices
if base.MACHINE in ["aarch64", "arm64"]:
    # ARM specific logic
    pass
```

### Common Paths

You can find the standard directories and executable paths in [Minify/core/base.py](/development/symbols/core.base):

- **[`mods_dir`](/development/symbols/core.base#mods_dir)**: The root directory where all mods are stored (`mods`).
- **[`config_dir`](/development/symbols/core.base#config_dir)**: Where configuration files and mod-specific assets are kept (`config`).

#### Example: Common Paths

```python
from core import base

# Accessing the mods directory
mods_path = os.path.join(base.minify_root, base.mods_dir)

# Checking if a specific tool exists
mod_file = os.path.join(base.config_dir, "file_needed_for_my_mod")
```

### Configuration Management

The [Minify/core/config.py](/development/symbols/core.config) module provides easy access to the application's global setting and individual mod configurations:

- **[`get(key, default_value)`](/development/symbols/core.config#getkey-default_value)**: Retrieve a value from the main config. If it doesn't exist, it is created with the `default_value`.
- **[`set(key, value)`](/development/symbols/core.config#setkey-value)**: Update a value in the main config.
- **[`get_mod(mod_name, default)`](/development/symbols/core.config#get_modmod_name-default)**: Get the configuration dictionary for a specific mod.
- **[`set_mod(mod_name, config_data)`](/development/symbols/core.config#set_modmod_name-config_data)**: Save configuration data for a specific mod.

#### Example: Configuration Management

```python
from core import config

# Get a global setting
is_debug = config.get("debug_env", False)

# Store a custom persistent value
config.set("my_mod_last_run", "2024-04-13")

# Access mod-specific settings
my_config = config.get_mod("my_mod_name")
my_config["enabled"] = True
config.set_mod("my_mod_name", my_config)
```

### Dota 2 Environment Paths

The [Minify/core/constants.py](/development/symbols/core.constants) module contains absolute paths to critical Dota 2 and Minify directories, resolved using the user's Steam library:

- **[`minify_dota_compile_input_path`](/development/symbols/core.constants#minify_dota_compile_input_path)**: The source directory for mod compilation (Addons content).
- **[`minify_dota_compile_output_path`](/development/symbols/core.constants#minify_dota_compile_output_path)**: The destination directory for compiled assets (Addons game).
- **[`minify_dota_tools_required_path`](/development/symbols/core.constants#minify_dota_tools_required_path)**: Path required for Dota 2 Workshop Tools interaction.
- **[`minify_default_dota_pak_output_path`](/development/symbols/core.constants#minify_default_dota_pak_output_path)**: Default location where Minify exports patched VPKs.
- **[`dota2_executable`](/development/symbols/core.constants#dota2_executable)**: Path to the `dota2.exe` (or platform equivalent).
- **[`dota2_tools_executable`](/development/symbols/core.constants#dota2_tools_executable)**: Path to the Dota 2 configuration/tools launcher.
- **[`dota_game_pak_path`](/development/symbols/core.constants#dota_game_pak_path)**: Path to the main `pak01_dir.vpk`.
- **[`dota_core_pak_path`](/development/symbols/core.constants#dota_core_pak_path)**: Path to the core engine `pak01_dir.vpk`.
- **[`dota_resource_compiler_path`](/development/symbols/core.constants#dota_resource_compiler_path)**: Path to the `resourcecompiler.exe`.

### Steam Integration

The [Minify/core/steam.py](/development/symbols/core.steam) module handles Steam path discovery and user management:

- **[`ROOT`](/development/symbols/core.steam#root)**: The absolute path to the Steam installation directory.
- **[`LIBRARY`](/development/symbols/core.steam#library)**: The absolute path to the Steam library containing Dota 2.
- **[`current_steam_id`](/development/symbols/core.steam#current_steam_id)**: The Steam32 ID of the currently active account (or the first found if not set).

### Mod Information

Access real-time information about the loaded mods:

- **[`visually_available_mods`](/development/symbols/core.constants#visually_available_mods)**: A list of mods that are currently visible and selectable in the UI.

### Utility Functions

Miscellaneous utilities to help with common script tasks:

- **[`open_thing(path, args)`](/development/symbols/core.fs#open_thingpath-args)**: (from `core.fs`) Opens a file, directory, or executable in the system's default application. Handles platform differences automatically.
- **[`move_path(src, dst)`](/development/symbols/core.fs#move_pathsrc-dst)**: Safely move or rename a file or directory, handling permissions automatically.
- **[`remove_path(*paths)`](/development/symbols/core.fs#remove_path)**: Recursively delete files or directories, handling permissions and skipping missing paths.
- **[`create_dirs(*paths)`](/development/symbols/core.fs#create_dirspaths)**: Recursively creates directories (like `mkdir -p`).
- **[`download_file(url, target_path, progress_tag)`](/development/symbols/core.fs#download_fileurl-target_path-progress_tag)**: Downloads a file from a URL. If a `progress_tag` is provided, it updates the UI with the download status.
- **[`extract_archive(archive_path, extract_dir, target_file)`](/development/symbols/core.fs#extract_archivearchive_path-extract_dir-target_file)**: Extracts a `.zip` or `.tar.gz` archive. Can optionally extract a single `target_file`.
- **[`get_file_type(path)`](/development/symbols/core.fs#get_file_typepath)**: Identifies the file type. It first checks magic bytes (e.g., `.png`, `.jpg`, `.webm`), and falls back to extracting the extension from the first dot in the filename if no known magic bytes are found.

### Logging

Use the application's logging system to report issues or informational messages:

- **[`write_warning(header)`](/development/symbols/core.log#write_warningheader)**: (from `core.log`) Writes a warning to the `logs/warnings.txt` file and displays it in the application's terminal.

### Context Managers & File Utilities

The [Minify/core/utils.py](/development/symbols/core.utils) module provides wrappers for safe execution and UTF-8 file handling:

- **[`try_pass()`](/development/symbols/core.utils#try_pass)**: A context manager that silently catches and ignores any exceptions within its block.
- **[`is_version_at_least(current, target)`](/development/symbols/core.utils#is_version_at_leastcurrent-target)**: A helper for comparing semantic version strings (e.g., `"1.13.1"` vs `"1.12.0"`). Returns `True` if `current >= target`.
- **[`open_utf8(file, mode)`](/development/symbols/core.utils#open_utf8file-mode)**: A context manager that patches `builtins.open` to use UTF-8 encoding by default.
- **[`open_utf8R(file, mode)`](/development/symbols/core.utils#open_utf8rfile-mode)**: similar to `open_utf8`, but also uses `errors="replace"` to handle corrupted or non-UTF-8 characters safely.

#### Example: Safe File Reading

```python
from core import utils

# Silently ignore errors if the file is missing or locked
with utils.try_pass():
    with utils.open_utf8R("some_risky_file.txt", "r") as f:
        content = f.read()
```

### Global Application State

The [Minify/helper.py](/development/symbols/helper) module tracks the current session's state:

- **[`output_path`](/development/symbols/helper#output_path)**: The absolute path where the main VPK will be exported. It tracks the final destination and is dynamically set based on user's settings.

#### Example: Checking Output Path

```python
import helper

print(f"VPKs will be saved to: {helper.output_path}")
```

### Dota 2 Asset Compilation

The [Minify/helper.py](/development/symbols/helper) module includes tools for compiling raw assets for the Source 2 engine:

- **[`compile_assets(input_path, ...)`](/development/symbols/helper#compile_assetsinput_path-output_path-pak_path-sender-app_data-user_data)**: A wrapper for the Dota 2 Resource Compiler. It automatically handles image compilation, creates necessary XML references, and can optionally package the result into a `.vpk`.

### Terminal UI

Interact with the application's built-in terminal window from your scripts:

- **[`add_text(text_or_id, *args, msg_type)`](/development/symbols/ui.terminal#add_texttext_or_id-args-msg_type-kwargs)**: (from `ui.terminal`) Adds a line of text to the terminal. If the string starts with `&`, it will be localized. `msg_type` can be `"error"`, `"warning"`, or `"success"`.
- **[`add_seperator()`](/development/symbols/ui.terminal#add_seperator)**: Adds a horizontal separator line to the terminal.
- **[`clean()`](/development/symbols/ui.terminal#clean)**: Clears all history and text from the terminal window.

#### Example: Compiling and Logging

```python
import helper
from ui import terminal

# Compile a folder of raw UI assets into a VPK
helper.compile_assets(
    input_path="my_raw_assets",
    pak_path="my_mod.vpk"
)

# Log the result to the UI
terminal.add_text("Compilation finished!", msg_type="success")
terminal.add_seperator()
```

#### Example: File Operations

```python
from core import constants, fs

# Open the main game pak location
fs.open_thing(os.path.dirname(constants.dota_game_pak_path))

# Check which mods are active
for mod in constants.visually_available_mods:
    print(f"Mod found: {mod}")
```
