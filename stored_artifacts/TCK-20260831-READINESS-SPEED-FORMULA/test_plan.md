---
status: historical
layer: combat
authority: P2
audience: agent
ticket_id: TCK-20260831-READINESS-SPEED-FORMULA
artifact_type: test_plan
tags: [combat, progression]
---

# Test Plan — TCK-20260831-READINESS-SPEED-FORMULA

## Regression Surface

**Unit — progression / derived stats:**
- `tests/unit/core/test_rpg_depth.py` (`TestEffectiveStats` class, lines 471-526) —
  `get_effective_stats()` wound/scar/breakthrough/evasion-clamp behavior. Must still pass
  unchanged since none of these tests assert on `readiness_speed`; adding a new dict key must not
  perturb `stats["atk"]`/`["max_hp"]`/etc. comparisons.
- `tests/unit/progression/test_progression_v2.py` — exercises `recalculate_combat_stats()`.
- `tests/unit/core/test_rpg_math.py` — exercises `recalculate_combat_stats()`.
- `tests/unit/core/test_domain_6_hardening.py` — exercises `recalculate_combat_stats()`.
- `tests/unit/quest/test_progression_lifecycle.py` — exercises `recalculate_combat_stats()`.
- `tests/unit/resource/test_durability_repair.py` — exercises `recalculate_combat_stats()`
  (equipment durability path).
- `tests/unit/progression/test_class_tiers.py` — `class_id_set` apply-path wiring through the
  same PH8 block this ticket's `replace(new_com, ...)` edit touches; must confirm the new
  `readiness_speed` kwarg does not disturb existing `class_id`/tier-bonus assertions.
- `tests/unit/progression/test_breakthroughs.py` — `active_breakthroughs` wiring through
  `get_effective_stats()`; same PH8 call-site risk as above.

**Unit — readiness mechanism itself:**
- `tests/unit/combat/test_readiness_regen.py` — all 4 existing tests
  (`test_readiness_regenerates_passively_per_tick`, `test_readiness_regen_clamps_at_100`,
  `test_readiness_speed_zero_disables_regen`, `test_readiness_speed_survives_to_readonly_
  reconstruction`) construct entities via `_build()` with an **explicit** `readiness_speed=`
  override, bypassing any derivation — these must keep passing unchanged since they never rely on
  the default-from-agility path.

**Integration / apply-path:**
- `tests/integration/pipeline/test_recovery_gaps.py` — touches `ApplyPath` PH8-adjacent recovery
  behavior; scoped in case the `replace(new_com, ...)` kwarg addition has any interaction.

**Arena-combat:**
- `tests/arena/test_arena_regional_control.py` — broad combat-outcome regression; run to confirm
  no unexpected shift in aggregate win/loss/regional-control outcomes from the formula change (this
  is a coarse guard, not a substitute for the corpus-validation AC below).
- `tests/integration/combat/test_class_tier_win_rate.py` — asserts tier bonus "does not decrease
  average combat win-rate vs. a fixed opponent roster"; a readiness_speed change that shifts
  overall combat pacing could interact with this baseline — run to confirm it still passes.

## New Tests Required

1. **`test_readiness_speed_derives_from_agility_two_values`**
   - Category: unit
   - Verifies: AC #1 — `recalculate_combat_stats()` (or `get_effective_stats()`, whichever Plan
     wires the formula into) returns different `readiness_speed` values for two
     `AttributeComponent`s that differ only in `agility` (e.g. `agility=5` vs `agility=15`), and
     the higher-agility entity's `readiness_speed` is strictly greater (direction matches the
     ticket's stated intent — higher agility, faster readiness regen). Satisfies the ticket's own
     AC wording "asserts the formula's output for >=2 distinct agility values."
   - Location: `tests/unit/core/test_rpg_depth.py` (new method on `TestEffectiveStats`, or a new
     `TestReadinessSpeedFormula` class in the same file — matches existing file's organization by
     derived-stat concern).

2. **`test_readiness_speed_reference_agility_backward_compatible`**
   - Category: unit
   - Verifies: AC #2 — an entity built with `AttributeComponent()`'s default (`agility=5`, the
     confirmed reference/baseline value) yields `readiness_speed == 10.0` exactly, matching the
     current flat default and every existing hardcoded fixture that never overrides agility.
   - Location: same file as test 1.

3. **`test_readiness_speed_survives_apply_path_replace`**
   - Category: unit / architecture guard
   - Verifies: the specific silent-drop hazard found in investigation — that a derived
     non-default `readiness_speed` (from a non-reference-agility entity) actually reaches the live
     `CombatComponent` after passing through `ApplyPath._apply_entity_update_to_dict()`'s PH8
     `replace(new_com, ...)` call (`src/engine/apply.py:507-515`), not just through
     `get_effective_stats()`'s returned dict. Build an entity with `agility != 5`, trigger a
     `stats_dirty` update (e.g. an `AttributeUpdate` or level-up), run it through `ApplyPath`, and
     assert `resulting_entity.combat.readiness_speed` matches the expected derived value (not the
     stale default). This is the direct regression guard for the "4th silent-drop point" risk
     flagged in investigation.md, mirroring the existing precedent
     `test_readiness_speed_survives_to_readonly_reconstruction` guards a sibling drop point.
   - Location: `tests/unit/combat/test_readiness_regen.py` (co-locate with the existing
     readiness-mechanism tests, since it exercises the same field through a different pipeline
     stage) or `tests/unit/core/test_rpg_depth.py`'s apply-path integration section — either is
     defensible; prefer `test_readiness_regen.py` for discoverability alongside the sibling
     silent-drop regression test it mirrors.

4. **Corpus-validation script/test (per ticket Scope — not a bare unit test)**
   - Category: integration / metamorphic-directional (hand-orchestrated, per
     `RACE-RELATIONS-MATRIX` precedent — `MutationLabOrchestrator` cannot target a `src/` code
     formula, only `WorldSpec`/`ScenarioSpec` fields)
   - Verifies: real, non-degenerate directional evidence that the agility-derived formula
     measurably increases combat throughput for a real corpus population, using
     `combat_damage`-events-per-tick (see investigation.md's Metric recommendation) computed from
     `simulation_events.jsonl` for a baseline run (pre-change code) vs. a compared run (post-change
     code) on the same real world/seeds, then `MetamorphicRuleEngine.evaluate_rules()` with a
     `monotonic_non_decreasing` (or stronger, if the evidence supports it) relationship spec. If
     the first attempt produces a degenerate baseline==compared result, follow the pilot ticket's
     own documented empirical approach (tune tick count / seed count before concluding no effect
     exists) rather than accepting a hollow PASSED.
   - Location: a throwaway script/test under this ticket's own `staging_artifacts/` or a scoped
     `tests/integration/combat/` test, per whatever shape Plan selects — must not be left as
     permanent CI-running infra unless Plan explicitly decides otherwise (the two same-batch
     precedents both treated their corpus-validation runs as throwaway, not new permanent test
     files, since they require a pre-change/post-change code split).

## Scoped Pytest Commands

```
pytest tests/unit/core/test_rpg_depth.py tests/unit/combat/test_readiness_regen.py \
       tests/unit/progression/ tests/unit/core/test_rpg_math.py \
       tests/unit/core/test_domain_6_hardening.py tests/unit/quest/test_progression_lifecycle.py \
       tests/unit/resource/test_durability_repair.py -m "not slow"
```

```
pytest tests/integration/pipeline/test_recovery_gaps.py \
       tests/integration/combat/test_class_tier_win_rate.py -m "not slow"
```

```
pytest tests/arena/test_arena_regional_control.py -m "not slow"
```

Never `pytest tests/` — scoped to combat/progression/apply-path domains only, per project testing
rule.

## Anti-Drift Test Guards

- **Sign-direction guard**: assert `readiness_speed` *increases* with agility (not decreases) —
  the adjacent `move_cost` formula in the same function decreases with agility
  (`- (attributes.agility * 0.1)`); a test that only checks "values differ" (not direction) would
  pass even if the formula were accidentally copy-paste-inverted from `move_cost`'s sign.
- **No wound/scar readiness penalty introduced as a side effect**: assert
  `get_effective_stats(attrs, wounds=[...])`'s `readiness_speed` (if present in the returned
  dict) is identical to the wound-free call's `readiness_speed` for the same attributes, unless
  Plan explicitly scopes a wound penalty (it is out of scope per investigation.md — wound
  `speed_penalty` is documented as computed-but-unread, and this ticket must not silently start
  reading it).
- **PH8 `replace()` regression guard**: test 3 above doubles as a guard against a future
  regression re-introducing the silent-drop bug (e.g. if the PH8 block is refactored again by a
  later ticket) — keep it in the permanent suite (`test_readiness_regen.py`), not as a throwaway.
- **COMB-298 non-regression**: `test_readiness_regenerates_passively_per_tick` and
  `test_readiness_speed_survives_to_readonly_reconstruction` (both still referenced by COMB-298's
  `test_path`) must keep passing unmodified — they pass an explicit `readiness_speed=` override
  and never touch the new derivation path, so they should be unaffected by construction; running
  them is the direct guard that COMB-298 remains `verified` without needing its own text edited.
- **Class-tier / breakthrough non-interaction guard**: run `test_class_tiers.py` and
  `test_breakthroughs.py` to confirm the new `readiness_speed=derived.get(...)` kwarg addition to
  `apply.py`'s `replace(new_com, ...)` call does not disturb the unrelated `class_id`/breakthrough
  fields that same call site also sets — a copy-paste error in that edit is the highest-risk single
  line in this ticket per investigation.md.
