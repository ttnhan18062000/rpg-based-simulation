---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261006-HELD-ATTACK-TASK-AGAINST-AN-OUT-OF-RANGE-TARGET-IS-NEVER-RE-DECIDED
artifact_type: test_plan
tags: [combat, cognition]
---

# Test plan

New: `tests/unit/actions/test_held_attack_out_of_range.py` (diagonal, other diagonal and far melee clear and report; orthogonal adjacent keeps its task; ranged inside range kept, beyond range cleared; readiness failure keeps its task; classification of the failure reasons). `tests/unit/engine/test_diagonal_melee_pair_strikes.py` (real Kernel, pinned target: first strike within 20 ticks; disabling control restores the old movement rule and misses the bound; one bracketing case ends only in orthogonal reach). Reversed: `test_attack_out_of_range_resets_task_to_idle`.

Existing, rerun: `tests/unit/engine`, `tests/unit/actions`, `tests/unit/combat`, `tests/unit/strategic`, `tests/unit/kernel`, the campaign episode tests (the deliberate-attack test must stay XFAIL), determinism tests. Gates: code-health ratchet, parity ledger schema, frontmatter validators, registry clean-export check.

## Proof Plan
- **Level**: unit (routing and classification), kernel-level constructed pair, corpus before/after.
- **Proof kind**: bounded-outcome test with a disabling control; before/after measurement.
- **Oracle source**: world rule MOV-07 (melee adjacency orthogonal) and the Sticky-Task Law (`docs/engine/kernel.md`: a persistent task must define how it ends).
- **Expected effect**: longest consecutive `OUT_OF_RANGE` run per entity falls from 258 to 2 on `frontier_living_world`; the diagonal pair strikes by tick 20 and by tick 39 without the movement guard.
- **Selected commands**: `pytest tests/unit/actions tests/unit/engine/test_diagonal_melee_pair_strikes.py tests/integration/campaigns/test_catalog_entity_spawn_wiring.py`; `probes/run5.sh` and `probes/run6.sh` for the corpus arms.
