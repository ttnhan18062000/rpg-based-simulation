---
status: active
layer: mechanics
authority: P2
audience: agent
ticket_id: TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE
artifact_type: test_plan
phase: investigate
date: 2026-08-08
tags: [progression, combat, feature-flags]
---

# Test Plan — TCK-20260808-PROGRESSION-GROWTH-ECONOMY-UNREACHABLE-IN-PRACTICE

## Existing coverage found

`tests/unit/movement/test_tactical_movement.py::test_opportunity_attack_on_egress` already
exercises the exact call site (`MovementSystem.resolve_move`'s opportunity-attack branch) and
already asserts `upd1.combat.is_opportunity_attack is True` / `upd1.combat.damage_taken > 0` — but
never sets up a *lethal* hit, so it never touches the `resource_transfers` bug at all. This is the
natural place to add a lethal-case sibling test, matching the existing fixture helpers
(`create_mock_state`, `create_mock_entity`).

## New/updated tests

**Unit — `tests/unit/movement/test_tactical_movement.py`**
1. `test_opportunity_attack_lethal_grants_resource_transfers_to_attacker` (new): construct a
   defender with `hp` low enough that the attacker(s)' opportunity-attack damage is lethal.
   Resolve via `AuthoritativeApplyPipeline.refine`. Assert:
   - The **attacker's** `EntityUpdate.resource_transfers` (top-level field, not nested under
     `.combat`) contains a `ResourceTransferIntent(source_kind="COMBAT", xp_reward=...)` with
     `xp_reward > 0`.
   - The **defender's** (victim's) own `EntityUpdate.resource_transfers` is empty — confirms the
     fix corrects attribution, not just presence.
2. Regression: keep `test_opportunity_attack_on_egress` (non-lethal) passing unchanged — the
   non-lethal path must not regress.

**Unit — `src/engine/movement.py` caller (or wherever the fix lands)**
3. If the fix changes `is_lethal` handling: a case where the opportunity attack is lethal and
   confirm `outcome_kind == "KILL"` (if Plan decides to also fix the hardcoded `is_lethal=False`)
   fires `entity_killed`-eligible state — decided at Plan time, not assumed here.

**Integration — real end-to-end verification (already-used pattern, not new infra)**
4. Reuse `tools/entity_lifecycle_score.py`'s own `_run_for_analysis()` (or a scratch script using
   the same pattern) on `sandbox_world` seed 42 at 2000 ticks, before/after the fix: confirm
   `entity.identity.evolution_points`/`evolution_level` for at least one real entity changes
   across the run post-fix (currently: zero changes in 2000 ticks, confirmed in investigation.md).
   This is the acceptance-criteria-mandated "measurable, verified increase in real xp_granted/
   level_up events on at least 2 real corpus worlds at 1000+ ticks" check — run on `sandbox_world`
   and `urban_political` (the same 2 worlds already measured in investigation.md's quest-rate
   table, for direct before/after comparability).

## Existing tests that must keep passing (regression guard)

- `tests/unit/movement/test_tactical_movement.py` (full file — opportunity-attack mechanics)
- `tests/unit/combat/test_direct_combat_outcomes.py` (`resolve_attack`/kill-reward logic — must
  stay untouched by this fix, which is scoped to the `resolve_multi_attack` caller in movement.py)
- `tests/integration/pipeline/test_combat_legality_matrix.py`,
  `tests/integration/pipeline/test_movement_micro_arena_position_swap.py` (broader movement/combat
  pipeline integration)

## Scoped pytest command

```
pytest tests/unit/movement/ tests/unit/combat/ tests/integration/pipeline/test_combat_legality_matrix.py tests/integration/pipeline/test_movement_micro_arena_position_swap.py -q
```
