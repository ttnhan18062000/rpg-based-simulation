#!/usr/bin/env bash
# prek pre-commit hook `code-health-ratchet`: run codebase.gates.staged_ratchet on the staged src files.
# .git/hooks is shared by every worktree on the machine, so this must never block a commit just because the
# project environment is missing: if python3 cannot import the module, say so and exit 0. A real new or worse
# violation exits 1 (from the module). Opt-in install: make install-prek-hooks.
if ! python3 -c "import codebase.gates.staged_ratchet" >/dev/null 2>&1; then
    echo "code-health hook skipped: environment not synced (uv sync) or codebase.health not importable here"
    exit 0
fi
exec python3 -m codebase.gates.staged_ratchet "$@"
