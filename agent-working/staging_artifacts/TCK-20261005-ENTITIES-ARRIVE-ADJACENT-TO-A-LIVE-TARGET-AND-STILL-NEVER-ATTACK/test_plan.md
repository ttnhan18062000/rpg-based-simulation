---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261005-ENTITIES-ARRIVE-ADJACENT-TO-A-LIVE-TARGET-AND-STILL-NEVER-ATTACK
artifact_type: test_plan
tags: [combat, strategy, cognition]
---

# Test plan

- `tests/unit/engine/test_pursuit_completion.py` (13): the helper (adjacent ends the pursuit; two tiles away does not for melee; a
  ranged entity ends at its range; live position beats the snapshot; dead or missing target and non-`PURSUE` modes unchanged) and
  both dispatchers (`LocalSequentialExecutor`, `default_simulation_worker`) ending and not ending. Control: with the helper
  disabled exactly the 4 "ends the pursuit" tests fail and the 9 "must not change" tests pass.
- `tests/unit/strategic/test_redirection_entity_objective.py` (3): an untyped objective still gets its navigation point (control);
  an entity-typed objective writes none; a carrying entity with an entity-typed objective is not sent home. Control: removing the
  `has_nav_update` claim fails exactly the last test. The `intelligence.py` redirection branch has no direct unit test.
- Wide sweep (certification, regression, architecture, engine, integrity, mechanic_scenarios, scenarios, integration/optimization,
  unit core/engine/domains/strategic/combat/tactical/world/systems, `-m "not slow"`) on the final tree.
- Measurement: the probes in `probes/` before and after, on five worlds, single runs, caveat stated.

## Proof Plan

- level: unit (helpers, dispatchers, redirection) plus engine integration (the measurements)
- proof kind: regression tests with a disabling control; before/after measurement for effect sizes
- oracle source: `docs/engine/kernel.md` (Sticky-Task Law) and `docs/engine/contracts/tactical_contract.md`
- expected effect: pursuit moves end in reach; the navigation target is not re-asserted from a snapshot; tile-swap pairs collapse;
  decision-path attack counts are reported whatever they are
- selected commands: `pytest tests/unit/engine/test_pursuit_completion.py tests/unit/strategic/test_redirection_entity_objective.py`
  and the wide sweep above
