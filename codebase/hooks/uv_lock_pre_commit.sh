#!/usr/bin/env bash
# prek pre-commit hook `uv-lock-check`: when pyproject.toml or uv.lock is staged, verify uv.lock still matches
# pyproject.toml. --offline: a commit must never wait for or fail on the network (CI runs `uv sync --locked`).
# Never blocks where uv is not installed (the hook directory is shared by every worktree on the machine).
if ! command -v uv >/dev/null 2>&1; then
    echo "uv-lock-check skipped: uv is not installed"
    exit 0
fi
exec uv lock --check --offline
