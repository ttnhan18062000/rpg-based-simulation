#!/usr/bin/env bash
# Post-commit hook: run incremental knowledge index reindex when docs/ or tickets/done/ changed.
# Install: make install-hooks
# No-op if knowledge-index/ does not exist or if HEAD~1 is unavailable (first commit).

set -euo pipefail

# Guard: no HEAD~1 on first commit
git rev-parse HEAD~1 2>/dev/null || exit 0

changed=$(git diff --name-only HEAD~1 HEAD 2>/dev/null || true)

if echo "$changed" | grep -qE '^(docs/|tickets/done/)'; then
    if [ -f knowledge-index/knowledge.db ]; then
        echo "[knowledge-search] Relevant files changed — running incremental reindex..."
        python3 tools/knowledge_search.py build --incremental
    fi
fi
