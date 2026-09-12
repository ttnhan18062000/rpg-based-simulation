---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT
phase: done
date: 2026-08-25
tags: [testing, ai]
---

# TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT

## Title
Narrow the second, sibling `os`-import guard in `test_redaction_retention_policy_doc.py` that TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY's own test-scoping missed

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI on PR #78 (`Architecture / docs / static` job) failed:
`tests/docs/test_redaction_retention_policy_doc.py::test_sqlite_defaults_not_silently_implemented`
asserts `"os" not in imported_modules` via an AST walk of `tools/retrieval_cache.py`.
`TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY` added a legitimate `import os` (for
`os.environ.get("CLAUDE_CODE_SESSION_ID")`, needed to read the per-session scoped sidecar file)
and correctly narrowed the *other* static guard that also blanket-banned `os` imports
(`tests/tools/test_retrieval_cache.py::test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration`)
— but missed this second, independent guard living in a different test file/directory
(`tests/docs/`, not `tests/tools/`), which that ticket's own Test phase never ran.

This guard's real purpose (per its own docstring) is to prevent `retrieval_cache.py` from
re-implementing SQLite connection-tuning (`PRAGMA busy_timeout`, `os.chmod`) that must stay
exclusively behind `knowledge_gateway_redaction.open_connection_with_limits()` — the blanket
`"os" not in imported_modules` check was an overbroad proxy for that, not the real substance
check. The real substance checks (`PRAGMA busy_timeout` string absence, `os.chmod`/`chmod` string
absence) remain fully valid and must stay enforced; only the overbroad `os`-import proxy needs
narrowing, mirroring exactly how the sibling guard in `tests/tools/test_retrieval_cache.py` was
already narrowed by the parent ticket.

## Scope
- Narrow `test_sqlite_defaults_not_silently_implemented` in
  `tests/docs/test_redaction_retention_policy_doc.py` so it no longer blanket-bans importing `os`
  — replace the `assert "os" not in imported_modules` line with a check for the actual substance
  this guard cares about (e.g. assert no `os.chmod`/`os.popen`/connection-tuning-relevant `os.*`
  call is present, or simply drop the import-level check now that the string-level
  `PRAGMA busy_timeout`/`os.chmod`/`chmod` assertions immediately above it already cover the real
  concern directly).
- Keep all other assertions in this test (`PRAGMA journal_mode`, `PRAGMA busy_timeout`,
  `busy_timeout`, `os.chmod`, `chmod` string absence) completely unchanged.

## Out of Scope
- Any change to `tools/retrieval_cache.py` itself — the `import os` addition is legitimate,
  already-shipped, already-tested behavior from `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`.
- Any change to `tests/tools/test_retrieval_cache.py::test_no_pragma_busy_timeout_chmod_or_os_import_introduced_by_level2_migration`
  — that guard was already correctly narrowed by the parent ticket.
- Any change to the other assertions/tests in `test_redaction_retention_policy_doc.py`.

## Acceptance Criteria
- [x] `test_sqlite_defaults_not_silently_implemented` passes against the real, current
      `tools/retrieval_cache.py` (which legitimately imports `os`).
- [x] The test still fails loudly if `PRAGMA busy_timeout`, `os.chmod`, or `chmod` (connection-tuning
      substance) is ever re-added to `retrieval_cache.py` — verified by temporarily reintroducing
      one such string in a scratch copy and confirming the test still catches it.
- [x] No other test in `tests/docs/test_redaction_retention_policy_doc.py` or
      `tests/tools/test_retrieval_cache.py` regresses.

## Related Tickets
- TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY (the ticket whose legitimate `import os` addition
  this hotfix's guard drift stems from)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
- `tests/docs/test_redaction_retention_policy_doc.py`
- `tools/retrieval_cache.py` (read-only reference; not modified by this ticket)

## Assumptions / Open Questions
None — root cause independently confirmed via real CI log (`gh api .../logs`), not guessed from
the job name, per this repo's CI Failure Triage rule.

## Implementation Notes
Root cause confirmed via real CI log (`gh api repos/.../actions/jobs/{id}/logs`), not guessed:
`test_sqlite_defaults_not_silently_implemented` blanket-banned any `os` import via an AST walk, as
an overbroad proxy for its real concern (no `os.chmod`/connection-tuning PRAGMA usage). Dropped the
AST import-scan block entirely; the string-level `PRAGMA journal_mode`/`PRAGMA busy_timeout`/
`busy_timeout`/`os.chmod`/`chmod` checks immediately above already enforce the real concern
directly and remain unchanged. Docstring updated with a narrowing note mirroring the existing
narrowing precedent already recorded in the same docstring.

Verified the guard still works (not just weakened to always pass): temporarily reintroduced
`os.chmod(...)` into a scratch copy of `tools/retrieval_cache.py`, confirmed the test still fails
loudly, then restored the file (`git diff --stat` confirmed zero residual diff).

## Test Summary
- `pytest tests/docs/test_redaction_retention_policy_doc.py tests/tools/test_retrieval_cache.py -q`
  → 120 passed.
- Full CI-equivalent scope for the failing job (`pytest tests/architecture tests/docs
  tests/integrity tests/static tests/refactor -m "not slow and not extra_slow" -q`) → 170 passed,
  2 skipped, 1 deselected, 2 xfailed, 0 failed (was 1 failed, 168 passed before this fix).
- Real-regression check: temporarily reintroduced `os.chmod(...)` into a scratch copy, confirmed
  the narrowed guard still fails loudly, then restored the file with zero residual diff.

## Files Changed
- `tests/docs/test_redaction_retention_policy_doc.py` — narrowed
  `test_sqlite_defaults_not_silently_implemented`'s overbroad `os`-import ban; all string-level
  substance checks unchanged.

## Completion Summary
Fixed a real CI failure on PR #78 caused by `TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`'s
legitimate `import os` addition tripping a second, sibling static guard
(`tests/docs/test_redaction_retention_policy_doc.py`) that ticket's own Test phase never ran
(distinct test directory from the sibling guard it did correctly narrow in `tests/tools/`).
Narrowed the guard's overbroad `os`-import proxy check while keeping its real substance checks
(`PRAGMA busy_timeout`, `os.chmod`, `chmod` string absence) fully intact and independently
re-verified to still catch a real reintroduction. Test-only change, no source/workflow file
touched.
