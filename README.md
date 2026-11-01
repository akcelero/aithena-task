# aithena

Analyses the Python files in a directory with Claude:

- **All files:** extracts the copyright holder, license name and license type.
- **Permissive license:** lists each function with its parameters.
- **Copyleft license:** lists functions if the file has more than 2; otherwise rewrites the file in Rust.

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

Or with Docker (reads `.env`):

```
docker compose up --build
```

## Test

```
uv run --group test pytest
```
