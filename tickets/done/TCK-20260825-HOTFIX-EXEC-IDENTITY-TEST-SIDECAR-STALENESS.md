---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS
phase: open
date: 2026-08-25
tags: [testing, ai]
---

# TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS

## Title
Fix a third os-import guard copy and a stale sidecar-writing test helper, both surfaced by the same CI re-run

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Real CI re-run on PR #78 (after `TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT`
landed) surfaced two further, distinct real failures in the same job:

1. `tests/tools/test_knowledge_gateway_redaction.py::TestSqliteOperationalLimits::test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py`
   — a **third**, near-identical copy of the same overbroad `"os" not in imported_modules` guard
   the sibling ticket already narrowed twice (in `tests/docs/` and `tests/tools/test_retrieval_cache.py`).
   A repo-wide grep after this fix confirms zero remaining copies.
2. `tests/tools/test_execution_identity_end_to_end.py::test_controlled_claude_execution_produces_coherent_identity_across_jsonl_sources`
   and `::test_newly_appended_lines_have_no_duplicate_identity_keys_and_correct_values` — this
   test's own `_write_sidecar()` helper only ever wrote the old unscoped `.claude/current_run`
   file, predating both `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE` (which made the real
   `writeSidecar()` write a scoped copy too) and `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`
   (which made `post_tool_hook.py` stop falling back to the unscoped file when no scoped file
   exists — writing null attribution instead). The test's own docstring commits to "mirrors the
   exact shape writeSidecar's body... now produce," so this is a genuine, real test-staleness gap
   this session's own prior changes exposed, not previously caught because this test file lives
   in neither of the two directories either sidecar ticket's own Test phase scoped.

## Scope
- Narrow `test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py` in
  `tests/tools/test_knowledge_gateway_redaction.py` identically to the two sibling guards already
  narrowed by `TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT` — drop the AST
  import-scan, keep all string-level substance checks (`PRAGMA busy_timeout`, `os.chmod`, `chmod`)
  unchanged.
- Update `_write_sidecar()` in `tests/tools/test_execution_identity_end_to_end.py` to also write
  the per-session-scoped `.claude/current_run.<session_id>` copy, mirroring the real, current
  `writeSidecar()` shape — computing one shared `session_id` value reused by both the sidecar
  write and the subsequent `_run_post_tool_hook()` call, so the hook's payload `session_id`
  matches the file it just wrote.
- Repo-wide grep confirming zero remaining copies of the `"os" not in imported_modules` pattern.

## Out of Scope
- Any change to `tools/retrieval_cache.py`, `tools/agent-monitoring/post_tool_hook.py`, or
  `.claude/workflows/implement-ticket.js` — all already-shipped, correct, tested behavior.
- The 24 additional local-only test failures observed in a local full-job repro
  (`tests/cli/*`, `tests/observability/*`) — cross-checked against the real GitHub Actions CI run,
  which shows none of these; classified as local-sandbox-only noise (this session's own
  environment, e.g. `CLAUDE_CODE_SESSION_ID` already being set, polluting subprocess-determinism
  tests that expect a clean env) per this repo's own documented CI-triage precedent for
  local-repro-only noise. Not touched.

## Acceptance Criteria
- [x] `test_sqlite_limits_functions_not_added_to_tools_retrieval_cache_py` passes against the
      real, current `tools/retrieval_cache.py`.
- [x] `grep -rln '"os" not in imported_modules' tests/` returns zero matches repo-wide.
- [x] Both `test_execution_identity_end_to_end.py` tests pass with the updated `_write_sidecar()`.
- [x] The updated `_write_sidecar()`'s scoped-file `session_id` matches exactly what
      `_run_post_tool_hook()` passes in its hook payload for the same simulated execution.
- [x] `tests/tools/test_execution_identity_end_to_end.py` and
      `tests/tools/test_knowledge_gateway_redaction.py` both pass in full (not just the named
      failing tests) — confirms no adjacent regression.

## Related Tickets
- TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT (sibling — narrowed the first two of
  the three total guard copies)
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE (introduced the scoped-sidecar-write convention this
  test helper was stale against)
- TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION (made the unscoped-file fallback stop working for
  sessions without a scoped file, exposing the staleness)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix — no staging artifacts).

## Related Code Areas
- `tests/tools/test_knowledge_gateway_redaction.py`
- `tests/tools/test_execution_identity_end_to_end.py`
- `tools/retrieval_cache.py` (read-only reference; not modified)
- `tools/agent-monitoring/post_tool_hook.py` (read-only reference; not modified)

## Assumptions / Open Questions
None — both root causes independently confirmed via real CI logs
(`gh api .../actions/jobs/{id}/logs`), not guessed. The 24 local-only failures were investigated
enough to confirm they don't touch any file this PR's 4 tickets changed, then cross-checked
against the real CI run (which doesn't show them) before being classified as environment noise
rather than chased further.

## Implementation Notes
Both root causes confirmed via real CI logs, not guessed. Repo-wide grep
(`grep -rln '"os" not in imported_modules' tests/`) confirmed exactly one remaining copy before
this fix, and zero after — the pattern is fully retired now.

For the sidecar staleness fix: traced `writeSidecar()`'s real current shape in
`.claude/workflows/implement-ticket.js` directly (not assumed) to confirm it writes the scoped
file keyed by the `CLAUDE_CODE_SESSION_ID` env var, and confirmed `post_tool_hook.py` reads the
scoped-file key from its own hook payload's `session_id` field — these are the same logical value
in real production use (the harness sets both consistently per session), so the test's own
`session_id` construction (`f"sess-{execution_id}"`) just needed to be computed once and reused
for both the sidecar write and the hook-payload call, rather than the hook call silently using an
unwritten key.

The 24 additional failures seen in a local full-job repro (`tests/cli/*`, `tests/observability/*`)
were investigated: none touch any file changed by this PR's 4 tickets, and the real GitHub Actions
CI run (clean environment) does not show them — classified as local-sandbox-only noise (this
session's own dev environment already has `CLAUDE_CODE_SESSION_ID` and other state set, which
subprocess-determinism-sensitive CLI tests are not designed to tolerate) per this repo's own
documented precedent for local-repro-only environmental noise. Not touched, not chased further.

## Test Summary
- `pytest tests/tools/test_execution_identity_end_to_end.py tests/tools/test_knowledge_gateway_redaction.py tests/tools/test_retrieval_cache.py tests/docs/test_redaction_retention_policy_doc.py -q`
  → 189 passed.
- `grep -rln '"os" not in imported_modules' tests/` → zero matches (was 1 before this fix, 3
  total across this ticket + its sibling).

## Files Changed
- `tests/tools/test_knowledge_gateway_redaction.py` — narrowed the third and final copy of the
  overbroad `os`-import guard.
- `tests/tools/test_execution_identity_end_to_end.py` — `_write_sidecar()` now also writes the
  per-session-scoped sidecar file, matching the real current `writeSidecar()` shape; its one call
  site updated to compute and share one `session_id` value across both the sidecar write and the
  `post_tool_hook.py` invocation.

## Completion Summary
Fixed the two remaining real CI failures on PR #78, both real regressions surfaced by this
session's own prior tickets (`TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY`'s legitimate `os`
import; `TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION`'s removal of the unscoped-file fallback).
The `os`-import guard pattern is now fully retired repo-wide (0 remaining copies, confirmed by
grep). The execution-identity test's sidecar-writing helper now matches the real, current
`writeSidecar()` shape instead of a pre-scoped-sidecar-era assumption. A separate class of local
sandbox-only failures was investigated and explicitly not chased, per this repo's own CI-triage
precedent for environment noise the real CI doesn't reproduce. Test-only changes, no
source/workflow file touched.
