---
status: historical
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260501-E4-PHASE-ONE
phase: done
date: 2026-05-01
tags: [e4, phase, one]
---

# TCK-20260501-E4-PHASE-ONE

## Title
Phase E4.1 — Determinism and Replay Completion

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary
Implement Phase E4.1 — Determinism and Replay Completion to ensure every gameplay result is reproducible across execution modes.

## Scope
- Harden RNG with Domain Separation and stateless access.
- Prove local/concurrent canonical state hash equivalence.
- Ensure replay reproduces accepted and rejected transactions exactly.
- Expand `CanonicalStateHasher` to include all gameplay-visible state (e.g., camps).
- Add long-run determinism tests (1,000+ ticks).

## Acceptance Criteria
- [x] No bare `random.` or `numpy.random` usage in `src/engine` or `src/systems`.
- [x] `CanonicalStateHasher` includes `camps` and all other missing V2 states.
- [x] Determinism test suite passes for 1,000+ ticks with same seed.
- [x] Replay hash equality matches exactly across rejections.

## Related Tickets
- TCK-20260501-E4-PHASE-ZERO (Done)

## Files Changed
- `src/platform/rng.py`
- `src/engine/checkpoint.py`
- `src/replay/fingerprint.py`
- `src/engine/kernel.py`
- `tests/engine/test_determinism_suite.py`
- `tests/engine/test_long_run_determinism.py`

## Completion Summary
Phase E4.1 is complete. Every gameplay result is now reproducible across execution modes. RNG is hardened with Domain Separation, and canonical hashing covers the entire gameplay state. Replay fidelity is byte-identical even across rejection paths. Verified with 1,000+ tick determinism tests.
