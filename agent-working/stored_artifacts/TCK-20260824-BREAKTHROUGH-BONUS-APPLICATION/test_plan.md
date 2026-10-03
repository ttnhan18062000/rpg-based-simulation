---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION
artifact_type: test_plan
tags: [progression]
---

# Test Plan — TCK-20260824-BREAKTHROUGH-BONUS-APPLICATION

## Regression Surface

**unit — progression**
- `tests/unit/progression/test_breakthroughs.py` — `test_breakthrough_addition`, `test_duplicate_breakthrough_suppression`. Must keep passing unchanged; they exercise the `breakthroughs_add` → `active_breakthroughs` mechanic, which this ticket does not touch.
- `tests/unit/progression/test_leveling.py` — regression surface for `LevelingService.recalculate_combat_stats`, which must stay bit-identical for entities with no active breakthroughs (this ticket must not change its formulas per Anti-Drift Hazards).
- `tests/unit/progression/test_progression_v2.py`, `tests/unit/progression/test_rpg_advancement.py` — broader progression regression surface (XP/level-up), unaffected but scoped-in since they share `leveling.py`/`apply.py` call paths.

**unit — core/engine**
- `tests/unit/core/test_rpg_depth.py` — specifically `TestSkillScaling`, `TestAttributeCaps`, `TestEffectiveStats` (`test_effective_stats_with_wounds`, `test_effective_stats_with_scars`, `test_evasion_capped`), `TestStaminaApplyIntegration`, `TestWoundApplyIntegration`. `get_effective_stats`'s existing signature is being extended (new optional `active_breakthroughs` parameter) — all existing call sites in this file must keep working with the new parameter defaulting to `None`/no bonus, and must produce identical output to today when no breakthroughs are supplied.

**architecture / apply-path**
- Any existing test exercising `ApplyPath._apply_entity_update_to_dict`'s `stats_dirty` gating (implicitly covered by `TestStaminaApplyIntegration`/`TestWoundApplyIntegration` in `test_rpg_depth.py`) — the `stats_dirty` OR-condition is being extended to include `update.identity.breakthroughs_add`; must not change behavior for updates that don't touch breakthroughs.

## New Tests Required

Per acceptance criteria:

1. **`test_apply_bonuses_iron_will_returns_spirit_wisdom_plus_two`**
   - Category: unit
   - Verifies: `BreakthroughService.apply_bonuses({"iron_will"}, base_attributes)` returns an `AttributeComponent` with `spirit == base_attributes.spirit + 2` and `wisdom == base_attributes.wisdom + 2`, all other attribute fields unchanged from `base_attributes`. Satisfies AC #1 directly.
   - Location: `tests/unit/progression/test_breakthroughs.py` (new test, alongside the existing two)

2. **`test_apply_bonuses_sums_multiple_breakthrough_ids`**
   - Category: unit
   - Verifies: `apply_bonuses({"iron_will", "titan_grip"}, base_attributes)` returns spirit+2/wisdom+2 (from iron_will) **and** strength+4 (from titan_grip) simultaneously — proves correct summation across multiple non-overlapping-attribute breakthroughs without needing `fleet_foot`'s `evasion_flat`. Satisfies AC #2.
   - Location: `tests/unit/progression/test_breakthroughs.py`

3. **`test_apply_bonuses_empty_ids_returns_unchanged`**
   - Category: unit
   - Verifies: `apply_bonuses(set(), base_attributes)` returns attributes equal to `base_attributes` (same field values), no exception raised.
   - Location: `tests/unit/progression/test_breakthroughs.py`

4. **`test_apply_bonuses_unknown_id_returns_unchanged_no_raise`**
   - Category: unit
   - Verifies: `apply_bonuses({"nonexistent_breakthrough_xyz"}, base_attributes)` returns attributes unchanged, no `KeyError`/exception. Satisfies AC #3 (unknown-id half).
   - Location: `tests/unit/progression/test_breakthroughs.py`

5. **`test_apply_bonuses_mixed_known_and_unknown_ids`**
   - Category: unit
   - Verifies: `apply_bonuses({"iron_will", "nonexistent_xyz"}, base_attributes)` applies only the known bonus (spirit+2/wisdom+2), silently ignores the unknown id, no raise. Closes the gap between "fully empty/unknown" (test 3/4) and "fully known" (test 1/2).
   - Location: `tests/unit/progression/test_breakthroughs.py`

6. **`test_get_effective_stats_applies_breakthrough_attribute_bonus`**
   - Category: unit
   - Verifies: `SkillScalingService.get_effective_stats(attrs, active_breakthroughs={"titan_grip"})` produces a higher `atk` than `SkillScalingService.get_effective_stats(attrs)` with no breakthroughs — proves the new `active_breakthroughs` parameter reaches `apply_bonuses` and its effect surfaces through `recalculate_combat_stats`'s existing strength→atk formula. Uses `titan_grip` (not `iron_will`) per the investigation's Risk #1 finding, since spirit/wisdom don't feed any derived combat stat.
   - Location: `tests/unit/core/test_rpg_depth.py`, new method in `TestEffectiveStats`

7. **`test_get_effective_stats_no_breakthroughs_unchanged`**
   - Category: unit / regression guard
   - Verifies: `get_effective_stats(attrs)` (no `active_breakthroughs` arg) and `get_effective_stats(attrs, active_breakthroughs=None)` and `get_effective_stats(attrs, active_breakthroughs=set())` all produce identical output — confirms the new parameter is fully backward compatible and defaults safely.
   - Location: `tests/unit/core/test_rpg_depth.py`, new method in `TestEffectiveStats`

8. **`test_apply_path_recomputes_combat_stats_from_active_breakthroughs`**
   - Category: integration (apply-path)
   - Verifies AC #4 end-to-end: build an entity via `V2EntityBuilder` with `identity.active_breakthroughs = {"titan_grip"}` already populated (constructed directly on the test entity, per the investigation's Anti-Drift note — NOT via the out-of-scope `breakthroughs_add` granting mechanism), run it through `ApplyPath.apply_generation`/`ApplyPath._apply_entity_update` with an `EntityUpdate` that makes `stats_dirty` True (e.g. an `AttributeUpdate` or `IdentityUpdate` with `learned_skills`), and assert the resulting `entity.combat.atk` reflects the `titan_grip` strength+4 bonus compared to an equivalent entity with no active breakthroughs.
   - Location: `tests/unit/core/test_rpg_depth.py`, new class `TestBreakthroughApplyIntegration` (mirrors `TestStaminaApplyIntegration`/`TestWoundApplyIntegration` pattern)

9. **`test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone`**
   - Category: integration (apply-path) / anti-drift guard
   - Verifies the `stats_dirty` gap fix (investigation Current Behavior #1): an `EntityUpdate` with `IdentityUpdate(breakthroughs_add=["titan_grip"])` and **nothing else** (no attribute/equipment/skill/trait/level change) still causes `combat.atk` to reflect the new breakthrough's bonus after `ApplyPath.apply_generation` — proves the dirty-check extension works, not just the `get_effective_stats` call itself.
   - Location: `tests/unit/core/test_rpg_depth.py`, `TestBreakthroughApplyIntegration`

## Scoped Pytest Commands

```
pytest tests/unit/progression/test_breakthroughs.py tests/unit/progression/test_leveling.py -v
pytest tests/unit/core/test_rpg_depth.py -v
pytest tests/unit/progression/ -v
```

Do not run `pytest tests/` — scope stays within `tests/unit/progression/` and `tests/unit/core/test_rpg_depth.py`, the two files that directly exercise the changed code (`src/progression/breakthroughs.py`, `src/progression/leveling.py`, `src/engine/rpg_depth.py`, `src/engine/apply.py`).

## Anti-Drift Test Guards

- **`test_get_effective_stats_no_breakthroughs_unchanged`** (New Test #7) directly guards against the most likely silent regression: a signature change to `get_effective_stats` that accidentally alters output for the (overwhelmingly common) no-breakthroughs case.
- **`test_apply_bonuses_empty_ids_returns_unchanged`** and **`test_apply_bonuses_unknown_id_returns_unchanged_no_raise`** (New Tests #3, #4) guard against `apply_bonuses` being implemented in a way that raises on missing registry entries — this would turn a passive-perk lookup into a crash risk anywhere it's called with stale/removed breakthrough IDs.
- **`test_apply_path_stats_dirty_triggers_on_breakthroughs_add_alone`** (New Test #9) guards specifically against a partial fix that makes `apply_bonuses`/`get_effective_stats` correct in isolation but leaves the `stats_dirty` gate unpatched — this is the exact "isolated calls only" failure mode the ticket's Scope bullet 3 warns about ("not just isolated calls").
- Existing `tests/unit/progression/test_breakthroughs.py::test_breakthrough_addition` and `::test_duplicate_breakthrough_suppression` continue to run unmodified — they are the guard against scope creep into the `breakthroughs_add`-construction gap (out of scope per this ticket and TCK-20260808).
- `tests/unit/progression/test_leveling.py` (existing, unmodified) guards against `recalculate_combat_stats`'s formulas being changed to make `spirit`/`wisdom` feed derived stats — per Anti-Drift Hazards in investigation.md, that would be an undocumented mechanics change, not "finish the stub."
