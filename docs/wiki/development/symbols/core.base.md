# core.base

Variables that almost never change

## Variables

### `VERSION`

<details open><summary>Source</summary>

```python
VERSION = "1.13.1"

```

</details>

### `TITLE`

<details open><summary>Source</summary>

```python
TITLE = f"Minify {VERSION}"

```

</details>

### `OS`

<details open><summary>Source</summary>

```python
OS = platform.system()

```

</details>

### `MACHINE`

<details open><summary>Source</summary>

```python
MACHINE = platform.machine().lower()

```

</details>

### `ARCHITECTURE`

<details open><summary>Source</summary>

```python
ARCHITECTURE = platform.architecture()[0]

```

</details>

### `WIN`

<details open><summary>Source</summary>

```python
WIN = "Windows"

```

</details>

### `LINUX`

<details open><summary>Source</summary>

```python
LINUX = "Linux"

```

</details>

### `MAC`

<details open><summary>Source</summary>

```python
MAC = "Darwin"

```

</details>

### `FROZEN`

<details open><summary>Source</summary>

```python
FROZEN = getattr(sys, "frozen", False)

```

</details>

### `OWNER`

<details open><summary>Source</summary>

```python
OWNER = "Egezenn"

```

</details>

### `REPO`

<details open><summary>Source</summary>

```python
REPO = "dota2-minify"

```

</details>

### `DOTA_TOOLS_EXECUTABLE_PATH`

<details open><summary>Source</summary>

```python
DOTA_TOOLS_EXECUTABLE_PATH = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2cfg.exe")

```

</details>

### `DOTA_EXECUTABLE_PATH_FALLBACK`

<details open><summary>Source</summary>

```python
DOTA_EXECUTABLE_PATH_FALLBACK = os.path.join("steamapps", "common", "dota 2 beta", "game", "bin", "win64", "dota2.exe")

```

</details>

### `STEAM_DOTA_ID`

<details open><summary>Source</summary>

```python
STEAM_DOTA_ID = "570"

```

</details>

### `STEAM_DOTA_WORKSHOP_TOOLS_ID`

<details open><summary>Source</summary>

```python
STEAM_DOTA_WORKSHOP_TOOLS_ID = "313250"

```

</details>

### `bin_dir`

<details open><summary>Source</summary>

```python
bin_dir = "bin"

```

</details>

### `build_dir`

<details open><summary>Source</summary>

```python
build_dir = "vpk_build"

```

</details>

### `replace_dir`

<details open><summary>Source</summary>

```python
replace_dir = "vpk_replace"

```

</details>

### `merge_dir`

<details open><summary>Source</summary>

```python
merge_dir = "vpk_merge"

```

</details>

### `logs_dir`

<details open><summary>Source</summary>

```python
logs_dir = "logs"

```

</details>

### `mods_dir`

<details open><summary>Source</summary>

```python
mods_dir = "mods"

```

</details>

### `config_dir`

<details open><summary>Source</summary>

```python
config_dir = "config"

```

</details>

### `cache_dir`

<details open><summary>Source</summary>

```python
cache_dir = "cache"

```

</details>

### `blank_files_dir`

<details open><summary>Source</summary>

```python
blank_files_dir = os.path.join(bin_dir, "blank-files")

```

</details>

### `img_dir`

<details open><summary>Source</summary>

```python
img_dir = os.path.join(bin_dir, "images")

```

</details>

### `localization_file_dir`

<details open><summary>Source</summary>

```python
localization_file_dir = os.path.join(bin_dir, "localization.json")

```

</details>

### `rescomp_override_dir`

<details open><summary>Source</summary>

```python
rescomp_override_dir = os.path.join(bin_dir, "rescomproot")

```

</details>

### `sounds_dir`

<details open><summary>Source</summary>

```python
sounds_dir = os.path.join(bin_dir, "sounds")

```

</details>

### `log_crashlog`

<details open><summary>Source</summary>

```python
log_crashlog = os.path.join(logs_dir, "crashlog.txt")

```

</details>

### `log_warnings`

<details open><summary>Source</summary>

```python
log_warnings = os.path.join(logs_dir, "warnings.txt")

```

</details>

### `log_unhandled`

<details open><summary>Source</summary>

```python
log_unhandled = os.path.join(logs_dir, "unhandled.txt")

```

</details>

### `log_s2v`

<details open><summary>Source</summary>

```python
log_s2v = os.path.join(logs_dir, "Source2Viewer-CLI.txt")

```

</details>

### `log_rescomp`

<details open><summary>Source</summary>

```python
log_rescomp = os.path.join(logs_dir, "resourcecompiler.txt")

```

</details>

### `dota_steam_inf_cache`

<details open><summary>Source</summary>

```python
dota_steam_inf_cache = os.path.join(cache_dir, "steam.inf")

```

</details>

### `main_config_file_dir`

<details open><summary>Source</summary>

```python
main_config_file_dir = os.path.join(config_dir, "minify_config.json")

```

</details>

### `mods_config_dir`

<details open><summary>Source</summary>

```python
mods_config_dir = os.path.join(config_dir, "mods.json")

```

</details>

### `discord`

<details open><summary>Source</summary>

```python
discord = "https://discord.com/invite/9867CPv7cy"

```

</details>

### `telegram`

<details open><summary>Source</summary>

```python
telegram = "https://t.me/dota2minify"

```

</details>

### `github`

<details open><summary>Source</summary>

```python
github = f"https://github.com/{OWNER}/{REPO}"

```

</details>

### `github_latest`

<details open><summary>Source</summary>

```python
github_latest = github + "/releases/latest"

```

</details>

### `github_io`

<details open><summary>Source</summary>

```python
github_io = f"https://{OWNER}.github.io/{REPO}"

```

</details>

### `main_window_width`

<details open><summary>Source</summary>

```python
main_window_width = 550

```

</details>

### `main_window_height`

<details open><summary>Source</summary>

```python
main_window_height = 440

```

</details>
