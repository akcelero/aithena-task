# aithena

Analyses the Python files in a directory with Claude:

- **All files:** extracts the copyright holder, license name and license type.
- **Permissive license:** lists each function with its parameters.
- **Copyleft license:** lists functions if the file has more than 2; otherwise rewrites the file in Rust.

A file that fails (unreadable, or a Claude error) is recorded in `errors.json` and the rest of the run continues.

## Setup

Requires Python 3.15 and [uv](https://docs.astral.sh/uv/).

```
uv sync
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

## Run

```
uv run aithena data output
```

Results are written to `output/`:
- `licenses.json`
- `functions.json`
- `rust/*.rs`
- `errors.json` (empty when every file succeeded)

Claude answers are cached in `output/cache/`, so re-running on unchanged files makes no API calls. Changing a prompt or model invalidates the affected entries. Deleting `output/` also clears the cache.

Options:
- `--dry-run`: shows the expected number of API calls without making any.
- `--max-calls N`: stops after N real API calls. Cached answers are free. If the limit is reached, the run exits with code 2 and keeps finished results.

Each run prints the API calls made, cache hits, and tokens used.

Or with Docker (reads `.env`):

```
docker compose up --build
```

## Test

```
uv run --group test pytest
```

Or run every check CI runs (lockfile, lint, type checks, tests):

```
just check
```
