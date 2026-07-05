---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260705-RETRO-INDEX-ALL-ROW
phase: done
date: 2026-07-05
tags: [agent-monitoring, retro, data-quality]
---

# TCK-20260705-RETRO-INDEX-ALL-ROW

## Title
Fix agent-monitoring/retro/index.md's "ALL" row, permanently hardcoded to 0|0|0

## Status
DONE

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
- [x] `_update_index()`'s handling of the `ALL` row uses `all_runs` directly (not a `runs_by_week` lookup keyed by the string `"ALL"`).
- [x] The ALL row's DONE/fails counts are computed via the existing `_resolve_status()` helper, not a new or duplicated counting path.
- [x] Re-running `python3 tools/agent-monitoring/generate_retro.py --all` produces an `index.md` ALL row (`484 | 406 | 58`) exactly matching `RETRO-ALL.md`'s own Run Summary table.
- [x] No other row in `index.md` changes behavior — `2026-W27`'s row (`83 | 80 | 3`) confirmed unaffected.

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
`tools/agent-monitoring/generate_retro.py`'s `_update_index()`: changed `week_runs = runs_by_week.get(name, [])` to `week_runs = all_runs if name == "ALL" else runs_by_week.get(name, [])`. The existing `_resolve_status()`-based DONE/fails computation two lines below was left completely untouched — no new counting path introduced, per the ticket's explicit instruction.

## Test Summary
No test harness exists for `tools/agent-monitoring/*.py` (established convention this session). Verified via direct re-execution: ran `python3 tools/agent-monitoring/generate_retro.py --all`, confirmed `index.md`'s ALL row (`484 | 406 | 58`) now exactly matches the regenerated `RETRO-ALL.md`'s own Run Summary table (`Total runs: 484`, `Completed (DONE): 406`, `Gate failures: 58`) at the same point in time. Confirmed the `2026-W27` row's numbers (`83 | 80 | 3`) were unaffected by this change (per-week lookup logic untouched). `ast.parse` confirmed syntax valid.

Regenerating `--all` reset `RETRO-ALL.md`'s Notes section to the placeholder (the same known behavior encountered in `TCK-20260705-RETRO-METRIC-ACCURACY`) — re-added institutional-memory Notes content documenting this fix. `RETRO-2026-W27.md`'s own Notes were unaffected (not regenerated by this `--all`-only run).

## Files Changed
- `tools/agent-monitoring/generate_retro.py`
- `agent-monitoring/retro/index.md` (regenerated output)
- `agent-monitoring/retro/RETRO-ALL.md` (regenerated output; Notes re-added)

## Completion Summary
`agent-monitoring/retro/index.md`'s "ALL" row, permanently hardcoded to `0|0|0` since the retro tool was built, now correctly shows the same totals as `RETRO-ALL.md`'s own Run Summary — a one-line fix (special-case the `ALL` key to use `all_runs` directly instead of a `runs_by_week` lookup that could never match) reusing the existing `_resolve_status()` helper rather than introducing a second counting path.
