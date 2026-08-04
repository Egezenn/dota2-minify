#!/bin/bash

cd "$(dirname "$0")"

rm -rf build
rm -rf dist

uv run pyinstaller Minify.spec

cp -r ../Minify/bin dist/Minify/bin
cp -r ../Minify/mods dist/Minify/mods
if [ -f ../Minify/bin/rescomproot ]; then
    cp -r ../Minify/bin/rescomproot dist/Minify/bin/rescomproot
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
