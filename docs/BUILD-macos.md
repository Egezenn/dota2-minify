# Build on macOS (manual)

This guide shows how to run and package Minify as a native macOS app. Core features (file replacement, blacklist mods, VRF decompiling, VPK packing) work. Workshop Tools (resourcecompiler) are Windows‑only, but you can enable them on macOS via Wine + SteamCMD.

## Prerequisites

- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (recommended): <https://brew.sh/>
- Python 3.13: `brew install python@3.13`
- Wine (to run Windows resourcecompiler and SteamCMD): for example `brew install --cask wine-stable` (or any Wine distribution you prefer)
- Optional but recommended:
  - ripgrep: `brew install ripgrep` (Minify can auto-download if missing)
  - uv: `brew install uv` (fast runner/venv)
  - Tcl/Tk (only if you want the Tk file picker): `brew install tcl-tk`

Notes

- Dear PyGui works on Apple Silicon and Intel.
- Tk is optional; Minify falls back to a manual path file if Tk is missing.

## Clone and run locally

```sh
git clone https://github.com/Egezenn/dota2-minify
cd dota2-minify

# Using uv (recommended)
uv run imgui.py

# Or using pip
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python imgui.py
```

If Minify can’t locate Steam/Dota automatically:

- Create `config/dota2path_minify.txt` with your Steam library root on a single line, for example:
  - `/Users/<you>/Library/Application Support/Steam`

## Enable Workshop Tools on macOS (Wine + SteamCMD)

You can download the Windows Dota build and the Workshop Tools depots, then Minify will run the Windows resourcecompiler.exe via Wine.

Requirements

- You must own Dota 2 and the Workshop Tools DLC (DLC id 313250) on your Steam account.
- Wine installed (see prerequisites above).

Steps (from within Minify):

1. Launch Minify on macOS.
2. Click the cog icon (Dev) → open the Tools window.
3. Click “Download workshop tools (SteamCMD)”.
4. In the Steam Login modal, enter:
   - Username and Password (Steam Guard is optional; provide a current code if prompted).
   - You can also leave fields empty if you’ve set environment variables `MINIFY_STEAM_USER`, `MINIFY_STEAM_PASS`, and optionally `MINIFY_STEAM_GUARD`.
5. Click Download. Minify will:
   - Download the Windows SteamCMD, run it via Wine, and fetch app 570 (Dota 2, Windows) into a local library.
   - Copy required folders into Minify’s override location (`rescomproot`): `game/bin`, `game/core`, `game/dota/bin`, `game/dota/tools`, and `game/dota/gameinfo.gi`.
   - Reconfigure paths so resourcecompiler.exe is used via Wine automatically.
6. After success, CSS and XML compilation features become available on macOS (see notes below for Apple Silicon).

Troubleshooting

- “Wine is required”: install Wine and retry.
- Steam Guard or login errors: re-open the modal, ensure credentials/Guard code are correct; check `logs/steamcmd.txt`.
- No tools after download: verify you own the Workshop Tools DLC (313250) on the same account; see `logs/steamcmd.txt`.
- Disk space: SteamCMD may pull several GB; ensure free space.

## Build a macOS app bundle

Install build deps (already in requirements.txt):

```bash
pip install -r requirements.txt
```

Build with PyInstaller:

```bash
pyinstaller \
  --windowed \
  --name Minify \
  --hidden-import=tkinter \
  imgui.py
```

Icon (optional)

- macOS prefers `.icns`. If you want an app icon, convert `bin/images/favicon.ico` to `Minify.icns` and add `--icon Minify.icns`.

## Bundle Minify resources

Copy runtime resources into the app bundle alongside the executable:

```bash
APP="dist/Minify.app/Contents/MacOS"
mkdir -p "$APP"
cp -R bin "$APP/bin"
cp -R mods "$APP/mods"
cp version "$APP/version" 2>/dev/null || true
```

Run the app:

```bash
open dist/Minify.app
```

First run

- Minify will download ValveResourceFormat (Source2Viewer-CLI) and ripgrep for your architecture if not present.
- If macOS Gatekeeper quarantines downloaded CLIs, clear quarantine and set execution bit:
  - `xattr -dr com.apple.quarantine Source2Viewer-CLI`
  - `chmod +x Source2Viewer-CLI`

## Using the build

1. Enable mods and Patch.
2. In Steam → Dota 2 → Properties → Launch Options, add your language flag, e.g.:
   - English (Minify language): `-language minify`
   - Another language: `-language <language_id>` (also pick it in the app’s top bar).
3. Launch Dota 2.

## Additional Wine setup (tested Sept 2025)

```bash
# install helper tools
brew install winetricks

# install DXVK and DirectX runtimes inside the default ~/.wine prefix
winetricks --unattended dxvk
winetricks --unattended d3dcompiler_43 d3dx11_43
```

These steps place the DXVK Vulkan-based D3D layer and required DirectX DLLs into the Wine prefix Minify uses. The patcher now logs the exact Wine command and exit code to `logs/resourcecompiler.txt` after every run.

## Limitations on macOS

- By default (fresh install), Workshop Tools are not present. Use the “Download workshop tools (SteamCMD)” flow above to enable them.
- On Intel Macs with a Vulkan-capable GPU and drivers supporting geometry shaders, Wine + DXVK can run `resourcecompiler.exe` successfully.
- **Apple Silicon (M1/M2/M3)**: MoltenVK does not expose geometry shaders, which DXVK requires for Direct3D 11.
  - Even with DXVK and the DirectX runtimes installed, `resourcecompiler.exe` exits with code 1 and logs `DXVK: No adapters found / device does not support required feature 'geometryShader'`.
  - Wine’s fallback OpenGL (`wined3d`) path still reports `Required feature D3D11_FEATURE_DATA_D3D10_X_HARDWARE_OPTIONS.ComputeShaders_Plus_RawAndStructuredBuffers_Via_Shader_4_x not supported.`
  - Practical workarounds:
    1. Run Minify’s patcher inside a Windows VM (Parallels, VMware, etc.) or on a Windows PC, then copy `pak66_dir.vpk` back to macOS.
    2. Use Linux with a Vulkan GPU that supports geometry shaders.
- Source2Viewer CLI decompile and VPK packing continue to work natively on macOS.
- If you prefer not to install Wine, compile on Windows/Linux and copy the VPK to your Mac under the selected language folder.

## Troubleshooting

- Missing Tk on startup

  - Minify now starts without Tk. If you want a GUI folder picker, install `tcl-tk` with Homebrew, or set `config/dota2path_minify.txt` manually.

- Can’t find Steam/Dota

  - Ensure `config/dota2path_minify.txt` points to your Steam library root (`…/Library/Application Support/Steam`).

- Downloaded tools won’t run (permission/quarantine)
  - Run `xattr -dr com.apple.quarantine <tool>` and `chmod +x <tool>` inside the app’s working directory (usually `…/Minify.app/Contents/MacOS`).
