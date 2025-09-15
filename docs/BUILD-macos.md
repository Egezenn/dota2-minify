# Build on macOS (manual)

This guide shows how to run and package Minify as a native macOS app. Core features (file replacement, blacklist mods, VRF decompiling, VPK packing) work. Workshop Tools (resourcecompiler) are Windows‑only, so CSS compilation and UI XML recompilation are not available on macOS.

## Prerequisites

- Xcode Command Line Tools: `xcode-select --install`
- Homebrew (recommended): https://brew.sh/
- Python 3.13: `brew install python@3.13`
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

## Limitations on macOS

- No Workshop Tools (resourcecompiler). As a result:
  - CSS (styling.txt) is not compiled to `.vcss_c` and is disabled on macOS.
  - UI XML changes that require recompilation to `.vxml_c` won’t apply.
- File replacement, blacklist mods, and any precompiled assets in `mods/*/files` work normally.

Tip: If you need styling/UI mods, build on Windows or Linux (where Workshop Tools exist) to produce the VPK, then copy the VPK to your Mac under the selected language folder.

## Troubleshooting

- Missing Tk on startup

  - Minify now starts without Tk. If you want a GUI folder picker, install `tcl-tk` with Homebrew, or set `config/dota2path_minify.txt` manually.

- Can’t find Steam/Dota

  - Ensure `config/dota2path_minify.txt` points to your Steam library root (`…/Library/Application Support/Steam`).

- Downloaded tools won’t run (permission/quarantine)
  - Run `xattr -dr com.apple.quarantine <tool>` and `chmod +x <tool>` inside the app’s working directory (usually `…/Minify.app/Contents/MacOS`).
