# syntax=docker/dockerfile:1
# Backend image built from uv.lock on the Python CI tests (TCK-20261008-BACKEND-IMAGE-BUILDS-FROM-UV-LOCK),
# following https://docs.astral.sh/uv/guides/integration/docker/. The uv version below is the one CI pins
# (`astral-sh/setup-uv` `version: "0.11.2"` in .github/workflows/test.yml); change both together.
# Base images are pinned by digest (the multi-arch index current on 2026-10-14; no version change). Dependabot's `docker` ecosystem bumps them.
FROM ghcr.io/astral-sh/uv:0.13.1@sha256:4a1f3666816dafadd20ceb71eac9a7d56d7ef30279f7d64048519ab901ada336 AS uv

FROM python:3.14.8-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS builder
COPY --from=uv /uv /uvx /bin/

# Bytecode at build time, copy (not hardlink) from the cache mount, no dev/lint tooling, and use this image's
# Python for both stages instead of letting uv download its own.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_NO_DEV=1 \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

# Dependencies first, in their own layer: only uv.lock / pyproject.toml changes invalidate it.
# --no-default-groups drops the project's default `dev` and `lint` groups (pyproject [tool.uv] default-groups).
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-default-groups

# Then the project itself, installed non-editable so the final venv does not point back at the build stage.
COPY pyproject.toml uv.lock /app/
COPY src/ /app/src/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-default-groups --no-editable

FROM python:3.14.8-slim@sha256:a2b82f3c48559aa0a8446d9af49826b6e2b2016f4cd2afabfe6013ec53729170 AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Source & data. `src/` is copied again on purpose even though the venv holds a non-editable install of it:
# `python -m src` runs from /app, so /app/src is the copy that is imported, and several modules locate repo
# files relative to their own path (e.g. src/content/validator.py `parents[2]`, src/engine/capability.py reads
# docs/engine/capability_registry.yaml). Imported from site-packages those lookups would resolve to the wrong
# directory. Dropping this COPY was tried in TCK-20261008-OPS-FILES-INTO-DOCKER-DIR and rejected for that reason.
COPY src/ /app/src/
COPY data/ /app/data/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "src", "serve", "--host", "0.0.0.0", "--port", "8000"]
