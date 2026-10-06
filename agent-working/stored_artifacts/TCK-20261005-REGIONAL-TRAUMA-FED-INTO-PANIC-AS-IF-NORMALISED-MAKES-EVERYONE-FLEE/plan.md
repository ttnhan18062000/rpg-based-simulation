---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE
artifact_type: plan
tags: [strategy, cognition, combat]
---

# Plan

Ruling (rpg-feature-planning, 2026-10-06): world rule AGENCY-06, owner decision 17. Regional dread scales
with trauma / 50.0 (Bible 05 section 2), saturates at its fullest there, and alone never crosses the flee
threshold; a threat to the subject itself may still decide flight alone. Curve and ceiling are engineering's.

1. Replace `panic += region_trauma * 0.5` in `AppraisalSystem.evaluate_emotional_state`
   (`src/engine/cognition.py`) with `regional_dread(region_trauma)`: `REGIONAL_DREAD_MAX * min(1, max(0,
   trauma) / HAZARD_GROWTH_TRAUMA_THRESHOLD)`. Reuse the existing `50.0` constant rather than a second copy.
2. Choose `REGIONAL_DREAD_MAX` from the constraint, not by tuning: strictly below the 0.4 flee threshold
   (never decides alone) and above the weakest threat-to-self term, 0.2 (health below 40%), so it can still
   tip. Any value in (0.2, 0.4) works; 0.3 leaves a 0.1 margin. Name `FLEE_PANIC_THRESHOLD` instead of the
   bare 0.4 so the test pins the same constant the gate uses.
3. Tests (`tests/unit/strategic/test_regional_dread_appraisal.py`): saturation alone does not flee; no trauma
   value from 0 to 1e9 flees alone at bravery 0; the old two-deaths input no longer floods flight; a near-death
   control still flees alone; saturated dread tips a 35%-health subject; monotonic, bounded, saturating;
   the ceiling sits in (0.2, 0.4). Disabling control: restore the old term, expect failures.
4. Re-measure with the ENTITIES-ARRIVE-ADJACENT probe set, before (main) against after, both worlds, seed 42,
   2000 ticks, `audit_mode`, budget off, each arm twice.
5. Docs: Bible 04 section on regional dread, parity ledger `strategic_cognition.yaml` (new STRAT-277, STRAT-251
   evidence note), divergence entry 2.73 with the re-baseline stated.
6. Gates: scoped pytest, code-health ratchet in a scratch venv, mechanism-registry advisory, registry
   regenerated from a clean export.

Out of scope, unchanged: the 0.4 threshold, bravery's weight, `trauma_score`'s own definition and the 50.0
threshold, the trauma producer, `kernel.py` and `scheduler.py`.
