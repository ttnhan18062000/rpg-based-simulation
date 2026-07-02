---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E12B-BLOCKER-RECAL
phase: done
date: 2026-06-20
tags: [balance, tuning, scoring, blocker-penalty, parity, phase-1]
---

# TCK-20260619-E12B-BLOCKER-RECAL

## Title
Epic 1.2B · blocker_penalty Recalibration

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`blocker_penalty = 2.0` is a fixed constant that acts as a near-binary filter on route selection. E12A data reveals blocker_frequency = 0.0 (< 5% threshold), so the constant is kept unchanged. This ticket documents all scoring formula constants.

## Scope
- Read E12A measurement: blocker frequency = 0.0 → Decision: KEEP 2.0 with justification
- Document all scoring formula constants in `docs/mechanics/04_strategic_cognition.md` (§6 added)
- Add parity ledger entry STRAT-227 in `docs/parity_ledger/strategic_cognition.yaml`
- No code change required; no divergence record needed (constant unchanged)

## Out of Scope
- Changing urgency weights
- Regression test suite (that's E12C)

## Acceptance Criteria
- [x] Decision documented: KEEP 2.0 (blocker_frequency < 5% from E12A)
- [x] All scoring formula constants documented in `docs/mechanics/04_strategic_cognition.md` §6
- [x] Parity ledger updated: STRAT-227 added with `status: verified`, v2_evidence citing scoring.py constants + E12A audit
- [x] No divergence record needed (no constant changed)

## Related Tickets
- TCK-20260619-E12A-BALANCE-MEASURE (prerequisite — DONE)
- TCK-20260619-E12-BALANCE-BASELINE (parent epic)
- TCK-20260619-E12C-BALANCE-TESTS (consumer — needs final constant values)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (§6 added — scoring constants)
- `docs/parity_ledger/strategic_cognition.yaml` (STRAT-227 added)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E12B-BLOCKER-RECAL/` (plan, investigation, test_plan)

## Related Code Areas
- `src/domains/adventure/scoring.py:L103–137` (all constants referenced in STRAT-227)

## Assumptions / Open Questions
- STRAT-193 says "Blockers have severity" (verified against BlockerState in strategic.py). The adventure route scorer uses AdventureRouteOption.blockers as Tuple[str, ...] (string-only, no severity field). These are separate blocker representations in different layers — no contradiction.

## Implementation Notes
Decision path: E12A → blocker_frequency = 0.0 → frequency < 5% threshold → keep 2.0 → document only. No code changed.

## Test Summary
No new tests (no code changed). Existing `tests/unit/domains/adventure/test_phase3_route_scoring.py` covers the scorer.

## Files Changed
- `docs/mechanics/04_strategic_cognition.md` — §6 added (scoring constants, risk multiplier, personality bias table, blocker_penalty justification, score range summary)
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 appended

## Completion Summary
E12B complete: documentation-only ticket. blocker_penalty = 2.0 kept unchanged. All scoring formula constants (risk multiplier coefficients 0.8/0.6/floor 0.1; personality_bias weight 0.25; confidence_bonus weight 0.15; risk weight 0.5; blocker_penalty 2.0) now documented in Chapter 4 §6 of the Mechanics Bible with measured justification from E12A. STRAT-227 parity entry added.
