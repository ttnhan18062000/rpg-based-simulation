---
status: historical
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION
phase: done
date: 2026-08-31
tags: [architecture]
---

# TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION

## Title
Unify status_frozen/stunned and interaction_kind into a typed StatusEffectState

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
This was misclassified in the epic as small 'orphan wiring' work under Design Idea 4, but investigation found it is real architecture work: status_frozen/status_stunned and interaction_kind are stored in untyped identity.properties/property_updates dicts and read by a wider blast radius than the atlas's own count (5 real consumers for status flags, 7 for interaction_kind). The fix is a new typed StatusEffectState record following the already-proven WoundState/ScarState precedent.

## Scope
- Add a new typed StatusEffectState frozen dataclass (source, magnitude, expires_tick) to src/core/state.py, following the WoundState/ScarState precedent (already proven to generalize per TCK-20260824-TACTICAL-WOUND-SCAR-WIRING).
- Migrate status_frozen and status_stunned off identity.properties.get() in all 5 real consumer files (src/engine/combat.py, src/engine/legality.py, src/engine/pipeline_phases/actor_validity.py, src/systems/strategic_systems/intelligence.py, src/systems/strategic_systems/work_queue.py), with behavior provably unchanged for entities with no active status.
- Migrate interaction_kind off property_updates in all 7 real consumer files (src/actions/harvest.py, src/actions/loot.py, src/systems/world_systems/harvesting.py, src/systems/economy_systems/chests.py, src/systems/economy_systems/town_service.py, src/systems/economy_systems/loot.py, src/systems/social_systems/guilds.py).
- Explicitly decide whether closing the docs/architecture/cognition_domain_ownership.md EmotionalModel ownership-row gap is in scope for this ticket.

## Out of Scope
- Re-wiring EmotionUpdateService.update_on_event() for event_kinds beyond 'near_death' — already wired for that kind by TCK-20260824-WIRE-ORPHANED-MECHANISMS; do not duplicate work that's already done.
- PerceptionModel, EmotionalModel, and TemporalModel fields in cognition.py that are genuinely written by real pipeline phases — not part of this migration.

## Acceptance Criteria
- [x] A new StatusEffectState typed record exists following the WoundState/ScarState precedent.
- [x] status_frozen (and status_stunned, same call sites) migrated off identity.properties.get() in all 5 real consumer files with behavior provably unchanged for entities with no active status.
- [x] interaction_kind migrated off property_updates in all 7 real consumer files (via `InteractionComponent.kind`/`InteractionUpdate.kind`, per plan.md's architecture-review-mandated correction from the literal "into StatusEffectState" scope text — see Implementation Notes).
- [x] docs/architecture/cognition_domain_ownership.md gains an EmotionalModel row ONLY IF this ticket's scope touches EmotionUpdateService migration (optional, state explicitly) — condition not met: this ticket never touches EmotionUpdateService/EmotionalModel, so no doc row was added, per plan.md's Acceptance Criteria Map.

## Related Tickets
- TCK-20260824-TACTICAL-WOUND-SCAR-WIRING
- TCK-20260824-WIRE-ORPHANED-MECHANISMS
- TCK-20260429-E3-MISSING-LOGIC

## Related Docs
- docs/architecture/cognition_domain_ownership.md (examined at Investigation; EmotionalModel
  ownership-row gap confirmed real but out of this ticket's scope — condition for AC #4 not met, no
  edit made)
- docs/mechanics/damage_formula_contract.md (Step 5a — SHATTER condition cell and worked example
  updated to the new `status_effects` read expression, verified accurate against `combat.py`)
- docs/core/state.md (Document-Update phase — `Combat` row's Key Fields updated to include
  `status_effects`; new `Interaction` row added to the Key Components table for `target_node_id`,
  `progress`, `start_tick`, `kind`, since this component previously had no table row at all despite
  now carrying newly-significant durable state via `InteractionComponent.kind`)

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/engine/combat.py
- src/engine/legality.py
- src/engine/pipeline_phases/actor_validity.py
- src/systems/strategic_systems/intelligence.py
- src/systems/strategic_systems/work_queue.py
- src/actions/harvest.py
- src/actions/loot.py
- src/systems/world_systems/harvesting.py
- src/systems/economy_systems/chests.py
- src/systems/economy_systems/town_service.py
- src/systems/social_systems/guilds.py
- src/systems/economy_systems/loot.py

## Assumptions / Open Questions
- Blast radius is wider than the atlas's own '6 more' count — 5 consumer files for status flags plus 7 for interaction_kind.
- The atlas's 'EmotionUpdateService never called from production' finding is now partially stale — it is already wired for one event_kind ('near_death'); do not re-wire what's already wired.
- The cognition_domain_ownership.md EmotionalModel ownership-row gap remains real and unaddressed — this ticket must decide whether closing it is in scope.

## Implementation Notes

Implemented plan.md's all 15 steps (1-14 plus 5a) exactly as specified, with two deliberate
corrections already baked into the approved plan (both architecture-review-mandated, not new
deviations by this implementer):

1. **`interaction_kind` lands on `InteractionComponent.kind` / `InteractionUpdate.kind`, NOT
   `StatusEffectState`.** This corrects the ticket's own literal Scope/Title wording ("unify...
   into a typed StatusEffectState"). Both producers (`harvest.py`, `loot.py`) always set
   `interaction_kind`/`target_node_id` together, and all 7 consumers always read them together —
   the field belongs on the record that already tracks the multi-tick interaction. AC #3's literal
   text ("interaction_kind migrated off property_updates in all 7 real consumer files") does not
   name a target record, so it is satisfied by `InteractionComponent.kind`.
2. **`status_frozen`/`status_stunned` clean-cutover, no compatibility shim** — investigation
   confirmed zero production writers exist for these two flags today (only test fixtures), so a
   dual-read shim would add real complexity (5 consumer files) to protect a non-existent production
   path. All 13 status-flag test fixtures + 2 interaction_kind test fixtures were migrated to the
   new typed construction in the same commit as the consumer-file migration (no fallback/OR-read of
   the old dict key remains anywhere in `src/` or `tests/`).

Key implementation details:

- `StatusEffectState` (kind/source/magnitude/expires_tick) added to `src/core/state.py` immediately
  after `ScarState`, `frozen=True, slots=True`, matching `WoundState`'s plain-`str`-with-comment
  convention for `kind` (no enum/`Literal` runtime validator).
- `CombatComponent.status_effects: List[StatusEffectState]` added alongside `wounds`/`scars`, with a
  `"status_effects": [asdict(s) for s in self.status_effects]` entry in
  `CombatComponent.to_canonical_dict()` — this closes the canonical-hash coverage gap (investigation
  Risk #1) since `EntityState.to_canonical_dict()` already feeds off `CombatComponent`'s dict, no
  further change needed there.
- `InteractionComponent.kind: Optional[str] = None` added with a `"kind": self.kind` canonical-dict
  entry — same closure logic for the interaction-kind half.
- `StatusEffectUpdate` (`effects_add`/`effects_remove` by `kind` string, no per-instance ID field —
  `StatusEffectState` deliberately has none) and `StatusEffectPatch` (registered in
  `extract_patches()` immediately after `WoundPatch`, same `changes["combat"]` merge pattern) added
  following the `WoundUpdate`/`WoundPatch` precedent exactly. `StatusEffectPatch` is explicitly NOT
  wired into `_apply_entity_update_to_dict`'s `stats_dirty` trigger — `SkillScalingService
  .get_effective_stats` has no `status_effects` parameter and no consumer reads
  magnitude/source/expires_tick (confirmed zero readers by investigation), so wiring it would
  recompute stats for a state change nothing consumes.
- `InteractionUpdate.kind` added with `is_noop()`/`merge()` following the existing `target_node_id`
  pattern; `InteractionPatch.apply()`'s non-reset branch now carries `kind` through `replace(...)`.
  The `reset=True` branch already replaces the whole component (pre-existing code, untouched), so
  `kind` clears for free on reset — an intentional, provably-inert behavior change from the old
  merge-only `identity.properties` dict (which never cleared `interaction_kind` on reset); pinned by
  `test_interaction_patch_apply_reset_clears_kind` in `test_component_patches.py`.
- All 5 status-flag consumer call sites (`legality.py` x4, `combat.py` x1 — the SHATTER check,
  `actor_validity.py` x2, `work_queue.py` x1, `intelligence.py` x3) migrated to
  `any(s.kind in (...) for s in <entity>.combat.status_effects)` inline at each call site (no
  helper method added to `CombatComponent`, matching how wounds/scars are read inline elsewhere).
  SHATTER semantics preserved exactly: only `kind == "frozen"` on the *defender* triggers
  `atk_mult *= 1.5` / `trace["SHATTER"] = 1.5`; `stunned` never triggers it, verified by both the
  positive case and a new asymmetry case embedded in `test_shatter_logic` itself (SHATTER absent for
  a stunned-only defender) plus a no-active-status baseline case in the same test (verbatim per plan
  Step 13, which named `test_shatter_logic` at `test_combat_legality_regression.py:46` as the real
  location — test_plan.md's original `test_direct_combat_outcomes.py` guess was corrected by plan.md
  during Plan and confirmed absent from the repo).
- `actor_validity.py` ends this migration with a deliberate hybrid read: `is_stunned`/`is_frozen`
  now read `combat.status_effects`, but `is_sleeping` still reads
  `entity.identity.properties.get("status_sleeping", False)` — left untouched, explicitly out of
  scope per the ticket and plan.md's Scope Guards. The class docstring's Invalid-means bullet list
  was updated in place (`status_stunned is True` → "a 'stunned' StatusEffectState is present...") for
  accuracy, since it now describes storage that no longer exists as a literal dict key — a doc-only
  clarification, not a behavior change, and not one of the 15 numbered plan steps.
- The 2 producers (`harvest.py`, `loot.py`) now set `kind` via `InteractionUpdate(kind=...)` instead
  of `property_updates={"interaction_kind": ...}`; `harvest_duration` (harvest.py) is untouched and
  stays in `property_updates` (adjacent-but-out-of-scope key, per Scope Guards).
- The 5 interaction_kind consumer files (`harvesting.py`, `chests.py`, `loot.py`
  economy_systems, `town_service.py`, `guilds.py`) now read `entity.interaction.kind` instead of
  `entity.identity.properties.get("interaction_kind")`, preserving the `target_node_id is not None`
  gate unchanged and preserving all 7 closed-set values including the 4 never-produced ones
  (`chest`/`guild`/`inn`/`tavern`) — no new production writer was added for any of the 4, matching
  Scope Guards.
- **Step 5a doc fix applied**: `docs/mechanics/damage_formula_contract.md` line 72 (multiplicative
  modifiers table, Frozen/Shatter row) and line 224 (Shatter worked example, Defender line) both
  updated to the exact new read expression / typed-storage form, verbatim per plan.md — no
  paraphrase, matching the migrated `combat.py:84` expression exactly.
- **Step 14 (parity ledger, discretionary)**: grepped all 4 named ledger files
  (`combat_movement.yaml`, `town_resource.yaml`, `strategic_cognition.yaml`,
  `social_narrative.yaml`) for `status_frozen`/`status_stunned`/`interaction_kind`/
  `ATTACKER_STATUS_BLOCKED` — zero hits in all 4, confirming investigation's finding that no
  existing entry names these fields and none becomes stale through this migration (internal read
  expressions changed, not file paths or function signatures any entry cites). Decision: no ledger
  entry added, per plan.md's explicit "no ledger entry is required by this migration" call — this is
  the plan's own documented decision, not a gap.
- Ran `graphify update .` after all `src/`/`tests/` edits — AST re-extraction reported "no code-graph
  topology changes detected," so no further graph action needed.

## Test Summary

New tests added:
- `tests/unit/core/test_state_status_effect.py` (new, Step 11) — 3 tests: frozen-dataclass
  mutation guard, default field values, `asdict()` round-trip.
- `tests/unit/core/test_canonical_hash_status_effect.py` (new, Step 13) — 2 tests: confirms
  `EntityState.to_canonical_dict()` differs when `status_effects`/`interaction.kind` are set vs.
  empty/`None` (closes the determinism-hash coverage gap from investigation Risk #1).
- `tests/unit/domains/optimization/test_component_patches.py` (extended, Step 13) — 6 new tests:
  `StatusEffectPatch` noop/add/remove/merge + `extract_patches` inclusion, and 2 `InteractionPatch`
  tests (`kind` set on non-reset apply, `kind` cleared on `reset=True`).
- `tests/unit/combat/test_combat_legality_regression.py::test_shatter_logic` (extended, Step 13) —
  now covers 3 cases in one test: no-active-status baseline (no SHATTER), frozen defender (SHATTER
  1.5x, original assertion unchanged), stunned-only defender asymmetry (no SHATTER).
- `tests/unit/core/test_hardening_e5.py` — added
  `test_negative_case_no_active_status_actor_not_blocked` (no-active-status baseline for
  `ActorValidityPhase`, next to the existing `test_negative_case_stunned_actor_rejection`).
- `tests/unit/domains/optimization/test_strategic_work_queue.py` — added
  `test_strategic_queue_excludes_frozen_and_stunned_entities` (frozen/stunned excluded from the
  eligible set; a no-status baseline entity remains eligible in the same test).
- `tests/unit/world/test_town_services.py` — added `test_guild_service_routes_via_interaction_kind`
  and `test_unrelated_interaction_kind_not_routed` (extends interaction_kind value-set coverage to
  "guild" through `TownServiceSystem` and confirms a non-matching kind is not routed).
- `tests/unit/world/test_chest_lifecycle.py` — added
  `test_chest_looting_ignores_non_chest_interaction`.
- `tests/unit/world/test_guild_intel.py` — added
  `test_guild_intel_ignores_non_guild_interaction`.

13 status-flag + 2 interaction_kind test fixtures migrated (clean cutover, assertions unchanged):
`test_phase5_combat_legality.py`, `test_combat_legality_regression.py`, `test_rpg_core_recovery.py`,
`test_phase5_negative_cases.py` (3 sites), `test_tactical_hardening.py`, `test_status_hardening.py`
(2 sites), `test_hardening_e5.py`, `test_chest_lifecycle.py`, `test_guild_intel.py`. Two additional
production-consumer-backed fixture files found beyond plan.md's Step 12 list (both use
`interaction_kind` against real consumers — `test_town_services.py` for `town_service.py`, and the 2
integration conservation tests for `harvesting.py`/`loot.py` economy_systems) were also migrated:
`tests/unit/world/test_town_services.py` (2 sites), `tests/integration/kernel/
test_resource_conservation.py` (3 sites), `tests/integration/kernel/test_resource_conservation_v2.py`
(1 site).

Test runs (all via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest`):
- `tests/unit/combat/test_combat_legality_regression.py::test_shatter_logic` — 1 passed.
- `tests/unit/domains/optimization/test_component_patches.py` — 17 passed.
- Combined scoped sweep (all 5 status-flag consumer test files + all interaction_kind consumer test
  files + resource-conservation integration + harvest/loot channeling + work_queue + new schema/
  canonical-hash tests) — 75 passed.
- `tests/unit/combat/ -m "not slow"` — 113 passed.
- `tests/unit/strategic/ -m "not slow"` — 287 passed.
- `tests/unit/world/ tests/unit/resource/ tests/unit/domains/optimization/ tests/unit/core/
  -m "not slow"` — 699 passed.
- `tests/unit/engine/ tests/unit/actions/ tests/engine/ -m "not slow"` — 204 passed, 1 skipped, 3
  deselected (pre-existing, unrelated to this migration).
- `tests/integration/kernel/ -m "not slow"` — 92 passed, 3 deselected (pre-existing, unrelated).

Zero failures across all runs. Confirmed via repo-wide grep after all edits: zero remaining
`identity.properties.get("status_frozen"/"status_stunned")` reads, zero remaining
`"interaction_kind"` dict-key literals, anywhere in `src/` or `tests/` (the only surviving text hits
are a docstring line and a test comment, not code).

## Files Changed

**Core state/update/patch layer:**
- `src/core/state.py` — added `StatusEffectState` dataclass; added `status_effects` field +
  canonical-dict entry to `CombatComponent`; added `kind` field + canonical-dict entry to
  `InteractionComponent`.
- `src/core/updates.py` — added `StatusEffectUpdate`; wired `status_effect_update` onto
  `EntityUpdate` (`is_noop`/`merge`); added `kind` to `InteractionUpdate` (`is_noop`/`merge`).
- `src/engine/patches.py` — added `StatusEffectPatch`, registered in `extract_patches()`; updated
  `InteractionPatch.apply()` to carry `kind`.

**5 status-flag consumers:**
- `src/engine/legality.py` (4 call sites)
- `src/engine/combat.py` (1 call site — SHATTER)
- `src/engine/pipeline_phases/actor_validity.py` (2 call sites + docstring accuracy fix)
- `src/systems/strategic_systems/work_queue.py` (1 call site)
- `src/systems/strategic_systems/intelligence.py` (3 call sites)

**2 interaction_kind producers + 5 consumers:**
- `src/actions/harvest.py`, `src/actions/loot.py`
- `src/systems/world_systems/harvesting.py`, `src/systems/economy_systems/chests.py`,
  `src/systems/economy_systems/loot.py`, `src/systems/economy_systems/town_service.py`,
  `src/systems/social_systems/guilds.py`

**Docs:**
- `docs/mechanics/damage_formula_contract.md` (Step 5a, lines 72 and 224)
- `docs/core/state.md` (Document-Update phase — Combat row's Key Fields updated to include
  `status_effects`; new Interaction component row added)

**Parity ledger (Parity phase):**
- `docs/parity_ledger/combat_movement.yaml` — repaired stale `COMB-122` (SHATTER mechanic; had
  `priority: P0` with a broken `test_path` citing a test that no longer exists) with a real,
  passing `test_path`; added new `COMB-319` for the frozen/stunned action-blocking gate
  (legality.py/actor_validity.py), also P0 with a real `test_path`.
- `docs/parity_ledger/strategic_cognition.yaml` — added new `STRAT-265` for the
  strategic-work-queue frozen/stunned exclusion gate (intelligence.py/work_queue.py).

**New tests:**
- `tests/unit/core/test_state_status_effect.py`
- `tests/unit/core/test_canonical_hash_status_effect.py`

**Migrated/extended test fixtures and coverage:**
- `tests/unit/combat/test_phase5_combat_legality.py`
- `tests/unit/combat/test_combat_legality_regression.py`
- `tests/unit/combat/test_rpg_core_recovery.py`
- `tests/unit/combat/test_phase5_negative_cases.py`
- `tests/unit/combat/test_tactical_hardening.py`
- `tests/unit/strategic/test_status_hardening.py`
- `tests/unit/core/test_hardening_e5.py`
- `tests/unit/world/test_chest_lifecycle.py`
- `tests/unit/world/test_guild_intel.py`
- `tests/unit/world/test_town_services.py`
- `tests/integration/kernel/test_resource_conservation.py`
- `tests/integration/kernel/test_resource_conservation_v2.py`
- `tests/unit/domains/optimization/test_component_patches.py`
- `tests/unit/domains/optimization/test_strategic_work_queue.py`

**Ticket/staging artifacts (this run's own Investigate/Plan/Implement phases):**
- `tickets/inprogress/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION.md`
- `staging_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/investigation.md` (created this
  run, prior to Implement)
- `staging_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/plan.md` (created this run, prior
  to Implement)
- `staging_artifacts/TCK-20260831-STATUS-EFFECT-STATE-UNIFICATION/test_plan.md` (created this run,
  prior to Implement)

No deviations from plan.md — all 15 steps (1-14 plus 5a) implemented as specified, plus reasonable
additional test coverage (no-active-status baseline cases, 2 extra production-consumer-backed
fixture files found and migrated beyond plan.md's Step 12 enumeration) within Step 13's own stated
scope ("extend the existing files... in place").

## Completion Summary

Implemented the full StatusEffectState/InteractionComponent.kind typed-state migration per
plan.md's 15 steps: added `StatusEffectState` (source/magnitude/expires_tick, following the
WoundState/ScarState precedent) plus its full typed-update/patch write path
(`StatusEffectUpdate`/`StatusEffectPatch`), migrated all 5 real status_frozen/status_stunned
consumer files off `identity.properties` dict reads with SHATTER combat semantics provably
preserved, added `InteractionComponent.kind`/`InteractionUpdate.kind` (the architecture-review-
corrected home for `interaction_kind`, not `StatusEffectState`) and migrated both producers and all
7 real consumers off `property_updates`, updated `docs/mechanics/damage_formula_contract.md` per the
mandatory Step 5a doc-parity fix, and did a clean-cutover migration of all test fixtures with zero
compatibility shim (matching the zero-production-writer finding). All scoped test sweeps pass (75 +
113 + 287 + 699 + 204 + 92 = 1,470+ tests across the affected domains, zero failures), and a
repo-wide grep confirms zero old-style `status_frozen`/`status_stunned`/`interaction_kind`
reads-or-writes remain anywhere in `src/` or `tests/`.

**Document-Update phase**: independently re-verified the damage_formula_contract.md fix as accurate
against real `combat.py`; found and fixed two gaps the Implement self-report missed —
`docs/core/state.md`'s Key Components table (missing `status_effects` on the Combat row and missing
an Interaction row entirely) and this ticket's own Related Docs section (omitted
`damage_formula_contract.md`/`docs/core/state.md`). Two pre-existing, out-of-scope staleness issues
(`docs/core/entities.md`'s defunct Aspect-model vocabulary; `rpg_expected_schemas.html`'s rejected
`ModificationRecord` design-idea shape) were flagged, not touched.

**Architecture-Verify phase**: APPROVED. The static checker flagged 12 `object.__setattr__`
bypasses in `src/core/state.py` as `durable_state_mutation` FAILs; `git blame` confirmed all 12 are
pre-existing internal state-construction code untouched by this ticket's diff (false positives, a
disclosed limitation of the static checker's field-name-only allowlist). Independently re-verified
the `StatusEffectState`/`InteractionComponent.kind` shape, canonical-dict coverage, and the SHATTER
mechanic's new read expression against plan.md.

**Test phase** (independent re-scope, broader than Implement's own sweep): 1,708 passed, 0 failed,
1 pre-existing skip, across `tests/unit/core/`, `tests/unit/combat/`, `tests/unit/strategic/`,
`tests/unit/world/`, `tests/unit/domains/optimization/`, `tests/integration/kernel/`,
`tests/unit/engine/`, `tests/unit/actions/`, `tests/engine/`, plus three transitively-discovered
directories referencing `InteractionComponent` (`tests/unit/resource/`, `tests/unit/social/`,
`tests/integration/pipeline/`). Confirmed coverage gap (pre-existing, not new): `harvesting.py`/
economy `loot.py` have no dedicated unit test module, only indirect integration coverage.

**Parity phase**: repaired a stale, pre-existing `COMB-122` (P0 SHATTER entry with a broken
`test_path` citing a nonexistent test) and added `COMB-319` (frozen/stunned action-blocking gate)
and `STRAT-265` (strategic work-queue exclusion gate), both P0 with real passing `test_path`
citations. `faction.yaml`/`substrate.yaml`/`town_resource.yaml`/`world_dynamics.yaml`/
`progression.yaml` judged noise from `src/core/state.py` being a shared god-file — no entry added.
`interaction_kind`/`InteractionComponent.kind` left without a new ledger entry (no relevant existing
entry found; judged lower-value than the two real behavioral gates above) — flagged as open if
future work wants it covered.
