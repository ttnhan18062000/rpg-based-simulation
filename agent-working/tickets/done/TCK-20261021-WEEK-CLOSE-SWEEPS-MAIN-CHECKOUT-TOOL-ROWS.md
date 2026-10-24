---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS
phase: done
date: 2026-10-21
tags: [agent-monitoring, data-quality]
---

# TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS

## Title
Week-close sweeps the main checkout's main.tools.jsonl into the closed week's canonical tools file (read-only on the main checkout)

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
The host-ubuntu part of TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH. Host u24desktop's agent-working seats closed that
ticket in #703 (2b4ecebbf, 2026-10-21) while host ubuntu was working it in parallel (#705, 587ab5e9e). Neither host had posted a
claim on #634. #703 lands the SessionStart lines: no tool-row hook, and uncommitted tool rows in any week's shard. It chose a reminder
rather than a flush. #705 overlaps with that and is replaced by this ticket.

What #703 doesn't cover: host ubuntu's measurement. All 18 distinct no-row closing sessions of W41-W43 with a transcript here had hooks
loaded, and their rows sit in the **main checkout's** `main.tools.jsonl`, written by lead and planner sessions launched in the main
checkout on branch `main`. A reminder can't fix that. A main-checkout session never commits through a PR branch, so its rows reach
`main` only if a worktree's week-close carries them. The owner chose (2026-10-21, via lead-planner) to back-fill W43 only, through
this sweep. Lead already restored the 809 W43 rows into the main checkout's file.

## Scope
1. **Port the reviewed sweep from 587ab5e9e unchanged.** That's `tools/agent-monitoring/week_close.py`: `find_main_checkout`, `_identity`, `sweep_main_checkout_tools`, the `close_week` call and the CLI line. Also port `tests/tools/test_week_close_main_checkout_sweep.py` and its README paragraph.
   - Rebase onto origin/main, which now has #703. Merge the README text with #703's new section and don't duplicate it. Keep the two documented limits: the other host's main checkout isn't swept, and a closed week only gains rows on a re-close.
2. **Evidence.** Add `stored_artifacts/TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS/` holding host ubuntu's measurement: `measure.py`, `sessions.csv`, `unknown_durations.py`, and a short `investigation.md` with findings 1-4 from #705. The ticket is a hotfix, so these are evidence, not required artifacts. Check that done_checker accepts the folder for a hotfix; if it objects, put the findings in the ticket's Implementation Notes instead.
   - Say plainly in that `investigation.md` where it agrees with #703's u24 measurement and where it differs: u24 found 6 sessions with no hook event and 5 with hook events but no row, while ubuntu found 0 unloaded.
3. **Don't touch** #703's SessionStart lines (`settings_freshness.py`, `session_start_hook.py`) or the closed ticket and its stored artifacts.

## Out of Scope
- Scope 1 of #705, the hook-not-loaded line: #703 already ships it.
- W41/W42 back-fill: the owner said no.
- The duration-derivation change: that's TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE, in the same batch, and its part 2 builds on this sweep.

## Acceptance Criteria
- On origin/main with #703, a worktree's week-close appends the closed week's main-checkout `main.tools.jsonl` rows that aren't already present. It's read-only on the main checkout, deduped by full row, idempotent, and never raises.
- The sweep tests pass, along with #703's freshness and SessionStart tests and the existing week_close tests. The README has one coherent section.
- The evidence is recorded, along with the comparison with #703.

## Related Tickets
- TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH (closed by #703, host u24; #705 is superseded by this)
- TCK-20261021-HAND-CLOSURE-DURATION-FROM-LAST-ACTIVITY-AND-WEEK-CLOSE-REDERIVE (same batch)

## Related Docs
- docs/agent-monitoring/README.md; issue #634 (the cross-host claim rule)

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261016-TOOLS-HOOK-LOADED-AND-LATE-ROWS-FLUSH/ (#703's, read-only here)

## Related Code Areas
- tools/agent-monitoring/week_close.py; tests/tools/test_week_close_main_checkout_sweep.py

## Assumptions / Open Questions
- The reviewed code from 587ab5e9e is reused as is. Any change beyond the rebase gets a fresh review.

## Implementation Notes
- 2026-10-21 (agent-working-planner): re-scoped after the #703/#705 collision. Batch 9, first ticket, dispatched to agent-working-implementer.

## Test Summary
tests/tools/test_week_close_main_checkout_sweep.py (9, ported unchanged from 587ab5e9e). Also passing: test_week_close.py, test_week_close_gate_verdicts_and_void.py, #703's test_session_settings_freshness.py and test_session_resolve_and_hook.py (126 in all). No full tests/tools run.

## Files Changed
- tools/agent-monitoring/week_close.py (`find_main_checkout`, `_identity`, `sweep_main_checkout_tools`, `close_week` call, CLI line), ported unchanged
- tests/tools/test_week_close_main_checkout_sweep.py (ported)
- docs/agent-monitoring/README.md (one bullet under "Closing a finished week", pointing at #703's section)
- agent-working/stored_artifacts/TCK-20261021-WEEK-CLOSE-SWEEPS-MAIN-CHECKOUT-TOOL-ROWS/ (investigation.md, measure.py, unknown_durations.py, sessions.csv)

## Completion Summary
A week close run from a worktree now appends the closed week's main-checkout `main.tools.jsonl` rows the canonical `tools.jsonl` lacks: read-only on the main checkout, full-row dedup, idempotent, never raises. W43 goes from 8 of 12 closing sessions with rows to 11 of 12 when it closes (simulated from the restored file). #703's SessionStart lines and the closed ticket were not touched. The evidence folder states where host ubuntu's measurement agrees with and differs from #703's u24 split.
