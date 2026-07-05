---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-RETRO-INDEX-ALL-ROW
phase: open
date: 2026-07-05
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260705-RETRO-INDEX-ALL-ROW

## Title
Fix agent-monitoring/retro/index.md's "ALL" row, permanently hardcoded to 0|0|0

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`tools/agent-monitoring/generate_retro.py`'s `_update_index()` builds each row of `agent-monitoring/retro/index.md` by looking up `runs_by_week.get(name, [])`, where `runs_by_week` groups all runs by `iso_week(r.get("start_ts", ""))` and `name` is derived from each `RETRO-*.md` filename (e.g. `2026-W27` for `RETRO-2026-W27.md`, `ALL` for `RETRO-ALL.md`). No run's `start_ts` ever produces the literal ISO-week string `"ALL"` — `RETRO-ALL.md` is the all-time snapshot, not a dated weekly report — so the lookup for that row always returns an empty list, and the "ALL" row in `index.md` has been permanently `0 | 0 | 0` since the retro tool was built, regardless of how much real data exists. Confirmed live right now: `agent-monitoring/retro/RETRO-ALL.md`'s own Run Summary shows real totals (hundreds of runs), while `index.md`'s ALL row still shows `0 | 0 | 0`.

This was found and explicitly disclosed (not fixed) during `TCK-20260705-RETRO-METRIC-ACCURACY`'s independent test-phase verification — flagged there as "worth a small follow-up ticket, not actioned in this one," since it's a distinct indexing-key bug, not part of that ticket's DONE-counting fix.

## Scope
- Fix `_update_index()` (`tools/agent-monitoring/generate_retro.py`) so the `ALL` row (or however `RETRO-ALL.md`'s row is identified) uses the full `all_runs` list directly, not a lookup into `runs_by_week` keyed by a string that can never match.
- **Reuse the existing `_resolve_status()` helper** (already used consistently for every other row in `_update_index()`, added by the sibling ticket `TCK-20260705-RETRO-METRIC-ACCURACY`) for the ALL row's DONE/fails counts — do not write a second, separate counting path that could silently reintroduce the legacy-schema undercounting bug that helper was built to fix. This is the specific "don't let legacy data break the next feature" concern to hold in mind: the ALL row must count legacy-schema (`status`-only) runs as DONE the same way every other row already does, not regress to a `final_status`-only check.
- Confirm the fixed `ALL` row's numbers match `RETRO-ALL.md`'s own Run Summary section exactly (both are computed from the same `all_runs`/`_resolve_status` combination, so they should agree by construction — verify this holds, don't just assume it).

## Out of Scope
- Any other row in `index.md` — only the `ALL` row is broken; per-week rows already correctly look up their own `iso_week` bucket.
- Regenerating/re-verifying the two already-committed reports beyond confirming `index.md`'s own numbers — `RETRO-ALL.md`/`RETRO-2026-W27.md` themselves are not affected by this bug (it's isolated to `_update_index()`'s ALL-row special case).
- Any change to `generate()`'s own per-report Run Summary computation — already correct, already uses `_resolve_status`.

## Acceptance Criteria
- [ ] `_update_index()`'s handling of the `ALL` row uses `all_runs` directly (not a `runs_by_week` lookup keyed by the string `"ALL"`).
- [ ] The ALL row's DONE/fails counts are computed via the existing `_resolve_status()` helper, not a new or duplicated counting path.
- [ ] Re-running `python3 tools/agent-monitoring/generate_retro.py --all` (which calls `_update_index()`) produces an `index.md` ALL row whose Runs/DONE/Gate-failures numbers exactly match `RETRO-ALL.md`'s own Run Summary table at the same point in time.
- [ ] No other row in `index.md` changes behavior.

## Related Tickets
- TCK-20260705-RETRO-METRIC-ACCURACY (found and disclosed this bug; added the `_resolve_status()` helper this fix must reuse, not duplicate)

## Related Docs
- docs/guides/agent_monitoring.md (if the index's purpose/behavior needs a one-line clarification once fixed)

## Related Stored Artifacts
None yet.

## Related Code Areas
- tools/agent-monitoring/generate_retro.py (`_update_index()`, `_resolve_status()`)
- agent-monitoring/retro/index.md (generated output — verify after fix, do not hand-edit)

## Assumptions / Open Questions
None — this is a narrow, well-evidenced, mechanical fix with the correct helper function already established and ready to reuse.

## Implementation Notes
(not yet implemented — ticket filed for review before proceeding)

## Test Summary
(not yet implemented)

## Files Changed
(not yet implemented)

## Completion Summary
(not yet implemented)
