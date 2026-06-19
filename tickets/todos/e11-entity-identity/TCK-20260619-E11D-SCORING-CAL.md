---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E11D-SCORING-CAL
phase: open
date: 2026-06-19
tags: [entity-differentiation, scoring, calibration, personality, behavioral-quality, phase-1]
---

# TCK-20260619-E11D-SCORING-CAL

## Title
E11-D · Calibrate personality bias weights in adventure scoring

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/domains/adventure/scoring.py` already applies bravery as a risk_multiplier (`max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)`), but the calibration is untested and may not produce the required 2× differential between bravery quartiles. After this ticket, the scoring parameters are tuned so the differentiation harness (E11C) passes strictly.

## Scope
- Read `src/domains/adventure/scoring.py` in full before any changes
- Measure current bravery effect: run E11C harness with current weights; record baseline combat_engage rate ratio
- Adjust the bravery risk multiplier coefficient (currently `0.6`) and/or the personality_bias addend for combat-type routes to achieve ≥2× ratio
- The adjustment must stay within constraints from `docs/mechanics/04_strategic_cognition.md` and the Mechanics Bible
- Update parity ledger entries in `docs/parity_ledger/strategic_cognition.yaml` for personality-scoring entries
- Document the chosen weights and rationale in the implementation notes

## Out of Scope
- Changing other personality trait effects (greed, sociability, industry) beyond what's necessary
- Calibrating non-adventure route scoring

## Acceptance Criteria
- Running E11C harness: `test_bravery_quartile_combat_rate_2x()` passes strictly (no xfail)
- Bravery coefficient documented in Implementation Notes of this ticket
- Parity ledger personality-scoring entries updated to `verified`

## Related Tickets
- TCK-20260619-E11-ENTITY-IDENTITY (parent epic)
- TCK-20260619-E11C-DIFF-HARNESS (prerequisite — needs harness to measure)

## Related Docs
- `docs/mechanics/04_strategic_cognition.md` (interruption resistance and scoring constraints)
- `docs/parity_ledger/strategic_cognition.yaml` (personality scoring entries)

## Related Code Areas
- `src/domains/adventure/scoring.py`
- `tests/integration/scenarios/test_entity_differentiation.py` (E11C harness)

## Assumptions / Open Questions
- What combat-type routes exist? Find route kinds in scoring.py that correspond to combat_engage.
- What's the current ratio baseline with default weights?

## Implementation Notes
_To be filled on completion._

## Test Summary
- E11C harness `test_bravery_quartile_combat_rate_2x()` — must pass strictly after calibration
- Existing adventure scoring tests must continue to pass (no regressions)

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
