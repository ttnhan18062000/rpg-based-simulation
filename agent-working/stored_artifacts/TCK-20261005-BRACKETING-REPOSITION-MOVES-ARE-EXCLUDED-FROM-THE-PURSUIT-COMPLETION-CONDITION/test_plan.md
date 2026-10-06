---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261005-BRACKETING-REPOSITION-MOVES-ARE-EXCLUDED-FROM-THE-PURSUIT-COMPLETION-CONDITION
artifact_type: test_plan
tags: [engine, combat]
---

# Test plan

Written retroactively at close, from the tests that exist.

- Unit, `tests/unit/engine/test_pursuit_completion.py` (21): normal flow (in-reach ends pursuit, intercept, bracketing); edge cases (ranged reach, live position over navigation snapshot, kiting holds range, out-of-reach keeps every kind); failure modes (dead, inactive and missing target end every kind); regression-prone paths (guard and cover-seeking unchanged, pursuit without `target_id` unchanged); both dispatchers (`LocalSequentialExecutor`, concurrent worker) including a dead-target bracketing and intercept, and a guard move that must be kept.
- Disabling controls: dead-target condition off fails exactly 6; extra modes off fails exactly 5.
- Registry pins: `test_mechanism_registry_completeness_check.py` (36 to 37 bound, 26 to 25 unbound) and `test_mechanism_state_caller_check.py`, measured by running the checks.
- Corpus: legacy vs fixed arms, 4 worlds x 2 runs, all pairs matched. PURSUE per-move identity cannot be compared once an entity is freed; that case rests on the unit pins.

Result: 46 passed after the rebase onto origin/main 9299891a9.

## Proof Plan

- Level: unit, plus a real-kernel corpus measurement.
- Proof kind: regression, with disabling controls.
- Oracle source: the Sticky-Task Law in `docs/engine/kernel.md` (a persisting task kind must define how it ends) and divergence 2.70.
- Expected effect: no live entity holds a PURSUE, INTERCEPT, BRACKETING or KITING move after its target is dead, inactive or gone; guard and cover-seeking moves are unchanged.
- Selected commands: `pytest tests/unit/engine/test_pursuit_completion.py tests/unit/tools/test_mechanism_registry_completeness_check.py tests/unit/tools/test_mechanism_state_caller_check.py`; probes in `probes/` for the corpus arms.
