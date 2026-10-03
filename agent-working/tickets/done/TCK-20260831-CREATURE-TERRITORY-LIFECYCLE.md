---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260831-CREATURE-TERRITORY-LIFECYCLE
phase: done
date: 2026-08-31
tags: [world, ecology]
---

# TCK-20260831-CREATURE-TERRITORY-LIFECYCLE

## Title
Creature Territories & Simple Life Cycles

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Creature Territories & Simple Life Cycles. Investigation confirmed this is substantial new subsystem work, not small wiring: monsters get zero biological simulation today, since BiologicalSystem gates hunger/sleep decay to entity.kind in [HERO, VILLAGER] only. CampService already couples camp maturity growth to regional trauma (trauma_score>50.0 -> maturity delta x1.5, matching Mechanics Bible Ch5 §2's exact threshold) — a real existing precedent for the SHAPE of tuning this idea needs, though not the actual per-species numeric values, which are genuinely free creative territory.

## Scope
- Build a creature life-cycle/territory maturity system applying a per-tick maturity delta to monster-kind entities anchored to a camp/territory, increasing when the owning region's trauma_score>50.0, reusing CampService's existing 1.5x multiplier shape.
- Add life-stage transition or new-territory-occupant spawning when creatures reach a defined maturity/age threshold.
- Explicitly decide whether the existing HERO/VILLAGER-only biological gate is respected (monsters stay outside generic hunger/sleep) or superseded, recording any supersession in docs/guidelines/intentional_divergences.md.
- Author per-species pacing constants as real inspectable content and pass at least one metamorphic directional check (region trauma increase does not decrease maturity growth rate) — a good candidate to run through the metamorphic lab tooling once proven working by the pilot ticket.
- Ship behind a FeatureMode flag, default OFF.
- Independently verify no hidden live consumer of CampState/maturity fields exists before extending them, since the atlas has no Cross-Cutting Risk table entry for this idea at all.

## Out of Scope
- Generic hunger/sleep biological simulation expansion beyond monster-kind entities.
- Any change to CampService's existing trauma-to-maturity multiplier for camps themselves — reused, not modified.

## Acceptance Criteria
- [x] A creature life-cycle/territory maturity system applies a per-tick maturity delta to monster-kind entities anchored to a camp/territory, increasing when owning region's trauma_score>50.0 (reusing CampService's existing 1.5x multiplier), verified by a deterministic test comparing trauma<=50 vs trauma>50 regions.
- [x] Creatures reaching a defined maturity/age threshold transition life stage or spawn a new territory occupant, verified by a test advancing tick state past the threshold.
- [x] The existing HERO/VILLAGER-only biological gate is either respected (monsters stay outside generic hunger/sleep) or superseded with an explicit intentional_divergences.md entry.
- [x] Per-species pacing constants are real inspectable content and pass at least one metamorphic directional check (region trauma increase does not decrease maturity growth rate).
- [x] Ships behind a FeatureMode flag, default OFF.

## Related Tickets
None.

## Related Docs
- docs/mechanics/05_world_evolution.md
- docs/parity_ledger/world_dynamics.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/world/camp.py
- src/systems/lifecycle_systems/biological.py
- src/engine/world_dynamics.py

## Assumptions / Open Questions
- No Cross-Cutting Risk table entry exists for this idea at all — a gap in the atlas's own risk pass; this ticket should independently verify no hidden live consumer of CampState/maturity fields before extending them.
- Per-species numeric pacing has zero anchor anywhere — genuinely free creative territory per Content & Balance Requirements.

## Implementation Notes

Implemented exactly per `staging_artifacts/TCK-20260831-CREATURE-TERRITORY-LIFECYCLE/plan.md`'s
7 steps, no deviations:

1. **Durable field** — added `territory_maturity: float = 0.0` to `IdentityComponent`
   (`src/core/state.py`), included it in `IdentityComponent.to_canonical_dict()`, added
   `territory_maturity_delta: float = 0.0` to `IdentityUpdate` (`src/core/updates.py`), and wired
   it into all three silent-drop points per CLAUDE.md's explicit warning: `IdentityUpdate.is_noop()`,
   `IdentityUpdate.merge()`, and `IdentityPatch.apply()`'s `replace(...)` kwargs
   (`src/engine/patches.py`) — confirmed via a full `ApplyPath.apply_generation()` round-trip test,
   not just isolated `.apply()`.
2. **Feature flag** — registered `ENABLE_CREATURE_TERRITORY_LIFECYCLE: FeatureMode.OFF` in
   `FeatureFlagManager.__init__` (`src/domains/optimization/feature_flags.py`), following the
   DEV-002 default-OFF policy convention (comment cites this ticket, no corpus/SHADOW evidence
   exists for a brand-new mechanic).
3. **New `CreatureTerritoryService`** (`src/world/creature_territory.py`, new file) — mirrors
   `CampService`'s trauma-multiplier shape without importing or modifying it. Per-species pacing
   table `TERRITORY_MATURITY_RATES` (`goblin_warrior: 0.04`, `orc_warrior: 0.03`) with a
   `DEFAULT_TERRITORY_MATURITY_RATE = 0.03` fallback. Anchoring is proximity-only (same 10x10 box
   check as `camp.py`), filtered via `entity.identity.role == EntityRole.MONSTER` (never
   `entity.kind` string matching).
4. **Threshold spawn** — same file/method: when an entity's `territory_maturity` would cross
   `TERRITORY_MATURITY_THRESHOLD = 100.0` on a tick, spawns a same-kind occupant via
   `generator.spawn_monster(...)` and resets that entity's emitted delta to
   `-current_maturity` (exact reset to 0.0, not a cap), monotonic exactly-once crossing enforced
   via the `new_maturity >= threshold and current_maturity < threshold` guard.
5. **Wiring** — added `# 3.9 Creature Territory Lifecycle` sub-step to `world_dynamics.py`'s
   existing cadence-gated macro-dynamics block, directly after `# 3.8 Seasonal calamity pressure
   propagation`, reading the flag off `state.feature_flags` (matching
   `ENABLE_GUILD_QUEST_GENERATION`'s pattern) and merging the result via `update.merge(...)` — the
   existing `update.replace(...)` call at the top of the block was left untouched, per the
   ticket's explicit instruction.
6. **Architecture guard test** — `test_monster_kind_entities_remain_outside_generic_biological_needs`
   asserts the new service never emits a `BiologicalUpdate`. AC #3 is satisfied by construction
   (additive-only design); confirmed `BiologicalSystem.update()` is dead code with zero production
   callers and the real live hunger/sleep/age path (`ApplyPath._compute_entity_changes`) is
   untouched, so no `docs/guidelines/intentional_divergences.md` entry was needed (nothing is being
   superseded — matches the plan's AC #3 resolution).
7. **Docs/parity** — added a "Creature Territory Lifecycle" subsection under §6 of
   `docs/mechanics/05_world_evolution.md`, and appended `WORLD-118` / `WORLD-119` to
   `docs/parity_ledger/world_dynamics.yaml` (both `status: verified`, `priority: P2`, real
   `test_path`s). Validated with `tools/validate_frontmatter.py` and a direct jsonschema check of
   the two new entries against `docs/parity_ledger/schema.json` (the file's one pre-existing schema
   violation, `WORLD-CULT-003`'s id pattern, predates this ticket and was left untouched).

No new abstractions beyond what the plan specified; `src/world/camp.py` and
`src/systems/lifecycle_systems/biological.py` were not modified.

**Deviation — post-Implement bug fix (Test phase, 2026-09-01):** `src/engine/apply.py` *was*
modified after all, to fix a real gap the Test phase caught. Two tests failed with
`AttributeError: 'IdentityComponent' object has no attribute 'territory_maturity'`:
`tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell` and
`tests/integration/pipeline/test_transaction_completion.py::TestQuestRewardAtomicity::test_quest_reward_retry_after_freeing_inventory`.

Root cause: `ApplyPath._fast_replace_identity` (`src/engine/apply.py:515-537`) hand-builds a new
`IdentityComponent` via `object.__new__` + one `object.__setattr__` call per field, entirely
bypassing `__init__`/`dataclasses.replace()`. It was never updated to carry `territory_maturity`
through. `IdentityPatch.apply()` (`src/engine/patches.py:224-225`) takes this fast path instead of
the normal `replace()` path whenever an `EntityUpdate` carries only `intent_results` (no
identity/group_id/property delta) — exactly the shape emitted by a shop buy/sell or quest-reward
intent. Every such update silently reset `territory_maturity` to the field's unset slot state
rather than the field's own default, and any later read of the attribute raised `AttributeError`
(since the component was built via `object.__new__`, which skips dataclass field defaults
entirely — there is no fallback to `0.0`).

This is a **fourth** silent-drop point, distinct from the three (`IdentityUpdate.is_noop()`,
`IdentityUpdate.merge()`, `IdentityPatch.apply()`'s main `replace()` kwargs) the plan's Step 1
identified and wired correctly. The plan's Step 1 change note *did* look at this exact fast-path
branch (`"Also check the fast-path branch at line 222 ... this path is only taken when
self.identity is falsy, so it never needs to apply a territory_maturity_delta and is
unaffected"`) but drew the wrong conclusion: it's true the fast path never needs to *apply a
delta* (there is no `IdentityUpdate` to read one from on this path), but the fast path still
*reconstructs the entire component from scratch* field-by-field, and any field missing from that
reconstruction is dropped outright — not "unaffected." The Step 1 integration test
(`test_new_maturity_field_survives_apply_generation_round_trip`) drove an identity-delta update
(`IdentityUpdate(territory_maturity_delta=5.0)`), which takes the normal `replace()` path, not the
fast path — so it could not have caught this.

**Fix applied:** added `object.__setattr__(res, "territory_maturity", id_comp.territory_maturity)`
to `_fast_replace_identity` (`src/engine/apply.py`), in the same field position as the dataclass
declaration (between `unspent_ap` and `class_id`), carrying the source component's current value
through unchanged — matching the pattern of every other field on this path, since this fast path
by definition applies no identity-affecting delta.

**New regression test added:**
`tests/unit/world/test_creature_territory_lifecycle.py::test_fast_replace_identity_preserves_territory_maturity_on_intent_only_update`
— constructs an `EntityUpdate` with only `intent_results` set (no `identity`/`group_id_set`/
`property_updates`), calls `ApplyPath.apply_generation()` directly, and asserts
`territory_maturity` survives. Verified this test fails with the exact reported `AttributeError`
when the fix is reverted (confirmed via `git stash` before finalizing), and passes with it
applied.

Both originally-failing tests (`test_shop_buy_and_sell`,
`test_quest_reward_retry_after_freeing_inventory`) now pass, along with the full existing
`test_creature_territory_lifecycle.py` suite (13/13), `test_component_patch_apply_parity.py`, and
`test_transaction_completion.py` (40 tests total, all passing).

## Test Summary

New tests, all passing (`.venv/bin/python3 -m pytest`):
- `tests/unit/world/test_creature_territory_lifecycle.py` (12 tests, new file): trauma-scaling
  (AC #1), per-species pacing table inspectability + 6-sample parametrized metamorphic directional
  check across the 50.0 threshold boundary (AC #4), threshold-crossing spawn + exact-reset-to-zero
  (AC #2), flag-ON activation, flag-default-OFF byte-for-byte no-op parity, and the AC #3
  architecture guard (no `BiologicalUpdate` ever emitted).
- `tests/integration/optimization/test_component_patch_apply_parity.py::test_new_maturity_field_survives_apply_generation_round_trip`
  (new test in existing file): full `ApplyPath.apply_generation()` round-trip proving the field
  survives all three wiring points.

Regression checks run and passing:
- `tests/unit/world/test_camp_lifecycle.py` (all 3) — confirms `CampService`'s own
  `maturity_delta == 0.075` output is unchanged.
- `tests/unit/world/test_world_dynamics.py`, `tests/unit/core/test_biological.py`,
  `tests/unit/engine/`, `tests/integration/optimization/` (200 passed, 1 skipped) — no regressions
  from the `IdentityComponent`/`IdentityUpdate`/`IdentityPatch` field additions.
- `tests/ -k feature_flag` (126 passed) — no regression from the new flag registration.

**Test-phase fix (2026-09-01):** `ApplyPath._fast_replace_identity` was missing `territory_maturity`
(4th silent-drop point, see Implementation Notes). Added
`test_fast_replace_identity_preserves_territory_maturity_on_intent_only_update` to
`tests/unit/world/test_creature_territory_lifecycle.py` (now 13 tests, all passing), driving an
intent-only `EntityUpdate` through `ApplyPath.apply_generation()` directly. Confirmed via
`git stash` that this test fails with the exact reported `AttributeError` when the fix is reverted.
Re-ran and confirmed passing:
`tests/unit/world/test_economy_contract.py::test_shop_buy_and_sell`,
`tests/integration/pipeline/test_transaction_completion.py::TestQuestRewardAtomicity::test_quest_reward_retry_after_freeing_inventory`,
and the full set (`test_creature_territory_lifecycle.py` + `test_economy_contract.py` +
`test_transaction_completion.py` + `test_component_patch_apply_parity.py`, 40 passed).

## Files Changed
- `src/core/state.py` — `IdentityComponent.territory_maturity` field + `to_canonical_dict()` entry
- `src/core/updates.py` — `IdentityUpdate.territory_maturity_delta` field + `is_noop()`/`merge()`
- `src/engine/patches.py` — `IdentityPatch.apply()` reads/applies/emits `territory_maturity`
- `src/engine/apply.py` — **(Test-phase fix)** `ApplyPath._fast_replace_identity` now carries
  `territory_maturity` through; this is the 4th silent-drop point, found post-Implement
- `src/domains/optimization/feature_flags.py` — registers `ENABLE_CREATURE_TERRITORY_LIFECYCLE` (OFF)
- `src/world/creature_territory.py` — new file, `CreatureTerritoryService`
- `src/engine/world_dynamics.py` — new flag-gated `# 3.9 Creature Territory Lifecycle` sub-step
- `tests/unit/world/test_creature_territory_lifecycle.py` — new file, 13 tests (12 original + 1
  Test-phase regression test for the `_fast_replace_identity` gap)
- `tests/integration/optimization/test_component_patch_apply_parity.py` — 1 new test
- `docs/mechanics/05_world_evolution.md` — new subsection under §6
- `docs/parity_ledger/world_dynamics.yaml` — new entries `WORLD-118`, `WORLD-119`
- `staging_artifacts/TCK-20260831-CREATURE-TERRITORY-LIFECYCLE/plan.md` — Deviations section added
  documenting the 4th silent-drop point found during Test
- `tickets/inprogress/TCK-20260831-CREATURE-TERRITORY-LIFECYCLE.md` — this file

## Completion Summary
Implemented `CreatureTerritoryService`, a new parallel-to-`CampService` system giving monster-kind
entities anchored by proximity to a camp a per-tick `territory_maturity` value that grows faster
(x1.5) in regions with `trauma_score > 50.0`, reusing `CampService`'s exact multiplier shape. When
an entity's maturity crosses a fixed threshold (100.0) it spawns a same-kind territory occupant and
resets to zero. The new durable field was wired through all three `IdentityUpdate`/`IdentityPatch`
silent-drop points that bit two prior tickets this session. The whole mechanic ships fully behind
`ENABLE_CREATURE_TERRITORY_LIFECYCLE`, default OFF, called from `world_dynamics.py`'s existing
cadence-gated block via `update.merge(...)` (the block's pre-existing `update.replace(...)` call was
left untouched). All 5 acceptance criteria are met and verified by new tests; docs and the parity
ledger were updated in the same session.

**Test-phase follow-up (2026-09-01):** the Test phase surfaced a real gap the original
implementation missed: `ApplyPath._fast_replace_identity` (`src/engine/apply.py`) — a separate,
hand-built `IdentityComponent` constructor used only when an `EntityUpdate` carries `intent_results`
with no identity/group/property delta (the shape of a shop buy/sell or quest-reward intent) — never
carried `territory_maturity` through, causing `AttributeError` on any later read. This was a fourth
silent-drop point beyond the three the plan's Step 1 wired correctly. Fixed by adding the missing
field to that constructor; added a targeted regression test exercising the fast path directly;
confirmed both originally-failing tests now pass. See Implementation Notes above for full detail.
