---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE
artifact_type: test_plan
tags: [strategy, cognition, combat]
---

# Test plan

New: `tests/unit/strategic/test_regional_dread_appraisal.py` (13 cases).
- Normal flow: saturated dread alone (full health, no hostile, bravery 0) gives panic 0.3 and does not flee.
- Edge cases: trauma 0, 1, 2, 25, 50, 500 and 1e9 never flee alone; negative trauma gives 0; dread saturates and is
  monotonic and bounded.
- Failure mode (regression of the old input): two deaths (trauma 2.0) add 0.012, not 1.0, and do not flee.
- Controls: a near-death subject (5% health, no trauma) still flees alone with panic 0.8; a 35%-health subject
  does not flee without dread and does with saturated dread; the ceiling sits in (0.2, 0.4).
- Disabling control: restoring `panic += region_trauma * 0.5` fails 8 of the 13.

Existing, unchanged and rerun: `tests/unit/strategic/test_cognition_immediate_fixes.py` (near-death and bravery
baselines), `tests/unit/combat/test_catalog_hostility_sweep.py`, then `tests/unit/strategic`,
`tests/unit/combat`, `tests/unit/engine` as a scoped sweep. Corpus: the before/after probe set in the
investigation. Gates: the code-health ratchet, ruff on the changed files against `main` (same findings),
the parity-ledger and frontmatter validators, the registry clean-export check.

## Proof Plan
- **Level**: unit (the appraisal function) plus corpus probes (real `Kernel.tick_once()` on two worlds).
- **Proof kind**: invariant test with a disabling control, and a before/after measurement with a trauma-off control.
- **Oracle source**: world rule `AGENCY-06` (regional dread alone never flees; a threat to the subject itself may) and Bible 05 section 2 (the 50.0 instability threshold).
- **Expected effect**: trauma-alone flees 3 to 0 in `crowded_frontier` and 0 to 0 in `frontier_living_world`; the near-death control still flees alone; saturated dread tips a 35%-health subject.
- **Selected commands**: `pytest tests/unit/strategic/test_regional_dread_appraisal.py tests/unit/strategic/test_cognition_immediate_fixes.py tests/unit/combat/test_catalog_hostility_sweep.py`; `probes/run2.sh` for the before/after arms.
