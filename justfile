default:
    @just --list

sync:
    uv sync --locked --group test

lock-check:
    uv lock --check

lint:
    uv run --locked --group test ruff check src tests

typecheck:
    uv run --locked --group test ty check src tests

test:
    uv run --locked --group test pytest

check: lock-check lint typecheck test

run data="data" out="output":
    uv run aithena {{data}} {{out}}

docker-test:
    docker build --target test -t aithena:test .

docker-build:
    docker build --target runtime -t aithena:local .

bump cooldown="7 days":
    uv lock --upgrade --exclude-newer "{{cooldown}}"
    just check
