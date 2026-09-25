---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET
phase: open
date: 2026-09-25
tags: [workflows, agent-monitoring, process-improvement]
---

# TCK-20260925-WORKING-LOG-PER-TICKET-WRITE-TARGET

## Title

`working_log.csv` still has no squash-merge protection — the per-ticket write-target fix stopped at
the JSONL shards

## Status

OPEN

## Tier

standard

## Type

bug

## Priority

P2

## Request Summary

`TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` gave the three
`agent-monitoring/data/*/*.jsonl` files per-ticket write targets, closing the gap where
`.gitattributes`' `merge=union` never engages under a GitHub squash-merge (this repo's near-universal
merge mode). **It deliberately did not do the same for `tickets/working_log.csv`, and closed with its
own AC3 stated as unsatisfied.** This ticket is that unfinished half, filed so the gap is tracked
rather than living only as a paragraph in a closed ticket's Completion Summary.

The reason it was descoped is sound and must be respected here rather than re-discovered:
`done_checker_static.py::check_working_log_exactly_one_row()` reads `working_log.csv`
**synchronously at every ticket's own close**. The JSONL files have no such dependency — CLAUDE.md's
Definition of Done says their coverage is "guaranteed by workflow — not verified by done-checker."
So the consolidation-at-retro-cadence design that works for the shards would, applied unchanged to
`working_log.csv`, break `working_log_exactly_one_row` for every ticket closed via the new path until
the next retro run. That check also carries deliberately nuanced reopen-vs-duplicate logic, so it
cannot simply be pointed at a different file and left alone.

This is not hypothetical exposure: `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` records a
real ~1586-row duplication from exactly this failure mode. Its detection-only mitigation is currently
the standing protection and remains so until this ticket lands.

## Scope

- Give `tickets/working_log.csv` squash-merge-safe write semantics, **without** breaking
  `working_log_exactly_one_row`'s synchronous read at ticket close. The two candidate shapes (see
  Open Questions) are: teach that check to read the per-ticket files directly, or keep a synchronous
  write while removing the shared-line collision.
- Extend the real-git-repo fixture from the shard ticket — the one that reproduces the sequential
  squash-merge shape — to cover `working_log.csv`, satisfying that ticket's AC3.
- Confirm `record_hand_orchestrated_closure.py`'s internal `append_working_log_row()` call and the
  standalone helper both route through whatever write path this ticket establishes. Two independent
  hand-rolled writers already produced an identical CRLF defect once
  (`TCK-20260912-WORKING-LOG-APPEND-HELPER`); a third path would repeat it.

## Out of Scope

- **Re-opening the shard ticket's JSONL design.** Per-ticket files plus
  `monitoring_consolidation.py` are settled and working; this ticket extends the idea, it does not
  revisit it.
- **Weakening or deleting `working_log_exactly_one_row`.** The check is the reason this is hard; it
  is not the obstacle to route around. Making it pass by making it check less is explicitly
  forbidden — Gate Integrity applies.
- **A manifest of per-ticket files.** The shard ticket rejected this deliberately: a manifest is
  itself new, small, non-append-only state with its own merge-conflict exposure — the exact class of
  problem being removed, reintroduced smaller. Do not reintroduce it here.
- **Changing `working_log.csv`'s columns, ordering, or its consumers' contract.**
- **Retroactively repairing the historical duplication** from `TCK-20260906`.

## Acceptance Criteria

1. Two tickets closing on two different branches, each squash-merged against `main` in sequence,
   never conflict or duplicate on `working_log.csv` — proven by the same real-git-repo fixture class
   the shard ticket used, not asserted by inspection. (This is that ticket's AC3.)
2. `working_log_exactly_one_row` passes identically for a ticket closed via the new write path,
   **at that ticket's own close**, with no dependency on a later consolidation run having happened.
3. Its reopen-vs-duplicate distinction still behaves identically — proven by a test over both cases,
   not by the check merely returning PASS.
4. After consolidation, `working_log.csv` is byte-identical in content and row order to what the old
   direct-append path would have produced for the same sequence of closes.
5. Consolidation is idempotent — running it twice produces no duplicate rows.
6. `record_hand_orchestrated_closure.py` and `append_working_log_row()` agree on the write path, with
   the existing double-write refusal (`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`)
   still firing.
7. Scoped tests pass; command and result recorded in `## Test Summary`.

## Related Tickets

- `TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE` — descoped this; its AC3 is AC1
  here.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` — the real ~1586-row duplication; its
  detection-only mitigation is the current protection.
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` — why a third independent writer must not appear.
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` — the double-write refusal.
- `TCK-20260924-DONE-CHECKER-DATA-RUNS-CLEAN-NO-START-TS` — separate, also in `done_checker_static.py`;
  independent, but a reason to check for edit collisions if both are in flight.

## Related Docs

- `CLAUDE.md` — "After Work"; Definition of Done.
- `docs/ai/ticket-lifecycle.md` — Verify / Step 0a.

## Related Stored Artifacts

- `stored_artifacts/TCK-20260924-MONITORING-SHARD-SQUASH-MERGE-CONFLICT-AVOIDANCE/` — its
  investigation records why this was split out.

## Related Code Areas

- `tools/working_log_writer.py` — `append_working_log_row()`
- `tools/agent-monitoring/record_hand_orchestrated_closure.py`
- `tools/agent-monitoring/monitoring_consolidation.py`
- `tools/gate_checks/done_checker_static.py` — `check_working_log_exactly_one_row()`
- `.gitattributes`, `tickets/working_log.csv`

## Assumptions / Open Questions

1. **The main design decision: which side moves.** Either (a) teach
   `check_working_log_exactly_one_row()` to read the per-ticket files in addition to the consolidated
   CSV, so a just-closed ticket's row is visible without consolidation having run; or (b) keep the
   synchronous write to `working_log.csv` but change *what* is written so two tickets cannot collide
   on the same diff hunk. (a) mirrors the shard ticket's shape and keeps one write path; (b) leaves
   the gate untouched but is harder to make genuinely conflict-free, since a squash-merge conflict is
   about adjacent lines, not semantics. **Recommendation: (a)**, but settle it in `plan.md` against
   the real check's logic, not on this sketch.
2. Whether the shard ticket's `monitoring_consolidation.py` should absorb `working_log.csv` or a
   separate consolidator is cleaner. Prefer absorbing it — one consolidation cadence, one thing to
   run — unless the CSV's ordering guarantees make that awkward.
3. Whether any other gate reads `working_log.csv` synchronously. `working_log_exactly_one_row` is the
   one confirmed; the investigation should sweep for others rather than assume it is alone. Note the
   shard ticket found a *third* undiscovered copy of the JSONL write-target formula in
   `tools/retrieval_events.py`, surfaced only by running the full regression suite and not named in
   its own Related Code Areas — run the suite here too rather than trusting the list above.

## Implementation Notes

_To be filled during implementation._

## Test Summary

_To be filled during implementation._

## Files Changed

_To be filled during implementation._

## Completion Summary

_To be filled during implementation._
