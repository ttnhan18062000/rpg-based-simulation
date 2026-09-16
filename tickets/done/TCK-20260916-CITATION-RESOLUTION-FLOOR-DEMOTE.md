---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE
phase: done
date: 2026-09-16
tags: [agent-monitoring, data-quality, process-improvement]
---

# TCK-20260916-CITATION-RESOLUTION-FLOOR-DEMOTE

## Title
`CITATION_RESOLUTION_FLOOR` broke `main`'s CI by closing one ordinary ticket — stop gating on it, keep the number

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`tools/gate_checks/premise_staleness_check.py`'s `CITATION_RESOLUTION_FLOOR` is a blocking ratchet
on the *percentage* of open-ticket `Related Code Areas` citations that resolve to real files. It
drifts on ordinary activity, and on 2026-09-16 it **broke `main`**.

**What happened, traced end to end:** PR #210 closed
`TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE`, moving it `tickets/todos/` →
`tickets/done/`. That shrank the open-ticket population 83 → 82, which moved the citation-resolution
rate 96.1% → 96.0% — below the floor, still pinned at 96.1 at that commit. `API / tools / logging`
failed on `main` at `0ab68f345` as a result. **No citation text changed. No broken reference was
introduced. A ticket was closed, which is the most routine legitimate act in this repo.**

The floor was then re-pinned 96.1 → 95.8 in PR #208, with the cause honestly traced in a code
comment — and, as with the attribution floor before it, **the guard test was edited to match**
(`assert CITATION_RESOLUTION_FLOOR == 95.8`).

**This is the same disease as the deleted attribution gate**
(`TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE`): a ratchet whose denominator is
"currently open tickets" moves whenever work happens, so it fires on legitimate activity rather than
on regression — an *inverted* signal. It will require re-pinning on every future closure.

**The governing principle (user, 2026-09-16):** *"we don't need to make the test too strictly for
agent working, since it's just the side effect, not the core simulation feature."* Ticket metadata
accuracy is agent-working telemetry, not simulation behaviour.

## Scope
- **Remove the blocking path**: `CITATION_RESOLUTION_FLOOR`, the real-corpus floor assertion, and
  the guard test that pins the constant. A constant nothing gates on is dead weight.
- **Keep the measurement.** `compute_open_ticket_citation_resolution_rate()` is genuinely useful and
  should keep reporting — surface it where the retro or the advisory sweep can show it. Losing the
  gate is the goal; losing the number is not.
- **Keep `find_potentially_stale_open_tickets()` entirely** — the advisory close-time sweep is the
  actual product of `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE` and is not
  affected by this. It already returns candidates rather than failing, which is the right shape.
- Record in the module why the floor was removed, so it is not rebuilt as a threshold later.

## Out of Scope
- The registry extractor fix and open-ticket indexing from
  `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE`. Those are correct and stay.
- Re-deriving citation accuracy as a one-off number; it was 96.0-96.1% across 328 citations, and
  the quality of the data is not in question — only the gating.
- The other ratchets with this shape — those are `TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-
  WITH-LIVE-REGRESSION`'s widened scope. Do not fix them here; do not duplicate them here.

## Acceptance Criteria
- [ ] Closing a ticket cannot fail CI via this check. Verify by simulating a population change
      (move a fixture ticket in a temp tree), not by reasoning about it.
- [ ] The citation-resolution rate is still computed and still reported somewhere a human reads.
- [ ] The advisory sweep is unchanged and still tested.
- [ ] A comment records why the floor is gone and that re-adding a threshold over this metric would
      reproduce the defect.

## Related Tickets
- `TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-UNMEETABLE` (done) — the same disease, deleted;
  read its Decision section for the full precedent and evidence standard
- `TCK-20260915-RATCHET-CONFLATES-HISTORICAL-DEBT-WITH-LIVE-REGRESSION` — the widened
  five-check version of this problem
- `TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE` (done) — introduced this module

## Related Docs
- `docs/plans/agent_infrastructure/reachability_verification_findings.md`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260913-TICKET-PREMISE-STALENESS-NOT-PROPAGATED-ON-CLOSE/`

## Related Code Areas
- `tools/gate_checks/premise_staleness_check.py` (`CITATION_RESOLUTION_FLOOR`,
  `check_related_code_areas_health`)
- `tests/tools/test_premise_staleness_check.py`

## Assumptions / Open Questions
- Whether the rate belongs in the retro report or only in the advisory sweep's own output is the
  implementer's call. Either satisfies "keep the number".
- A narrower detector is conceivable later — e.g. citations that *were* resolving and stopped, which
  would be a real staleness signal rather than a population artifact. Out of scope here; file it
  separately if wanted, with a measured baseline.

## Implementation Notes
The precedent to follow is the attribution-gate deletion: remove the gate, keep the measurement,
document why, and do not lower a threshold as an alternative.

## Test Summary
- `pytest tests/tools/test_premise_staleness_check.py -v` (`.venv313`): 23 passed, including a new
  `test_closing_a_ticket_moves_the_rate_but_cannot_fail_ci` that simulates the exact real-world
  event that broke `main` (a ticket leaving the open population) via a synthetic before/after
  population and confirms the CLI always exits 0 regardless.
- `python3 tools/gate_checks/premise_staleness_check.py` run standalone: reports the rate as an
  informational PASS marker.
- Verified before editing: `grep -rln "CITATION_RESOLUTION_FLOOR\|check_related_code_areas_health"`
  found no consumer outside this module and its own test.
- Full `pytest tests/tools/ -m "not slow and not extra_slow"`: 2735 passed, 0 failed (run together
  with this batch's other three tickets' changes).

## Files Changed
- `tools/gate_checks/premise_staleness_check.py` — removed `CITATION_RESOLUTION_FLOOR` and
  `check_related_code_areas_health()` (the blocking floor path); kept
  `compute_open_ticket_citation_resolution_rate()` unchanged; `find_potentially_stale_open_tickets()`
  untouched, as scoped; rewrote the module docstring to record why this must not be rebuilt as a
  threshold; `main()` now reports the rate as an always-PASS marker.
- `tests/tools/test_premise_staleness_check.py` — removed the four tests tied to the deleted
  floor/guard; added a population-change test proving the check can no longer fail CI.
- `Makefile` — reworded the `premise-staleness-check` target's help text to "Report ...
  non-blocking".

## Completion Summary
Removed the same class of gate the sidecar-attribution floor's deletion established precedent for:
a threshold over "currently open tickets" moves on ordinary ticket closures, not on citation
quality regressions — closing one ticket (`TCK-20260915-SIDECAR-ATTRIBUTION-RATCHET-FLOOR-
UNMEETABLE`) broke `main`'s CI on 2026-09-16 for exactly this reason. The measurement survives
unchanged for anyone who wants the number; only the gate is gone.
