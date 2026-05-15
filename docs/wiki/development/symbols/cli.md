# cli

## `run()`

*No documentation available.*

<details open><summary>Source</summary>

```python
def run():
    parser = argparse.ArgumentParser(description="Dota2-Minify CLI", epilog="Run without args for the GUI")
    parser.add_argument("-p", "--patch", action="store_true", help="Run a patch")
    parser.add_argument("-c", "--conditional-patch", action="store_true", help="Run a conditional patch")
    parser.add_argument("-l", "--list", action="store_true", help="List all available mods and their state")
    parser.add_argument("-u", "--uninstall", action="store_true", help="Uninstall all mods")
    parser.add_argument("-v", "--version", action="store_true", help="Print version and exit")

    args = parser.parse_args()

    if args.version:
        print(base.VERSION)
        return

    if args.list:
        mods_shared.scan_mods()
        print(f"{'Mod Name':<40} | {'Status':<10}")
        print("-" * 55)
        for mod in constants.mods_with_order:
            status = "Enabled" if mods_shared.get_state(mod) else "Disabled"
            print(f"{mod:<40} | {status:<10}")
        return

    if args.uninstall:
        print("Uninstalling mods...")
        patch.unins.uninstall()
        return

    if args.conditional_patch:
        current_version = ""
        if os.path.exists(constants.dota_steam_inf_path):
            with utils.open_utf8R(constants.dota_steam_inf_path) as f:
                current_version = f.read()

        cached_version = ""
        if os.path.exists(base.dota_steam_inf_cache):
            with utils.open_utf8R(base.dota_steam_inf_cache) as f:
                cached_version = f.read()

        if current_version == cached_version and cached_version:
            print("Dota 2 version has not changed. Skipping patch.")
            return

        print("Dota 2 version changed or first run. Starting patch...")

    if args.patch or args.conditional_patch:
        from core import log

        print("Starting patch process...")
        try:
            patch.patcher()
        except Exception:
            log.write_crashlog()
        return

    parser.print_help()

```

</details>
