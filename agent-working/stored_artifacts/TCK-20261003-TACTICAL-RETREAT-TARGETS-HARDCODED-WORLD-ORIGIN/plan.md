---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261003-TACTICAL-RETREAT-TARGETS-HARDCODED-WORLD-ORIGIN
artifact_type: plan
tags: [combat, world, root-cause]
---

# Plan: region-contained retreat and wander destinations

1. New pure module `src/engine/tactical_destinations.py`: `containing_region` (strict bounds),
   `retreat_destination(state, entity, threats)` and `wander_destination(state, entity)`. No state mutation.
2. `src/engine/tactical.py`: module-top imports (ruff PLC0415), `_perceived_threats` and
   `_destination_or_hold` helpers, and the four call sites. The hold fallback is the entity's own position.
3. Retreat order per the ruling: away-vector clamped into the current region (accepted only if it moves the
   entity strictly farther from its nearest threat), else `strategic.home_region_id` region centre, else
   hold. `RETREAT_STEP = 10.0` is one perception radius; `WANDER_RADIUS = 5.0`.
4. Wander is a separate derivation: seeded by `DeterministicRNG(state.seed)` on `Domain.TACTICAL`, scoped by
   tick and entity id.
5. Tests, docs, divergence record (§2.66, `Bug Fix`), parity entry `COMB-327`.

Scope guards: no change to firing rates, thresholds, or the leash/home return branch. The ruling's rejected
options (settlement, friendly region, literal coordinate) are not used. The contested files are untouched.
