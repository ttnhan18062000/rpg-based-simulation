---
ticket_id: TCK-20260619-E62C-MOTIVATION-OVERLAY
phase: plan
date: 2026-06-23
---

# Plan — TCK-20260619-E62C-MOTIVATION-OVERLAY

## Files Created / Modified

| File | Action |
|---|---|
| `src/domains/culture/applicator.py` | New — CulturalBiasApplicator |
| `src/domains/motivation/service.py` | Modified — optional culture_values param |
| `docs/world/culture_drift_contract.md` | New — full system contract |
| `tests/unit/culture/test_culture_applicator.py` | New — 11 tests |
| `tests/unit/motivation/__init__.py` | New |
| `tests/unit/motivation/test_motivation_bias_culture.py` | New — 4 tests |

## Deferred Wiring Note

`compute_bias_multiplier` has no live call site in the adventure/tick loop yet.
The service extension is backward-compatible; actual call-site wiring requires
a future ticket when AdventureRouteScorer or similar integrates the service.
