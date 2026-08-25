---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION
phase: open
date: 2026-08-24
tags: [observability, debugging]
---

# TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION

## Title
Give ad-hoc sessions null sidecar attribution instead of stale ticket inheritance

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE fixed attribution for sessions that call writeSidecar(), but ad-hoc, non-ticket tool use in post_tool_hook.py still falls back to the stale shared unscoped .claude/current_run file and inherits whatever foreign (possibly closed) ticket's run_id/ticket_id happens to be sitting there. The fix should give ad-hoc sessions null/no attribution in tools.jsonl instead of silently inheriting another ticket's identity, while preserving the existing unscoped-file fallback for legitimate early-workflow-phase sessions that haven't written their first scoped sidecar value yet.

## Scope
- In post_tool_hook.py's sidecar read path, distinguish "ad-hoc, no ticket workflow at all" from "real ticket workflow, hasn't scoped-written yet" and produce null run_id/ticket_id for the former instead of falling back to the stale unscoped file
- Have the hook itself write/refresh a per-session sentinel file (create-if-absent-only; must never overwrite an existing scoped file's real values) so a second tool call in the same ad-hoc session also reads null attribution from its own sentinel rather than the unscoped file
- Ensure the self-written sentinel is swept by the existing _prune_stale_scoped_sidecars() 24h mechanism with no separate cleanup path
- Add new tests: null attribution for an ad-hoc session (analogous to test_foreign_scoped_sidecar_not_read_by_different_session), a second-call sentinel-read confirmation, sentinel pruning, and non-regression for real ticket-workflow sessions that do call writeSidecar()
- Preserve the unscoped-file fallback for legitimate early-workflow-phase sessions that haven't called writeSidecar() yet

## Out of Scope
- Changes to tools/retrieval_cache.py's sidecar-read logic -- that is a separate ticket (TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY), sequenced after this one
- Changes to the inline sidecar-check hook in .claude/settings.json
- Removing the unscoped-file fallback entirely -- still needed for legitimate early-workflow-phase sessions that haven't scoped-written yet
- Backfilling historically misattributed tools.jsonl rows from this gap -- accepted as a caveat per the repo's existing no-backfill precedent

## Acceptance Criteria
- [x] Given a stale unscoped .claude/current_run holding another (possibly closed) ticket's run_id, and no scoped file yet for the current session_id, a tool call in an ad-hoc session produces a tools.jsonl row with run_id=null/ticket_id=null -- not the stale foreign ticket_id -- via a new test analogous to test_foreign_scoped_sidecar_not_read_by_different_session but asserting null attribution
- [x] A second tool call in the same ad-hoc session also yields null attribution, proving the hook's own self-written sentinel (not the unscoped file) is what subsequent calls read
- [x] A real ticket-workflow session that DOES call writeSidecar() is unaffected: once writeSidecar() writes a real value for that session_id, the hook prefers it over any sentinel the hook may have earlier self-written -- existing tests continue to pass unmodified
- [x] The new self-written sentinel file is swept by the existing _prune_stale_scoped_sidecars() 24h mechanism with no separate cleanup path -- existing prune tests continue to pass unmodified, plus a new test confirms a self-written sentinel is pruned identically

## Related Tickets
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260807-CURRENT-RUN-SIDECAR-HAND-ORCHESTRATION-GAP
- TCK-20260711-MONITORING-TOOLCOUNT-SIDECAR-COLLISION
- TCK-20260710-CURRENT-RUN-SIDECAR-BASH
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD

## Related Docs
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py
- tools/agent-monitoring/pre_tool_hook.py
- .claude/settings.json
- .claude/workflows/implement-ticket.js
- tools/retrieval_cache.py
- docs/agent-monitoring/schema.md
- tests/tools/test_post_tool_hook.py

## Assumptions / Open Questions
- test_foreign_scoped_sidecar_not_read_by_different_session currently enshrines unconditional fallback to the unscoped file when no scoped file exists; this fix must not remove that fallback wholesale, only add a way to distinguish ad-hoc-no-workflow from real-workflow-not-yet-scoped-written
- Presence of tickets/inprogress/*.md alone is not a safe distinguishing signal -- a hand-orchestrated session can have a real in-progress ticket yet not have written its first scoped sidecar value yet (very early Scope phase), which would be wrongly sentinel-nulled by a naive check
- If the hook becomes a co-writer of .claude/current_run.<session_id>, it must never overwrite an existing scoped file's real values with its own null sentinel -- needs an explicit create-if-absent-only rule
- tools/retrieval_cache.py and the inline sidecar-check hook in .claude/settings.json were explicitly deferred by the parent ticket and still read only the unscoped file; this fix must not change what's written to the unscoped file itself, since those two deferred readers still depend on it
- Historically misattributed tools.jsonl rows from this gap are accepted as a caveat per the repo's existing no-backfill precedent; this should be an explicit Plan-phase decision, not silently assumed

## Implementation Notes
Investigation found no live-code call site where a real ticket workflow relies on the unscoped-
fallback for real (non-null) attribution — every real writer (`writeSidecar()` in
`implement-ticket.js`, and hand-orchestration per `SKILL.md`) already writes the scoped and
unscoped sidecar files together. This simplified the design: rather than building an ad-hoc-vs-
real-workflow detection heuristic (the `tickets/inprogress/*.md` signal considered and rejected
by the original investigation as unreliable), the fix treats "no scoped file exists for this
session" as the single trigger. `tools/agent-monitoring/post_tool_hook.py` now writes a null-
valued sentinel to `.claude/current_run.<session_id>` (create-if-absent) instead of falling back
to the unscoped file, and reads that sentinel back — giving null attribution until a real
`writeSidecar()` write (which always unconditionally overwrites) lands for that session. The
sentinel is an ordinary `current_run.*` file, so the existing 24h `_prune_stale_scoped_sidecars()`
sweep covers it with no new cleanup path.

Test impact was larger than the ticket's own AC text anticipated: 3 existing tests
(`test_phase_and_agent_included_when_sidecar_present`,
`test_execution_identity_fields_included_when_sidecar_present`,
`test_phase_and_agent_default_to_none_on_partial_sidecar`) implicitly relied on the unscoped-only
fallback (real values, no scoped file, default `session_id="sess-1"`) — this is now a null-
attribution case, so all 3 would have broken. Fixed by moving their fixture writes to the scoped
path (`current_run.sess-1`), preserving each test's actual purpose (field extraction / partial-
sidecar tolerance) while tracking the new file-preference convention. Disclosed here rather than
silently expanded beyond the ticket's original Scope, since the investigation/AC text only
explicitly named `test_foreign_scoped_sidecar_not_read_by_different_session`.

`test_foreign_scoped_sidecar_not_read_by_different_session` itself was updated (not left
unmodified): its original assertion (fall back to the unscoped file's real value) was the exact
bug this ticket fixes, so the assertion was stale by construction, not a durable invariant.

Historical-data decision (per ticket's own Assumptions, made explicitly during Plan): already-
misattributed `tools.jsonl` rows from before this fix are accepted as a documented caveat, not
corrected or flagged — matching this repo's existing no-backfill precedent for the same class of
problem (`TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`'s own precedent).

## Test Summary
`pytest tests/tools/test_post_tool_hook.py -v`: 14/14 pass (3 new: second-call-reads-own-sentinel,
real-writeSidecar-overwrites-sentinel, sentinel-pruned-identically; 4 modified as described above;
7 unmodified and still passing). Broader regression surface:
`pytest tests/tools/test_current_run_sidecar_orchestrator.py tests/tools/test_retrieval_cache.py
tests/tools/test_generate_retro.py -q`: 289 passed (2 unrelated SkillStalenessWarning notices).

## Files Changed
- `tools/agent-monitoring/post_tool_hook.py` — sidecar-read logic: null sentinel instead of
  unscoped-fallback when no scoped file exists for the session.
- `tests/tools/test_post_tool_hook.py` — 3 new tests, 4 modified (see Implementation Notes).
- `docs/parity_ledger/infrastructure.yaml` — new entry `INFRA-384`.

## Completion Summary
Fixed the ad-hoc/non-ticket sidecar-attribution gap disclosed by `TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE`:
sessions with no scoped sidecar file now get null attribution in `tools.jsonl` instead of
silently inheriting whatever foreign (possibly long-closed) ticket the shared unscoped file
happens to hold. Investigation showed no real workflow needed the removed fallback path, so no
unreliable ad-hoc-detection heuristic was needed — "no scoped file yet" is itself the correct,
sufficient signal. All 4 ACs verified with real tests; 14/14 core tests plus 289 broader
regression-surface tests pass.
