"Variables that depend on 3rd parties"

import os

from core import base, mods_shared, steam

rescomp_override = os.path.exists(base.rescomp_override_dir)

minify_dota_compile_input_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "content", "dota_addons", "minify"
)
minify_dota_compile_output_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_addons", "minify"
)
minify_dota_tools_required_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "content", "dota_minify"
)
minify_default_dota_pak_output_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota_minify"
)
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

## base game
dota2_executable = os.path.join(steam.LIBRARY, base.DOTA_EXECUTABLE_PATH)
dota2_tools_executable = os.path.join(steam.LIBRARY, base.DOTA_TOOLS_EXECUTABLE_PATH)
dota_game_pak_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "pak01_dir.vpk")
dota_core_pak_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "core", "pak01_dir.vpk")
dota_steam_inf_path = os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "steam.inf")
dota_resource_compiler_path = os.path.join(
    steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "bin", "win64", "resourcecompiler.exe"
)

dota_tools_paths = [
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "bin"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "core"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "bin"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "tools"),
    os.path.join(steam.LIBRARY, "steamapps", "common", "dota 2 beta", "game", "dota", "gameinfo.gi"),
]
dota_tools_extraction_paths = [
    os.path.join(base.rescomp_override_dir, "game", "bin"),
    os.path.join(base.rescomp_override_dir, "game", "core"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "bin"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "tools"),
    os.path.join(base.rescomp_override_dir, "game", "dota", "gameinfo.gi"),
]

s2v_cli_ver = "18.0"
rg_ver = "15.1.0"

try:
    if base.OS == base.WIN:
        s2v_executable = "Source2Viewer-CLI.exe"

        if base.MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-x64.zip"
        else:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-windows-x64.zip"

        rg_executable = "rg.exe"
        if base.ARCHITECTURE == "64bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-pc-windows-msvc.zip"
        else:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-i686-pc-windows-msvc.zip"

    elif base.OS == base.LINUX:
        s2v_executable = "Source2Viewer-CLI"
        if base.MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-arm64.zip"
        elif base.MACHINE in ["armv7l", "arm"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-arm.zip"
        elif base.ARCHITECTURE == "64bit":
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-linux-x64.zip"

        rg_executable = "rg"
        if base.MACHINE in ["aarch64", "arm64"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-aarch64-unknown-linux-gnu.tar.gz"
        elif base.MACHINE in ["armv7l", "arm"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-armv7-unknown-linux-gnueabihf.tar.gz"
        elif base.MACHINE == "ppc64":  # unlikely
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-powerpc64-unknown-linux-gnu.tar.gz"
        elif base.MACHINE == "s390x":  # unlikely
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-s390x-unknown-linux-gnu.tar.gz"
        elif base.ARCHITECTURE == "64bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-unknown-linux-musl.tar.gz"
        elif base.ARCHITECTURE == "32bit":
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-i686-unknown-linux-gnu.tar.gz"

    elif base.OS == base.MAC:
        s2v_executable = "Source2Viewer-CLI"
        if base.MACHINE in ["aarch64", "arm64"]:
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-arm64.zip"
        elif base.ARCHITECTURE == "64bit":
            s2v_latest = f"https://github.com/ValveResourceFormat/ValveResourceFormat/releases/download/{s2v_cli_ver}/cli-macos-x64.zip"

        rg_executable = "rg"
        if base.MACHINE in ["aarch64", "arm64"]:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-aarch64-apple-darwin.tar.gz"
        else:
            rg_latest = f"https://github.com/BurntSushi/ripgrep/releases/download/{rg_ver}/ripgrep-{rg_ver}-x86_64-apple-darwin.tar.gz"
    else:
        raise Exception("Unsupported platform!")

except Exception:
    from core import log

    log.write_crashlog(f"Unsupported configuration ({base.OS}/{base.MACHINE}/{base.ARCHITECTURE})")


mods_shared.scan_mods()
mods_alphabetical = mods_shared.mods_alphabetical
mods_with_order = mods_shared.mods_with_order
visually_unavailable_mods = mods_shared.visually_unavailable_mods
visually_available_mods = mods_shared.visually_available_mods
mod_dependencies_list = mods_shared.mod_dependencies_list
