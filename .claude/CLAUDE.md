# aithena

## Task

Complete actions described below for files located in `data` directory
using your favorite LLM framework.

Extract copyright holder, license name and save them as structured data.

If license type is open source permissive (not GPL or similar):
- extract function names with number of arguments for each function and save them as structured data

If license type open source and copyleft (GPL and similar):
- count number of functions in file
- if number of functions > 2
  - extract function names with number of arguments for each function and save them as structured data
- else
  - use LLM to rewrite file in rust (save result)

Bonus point for:
- Tests
- Dockerfile

## Project setup

- Python 3.15 (`.python-version`, `requires-python`). Package code lives in `src/aithena/`.
- Dependencies are managed with uv. `uv.lock` must stay in sync: run `uv lock --check` after changing dependencies.
- Run the app: `uv run aithena data output`. Run tests: `uv run --group test pytest`.
- The Anthropic API key is read from `ANTHROPIC_API_KEY`, from the environment or `.env`. Never hardcode it or commit `.env`.
- Docker: `docker compose up --build`. The image must not contain secrets.

## Python best practices

Type checking and linting
- Every function has type hints. Do not use `Any`; prefer precise types, generics (PEP 695 syntax), or a named alias such as `JsonValue`.
- `mypy --strict src/aithena`, `pyright src` and `ty check src tests` must pass. `ruff check src tests` must pass.
- Remove unused code, imports and variables rather than leaving them around.

Design
- Keep modules focused and group them into packages by concern (config, models, llm, extraction, pipeline, output).
- Dependency injection: create external clients only in the entry point (`main.py`) and pass them down. Library code never builds its own client and never falls back to a default.
- Pass configuration (such as models) explicitly as arguments; do not read globals.
- Write results through writer objects that receive their destination in the constructor. The pipeline returns data and never writes files.
- Use Pydantic models for structured data crossing the LLM boundary. Schemas describe only what the model must return; derive anything else (such as counts) in code.

Code style
- Prefer `pathlib.Path` over `os.path`. Always pass `encoding="utf-8"` for text files.
- Use explicit names and small functions. Avoid clever one-liners that hide logic.
- No mutable default arguments.
- Raise specific exceptions with context (file name, cause). Do not swallow exceptions.
- Use `print` only in the CLI entry point; library code returns values.
- Docstrings for public functions.
- Comments: only where the code cannot show the reason on its own (a non-obvious constraint, a workaround, a deliberate trade-off). Never restate what the code does, never label sections, and delete comments that go stale when code changes.
- Spacing: a blank line after a function docstring, before the first statement. Blank lines before and after each `if`/`elif`/`for`/`while`/`with`/`try` block, and between a simple statement and the block that follows it. No blank line directly after a block header (`if ...:`, `for ...:`). Consecutive simple statements stay together.

Testing
- Tests use pytest and live under `tests/`.
- Test through injected fakes (for example a fake client object passed as an argument), not by patching module attributes.
- Tests must not call the real API.

Dependencies
- Add runtime dependencies with `uv add <pkg>`, and test-only ones with `uv add --group test <pkg>`.
- Keep the Docker image free of test tools: build with `uv sync --locked --no-dev`.
