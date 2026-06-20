---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12B-BLOCKER-RECAL
phase: open
date: 2026-06-20
tags: [balance, tuning, scoring, blocker-penalty, parity, phase-1]
---

# TCK-20260619-E12B-BLOCKER-RECAL

## Title
Epic 1.2B · blocker_penalty Recalibration

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`blocker_penalty = 2.0` is a fixed constant that acts as a near-binary filter on route selection. E12A measurement data will reveal whether blockers are common and minor (flat 2.0 is too blunt) or rare and critical (2.0 is appropriate). This ticket uses that data to decide and implement the right penalty curve, then documents all scoring constants.

**Depends on:** TCK-20260619-E12A-BALANCE-MEASURE (must be DONE first)

## Scope
- Read E12A measurement: blocker frequency ratio, severity distribution
- Decision:
  - If blocker frequency < 5% of scored routes → keep 2.0, document with justification
  - If frequency ≥ 5% AND mostly minor severity → implement graduated penalty by severity
- If implementing graduated penalty:
  - `src/domains/adventure/scoring.py:L128–131`: replace fixed constant with severity-keyed lookup
  - Minor blocker → 0.5, Major → 1.5, Critical → 2.0 (cap total at 2.0)
  - Requires `Blocker.severity` field on route blockers — check schema and add if absent
- Document **all** scoring formula constants in `docs/mechanics/04_strategic_cognition.md` (with measured justification from E12A)
- Update `docs/parity_ledger/strategic_cognition.yaml` (STRAT-* entries for blocker_penalty)
- If constant changed: record in `docs/guidelines/v2_intentional_divergences.md` (class: `Intentional Gameplay Change`)
- Run `make knowledge-index-update` after docs/ changes

## Out of Scope
- Changing urgency weights (separate calibration problem)
- Regression test suite (that's E12C)

## Acceptance Criteria
- Decision documented (keep or change) with evidence from E12A data
- If changed: `blocker_penalty` is severity-graduated; minor-blocked high-urgency route can outscore unblocked mediocre route
- If unchanged: existing 2.0 documented with explicit justification in `docs/mechanics/04_strategic_cognition.md`
- All scoring formula constants documented in `docs/mechanics/04_strategic_cognition.md`
- Parity ledger updated (`status: verified`, `v2_evidence` cites E12A measurement)
- If changed: divergence recorded in `v2_intentional_divergences.md`

## Related Tickets
- TCK-20260619-E12A-BALANCE-MEASURE (prerequisite — must be DONE)
- TCK-20260619-E12-BALANCE-BASELINE (parent epic)
- TCK-20260619-E12C-BALANCE-TESTS (consumer — needs final constant values)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (scoring constants section — update)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-* blocker_penalty entries)
- `docs/guidelines/v2_intentional_divergences.md` (add if constant changes)
- `docs/audits/D04_balance_tuning.md` (reference for E12A data)

## Related Code Areas
- `src/domains/adventure/scoring.py:L128–134` (blocker penalty logic)
- Route blocker schema (check if `Blocker.severity` exists)

## Assumptions / Open Questions
- Does the `Blocker` model have a `severity` field? If not, adding it is in-scope for this ticket.
- What is the parity ledger entry ID for blocker_penalty in strategic_cognition.yaml? Look up before updating.

## Implementation Notes
If no code change is made (keep 2.0): this ticket still completes — documentation is the deliverable.
If code change is made: run adventure unit tests before committing:
```bash
pytest tests/unit/domains/adventure/ -x -v
```

## Test Summary
If `blocker_penalty` changes:
- `tests/unit/domains/adventure/test_scoring.py`:
  - `test_minor_blocked_route_not_universally_rejected`
  - `test_critical_blocked_route_still_rejected`

If no change: no new tests required.

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
