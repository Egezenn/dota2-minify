#!/bin/bash

cd "$(dirname "$0")"

rm -rf build
rm -rf dist

SRC="$(pwd)/../Minify"

SYM_LINK=false
NO_PLUGINS=false

for arg in "$@"; do
    case "$arg" in
        -sym|--sym)
            SYM_LINK=true
            ;;
        --no-plugins)
            NO_PLUGINS=true
            ;;
    esac
done

if [ -d "$SRC/ui/web" ]; then
    if [ "$NO_PLUGINS" = true ]; then
        echo "Building web UI (no plugins)..."
        (cd "$SRC/ui/web" && npm run build -- --no-plugins)
    else
        echo "Building web UI and plugins..."
        (cd "$SRC/ui/web" && npm run build)
    fi
fi

uv run pyinstaller Minify.spec

if [ "$SYM_LINK" = true ]; then
    ln -s "$SRC/bin" dist/Minify/bin
    ln -s "$SRC/mods" dist/Minify/mods
    ln -s "$SRC/ui/dist" dist/Minify/ui
    if [ "$NO_PLUGINS" = false ] && [ -d "$SRC/plugins" ]; then
        ln -s "$SRC/plugins" dist/Minify/plugins
    fi
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
    cp -r ../Minify/ui/dist dist/Minify/ui

    if [ "$NO_PLUGINS" = false ] && [ -d ../Minify/plugins ]; then
        cp -r ../Minify/plugins dist/Minify/
    fi
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
