# core.constants

Variables that depend on 3rd parties

## Variables

### `rescomp_override`

<details open><summary>Source</summary>

```python
rescomp_override = os.path.exists(base.rescomp_override_dir)

```

</details>

### `minify_dota_compile_input_path`

<details open><summary>Source</summary>

```python
minify_dota_compile_input_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "content", "dota_addons", "minify"
)

```

</details>

### `minify_dota_compile_output_path`

<details open><summary>Source</summary>

```python
minify_dota_compile_output_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_addons", "minify"
)

```

</details>

### `minify_dota_tools_required_path`

<details open><summary>Source</summary>

```python
minify_dota_tools_required_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "content", "dota_minify"
)

```

</details>

### `minify_default_dota_pak_output_path`

<details open><summary>Source</summary>

```python
minify_default_dota_pak_output_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_minify"
)

```

</details>

### `minify_dota_possible_language_output_paths`

<details open><summary>Source</summary>

```python
minify_dota_possible_language_output_paths = [
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_minify"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_brazilian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_bulgarian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_czech"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_danish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_dutch"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_finnish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_french"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_german"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_greek"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_hungarian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_italian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_japanese"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_koreana"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_latam"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_norwegian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_polish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_portuguese"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_romanian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_russian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_schinese"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_spanish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_swedish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_tchinese"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_thai"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_turkish"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_ukrainian"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_vietnamese"),
]

```

</details>

### `minify_output_list`

<details open><summary>Source</summary>

```python
minify_output_list = [
    "minify",
    "brazilian",
    "bulgarian",
    "czech",
    "danish",
    "dutch",
    "finnish",
    "french",
    "german",
    "greek",
    "hungarian",
    "italian",
    "japanese",
    "koreana",
    "latam",
    "norwegian",
    "polish",
    "portuguese",
    "romanian",
    "russian",
    "schinese",
    "spanish",
    "swedish",
    "tchinese",
    "thai",
    "turkish",
    "ukrainian",
    "vietnamese",
]

```

</details>

### `dota2_executable`

<details open><summary>Source</summary>

```python
dota2_executable = os.path.join(steam.LIBRARY, base.DOTA_EXECUTABLE_PATH)

```

</details>

### `dota2_tools_executable`

<details open><summary>Source</summary>

```python
dota2_tools_executable = os.path.join(steam.LIBRARY, base.DOTA_TOOLS_EXECUTABLE_PATH)

```

</details>

### `dota_game_pak_path`

<details open><summary>Source</summary>

```python
dota_game_pak_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "pak01_dir.vpk")

```

</details>

### `dota_core_pak_path`

<details open><summary>Source</summary>

```python
dota_core_pak_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "core", "pak01_dir.vpk")

```

</details>

### `dota_steam_inf_path`

<details open><summary>Source</summary>

```python
dota_steam_inf_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "steam.inf")

```

</details>

### `dota_resource_compiler_path`

<details open><summary>Source</summary>

```python
dota_resource_compiler_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "resourcecompiler.exe"
)

```

</details>

### `dota_tools_paths`

<details open><summary>Source</summary>

```python
dota_tools_paths = [
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "bin"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "core"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "bin"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "tools"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "gameinfo.gi"),
]

```

</details>

### `dota_tools_extraction_paths`

<details open><summary>Source</summary>

```python
dota_tools_extraction_paths = [
    os.path.join(base.rescomp_override_dir, "game", "bin"),
    os.path.join(base.rescomp_override_dir, "game", "core"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "bin"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "tools"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "gameinfo.gi"),
]

```

</details>

### `s2v_cli_ver`

<details open><summary>Source</summary>

```python
s2v_cli_ver = "18.0"

```

</details>

### `rg_ver`

<details open><summary>Source</summary>

```python
rg_ver = "15.1.0"

```

</details>

### `mods_alphabetical`

<details open><summary>Source</summary>

```python
mods_alphabetical = mods_shared.mods_alphabetical

```

</details>

### `mods_with_order`

<details open><summary>Source</summary>

```python
mods_with_order = mods_shared.mods_with_order

```

</details>

### `visually_unavailable_mods`

<details open><summary>Source</summary>

```python
visually_unavailable_mods = mods_shared.visually_unavailable_mods

```

</details>

### `visually_available_mods`

<details open><summary>Source</summary>

```python
visually_available_mods = mods_shared.visually_available_mods

```

</details>

### `mod_dependencies_list`

<details open><summary>Source</summary>

```python
mod_dependencies_list = mods_shared.mod_dependencies_list

```

</details>

### `mod_conflicts_list`

<details open><summary>Source</summary>

```python
mod_conflicts_list = mods_shared.mod_conflicts_list

```

</details>
