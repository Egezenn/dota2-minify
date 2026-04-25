# Contributing to dota2-minify

Thank you for your interest in contributing to `dota2-minify`! Here are the guidelines to ensure a smooth contribution process.

**Before you start**: To avoid redundant work or conflicting implementations, please **create an issue** or contact the developers before you begin any major work.

**AI Usage**: The use of AI tools is permitted and even encouraged due to the project's complexity. However, the quality of submitted code must resemble logical thinking; hallucinations, overly assumptive, non-functional boilerplate are not acceptable.

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

## Pull Request Process

1. Create a descriptive branch for your feature or bugfix.
2. Ensure your code passes all checks by running `scripts/precommit.sh`.
3. If your changes affect core architecture or build logic, maintain compatibility with the automated release workflow (`.github/workflows/release.yml`).
4. Review standard project architecture in `AGENTS.md` (even if you aren't an AI, it provides a great technical overview).
5. Submit your PR and wait for review!
