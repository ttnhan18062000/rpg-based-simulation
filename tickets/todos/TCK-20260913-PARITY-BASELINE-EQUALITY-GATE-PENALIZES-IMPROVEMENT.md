---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT
phase: open
date: 2026-09-13
tags: [testing, registry]
---

# TCK-20260913-PARITY-BASELINE-EQUALITY-GATE-PENALIZES-IMPROVEMENT

## Title
`test_parity_index_baseline.py`'s exact-equality drift assertion has needed 4 hotfixes in 2 weeks — every legitimate ledger correction costs a ticket, leaving the ledger alone costs nothing

## Status
OPEN

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
`tests/tools/test_parity_index_baseline.py::test_baseline_manifest_does_not_coerce_missing_test_path`
hardcodes an exact-equality assertion (`assert live_missing == N`) against the count of parity
ledger entries with `status in ("verified", "divergent")` and a missing `test_path`. Every time a
real fix moves an entry out of that count — by adding a real citation, or by correcting a false
`verified` claim to `missing`/`divergent` with honest evidence — the hardcoded `N` goes stale and
CI goes red, requiring a dedicated hotfix ticket just to update the number.

**This has now happened four times in two weeks**, each one legitimate and each one following the
documented process correctly:

- `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`
- `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`
- `TCK-20260905-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`
- `TCK-20260913-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (today, this batch — `PROG-014`
  moving from a false `verified` to an honest `missing`)

**The incentive runs backwards.** Correcting a bad parity entry costs whoever does it a full hotfix
ticket cycle; leaving a known-bad entry alone costs nothing and never trips CI. Four instances in
two weeks is not hypothetical friction — it is a real, recurring tax specifically on the behavior
this whole audit arc has been trying to encourage.

**This matters imminently, not eventually.** `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`
(agent-process track) measured **1307 P0/`verified` entries with no `test_path` at all** — about
60% of the ledger. If any meaningful slice of that sweep lands, this test breaks catastrophically
and repeatedly: whoever runs that sweep faces a choice between a stream of baseline hotfixes
mid-sweep, or not doing the correction work at all.

## Scope
This ticket is scoped as **the question, not a chosen fix** — read the four precedent tickets
before proposing a shape, since the second assertion's own stated rationale (per
`TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT`) is "a second-order guard
against silent large swings" — not an arbitrary choice, and there may be a reason exact equality
was picked over a one-directional check that isn't fully spelled out in the comments.

**One candidate worth naming, not committing to**: a ratchet asserting the count never
*increases* — `assert live_missing <= N` — would still catch the actual regression this test
exists to prevent (a new or re-marked entry silently claiming `verified`/`divergent` status with no
real evidence), while letting every legitimate downward correction through without requiring a
hotfix. The tradeoff to weigh honestly: a pure ratchet would **not** catch a large, unexplained
*decrease* — e.g., something silently reclassifying many entries away from `verified` without real
justification, which the current exact-equality check would catch and a one-directional ratchet
would not. Whether that failure mode is worth guarding against, and how it could happen in
practice given `write_entry()`'s own validation, is real investigation work, not assumed here.

Other candidates worth considering during investigation, not pre-selected:
- A tolerance band instead of exact equality (allow small drift without update, still catch large
  swings in either direction).
- Move the "large swing" guard to compare against the *previous* recorded value with a percentage
  threshold, rather than a single hardcoded absolute number that must be hand-updated per fix.
- Keep exact equality but make the update itself cheaper/lower-ceremony (e.g., a script that
  regenerates the constant and its comment automatically) rather than changing the assertion's own
  semantics — addresses the *cost* of updating without changing what's being asserted.

## Out of Scope
- Actually changing the assertion — this ticket investigates and recommends; it does not implement.
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS`'s own corpus-wide policy question (what to do
  with the 1307 uncited entries) — independent of how this test's own gate is shaped, though this
  ticket's own urgency is driven by that sweep's proximity.
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP`'s own narrower dangling-reference scope
  — unrelated to this test's assertion shape.
- Standing alone, not bundled into any other ticket's batch, per explicit instruction.

## Acceptance Criteria
- [ ] All four precedent tickets read in full before proposing a shape, with the "second-order
      guard against silent large swings" rationale directly addressed (confirmed, refined, or
      shown not to hold) rather than assumed obsolete.
- [ ] At least the ratchet candidate and one alternative evaluated on the same axis: does it still
      catch the regression this test exists to prevent, and does it stop penalizing legitimate
      corrections?
- [ ] A recommendation brought to peer/user review before any implementation.
- [ ] No implementation without that review.

## Related Tickets
- `TCK-20260830-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent 1)
- `TCK-20260902-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent 2 — states the
  "second-order guard against silent large swings" rationale)
- `TCK-20260905-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent 3)
- `TCK-20260913-HOTFIX-PARITY-INDEX-MISSING-TEST-PATH-BASELINE-DRIFT` (precedent 4, this batch)
- `TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS` (agent-process track, `parity-writer-invalid-
  corpus`) — the imminent-urgency driver: if a meaningful slice of its 1307-entry corpus-wide
  correction lands, this test breaks repeatedly under its current shape.
- `TCK-20260913-PARITY-LEDGER-VERIFIED-NULL-EVIDENCE-SWEEP` (this batch's own narrower ticket —
  unrelated scope, named only because it shares the same test file as a downstream consumer)

## Related Docs
None yet.

## Related Stored Artifacts
None yet — standard tier, staging artifacts created when picked up.

## Related Code Areas
- `tests/tools/test_parity_index_baseline.py`
  (`test_baseline_manifest_does_not_coerce_missing_test_path`)

## Assumptions / Open Questions
- Whether the exact-equality shape was a deliberate choice with a real, undocumented reason, or
  simply the first thing that worked when the test was written, is the central open question this
  ticket exists to answer — not assumed either way here.

## Implementation Notes
_(pending — filed, not yet picked up)_

## Test Summary
_(pending)_

## Files Changed
_(pending)_

## Completion Summary
_(pending)_
