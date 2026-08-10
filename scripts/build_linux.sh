#!/bin/bash

cd "$(dirname "$0")"

rm -rf build
rm -rf dist

uv run pyinstaller Minify.spec

SRC="$(pwd)/../Minify"

if [ "$1" = "-sym" ]; then
    ln -s "$SRC/bin" dist/Minify/bin
    ln -s "$SRC/mods" dist/Minify/mods
    if [ -d "$SRC/config" ]; then
        ln -s "$SRC/config" dist/Minify/config
    fi
    ln -s "$SRC"/lib*.so dist/Minify/
    ln -s "$SRC/README.md" dist/Minify/README.md
    ln -s "$SRC/LICENSE" dist/Minify/LICENSE
    if [ -f "$SRC/Source2Viewer-CLI" ]; then
        ln -s "$SRC/Source2Viewer-CLI" dist/Minify/Source2Viewer-CLI
    fi
    if [ -f "$SRC/rg" ]; then
        ln -s "$SRC/rg" dist/Minify/rg
    fi
else
    cp -r ../Minify/bin dist/Minify/bin
    cp -r ../Minify/mods dist/Minify/mods
    if [ -d ../Minify/bin/rescomproot ]; then
        cp -r ../Minify/bin/rescomproot dist/Minify/bin/
    fi
    if [ -d ../Minify/config ]; then
        cp -r ../Minify/config dist/Minify/
    fi
    cp ../Minify/lib*.so dist/Minify/
    cp ../README.md dist/Minify/README.md
    cp ../LICENSE dist/Minify/LICENSE
    if [ -f ../Minify/Source2Viewer-CLI ]; then
        cp ../Minify/Source2Viewer-CLI dist/Minify/
    fi
    if [ -f ../Minify/rg ]; then
        cp ../Minify/rg dist/Minify/
    fi
fi
