---
ticket_id: TCK-20260619-E12B-BLOCKER-RECAL
phase: plan
date: 2026-06-20
---

# Plan: blocker_penalty Recalibration

## Decision Gate (from E12A)

- E12A blocker_frequency = 0.0 (< 5% threshold)
- Decision: KEEP blocker_penalty = 2.0 unchanged
- No code change required

## Implementation Steps

1. Add §6 to `docs/mechanics/04_strategic_cognition.md` with all scoring formula constants
2. Add STRAT-227 to `docs/parity_ledger/strategic_cognition.yaml`

## Files Changed

- `docs/mechanics/04_strategic_cognition.md` — §6 new section
- `docs/parity_ledger/strategic_cognition.yaml` — STRAT-227 appended
