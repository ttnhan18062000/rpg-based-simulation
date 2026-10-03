---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E11D-SCORING-CAL
phase: done
date: 2026-06-19
tags: [entity-differentiation, scoring, calibration, personality, behavioral-quality, phase-1]
---

# TCK-20260619-E11D-SCORING-CAL

## Title
E11-D · Calibrate personality bias weights in adventure scoring

## Status
DONE

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
No coefficient changes were required. The existing formula already produces 4.92× ratio at SEED=42, TICKS=400 — well above the ≥2× acceptance criterion.

- Bravery coefficient: `0.6`; caution coefficient: `0.8`
- Formula: `risk_multiplier = max(0.1, (1.0 + caution * 0.8) - bravery * 0.6)`
- Measured ratio: 4.92× at SEED=42, TICKS=400 (bot_rate=0.1150, top_rate=0.5663)
- No formula changes made; deliverables are test marker removal, parity ledger entry, and contract doc update

Two pre-existing defects in the E11C harness were corrected as part of promotion to strict-pass:

1. **Tick-padding sleep**: `_test_profile()` sets `max_tick_budget_ms=200.0`; the kernel was sleeping 200ms per tick, making 400 ticks × 200ms = 80s minimum — exceeding the 60s conftest `medium` budget. Fixed by adding `"no_frame_pacing": True` to the kernel flags (supported flag, gated at `kernel.py:329`).

2. **QueueDrainWorker thread leak**: The kernel was never shut down after the tick loop, causing a background drain-worker thread to persist past the test session. Fixed by wrapping the tick loop in `try/finally: kernel.shutdown()`, matching the pattern used by all other Kernel-creating tests.

## Test Summary
- E11C harness `test_bravery_quartile_combat_rate_2x()` — must pass strictly after calibration
- Existing adventure scoring tests must continue to pass (no regressions)

## Files Changed
- `tests/integration/scenarios/test_entity_differentiation.py` — removed `@pytest.mark.xfail(strict=False, ...)` decorator; updated docstring; added `"no_frame_pacing": True` kernel flag; added `try/finally: kernel.shutdown()`
- `docs/parity_ledger/strategic_cognition.yaml` — appended STRAT-226 entry (status: verified)
- `docs/simulation/domains/adventure_contract.md` — added Calibration Note subsection after Scoring formula tables

## Completion Summary
E11D delivered without any scoring formula changes. The existing bravery coefficient (0.6) and caution coefficient (0.8) already produce 4.92× differentiation — confirmed by strict-pass integration test. Two E11C harness defects (tick-padding sleep, missing kernel.shutdown) were corrected as part of xfail promotion. STRAT-226 parity ledger entry added. adventure_contract.md calibration note added. All 26 adventure unit tests and both integration tests pass.
