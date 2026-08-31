#!/usr/bin/env python3
"""Cross-platform build script for Dota 2 Minify."""

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MINIFY_DIR = REPO_ROOT / "Minify"
DIST_DIR = REPO_ROOT / "scripts" / "dist"
DIST_MINIFY_DIR = DIST_DIR / "Minify"
BUILD_DIR = REPO_ROOT / "scripts" / "build"
WEB_DIR = MINIFY_DIR / "ui" / "web"
SPEC_FILE = REPO_ROOT / "scripts" / "Minify.spec"


def log(msg: str) -> None:
    print(f"[BUILD - {time.strftime('%H:%M:%S')}] {msg}")


def remove_existing(target: Path) -> None:
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()


def link_or_copy(src: Path, dst: Path, use_symlink: bool) -> None:
    if not src.exists():
        return

    remove_existing(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    if use_symlink:
        try:
            os.symlink(src, dst, target_is_directory=src.is_dir())
            log(f"Symlinked: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
            return
        except Exception as e:
            log(f"Warning: Symlink failed ({e}), falling back to copy for {src.name}")

    if src.is_dir():
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", ".DS_Store"),
        )
        log(f"Copied directory: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")
    else:
        shutil.copy2(src, dst)
        log(f"Copied file: {src.relative_to(REPO_ROOT)} -> {dst.relative_to(REPO_ROOT)}")


def copy_bin_selective(src_bin: Path, dst_bin: Path, use_symlink: bool) -> None:
    if not src_bin.exists():
        return
    if dst_bin.is_symlink():
        dst_bin.unlink()
    dst_bin.mkdir(parents=True, exist_ok=True)
    for item in src_bin.iterdir():
        if item.name in ("settings.json", "localization.json"):
            continue
        link_or_copy(item, dst_bin / item.name, use_symlink=use_symlink)


def copy_plugins_selective(src_plugins: Path, dst_plugins: Path, use_symlink: bool) -> None:
    if dst_plugins.is_symlink():
        dst_plugins.unlink()

    dst_plugins.mkdir(parents=True, exist_ok=True)

    for root_file in src_plugins.glob("__init__.*"):
        if root_file.is_file():
            link_or_copy(root_file, dst_plugins / root_file.name, use_symlink=use_symlink)

    for item in src_plugins.iterdir():
        if not item.is_dir() or item.name.startswith(".") or item.name.startswith("_"):
            continue

        p_dst = dst_plugins / item.name
        if p_dst.is_symlink():
            p_dst.unlink()
        p_dst.mkdir(parents=True, exist_ok=True)

        manifest = item / "manifest.json"
        if manifest.is_file():
            link_or_copy(manifest, p_dst / "manifest.json", use_symlink=use_symlink)

        for py_file in item.glob("*.py"):
            if py_file.is_file():
                link_or_copy(py_file, p_dst / py_file.name, use_symlink=use_symlink)

        ui_dir = item / "ui"
        if ui_dir.is_dir():
            link_or_copy(ui_dir, p_dst / "ui", use_symlink=use_symlink)


def clean_release_dir(dst_dir: Path) -> None:
    for root, dirs, files in os.walk(dst_dir, topdown=False):
        root_path = Path(root)
        for d in list(dirs):
            if d == "__pycache__" or (d == "src" and "plugins" in root_path.parts):
                shutil.rmtree(root_path / d, ignore_errors=True)
        for f in files:
            if f.endswith((".pyc", ".pyo")) or f in ("package.json", "tsconfig.json"):
                if "plugins" in root_path.parts:
                    (root_path / f).unlink(missing_ok=True)


def run_npm_build(no_plugins: bool) -> None:
    if not WEB_DIR.exists():
        log("Notice: Web UI directory not found, skipping npm build.")
        return

    cmd = ["npm", "run", "build"]
    if no_plugins:
        cmd.extend(["--", "--no-plugins"])

    log(f"Running npm build in {WEB_DIR}...")
    result = subprocess.run(cmd, cwd=WEB_DIR, shell=sys.platform == "win32")
    if result.returncode != 0:
        log("Error: npm build failed.")
        sys.exit(result.returncode)


def run_pyinstaller() -> None:
    log("Running PyInstaller...")
    executable = "uv" if shutil.which("uv") else "pyinstaller"
    dist_path = str(REPO_ROOT / "scripts" / "dist")
    work_path = str(REPO_ROOT / "scripts" / "build")
    spec_path = str(REPO_ROOT / "scripts" / "Minify.spec")

    if executable == "uv":
        cmd = ["uv", "run", "pyinstaller", "--noconfirm", "--distpath", dist_path, "--workpath", work_path, spec_path]
    else:
        cmd = ["pyinstaller", "--noconfirm", "--distpath", dist_path, "--workpath", work_path, spec_path]

    result = subprocess.run(cmd, cwd=REPO_ROOT / "scripts")
    if result.returncode != 0:
        log("Error: PyInstaller build failed.")
        sys.exit(result.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Dota 2 Minify application distribution package.")
    parser.add_argument(
        "--symlink",
        "-s",
        action="store_true",
        help="Create symbolic links instead of copying assets into dist/Minify",
    )
    parser.add_argument(
        "--no-plugins",
        action="store_true",
        help="Build application without plugins",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build/ and dist/ directories before building",
    )
    parser.add_argument(
        "--skip-npm",
        action="store_true",
        help="Skip npm frontend build step",
    )
    parser.add_argument(
        "--skip-pyinstaller",
        action="store_true",
        help="Skip PyInstaller binary compilation step",
    )

    args = parser.parse_args()

    if args.clean:
        log("Cleaning build and dist directories...")
        remove_existing(BUILD_DIR)
        remove_existing(DIST_DIR)

    if not args.skip_npm:
        run_npm_build(args.no_plugins)

    if not args.skip_pyinstaller:
        run_pyinstaller()

    DIST_MINIFY_DIR.mkdir(parents=True, exist_ok=True)
    use_symlink = args.symlink

    log("Packaging release assets into dist/Minify...")

    copy_bin_selective(MINIFY_DIR / "bin", DIST_MINIFY_DIR / "bin", use_symlink)

    if (MINIFY_DIR / "config").exists():
        link_or_copy(MINIFY_DIR / "config", DIST_MINIFY_DIR / "config", use_symlink)

    link_or_copy(MINIFY_DIR / "mods", DIST_MINIFY_DIR / "mods", use_symlink)

    if (MINIFY_DIR / "plugins").exists():
        if args.no_plugins:
            dst_plugins = DIST_MINIFY_DIR / "plugins"
            dst_plugins.mkdir(parents=True, exist_ok=True)
            for root_file in (MINIFY_DIR / "plugins").glob("__init__.*"):
                if root_file.is_file():
                    link_or_copy(root_file, dst_plugins / root_file.name, use_symlink=use_symlink)
        else:
            copy_plugins_selective(MINIFY_DIR / "plugins", DIST_MINIFY_DIR / "plugins", use_symlink)

    license_file = REPO_ROOT / "LICENSE"
    if not license_file.exists():
        license_file = MINIFY_DIR / "LICENSE"
    if license_file.exists():
        link_or_copy(license_file, DIST_MINIFY_DIR / "LICENSE", use_symlink)

    readme_file = REPO_ROOT / "README.md"
    if not readme_file.exists():
        readme_file = MINIFY_DIR / "README.md"
    if readme_file.exists():
        link_or_copy(readme_file, DIST_MINIFY_DIR / "README.md", use_symlink)

    for s2_name in ("Source2Viewer-CLI", "Source2Viewer-CLI.exe"):
        s2_path = MINIFY_DIR / s2_name
        if not s2_path.exists():
            s2_path = REPO_ROOT / s2_name
        if s2_path.exists():
            link_or_copy(s2_path, DIST_MINIFY_DIR / s2_name, use_symlink)

    for rg_name in ("rg", "rg.exe"):
        rg_path = MINIFY_DIR / rg_name
        if not rg_path.exists():
            rg_path = REPO_ROOT / rg_name
        if rg_path.exists():
            link_or_copy(rg_path, DIST_MINIFY_DIR / rg_name, use_symlink)

    for ext in ("*.so*", "*.dll", "*.dylib"):
        for lib_path in MINIFY_DIR.glob(ext):
            if lib_path.is_file():
                link_or_copy(lib_path, DIST_MINIFY_DIR / lib_path.name, use_symlink)

    clean_release_dir(DIST_MINIFY_DIR)

    log("Build process completed successfully.")


if __name__ == "__main__":
    main()
