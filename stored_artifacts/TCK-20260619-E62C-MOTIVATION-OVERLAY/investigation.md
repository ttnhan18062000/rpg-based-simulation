---
ticket_id: TCK-20260619-E62C-MOTIVATION-OVERLAY
phase: investigation
date: 2026-06-23
---

# Investigation — TCK-20260619-E62C-MOTIVATION-OVERLAY

## Key Findings

- `MotivationBiasService.compute_bias_multiplier()` exists in `src/domains/motivation/service.py` but has NO call sites in `src/systems/` or `src/domains/adventure/` — the adventure scoring path (`AdventureRouteScorer`) computes personality_bias inline without calling the service
- Per the ticket assumption, the overlay is implemented at `MotivationBiasService` level (backward-compatible optional param); wiring into the tick loop is deferred to when a live call site exists
- `ValuePreferenceProfile` has: survival, reward, pride, curiosity (float 0.5 default)
- `IdentityDoctrine` has: preferred_route_tags, avoided_route_tags (Mapping[str, float])
- Existing tests in `tests/unit/domains/motivation/test_phase14_bias_service.py` provide reference fixture pattern
