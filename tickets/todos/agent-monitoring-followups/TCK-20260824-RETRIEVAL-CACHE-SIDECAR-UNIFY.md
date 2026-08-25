---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY
phase: open
date: 2026-08-24
tags: [observability]
---

# TCK-20260824-RETRIEVAL-CACHE-SIDECAR-UNIFY

## Title
Unify retrieval_cache.py's sidecar-read logic with post_tool_hook.py's scoped convention

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
tools/retrieval_cache.py's read_current_run_sidecar()/_sidecar_run_is_stale() duplicate post_tool_hook.py's sidecar-reading logic but were deliberately left on the old unscoped-only read path when the scoped-sidecar convention was introduced. The fix migrates retrieval_cache.py's read path to the same scoped-then-unscoped-fallback preference order (using CLAUDE_CODE_SESSION_ID directly, since this call path has no hook-payload session_id), adds cross-referencing docstrings/comments at both call sites so a future change to one is discoverable from the other, and keeps the two distinct "staleness" concepts (ticket-closed vs mtime-based scoped-file pruning) separate rather than merging them -- without giving retrieval_cache.py its own pruning logic. Because this ticket's unification target depends on whatever convention TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION lands with, it should be sequenced after that ticket.

## Scope
- Migrate tools/retrieval_cache.py's read_current_run_sidecar() to read .claude/current_run.<CLAUDE_CODE_SESSION_ID> (via os.environ.get) when that scoped file exists, falling back to the unscoped .claude/current_run when it does not, mirroring post_tool_hook.py's exact preference order
- Preserve the existing file-existence-based _sidecar_run_is_stale() (done-vs-inprogress ticket check) unchanged; all 7 current TestReadCurrentRunSidecar cases must continue to pass verbatim
- Add a docstring/comment cross-reference at both read_current_run_sidecar() and post_tool_hook.py's inline sidecar block pointing at each other
- Add a new test proving a scoped file's field values win over a stale unscoped file's when both exist
- Add a new test asserting no new file-deletion side effect is introduced in retrieval_cache.py's sidecar read path

## Out of Scope
- Merging the two distinct "staleness" concepts (ticket-closed file-existence check vs mtime-based scoped-file prune threshold) into one function
- Giving retrieval_cache.py its own _prune_stale_scoped_sidecars()-equivalent -- pruning stays solely owned by post_tool_hook.py
- Extracting a fully shared helper module between the two files (true unification beyond mirroring the read order) -- a larger structural change not warranted here
- Beginning implementation before TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION lands, since that ticket may change the scoped-sidecar convention this ticket targets

## Acceptance Criteria
- [ ] read_current_run_sidecar() reads .claude/current_run.<CLAUDE_CODE_SESSION_ID> (via os.environ.get) when that scoped file exists, falling back to unscoped .claude/current_run when it does not -- mirroring post_tool_hook.py's exact preference order -- with a new test proving a scoped file's field values win over a stale unscoped file's when both exist
- [ ] The existing file-existence-based _sidecar_run_is_stale() (done-not-inprogress ticket check) is preserved unchanged and continues to pass all 7 current TestReadCurrentRunSidecar cases verbatim -- migration is additive to the read-path selection, not a rewrite of staleness semantics
- [ ] retrieval_cache.py does NOT gain its own _prune_stale_scoped_sidecars()-equivalent -- pruning stays solely owned by post_tool_hook.py -- verified by a test asserting no new file-deletion side effect in retrieval_cache.py's sidecar read path
- [ ] A docstring/comment cross-reference is added at both read_current_run_sidecar() and post_tool_hook.py's inline sidecar block pointing at each other so a future change to one is discoverable from the other

## Related Tickets
- TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION
- TCK-20260824-SIDECAR-CROSS-SESSION-SCOPE
- TCK-20260818-STANDARD-KGMCP-CACHE-ATTRIBUTION-AND-SKILL-USAGE-DASHBOARD
- TCK-20260824-KGMCP-KEEP-OR-DEPRECATE

## Related Docs
- docs/agent-monitoring/schema.md

## Related Stored Artifacts
None.

## Related Code Areas
- tools/retrieval_cache.py
- tools/agent-monitoring/post_tool_hook.py
- tests/tools/test_retrieval_cache.py
- .claude/workflows/implement-ticket.js

## Assumptions / Open Questions
- SEQUENCING: this ticket depends on TCK-20260824-SIDECAR-ADHOC-NULL-ATTRIBUTION. If that ticket changes how/when scoped sidecar files get written (e.g. the hook becoming a co-writer with a null-sentinel convention), this ticket's unification target moves; this ticket should be implemented after that one lands, or explicitly re-scoped to whatever convention it leaves in place
- retrieval_cache.py's read_current_run_sidecar() takes no session_id argument and is called from CLI/library contexts, not a hook payload; it must use CLAUDE_CODE_SESSION_ID directly (confirmed already used identically at 2 call sites in implement-ticket.js)
- The two "staleness" concepts share a name but are semantically unrelated (file-existence done-vs-inprogress check vs 24h mtime-based prune threshold) and must stay separate, not merged
- KGMCP (the sole real consumer of retrieval_cache.py's sidecar_stale flag) was ratified "keep as-is, no further investment," supporting P2/low-urgency framing but not making the drift risk zero, since post_tool_hook.py keeps evolving independently
- No shared helper module previously existed for this logic; true unification (vs parity-by-copy) would require extracting a shared module both files import -- a larger structural change deferred out of this ticket's scope

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
