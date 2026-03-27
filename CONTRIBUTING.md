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

- **Line Length**: We use a line length of **120** characters.
- **Formatter**: Use `black` logic (via `black` or `ruff format`).
- **Linter**: Use `ruff check`.
- **Imports**: To organize imports, run:

  ```shell
  ruff check . --select I --fix
  ```

- **Pylint**: Configuration is kept in `pyproject.toml`. Usage is **suggested but not required**; it can be helpful for checking major changes. You are not expected to fix existing warnings that weren't caused by your submission, as Pylint can be overcautious.

### VSCode Extensions

If you are using VSCode, the following recommended extensions can be found in `.vscode/extensions.json`.

## Mod Development

If you are contributing new mods or features to existing ones:

- Refer to [`docs/wiki/development.md`](https://egezenn.github.io/dota2-minify/wiki/#/development) for a full breakdown of the mod structure (`modcfg.json`, `notes.md`, etc.).
- Ensure that any feature requiring internet connectivity **fails silently** to avoid crashing the application for offline users.
- Decouple highly specific or complex logic into its own script within the mod folder.

## Pull Request Process

1. Create a descriptive branch for your feature or bugfix.
2. Ensure your code passes linting (`ruff check`).
3. If your changes affect core architecture or build logic, maintain compatibility with the automated release workflow (`.github/workflows/release.yml`).
4. Review standard project architecture in `AGENTS.md` (even if you aren't an AI, it provides a great technical overview).
5. Submit your PR and wait for review!
