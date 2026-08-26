---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260826-KGMCP-CACHE-TICKET-ATTRIBUTION
phase: open
date: 2026-08-26
tags: [observability, debugging, data-quality]
---

# TCK-20260826-KGMCP-CACHE-TICKET-ATTRIBUTION

## Title
Fix KGMCP cache-access-log ticket_id attribution root cause in read_current_run_sidecar()

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P1

## Request Summary
Every retrieval_cache_access_log row is unattributed by ticket_id (100% NULL, not just the 43.5% already flagged stale). Root cause confirmed at tools/retrieval_cache.py:555-615: read_current_run_sidecar() computes an internal effective_ticket_id (ticket_id, falling back to run_id when it starts with 'TCK-') but uses that value only for the sidecar_stale check at line 614 -- the dict's own returned 'ticket_id' key at line 613 is the raw sidecar.get('ticket_id'), which is always None because no sidecar writer ever sets that distinct explicit key. log_cache_access() (line 679) writes that raw None verbatim into the ticket_id column. This is exactly why per-agent breakdown in compute_kgmcp_cache_efficiency_metrics() works (agent has no such fallback indirection) while per-ticket breakdown silently groups everything under 'unattributed'. generate_retro.py's read/grouping side was confirmed symmetric and not buggy -- the fix belongs entirely on the write side in tools/retrieval_cache.py.

## Scope
- Fix read_current_run_sidecar() and/or log_cache_access() in tools/retrieval_cache.py so the ticket_id ultimately written to retrieval_cache_access_log reflects the effective_ticket_id (explicit ticket_id, or run_id fallback when it starts with 'TCK-'), not the raw always-None sidecar.get('ticket_id').
- Explicitly decide during Plan whether the fix changes read_current_run_sidecar()'s general public 'ticket_id' key contract, or is scoped narrowly inside log_cache_access() (computing effective_ticket_id locally, leaving read_current_run_sidecar()'s public contract untouched).
- Add/update tests confirming compute_kgmcp_cache_efficiency_metrics()'s per_ticket breakdown groups a freshly-logged row (from a run_id-only sidecar fixture) under the real ticket_id key.
- Grep more broadly than tools/retrieval_cache.py for other consumers of read_current_run_sidecar()'s returned dict before finalizing the fix location.
- Re-verify the fix does not break any documented intentional divergence from post_tool_hook.py established by the SIDECAR-UNIFY/SIDECAR-ADHOC-NULL-ATTRIBUTION tickets.

## Out of Scope
- Retroactive backfill of the ~350 hits / 222 writes already persisted with ticket_id=NULL -- Plan must explicitly decide to include or exclude this (default: document as an accepted historical gap, matching this repo's established no-backfill precedent), not silently do either.
- Any change to generate_retro.py's read/grouping logic (confirmed symmetric and not buggy).
- The separate, already-tracked near-zero (~1.4%) coverage_rate failure mode under TCK-20260824-RETRO-METRIC-CAVEATS -- not this ticket's concern.

## Acceptance Criteria
- [x] Given .claude/current_run contains only run_id (a 'TCK-...' value, with no explicit ticket_id key -- the real shape every sidecar writer produces), read_current_run_sidecar()['ticket_id'] returns that run_id value, not None.
- [x] A log_cache_access() call made under that same run_id-only sidecar writes a retrieval_cache_access_log row whose ticket_id column equals the real ticket ID, not NULL.
- [x] compute_kgmcp_cache_efficiency_metrics()'s per_ticket breakdown groups a freshly-logged row (from a run_id-only sidecar fixture) under the real ticket_id key, not 'unattributed'.
- [x] test_explicit_ticket_id_field_used_over_run_id_when_both_present continues to pass unchanged -- explicit ticket_id must still win over run_id-fallback.
- [x] Plan explicitly records the decision on whether to retroactively backfill the ~350/222 already-NULL historical rows, or to document them as an accepted historical gap (default), rather than leaving the question unaddressed.

## Related Tickets
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
- TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY
- TCK-20260824-RETRO-METRIC-CAVEATS
- TCK-20260825-HOTFIX-EXEC-IDENTITY-TEST-SIDECAR-STALENESS
- TCK-20260825-HOTFIX-RETRIEVAL-CACHE-OS-IMPORT-GUARD-DRIFT

## Related Docs
- docs/observability/retrieval_retention_redaction_policy.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/retrieval_cache.py
- tools/agent-monitoring/generate_retro.py
- .claude/workflows/implement-ticket.js
- tests/tools/test_retrieval_cache.py

## Assumptions / Open Questions
- Plan decision: fix lives in read_current_run_sidecar()'s general public contract (the "ticket_id" key now returns effective_ticket_id), not narrowly inside log_cache_access(). Justification: a repo-wide grep confirmed log_cache_access() is the sole production consumer of the returned dict (all other matches are tests, docstrings, or comments), so fixing the general contract is a single-source-of-truth change with no duplicated fallback logic, and every existing test in TestReadCurrentRunSidecar continues to pass unchanged (verified) because none of them asserted the old (buggy) raw-None behavior for the run_id-only case.
- Plan decision: historical ~350 hits / 222 writes already persisted with ticket_id=NULL are NOT backfilled -- documented here as an accepted historical gap, matching this repo's established no-backfill precedent (same precedent already used for tools.jsonl/sidecar-staleness fixes this session).
- Broader grep confirmed: log_cache_access() is the sole production consumer of read_current_run_sidecar()'s return dict.
- Fix does not touch post_tool_hook.py or its SIDECAR-UNIFY/SIDECAR-ADHOC-NULL-ATTRIBUTION behavior at all -- confirmed by inspection, zero overlap.

## Implementation Notes
Root cause fix: `tools/retrieval_cache.py`'s `read_current_run_sidecar()` previously returned the
raw `sidecar.get("ticket_id")` (always None, since no sidecar writer sets that distinct key) under
the `"ticket_id"` dict key, while separately computing `effective_ticket_id` (explicit ticket_id,
or run_id fallback when it starts with "TCK-") but only using that value for the `sidecar_stale`
check. Changed the returned dict to use `effective_ticket_id` for the `"ticket_id"` key instead of
the raw value. `log_cache_access()` (the sole production consumer, confirmed via repo-wide grep)
now writes the real effective ticket ID into `retrieval_cache_access_log.ticket_id` for every future
row. Docstring updated to describe the corrected contract. No change to `_sidecar_run_is_stale()`,
`post_tool_hook.py`, or `generate_retro.py`'s read/grouping side (confirmed already symmetric).

## Test Summary
`.venv/bin/python3 -m pytest tests/tools/test_retrieval_cache.py -q -m "not slow"` -- 115 passed, 0
failed (113 pre-existing + 2 new: `test_run_id_only_sidecar_reports_effective_ticket_id_not_none`
in `TestReadCurrentRunSidecar`, and `test_run_id_only_sidecar_writes_real_ticket_id_into_per_ticket_
kgmcp_breakdown` in `TestLogCacheAccess`, the latter a true end-to-end test bridging
`tools/retrieval_cache.py` and `tools/agent-monitoring/generate_retro.py`'s
`compute_kgmcp_cache_efficiency_metrics()`). Also added one new assertion
(`rows[0]["ticket_id"] == "TCK-A"`) to the pre-existing
`test_logs_a_real_level1_hit_with_query_hash_and_repo_branch_scope`.
`test_explicit_ticket_id_field_used_over_run_id_when_both_present` re-confirmed passing unchanged.

## Files Changed
- `tools/retrieval_cache.py` -- `read_current_run_sidecar()`'s returned `"ticket_id"` key now
  reflects `effective_ticket_id`, not the raw always-None sidecar field; docstring updated.
- `tests/tools/test_retrieval_cache.py` -- 2 new tests, 1 new assertion on an existing test.

## Completion Summary
Fixed the confirmed root cause of KGMCP cache-access-log's 100% `ticket_id` attribution gap: the
effective ticket ID was already being computed internally in `read_current_run_sidecar()` but only
used for the staleness check, never returned under the function's own `"ticket_id"` key. The fix
is a two-line change plus a docstring update, scoped to the function's general contract (confirmed
safe via a repo-wide grep showing `log_cache_access()` as the sole production consumer, and via all
pre-existing tests continuing to pass unchanged). Historical NULL rows (~350 hits/222 writes) are
explicitly not backfilled, documented as an accepted historical gap. New end-to-end test proves the
fix all the way through `generate_retro.py`'s per-ticket breakdown, not just the isolated function.
