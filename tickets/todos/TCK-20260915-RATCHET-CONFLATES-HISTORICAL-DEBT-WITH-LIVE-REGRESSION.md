---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION
phase: open
date: 2026-09-15
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION

## Title
`monitoring_integrity_backlog_check`'s item-2 ratchet counts frozen historical debt and brand-new regressions in one number, so a failure cannot be read without an investigation — and the obvious fix for it is the wrong one

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
Found 2026-09-15, immediately after `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` landed its ratchet,
when the user asked a reasonable question about the constant: *"is that we need to update every
ticket landed?"*

The check failed with:

```
FAIL: working_log DONE rows with no run record (item 2): 219 exceeds the ratchet ceiling (218) by 1
```

**That failure is correct and valuable** — three of the monitoring-anomaly epic's own tickets
(`MONITORING-INTEGRITY-BACKLOG`, `MONITORING-ANOMALY-VALIDATOR`,
`RETRO-CLI-OVERWRITES-HAND-AUTHORED-NOTES`) closed with zero run records *and* zero event rows,
i.e. `record_hand_orchestrated_closure.py` was never run for them despite CLAUDE.md's After Work
rule requiring it. The ratchet caught a real, current process miss on its first outing.

**The problem is that the number cannot be read.** Item 2's count is
`historical_debt + live_regressions` in a single integer:

- ~216 rows are pre-existing, unreconstructable debt nobody is going to backfill (it spans
  2026-03 → 2026-09; 462 further rows predate the check's own `MONITORING_START` cutoff entirely).
- 3 rows are a live process miss from today, fixable in minutes.

A reader seeing `219 exceeds 218 by 1` cannot tell which they are looking at. Establishing it took
four separate corpus queries. **The failure mode that follows is predictable**: the cheapest
resolution looks like raising the ceiling to 219, which is exactly what the constant's own comment
forbids ("Raising any of them to paper over a newly-introduced instance defeats the point of this
check") — and it would silence the mechanism on the first real thing it ever caught. A gate whose
correct response requires an investigation, and whose incorrect response is a one-character edit,
will eventually be resolved the wrong way by someone in a hurry.

This is a variant of the pattern this whole arc has been cataloguing, one step removed: not a
mechanism that fails to measure, but a mechanism that measures correctly and reports
uninterpretably.

## Scope
- Split item 2 into two conditions with different semantics:
  - **Frozen historical debt** — rows on/after `MONITORING_START` but before a new freeze date
    (the date this ticket lands). Ratcheted, may only decrease, expected to sit still forever.
  - **Live coverage** — rows after the freeze date. This should be **zero-tolerance**: any DONE
    working_log row written after the freeze with no run record is a process miss that is always
    fixable by running `record_hand_orchestrated_closure.py`, so a non-zero count is always
    actionable and never historical.
- Make each condition's evidence string say which kind it is, and — for the live condition — name
  the offending ticket ids directly, so the fix is obvious from the failure text without any
  investigation.
- Consider whether the same split applies to the other three conditions (unusable `ts`, unknown-week
  rows). Evidence so far says they are purely historical (all W24–W27 / June-era), so they may
  legitimately stay single-valued — confirm rather than assume.

## Out of Scope
- Backfilling the ~216 historical rows. They are unreconstructable; that was settled by
  `TCK-20260915-MONITORING-INTEGRITY-BACKLOG`.
- Fixing the three uncovered epic closures — that is immediate remediation happening now, not this
  ticket's work. This ticket assumes they are already recorded and the count is back at ~216.
- ~~The other ratchets introduced by the anomaly epic (duplicate runs, seq integrity, tool-call
  mismatch, vocabulary drift). If any shares this conflation shape, note it here rather than
  widening scope.~~ **Superseded 2026-09-16 — see "Scope widened" below. Two of them demonstrably
  share the shape, so treating them as out of scope would fix one instance of a five-instance
  pattern.**

## Scope widened — 2026-09-16 (user decision)

The original Out-of-Scope line above assumed the other ratchets probably did not share this
conflation. **One day of real operation disproved that.** Five checks now demonstrably move on
*legitimate activity* rather than on regression:

| Check | What moved it | Cost |
|---|---|---|
| `no-run-record` (item 2) | historical debt + live misses in one integer | the original finding |
| `working_log_duplicate` (84→85) | a legitimate `BLOCKED`→`DONE` reopen | re-pin |
| `event_seq_integrity` (71→72) | the same reopen | re-pin |
| `ATTRIBUTION_RATE_FLOOR` | hand-orchestrated work (a sanctioned mode) | **gate deleted** |
| `CITATION_RESOLUTION_FLOOR` | closing one ordinary ticket (pop. 83→82) | **broke `main`'s CI** |

The generalisation, in the user's words (2026-09-16): *"we don't need to make the test too strictly
for agent working, since it's just the side effect, not the core simulation feature."* And the
sharper diagnostic framing, from `rpg-feature-planning`: **a check that fails on legitimate activity
is not a weak signal, it is an inverted one — it fires *because* work is happening.**

**What this adds to this ticket's scope:**

- Treat `working_log_duplicate` and `event_seq_integrity` as in scope. A legitimate two-phase
  closure must not consume ratchet headroom in any of them; today it consumed headroom in two.
- Apply the same test to every remaining ratchet in `tools/gate_checks/`: **does its value move
  when nothing is wrong?** If yes, it is inverted and the disposition is to stop gating, not to
  tune the threshold.
- Prefer **removing the gate and keeping the reported number** over splitting the metric, where the
  measurement is genuinely useful. That is what the attribution floor's deletion established as
  precedent, and it is cheaper and more honest than a two-condition split that still needs pinning.
- The split-the-metric design in this ticket's original Scope remains valid *only* where a check
  genuinely mixes frozen historical debt with live regressions (`no-run-record` is the clear case).
  Do not apply it mechanically to the inverted ones.

**Two checks that are NOT in scope and should stay ratcheted**, so this does not become a general
deratcheting exercise: `tool_call_count_mismatch` and `vocabulary_drift` both count corpus debt that
grows only through a real mistake, and neither moved on any legitimate activity during this period.
Ratchets remain the right tool for that shape.

`TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE` handles the citation floor separately and is already
scoped; do not duplicate it here.

## Acceptance Criteria
- [ ] Item 2 reports at least two distinct conditions: frozen historical debt (ratcheted) and
      post-freeze live coverage (zero-tolerance).
- [ ] The live condition's failure evidence names the specific offending `ticket_id`s.
- [ ] A test proves the live condition fails on a planted post-freeze uncovered closure, and that
      the historical condition is unaffected by it.
- [ ] A test proves a pre-freeze row does **not** trip the live condition.
- [ ] The historical ceiling is re-derived at implementation time and set to the then-current
      measured value, not carried over from 218 — by then the three epic closures should be
      recorded, so the honest number is expected to be lower.

## Related Tickets
- `TCK-20260915-MONITORING-INTEGRITY-BACKLOG` (done) — introduced the ratchet this refines
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the parent epic
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done) — the original
  coverage gap; this ticket's live condition is what would have caught its recurrence immediately
- `TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT` (open) — sibling case of a
  gate whose arithmetic makes the wrong response cheaper than the right one

## Related Docs
- `agent-monitoring/retro/RETRO-LAST14D.md`
- `docs/agent-monitoring/schema.md`
- `CLAUDE.md` — After Work, the `record_hand_orchestrated_closure.py` requirement

## Related Stored Artifacts
- `stored_artifacts/TCK-20260915-MONITORING-INTEGRITY-BACKLOG/`

## Related Code Areas
- `tools/gate_checks/monitoring_integrity_backlog_check.py`
  (`NO_RUN_RECORD_CEILING`, `MONITORING_START`, `find_working_log_rows_missing_run_record`)
- `tests/tools/test_monitoring_integrity_backlog_check.py`
  (`test_real_corpus_is_at_or_below_all_four_ratchet_ceilings` — the CI-gating pin)

## Assumptions / Open Questions
- The freeze date should probably be this ticket's own landing date, but an argument exists for
  `TCK-20260903`'s date (when hand-orchestrated coverage was first required) — that would classify
  more rows as "live" and might surface real, still-fixable misses. Worth measuring before choosing.
- Whether the live condition should be zero-tolerance or a small ratchet depends on whether every
  post-freeze miss is genuinely always fixable. The three found today were; that is a sample of
  three.

## Implementation Notes
Reproduce the motivating failure by running the check against the corpus before the three epic
closures are recorded. After they are recorded, item 2 should read ~216 and pass.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
