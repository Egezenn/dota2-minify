# Contributing to dota2-minify

Thank you for your interest in contributing! Whether you're fixing a bug, suggesting a feature, or improving documentation, your help is what makes `dota2-minify` grow.

**Before you start**: To avoid redundant work or conflicting implementations, please **create an issue** or contact the developers before you begin any major work.

**AI Usage**: We embrace the future! The use of AI tools is permitted and encouraged. We believe that humans and AI working together can achieve incredible results. However, we ask that you review all AI-generated code carefully to ensure it's logical, functional, and free of "hallucinations" or unnecessary boilerplate.

## Getting Started

1. **Fork and Clone**:

   ```shell
   git clone https://github.com/Egezenn/dota2-minify
   cd dota2-minify
   ```

2. **Setup Dependencies**:
   This project uses `uv` for dependency management.

   ```shell
   uv run Minify
   ```

   *Note: This will automatically handle the environment and dependencies.*

## Development Workflow

### Formatting & Linting

We prioritize code quality and consistent styling:

To ensure your code meets our standards, simply run the pre-commit script before submitting any changes:

```shell
bash scripts/precommit.sh
```

This script will automatically sync dependencies, check formatting, run the linter, and execute all tests.

### VSCode Integrations

If you are using VSCode, the following recommended extensions can be found in `.vscode/extensions.json`.

Additionally, we have pre-configured tasks available to streamline development. You can quickly run the application using `Ctrl+Shift+B`.
Other handy tasks available via `Tasks: Run Task` include:

- **Build via PyInstaller**: Compiles the standalone executable.
- **Build Installer**: Compiles the app and generates the Inno Setup installer.
- **Clean**: Clears out build directories (`build/`, `dist/`).
- **Launch Setup / Installed App**: Quickly test the generated installer or the installed application.

Debugger configurations are also available in `.vscode/launch.json`. However, the overhead of a debugger is rarely worth it; you can typically achieve the same results much faster through rapid iteration—simply run the application and fix errors as they appear in the terminal or `Minify/logs`.

## Mod Development

If you are contributing new mods or features to existing ones:

- Refer to [`docs/wiki/development.md`](https://egezenn.github.io/dota2-minify/wiki/#/development) for a full breakdown of the mod structure (`modcfg.json`, `notes.md`, etc.).
- Ensure that any feature requiring internet connectivity **fails silently** to avoid crashing the application for offline users.
- Decouple highly specific or complex logic into its own script within the mod folder.

## Translations

We use **Weblate** for community translations. To make this work with our single `localization.json` structure, we use a helper script:

1. **Translating**: Contribute via our Weblate instance (linked on the website).
2. **Syncing**: If you are a maintainer merging new translations:
    - Weblate will push individual JSON files to `scripts/weblate/`.
    - Run `uv run scripts/localization_manager.py merge` to update the main `Minify/bin/localization.json`.
    - Commit the updated `localization.json`.

## Pull Request Process

1. Create a descriptive branch for your feature or bugfix.
2. Ensure your code passes all checks by running `scripts/precommit.sh`.
3. If your changes affect core architecture or build logic, maintain compatibility with the automated release workflow (`.github/workflows/release.yml`).
4. Review standard project architecture in `AGENTS.md` (even if you aren't an AI, it provides a great technical overview).
5. Submit your PR and wait for review!
