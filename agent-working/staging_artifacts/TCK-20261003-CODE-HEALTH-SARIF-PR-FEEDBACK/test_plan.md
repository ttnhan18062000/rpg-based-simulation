---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK
artifact_type: test_plan
tags: [delivery, security]
---

# Test Plan — TCK-20261003-CODE-HEALTH-SARIF-PR-FEEDBACK

All runs one at a time under `systemd-run --user --scope -q -p MemoryMax=2G -p MemorySwapMax=0`; exit status checked separately.

- Unit (new `tests/tools/test_code_health_sarif_feedback.py`): matching row filtered; no row kept; worse-than-row kept; at-ceiling ruff group dropped; ruff name -> code map; absolute uri made relative; complexipy `Class::method` -> `Class.method` key; cap and truncation count; malformed SARIF raises `SarifError`; CLI could-not-run (tool missing, malformed output) writes the summary line, warning and exit 2; no changed files; summary appended not overwritten.
- End to end (local, real ruff and complexipy): a tmp git-less project with a registry seeded from a scan, then one added violation in one file -> the SARIF contains exactly that finding and nothing from the registry's rows.
- Static: only the new job has `security-events: write`; no top-level `permissions:` write; fork guard present; `continue-on-error`; the action pinned to a 40-char SHA; allowlist of `uses:` updated; `tests/static`, `test_ci_workflow_test_coverage`, `test_generate_registry`, old-root guard.
- Security-Review: the `security-reviewer` agent on the diff; verdict recorded.
- Real data: run the CLI on a realistic changed-file list (for example the files changed by this branch) and record kept/dropped counts and wall time.
- PR run (after owner push): job green; the upload step outcome recorded; if code scanning rejects the upload, record the exact message as an owner action.
