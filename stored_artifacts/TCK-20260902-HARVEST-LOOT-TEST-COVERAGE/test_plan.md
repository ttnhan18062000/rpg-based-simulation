---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260902-HARVEST-LOOT-TEST-COVERAGE
artifact_type: test_plan
tags: [testing, economy]
---

# Test Plan — TCK-20260902-HARVEST-LOOT-TEST-COVERAGE

## Regression Surface

**Unit** (must keep passing, extended in place — no existing test function renamed/removed):
- `tests/unit/resource/test_harvest_channeling.py::test_harvest_channeling_and_yield`
- `tests/unit/resource/test_harvest_channeling.py::test_harvest_node_cooldown`
- `tests/unit/resource/test_loot_channeling.py::test_loot_channeling_completion`
- `tests/unit/resource/test_loot_channeling.py::test_loot_interruption_by_distance`

**Integration** (read-only reference per Out of Scope; must not regress):
- `tests/integration/kernel/test_resource_conservation.py` — specifically
  `test_harvest_full_inventory_does_not_deplete_node`,
  `test_loot_ground_item_full_inventory_does_not_remove_item`,
  `test_loot_corpse_full_inventory_does_not_remove_corpse` (already covers corpse +
  full-inventory at the `refine()` layer — new corpse unit test must be complementary, not a
  duplicate of this).
- `tests/integration/kernel/test_resource_conservation_v2.py` — uses `HarvestSystem` directly;
  confirm no import-path or shared-fixture collision from new test additions (there should be
  none, since these are separate files/modules).

## New Tests Required

### `tests/unit/resource/test_harvest_channeling.py`

1. **`test_harvest_no_interaction_or_no_target_is_skipped`**
   Category: unit.
   Verifies: an entity with `interaction=None` (or with an `InteractionComponent` whose
   `target_node_id is None`) produces no entry in `HarvestSystem.update(state).entity_updates`
   for that entity (harvesting.py:16-17).
   Location: `tests/unit/resource/test_harvest_channeling.py`.

2. **`test_harvest_skips_non_harvest_interaction_kind`**
   Category: unit.
   Verifies: an entity with `interaction.kind="ground_item"` (or `"corpse"`) and a valid
   `target_node_id` is not touched by `HarvestSystem.update()` — no `entity_updates` entry
   produced (harvesting.py:19-20). Use a real `ResourceNodeState` as the target to confirm the
   skip happens purely on `kind` mismatch, not because the node lookup fails.
   Location: `tests/unit/resource/test_harvest_channeling.py`.

3. **`test_harvest_resets_on_missing_or_depleted_node`**
   Category: unit.
   Verifies two sub-cases (either two test functions or one parametrized test):
   (a) entity's `interaction.target_node_id` does not exist in `state.resource_nodes` at all →
   `EntityUpdate.interaction.reset == True`;
   (b) entity's target node exists but `remaining_charges <= 0` → same reset outcome
   (harvesting.py:26-31). Assert `entity_updates[entity.id].interaction.reset is True`.
   Location: `tests/unit/resource/test_harvest_channeling.py`.

4. **`test_harvest_resets_on_distance`**
   Category: unit.
   Verifies: entity with a live `harvest` interaction and a valid, non-depleted target node whose
   Manhattan distance from the entity's position exceeds `1.5` → `EntityUpdate.interaction.reset
   == True` (harvesting.py:33-39). Mirror the structure of the existing
   `test_loot_interruption_by_distance` in the sibling file (start close, move away, then call
   `HarvestSystem.update()`, or construct the far-apart state directly since `HarvestSystem` is
   stateless per-call).
   Location: `tests/unit/resource/test_harvest_channeling.py`.

5. **Node-cooldown merge branch (harvesting.py:69-74) — CONDITIONAL, planner/implementer
   decision required.** Per investigation.md's Risks section, this branch appears unreachable
   through the public `HarvestSystem.update()` API within a single call (each `node.id` is
   processed at most once per call, and `node_updates` starts empty each call). Do **not**
   force a test that cannot actually exercise the branch (e.g. via monkeypatching internals or
   constructing two nodes with a colliding `id`, which is itself an invalid state). Instead:
   - If the implementer confirms it is unreachable, add a short code comment or a skipped/xfail
     test documenting the finding (`@pytest.mark.skip(reason="...")` with the file:line
     citation) rather than a passing test that doesn't actually hit lines 69-74, OR omit a test
     for this branch entirely and note the dead-code finding in the ticket's Implementation Notes.
   - Do not silently claim full coverage of this branch if it cannot be genuinely exercised.

### `tests/unit/resource/test_loot_channeling.py`

6. **`test_loot_no_interaction_or_no_target_is_skipped`**
   Category: unit.
   Verifies: an entity with `interaction=None` (or `target_node_id is None`) produces no
   `entity_updates` entry (loot.py:17-18).
   Location: `tests/unit/resource/test_loot_channeling.py`.

7. **`test_loot_skips_non_lootable_interaction_kind`**
   Category: unit.
   Verifies: an entity with `interaction.kind="harvest"` and a valid `target_node_id` is not
   touched by `LootSystem.update()` (loot.py:20-22).
   Location: `tests/unit/resource/test_loot_channeling.py`.

8. **`test_loot_corpse_completion_transfers_all_item_stacks`**
   Category: unit.
   Verifies: an entity with `interaction.kind="corpse"`, `target_node_id` pointing at a
   `CorpseState` with **≥2 distinct `ItemStack` entries** in `items`, driven to completion
   (progress reaches the `required = 10.0` threshold) produces a `ResourceTransferIntent` with
   `source_kind == "CORPSE"` and `items_add` equal to the corpse's full `items` list (all
   stacks, not just the first) (loot.py:66-68). Follow the existing
   `test_loot_channeling_completion` pattern: drive progress ticks, assert `sys_upd` shape
   directly and/or run `AuthoritativeApplyPipeline.refine()` + `ApplyPath.apply_generation()` to
   confirm both inventory receipt of all stacks and `301 in refined.corpses_remove`. This is the
   ticket's headline gap — corpse looting has never been executed by any unit test.
   Location: `tests/unit/resource/test_loot_channeling.py`.

9. **`test_loot_resets_on_target_gone`**
   Category: unit.
   Verifies two sub-cases (parametrized or two functions):
   (a) `interaction.kind="ground_item"` targeting an id absent from `state.ground_items`;
   (b) `interaction.kind="corpse"` targeting an id absent from `state.corpses`.
   Both → `EntityUpdate.interaction.reset == True` (loot.py:35-41, the `target_pos` stays
   `None` path).
   Location: `tests/unit/resource/test_loot_channeling.py`.

10. **`test_loot_corpse_interruption_by_distance`**
    Category: unit.
    Verifies: entity with a live `corpse` interaction whose distance from the corpse exceeds
    `1.5` → `EntityUpdate.interaction.reset == True` and the corpse remains in
    `state.corpses` after applying the update (loot.py:44-50, corpse variant). Mirror
    `test_loot_interruption_by_distance`'s existing ground-item structure exactly, swapping in a
    `CorpseState` target and `kind="corpse"`.
    Location: `tests/unit/resource/test_loot_channeling.py`.

## Scoped Pytest Commands

Primary (required by Acceptance Criteria):
```
pytest tests/unit/resource/test_harvest_channeling.py tests/unit/resource/test_loot_channeling.py -v
```

Regression check against indirect integration coverage (must not be broken by this change):
```
pytest tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -v
```

Combined domain sweep (optional, wider net for the `resource`/`kernel` interaction domain before
Verify):
```
pytest tests/unit/resource/ tests/integration/kernel/test_resource_conservation.py tests/integration/kernel/test_resource_conservation_v2.py -v
```

Never run the full suite (`pytest tests/`) per project testing rule — scope stays within the
`resource`/`kernel` domain touched by this ticket.

## Anti-Drift Test Guards

- **File-unchanged guard**: `git diff --stat src/systems/world_systems/harvesting.py
  src/systems/economy_systems/loot.py` must show no output before closing the ticket — confirms
  the "byte-for-byte unmodified" acceptance criterion. Run this as a final check, not a pytest
  test (there is no existing architecture-guard test file scoped to these two modules
  specifically; adding one would be new-file creation against the no-duplication policy for a
  one-off check better done via `git diff`).
- **No accidental integration-test duplication**: any new corpse-completion unit test
  (`test_loot_corpse_completion_transfers_all_item_stacks`) must assert on `LootSystem.update()`'s
  *proposed* transfer shape (happy path, sufficient inventory), not re-assert the existing
  integration file's full-inventory-rejection assertion — keep the two conceptually and
  textually distinct so a reviewer can see they are not the same case restated.
  `tests/integration/kernel/test_resource_conservation.py::test_loot_corpse_full_inventory_does_not_remove_corpse`
  remains the sole owner of the inventory-pressure-rejection case for corpses.
  `test_harvest_full_inventory_does_not_deplete_node` remains sole owner of the same for harvest.
- **Import-path guard**: all new tests must import `HarvestSystem`/`LootSystem` via the existing
  shim modules (`src.systems.harvest_system`, `src.systems.loot_system`), matching every existing
  test in both files — a new test importing from `src.systems.world_systems.harvesting` /
  `src.systems.economy_systems.loot` directly would silently start a path migration that is
  explicitly out of scope.
- **Marker guard**: every new test function must carry `@pytest.mark.v2_contract`, matching the
  existing convention in both files (no `differential`/`regression`/`intentional_divergence`
  markers — this ticket introduces no divergence and proves no legacy parity).
- **Determinism guard**: none of the new tests should introduce a real RNG dependency (seed
  variance) — confirmed in investigation.md that neither system consumes `state.seed`; if a new
  test ends up needing seed-dependent assertions, that itself is a signal something was
  misunderstood about the system's determinism and should be re-examined before landing.
