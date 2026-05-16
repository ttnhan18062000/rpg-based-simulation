# Milestone 2 — Fix DirtySet Lifecycle Correctness

## Goal

Make DirtySet safe before using it for O(Dirty) optimization.

The code currently creates `DirtySet.from_update(state, update)` after action routing, then later phases still add movement, interaction, world dynamics, quest reward, resource transaction, lifecycle, group, and capacity changes. The pipeline snippet shows DirtySet being created before position swaps, movement routing, interaction routing, interaction enforcement, world dynamics, and quest reward authority. 

DirtySet itself is explicitly intended to track modified entities/world objects so systems can avoid O(N) scans.  The checklist also claims Shop, Group, Strategic, and CapacityEnforcement use DirtySet to avoid full scans. 

That combination is dangerous: **an early DirtySet can make optimized systems skip entities changed by later phases.**

## Decision

Use this design:

```text
DirtySet must be updated after every phase that can add or transform updates.
```

Do not use a single early snapshot.

## Tasks

| Task                                                     | Narrow implementation logic                                                                 | Files / area             |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------ |
| M2.1 Add dirty recompute helper                          | Add internal helper: `_refresh_dirty_set(state, update) -> StateUpdate`.                    | `src/engine/pipeline.py` |
| M2.2 Call helper after action routing                    | Keep current post-action DirtySet, but make it explicit.                                    | pipeline                 |
| M2.3 Call helper after movement routing                  | Movement can add `new_position`, town membership impact, group proximity impact.            | pipeline                 |
| M2.4 Call helper after interaction routing/enforcement   | Harvest/loot can add inventory/resource/node/corpse changes.                                | pipeline                 |
| M2.5 Call helper after world dynamics                    | Entity spawn/despawn, region, nodes, scars, corpses must be reflected.                      | pipeline                 |
| M2.6 Call helper after quest reward/resource transaction | Reward delivery affects inventory and strategic state.                                      | pipeline                 |
| M2.7 Call helper after lifecycle                         | Death, corpse creation, alive flag, group impact must be reflected.                         | pipeline                 |
| M2.8 Call helper before every O(Dirty) consumer          | Before Strategic, Group, Shop, CapacityEnforcement, or any phase that branches on DirtySet. | pipeline phases          |
| M2.9 Add DirtySet invariant check in debug/audit mode    | If audit mode is on, recompute DirtySet at the end and assert it matches final update.      | `DirtySet`, pipeline     |

## New tests to add

```python
def test_dirty_set_includes_movement_added_after_action_phase():
    """
    Law:
        Movement generated after action routing must appear in DirtySet.
    """

def test_dirty_set_includes_inventory_from_interaction_enforcement():
    """
    Law:
        Harvest/loot output must mark inventory and strategic dirtiness.
    """

def test_dirty_set_includes_resource_node_updates():
    """
    Law:
        Resource node charge/cooldown changes must mark resource_node_ids.
    """

def test_dirty_set_includes_lifecycle_death_and_corpse_creation:
    """
    Law:
        Death/lifecycle changes must mark combat, lifecycle, strategic, and world dirtiness.
    """

def test_dirty_set_includes_world_dynamics_spawned_entities():
    """
    Law:
        Spawned entities must not be invisible to downstream optimized systems.
    """

def test_final_dirty_set_matches_final_state_update_in_audit_mode():
    """
    Law:
        Final DirtySet must be exhaustive for the final StateUpdate.
    """
```

## Acceptance checklist

```text
[ ] DirtySet is not treated as a once-per-pipeline snapshot.
[ ] Every phase that mutates StateUpdate either refreshes or merges DirtySet.
[ ] O(Dirty) consumers only run after DirtySet is current.
[ ] DirtySet audit-mode invariant exists.
[ ] Movement-derived dirtiness is tested.
[ ] Interaction/resource-derived dirtiness is tested.
[ ] Lifecycle/world-derived dirtiness is tested.
[ ] Strategic/capacity dirty behavior is tested.
```

## Exit condition

Any subsystem using DirtySet can no longer silently skip newly changed entities.

---
