# core.vpk_utils

## `dump_vpk(vpk_obj, output_dir, check_exists)`

*No documentation available.*

<details open><summary>Source</summary>

```python
def dump_vpk(vpk_obj, output_dir, check_exists=True):
    for filepath in vpk_obj:
        # Sanitize filepath to prevent invalid characters or quotes
        clean_path = filepath.strip().strip('"').strip("'").replace("\\", "/").lstrip("/")
        full_path = os.path.join(output_dir, clean_path)
        if check_exists and os.path.exists(full_path):
            continue

        fs.create_dirs(os.path.dirname(full_path))
        vpk_obj.get_file(filepath).save(full_path)

```

</details>

## `dump_metadata(target_dir, mod_name, vpk_mods, extra_lists)`

Standardizes metadata files for generated Paks.

- target_dir: Where to dump.
- mod_name: If provided, creates {mod_name}.txt (for single mod patches).
- vpk_mods: List of VPK mod names for minify_vpk_mods.txt.
- extra_lists: Dict of {filename: [lines]} for additional metadata files.

<details open><summary>Source</summary>

```python
def dump_metadata(target_dir, mod_name=None, vpk_mods=None, extra_lists=None):
    """
    Standardizes metadata files for generated Paks.
    - target_dir: Where to dump.
    - mod_name: If provided, creates {mod_name}.txt (for single mod patches).
    - vpk_mods: List of VPK mod names for minify_vpk_mods.txt.
    - extra_lists: Dict of {filename: [lines]} for additional metadata files.
    """
    # 1. Base Info
    if mod_name is None:
        shutil.copy(base.mods_config_dir, os.path.join(target_dir, "minify_mods.json"))
    else:
        open(os.path.join(target_dir, f"{mod_name}.txt"), "w").close()

    # 2. Lists
    if vpk_mods:
        with utils.open_utf8(os.path.join(target_dir, "minify_vpk_mods.txt"), "w") as f:
            f.write("\n".join(vpk_mods))

    if extra_lists:
        for filename, lines in extra_lists.items():
            with utils.open_utf8(os.path.join(target_dir, filename), "w") as f:
                f.write("\n".join(lines))

    # 3. Minify Version
    with utils.open_utf8(os.path.join(target_dir, "minify_version.txt"), "w") as f:
        f.write(base.VERSION)

    # 4. Dota Version (steam.inf)
    if os.path.exists(constants.dota_steam_inf_path):
        shutil.copy(constants.dota_steam_inf_path, os.path.join(target_dir, "steam.inf"))

```

</details>
