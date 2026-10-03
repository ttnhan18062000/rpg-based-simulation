# Plan — TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION

## Design decision: distinguishing signal for "ad-hoc" vs "real, not-yet-scoped" workflow

Per investigation.md: no such distinction is actually needed. Every real writer in this repo's
current code writes the scoped and unscoped sidecar files together, atomically. A session with
no scoped file has, by construction, made no real ticket-attributed write yet — there is no real
attribution being lost by reporting null for it, whether the session is truly ad-hoc chat use or
a ticket workflow whose very first phase-transition write hasn't landed yet. **Decision: treat
"no scoped file for this session" as the single, simple trigger — no separate ad-hoc detection
heuristic.**

## Mechanism

1. On a tool call: if `.claude/current_run.<session_id>` exists, read it (unchanged from the
   prior ticket).
2. If it does NOT exist (and `session_id` is present in the hook payload — always true for real
   Claude Code hooks): write a null-valued sentinel to that same path (create — there is nothing
   to overwrite yet), then read it back (yielding null attribution for this call).
3. A later real `writeSidecar()` call for the same `session_id` unconditionally overwrites the
   same path with real values (it always does an unconditional write, never checks for an
   existing file) — so the sentinel never blocks or gets confused with real attribution once
   real ticket work starts for that session.
4. The sentinel is an ordinary `current_run.*` file, so the existing
   `_prune_stale_scoped_sidecars()` 24h sweep (added by TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE)
   already covers its cleanup — no new lifecycle code needed.

## Historical-data decision (Plan-phase, per ticket's own Assumptions)

Already-misattributed `tools.jsonl` rows from before this fix are accepted as a documented
caveat, not corrected or flagged — matching this repo's existing no-backfill precedent for the
same class of problem (established explicitly by `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s
own Completion Summary, and the broader convention in `docs/agent-monitoring/schema.md` for
legacy/pre-fix rows generally). No schema change, no new field, no correction script.

## Test plan

- Update `test_foreign_scoped_sidecar_not_read_by_different_session`: assert null attribution
  (not the old unscoped-fallback value); assert a new sentinel file now exists for the calling
  session with null `run_id`; assert the unscoped and foreign-session files are untouched.
- Update the 3 tests that implicitly relied on unscoped-only fallback
  (`test_phase_and_agent_included_when_sidecar_present`,
  `test_execution_identity_fields_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`): write their fixture sidecar to the
  scoped path instead of the unscoped path — same testing purpose (field extraction / partial-
  content tolerance), tracking the new file-preference convention.
- New: two-call-same-session test proving the SECOND call reads its own sentinel, not a
  since-changed unscoped file.
- New: real-writeSidecar-overwrites-earlier-sentinel test proving no data loss once real
  attribution starts.
- New: sentinel pruning test (stale null-valued sentinel gets swept identically to any other
  scoped file).
- No changes to `test_current_run_sidecar_orchestrator.py` (implement-ticket.js itself untouched
  by this ticket), `test_retrieval_cache.py` (deferred to TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY),
  or `.claude/settings.json` (out of scope).

## Parity ledger

New entry required in `docs/parity_ledger/infrastructure.yaml` (real `tools/` behavior change)
citing `tools/agent-monitoring/post_tool_hook.py` and the new/updated tests.
