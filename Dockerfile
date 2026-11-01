FROM ghcr.io/astral-sh/uv:python3.15-trixie-slim AS base

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so this layer is reused until the lockfile changes.
COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY src ./src
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Test stage, not part of the runtime image: docker build --target test .
FROM base AS test
COPY tests ./tests
RUN --mount=type=cache,target=/root/.cache/uv \
    uv run --locked --group test pytest

# Runtime stage: last, so it is the default build target.
FROM base AS runtime

# Run as an unprivileged user. Files stay root-owned, so the app cannot modify its own code.
RUN useradd --uid 1000 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir /app/output \
    && chown app /app/output

USER app

# The API key is read from the environment (ANTHROPIC_API_KEY); it is never baked into the image.
ENTRYPOINT ["aithena"]
CMD ["data", "output"]
