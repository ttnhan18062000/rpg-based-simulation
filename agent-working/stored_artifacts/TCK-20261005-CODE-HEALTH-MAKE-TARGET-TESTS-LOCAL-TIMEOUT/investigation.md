---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT
artifact_type: investigation
tags: [testing]
---

# Investigation — TCK-20261005-CODE-HEALTH-MAKE-TARGET-TESTS-LOCAL-TIMEOUT

## Findings
- Baseline test 58.98-59.1 s, snapshot test 65.2 s with the budget off; load average 2.3-3.2, so not idle.
- Dominant cost in both: `git log --shortstat --pretty=format:...` (full-history churn walk), 27.6-28.0 s per call, paid twice per test (in-process and via `make`).
- The shared `.venv` has no `ast-grep` or `ruff`; a first snapshot run failed with "ast-grep not found". Resolved with a scratch `uv sync --locked --no-install-project --native-tls` (plain `uv sync` failed on a TLS certificate error here).
- Edit-ratchet hook test: 3 of 3 passed at 0.15 s; does not reproduce.
- CI per-test durations were not available (log hosts TLS-blocked); none claimed.
- Context scan: `search_docs` unavailable; `tools/knowledge_search.py` had no index in the new worktree.
