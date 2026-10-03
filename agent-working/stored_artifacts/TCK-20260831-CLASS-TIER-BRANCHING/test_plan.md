---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260831-CLASS-TIER-BRANCHING
artifact_type: test_plan
tags: [progression]
---

# Test Plan — TCK-20260831-CLASS-TIER-BRANCHING

## Regression Surface

**Unit — progression:**
- `tests/unit/core/test_class_registry.py` — must keep passing unchanged if the new tier registry lives in a separate module (`src/progression/class_tiers.py`, per investigation Risk #1's recommendation); if instead `ClassDefinition`/`CLASS_REGISTRY` itself is extended, every test here (`test_class_registry_lookup`, `test_explicit_warrior_class_application`, `test_explicit_mage_class_application`, `test_builder_stores_class_id_without_hidden_registry_application`) must still pass since they assert on today's exact 4-entry, no-tier shape.
- `tests/unit/progression/test_evolution.py` — `test_goblin_evolution`, `test_no_evolution_before_threshold`, and the rest of this file must be unaffected: `EvolutionSystem`'s `kind_set`/`_get_evolved_kind` linear-chain mechanism is untouched by this ticket (a separate mechanism, per the ticket's own framing of "generalize the pattern, not copy it").
- `tests/unit/progression/test_breakthroughs.py` — must keep passing unchanged; breakthroughs remain out of scope (Out of Scope: "Making breakthroughs mutually exclusive... a separate concept").
- `tests/unit/progression/test_leveling.py`, `tests/unit/progression/test_leveling_veterancy.py`, `tests/unit/progression/test_attribute_growth.py` — regression guard that `LevelingService`/`recalculate_combat_stats`/attribute-growth formulas are untouched.
- `tests/unit/core/test_rpg_depth.py` — covers `get_effective_stats()`/`stats_dirty` wiring (`TestSkillScaling`, `TestEffectiveStats`, `TestStaminaApplyIntegration`, `TestWoundApplyIntegration`); must keep passing since this ticket adds a new `stats_dirty` OR-clause branch (`class_id_set`) alongside the existing ones, not a rewrite.
- `tests/unit/entity/test_entity_archetypes.py::test_hero_archetypes_cover_combat_mage_rogue` — the PROG-108 `test_path`; must keep passing (asserts spawn-time class assignment only, no ticks run — see investigation Risk #5). If Plan decides to update its docstring for clarity, behavior must remain unchanged.

**Integration — apply path / updates:**
- `tests/integration/pipeline/test_recovery_gaps.py` — exercises the broader apply-path/`extract_patches` machinery `class_id_set`'s new `IdentityPatch` branch plugs into.
- Any existing `IdentityUpdate.merge()`/`is_noop()` coverage (search `tests/unit/core/` for `IdentityUpdate` construction) — must confirm the new `class_id_set` field doesn't break merge semantics for updates that don't set it (default `None` = noop, matching every sibling `*_set` field).

**Combat (for AC #4's win-rate check):**
- `tests/unit/*` combat-resolution tests covering `src/engine/combat.py`/`CombatResolutionSystem` — must remain green; the new win-rate comparison test is additive, not a replacement of existing combat-resolution unit tests.

## New Tests Required

Per acceptance criteria:

1. **AC #1 — class-tier registry defines ≥2 mutually-exclusive next-tier options per base class.**
   - Test name: `test_class_tier_registry_has_branching_options` (or per Plan's actual registry module name)
   - Category: unit
   - What it verifies: for at least one base class (e.g. `WARRIOR`), the registry returns/contains ≥2 distinct tier-option entries, each with a distinct `id`/`class_id` value, and confirms the registry is NOT a 1:1 linear mapping (i.e., assert `len(options) >= 2`, and assert no base class maps to exactly one hardcoded next value the way `EvolutionSystem._get_evolved_kind`'s dict does).
   - Where it should live: `tests/unit/progression/test_class_tiers.py` (new file, matching `test_breakthroughs.py`'s sibling naming convention) if the registry lands in `src/progression/`; otherwise added to `tests/unit/core/test_class_registry.py` if it extends `CLASS_REGISTRY` directly.

2. **AC #2 — `class_id_set` on `IdentityUpdate` authoritatively mutates `class_id` via the apply path.**
   - Test name: `test_class_id_set_applies_via_identity_patch`
   - Category: unit (apply-path integration, same style as `test_class_registry.py`'s builder-round-trip tests)
   - What it verifies: construct an `EntityState` with `class_id="WARRIOR"`, build an `EntityUpdate(identity=IdentityUpdate(class_id_set="WARRIOR_<TIER2_OPTION>"))`, run through `ApplyPath.apply_generation` (or `_apply_entity_update`, matching `test_evolution.py`'s pattern), assert `new_entity.identity.class_id == "WARRIOR_<TIER2_OPTION>"`. Also assert `IdentityUpdate(class_id_set=None).is_noop()` still returns True for the field's noop default, and that `merge()` correctly last-write-wins on `class_id_set` (mirroring the existing `evolution_level_set`/`life_stage_set` merge tests, if any exist as a pattern to follow).
   - Where it should live: `tests/unit/progression/test_class_tiers.py` or `tests/unit/core/test_updates.py` if such a file exists for `IdentityUpdate` unit coverage (check at Plan/Implement time; if no such file exists, colocate with test 1's new file).

3. **AC #2 (continued) — divergence from PROG-108 recorded.**
   - Not a pytest test — this AC is satisfied by a `docs/guidelines/intentional_divergences.md` entry (verified by `done-checker`'s doc-coverage check on the investigation's Docs Requiring Update bullets, not by a test). No test entry needed here, but note it explicitly so Plan/Implement doesn't treat it as covered by test 2 above.

4. **AC #3 — two entities with identical starting class/race but different branch-selection inputs end up with different `class_id`/tier state (test analogous to `test_goblin_evolution`).**
   - Test name: `test_branch_selection_diverges_class_id` (naming mirrors `test_goblin_evolution`'s "prove divergence from identical starting state" shape)
   - Category: unit, direct behavioral-divergence test
   - What it verifies: build two entities from identical starting state (same `class_id="WARRIOR"`, same level/attributes, via a shared builder helper analogous to `test_class_registry.py::make_class_entity`), apply two different branch-selection `EntityUpdate(identity=IdentityUpdate(class_id_set=<option_A>))` vs. `class_id_set=<option_B>)` through `ApplyPath.apply_generation`, and assert the two resulting entities' `identity.class_id` differ from each other AND both differ from the original `"WARRIOR"`. This is the direct AC #3 fraud-catcher: "same starting inputs diverge only because of different branch-selection input," matching `test_goblin_evolution`'s own stated "fraud this catches" framing.
   - Where it should live: `tests/unit/progression/test_class_tiers.py`.

5. **AC #4 — a tier's stat bonuses do not decrease average combat win-rate (metamorphic-style comparison).**
   - Test name: `test_tier_bonus_does_not_decrease_win_rate`
   - Category: integration (small custom metamorphic-style harness, not the full `src/lab/metamorphic.py` pipeline — see investigation Risk #4)
   - What it verifies: run N (e.g. 30-100, seeded/deterministic per-run) isolated combat resolutions between a fixed baseline opponent and (a) an entity at the pre-branch tier vs. (b) an identical entity post-`class_id_set` with the tier's attribute bonuses applied; assert win_rate(b) >= win_rate(a) (allowing for a small statistical tolerance if combat has any RNG component — confirm determinism/seeding requirements against `docs/engine/kernel.md`'s determinism law before finalizing the exact assertion, since the project's Hard Rules forbid breaking determinism). Uses `CombatResolutionSystem`/`src/engine/combat.py` directly, not the full `Kernel.tick_once()` loop, to keep the test fast and scoped.
   - Where it should live: `tests/integration/combat/test_class_tier_win_rate.py` (new file) or `tests/unit/progression/test_class_tiers.py` if Plan judges it lightweight enough to be a unit test — Plan should confirm which existing `tests/integration/` or `tests/unit/` combat-adjacent directory best fits, since no prior win-rate-style test exists to anchor the placement convention (investigation Risk #4).

6. **Guard test — tier bonuses expressed as attribute deltas, not combat-stat deltas (regression guard for investigation Risk #3).**
   - Test name: `test_tier_bonus_survives_subsequent_stats_dirty_event`
   - Category: unit, architecture/regression guard
   - What it verifies: apply a tier's `class_id_set` + attribute bonus, then trigger an unrelated `stats_dirty` event on the same entity (e.g. an AP spend or another attribute delta), and assert the tier's attribute-derived combat bonus (e.g. `atk`/`max_hp`) is still present after the second event — catching the exact "tier bonus silently wiped by the next stats_dirty recompute" failure mode identified in investigation Current Behavior #6/Risk #3, without requiring this ticket to fix that pre-existing bug (the guard just confirms the *chosen implementation shape* — attribute-level bonuses — correctly sidesteps it).
   - Where it should live: `tests/unit/progression/test_class_tiers.py`.

## Scoped Pytest Commands

```
# Core new/changed area
pytest tests/unit/progression/ tests/unit/core/test_class_registry.py -v

# Apply-path / IdentityUpdate regression surface
pytest tests/unit/core/ -k "identity or class or update or rpg_depth" -v

# Evolution system regression (must remain untouched)
pytest tests/unit/progression/test_evolution.py -v

# PROG-108 parity test
pytest tests/unit/entity/test_entity_archetypes.py -v

# New win-rate / combat integration test(s)
pytest tests/integration/combat/ tests/unit/progression/ -k "win_rate or tier" -v

# Full progression + core domain regression sweep before Verify
pytest tests/unit/progression/ tests/unit/core/ tests/integration/pipeline/test_recovery_gaps.py -m "not slow"
```

Never `pytest tests/` — scoped to `progression`/`core`/apply-path/combat domains per the file lists above.

## Anti-Drift Test Guards

- **Breakthroughs must stay additive and mutually-inclusive.** Add/keep a guard assertion (in `tests/unit/progression/test_breakthroughs.py` or a new cross-check in `test_class_tiers.py`) that granting a tier via `class_id_set` does not interact with or gate `active_breakthroughs`/`breakthroughs_add` — the two mechanisms must remain fully independent, per Out of Scope.
- **`EvolutionSystem`'s linear `_get_evolved_kind` mapping must not be touched or reused.** A regression test (or a code-review-level check, if not naturally testable) should confirm the new class-tier mechanism does not modify `src/engine/evolution.py`'s hardcoded kind-mapping dict — the ticket explicitly requires *generalizing the pattern*, not extending or repurposing the existing linear one.
- **`IdentityUpdate.is_noop()`/`merge()` must correctly no-op when `class_id_set` is absent.** A dedicated assertion (can be folded into test 2 above) that an `EntityUpdate` with no `class_id_set` produces no `KindPatch`/`IdentityPatch`-equivalent mutation and does not spuriously mark the entity dirty — guards against the `stats_dirty`-omission class of bug (investigation Current Behavior #6/Prior Work) recurring for the new field.
- **PROG-108's `test_hero_archetypes_cover_combat_mage_rogue` must not be silently loosened to tolerate mid-run branching it was never designed to allow.** If Plan/Implement touches this test at all (e.g. to add a clarifying docstring per investigation Risk #5), the guard is: the test's actual assertions (`hero_classes <= {"WARRIOR", "MAGE", "ROGUE"}`) must remain byte-identical, since it tests spawn-time-only compiled state, not apply-path mutation — any assertion loosening here is scope creep into re-validating spawn-time class assignment law, which this ticket does not touch.
- **`CLASS_REGISTRY`'s existing 4 entries (`NOVICE`, `WARRIOR`, `MAGE`, `ROGUE`) and their exact `base_hp`/`base_atk`/`base_def`/`starting_skills`/`starting_gear` values must be unchanged** unless Plan explicitly extends `ClassDefinition` itself (investigation Risk #1) — a guard re-running `test_class_registry.py`'s existing exact-value assertions (`w_defn.base_hp == 150`, etc.) after implementation catches any accidental base-stat drift introduced while wiring in tier data.
