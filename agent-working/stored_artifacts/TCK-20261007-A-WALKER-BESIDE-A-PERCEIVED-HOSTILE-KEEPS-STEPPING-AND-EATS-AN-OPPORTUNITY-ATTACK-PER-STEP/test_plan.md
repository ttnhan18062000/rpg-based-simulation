---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261007-A-WALKER-BESIDE-A-PERCEIVED-HOSTILE-KEEPS-STEPPING-AND-EATS-AN-OPPORTUNITY-ATTACK-PER-STEP
artifact_type: test_plan
tags: [combat]
---

# Test plan

New `tests/unit/engine/test_action_task_does_not_move.py` (10 cases): an action holder (ENTITY_ACT with a payload) is recognised and an idle or moving entity is not; live tracking follows the target only for entity-tracking moves (never for an ATTACK holder, whatever its leftover mode); the candidate selector does not offer an action holder a move but offers an idle entity one; an action holder still moves on a tick that sets a target; an ATTACK emission clears the navigation target it inherits; a kernel-level case where an adjacent attacker holding an ATTACK task and a leftover target stays on its tile and takes no opportunity attack (fails on `main`); an errand walk still walks and a pursuit still live-retargets. One existing fixture changed (`test_resolve_live_tracking_target_returns_live_position_when_target_alive` sets `movement_mode=PURSUE`).

## Proof Plan
- **Level**: unit, a kernel-level constructed pair, and a five-seed, three-world pinned corpus before and after.
- **Proof kind**: a regression test that fails on `main`; before and after measurement with hits split into decided, held and neither.
- **Oracle source**: world rule MOV-07 (orthogonal adjacency), COMB-009/272 (a step away from an engaged hostile gives it a free swing), and the movement-follows-a-decided-movement rule of the re-scoped ticket.
- **Expected effect**: the "neither" class of opportunity-attack hits falls (162.4 / 154.2 / 104.6 to 69.2 / 37.0 / 41.2); held-move hits unchanged on the first two worlds; landed attacks rise; `urban_political` deaths rise and are attributed, not tuned.
- **Selected commands**: `pytest tests/unit/engine/test_action_task_does_not_move.py tests/unit/domains/optimization tests/unit/movement tests/unit/engine tests/unit/combat tests/integration`; `probes/oa_fix_ms.py <root> <world> 1500 <seed> <label>` for seeds 42 to 46 on three worlds for each arm; `probes/oa_attr.py` for the attribution; `probes/oa_instr.py` for the instrumentation facts.
