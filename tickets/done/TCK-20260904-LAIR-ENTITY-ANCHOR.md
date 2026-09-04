---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-LAIR-ENTITY-ANCHOR
phase: open
date: 2026-09-04
tags: [content, determinism]
---

# TCK-20260904-LAIR-ENTITY-ANCHOR

## Title
Generalize Boss's entity-anchor idempotency pattern to Place-scoped Lair spawning

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 47 (Lair). Generalizes `BossService.check_for_boss_spawn`'s per-region entity-anchor idempotency pattern (`identity.properties["boss_region_id"]`, `src/world/boss.py`) to per-Place scoping using `PlaceState.occupant_entity_id` (kind=LAIR, already schema-frozen by idea 66 and documented as "reused from boss_region_id pattern"), since a Region can hold multiple LAIR Places where the old per-Region keying would collide.

## Scope
- Extend the `boss_region_id` idempotency pattern in `src/world/boss.py` to key off `PlaceState.occupant_entity_id` per LAIR-kind Place (`place_id`) instead of per-Region, so multiple LAIR Places within one Region each get independent, idempotent spawn tracking.
- Extend `tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region` to a Place-scoped variant proving idempotency holds across multiple LAIR Places in one Region.
- Add real LAIR-kind content to at least one world corpus profile, or a synthetic fixture, since no LAIR-kind Place exists in the current 21-world corpus (Stage B rollout explicitly declined to add one).

## Out of Scope
- Lair dissolution or transformation on occupant death — idea 47's own card wants this, but the mechanism belongs to idea 48 (place-type transitions), which has no ticket yet. This ticket must not silently assume or half-build that behavior.
- Writing the first-ever dedicated boss-spawn test suite from scratch — an idempotency test already exists (`test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`); this ticket extends/generalizes it to Place-scoping, it does not establish boss-spawn testing for the first time. Boss-spawn logic overall still has minimal dedicated test coverage beyond this — budget test-writing accordingly per the epic doc's depth-audit note.
- Any change to CampService/Camp-Nest classification (C1) or CampState/PlaceState bridging (C2).

## Acceptance Criteria
- [x] Lair spawn idempotency is keyed per-Place (via `PlaceState.occupant_entity_id` / `place_id`), not per-Region, and is proven not to double-spawn when multiple LAIR Places exist in the same Region. (Satisfied per plan.md Decision #1's documented AC reinterpretation: keyed by `place_id` via `identity.properties["lair_place_id"]`, the entity-property pattern generalized from `boss_region_id`; `PlaceState.occupant_entity_id` itself stays unwritten — Option A, explicitly accepted by architecture review.)
- [x] `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`-style coverage is extended (not replaced) to cover the Place-scoped case.
- [x] At least one real LAIR-kind Place exists in a chosen corpus world OR a synthetic fixture is added and clearly labeled as such, sufficient to exercise the new logic in tests.
- [x] Dissolution/transformation on occupant death is explicitly listed in Out of Scope in the ticket, with idea 48 named as the deferred owner — not silently omitted.

## Related Tickets
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/brainstorm/rpg_feature_atlas.html (idea 47)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/world/boss.py (check_for_boss_spawn, boss_region_id pattern)
- src/core/state.py (PlaceState.occupant_entity_id, PlaceKind.LAIR)
- tests/unit/world/test_world_dynamics.py

## Assumptions / Open Questions
- Idea 48 (place-type transitions) does not yet have a ticket — Lair dissolution-on-death depends on it and is explicitly deferred, not silently dropped.
- No real LAIR-kind Place exists in the current 21-world corpus; Stage B rollout explicitly declined to add one, so this ticket must add real content or a clearly-labeled synthetic fixture.
- Boss-spawn logic generally has minimal dedicated test coverage beyond the one idempotency test being extended — budget accordingly rather than assuming a mature test base.

## Implementation Notes
Implemented exactly per `staging_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/plan.md`'s 10 ordered
steps, Option A (entity-property keying, no new apply-path plumbing):

1. Added `BossService.check_for_lair_spawn` to `src/world/boss.py` as a direct sibling of
   `check_for_boss_spawn`, with local closures `_is_active_living_lair_occupant` (`entity.kind ==
   "dragonkin" and entity.lifecycle.active and entity.combat.alive`) and `_lair_place_id` (reads
   `entity.identity.properties.get("lair_place_id")`, deliberately no fallback layer since Lair
   occupancy is entirely new — no legacy occupants to support). Builds `place_occupant_map` by
   scanning `state.entities.values()`, keyed by `_lair_place_id(entity)`. Added a real (non-
   `TYPE_CHECKING`) `from src.core.state import PlaceKind` import since `place.kind != PlaceKind.LAIR`
   is a runtime comparison. `check_for_boss_spawn`/`_is_active_living_boss`/`_boss_region_id`/
   `region_boss_map` left byte-identical.
2. Spawn loop iterates `state.places.items()`, filters `kind == PlaceKind.LAIR`, skips places already
   in `place_occupant_map`, reads the parent Region via `state.regions.get(place.region_id)`, reuses
   the exact `state.maturity >= BossService.BOSS_SPAWN_THRESHOLD and region.trauma_score >= 20.0` gate
   (no new Place-local trigger condition). Spawns via `generator.spawn_monster(place.position,
   state=state, kind="dragonkin", difficulty_tier=5)`, tags `identity.properties["lair_place_id"]` +
   `"lair_spawn_tick"`. No `ancient_core` item stack, no `strategic.home_region_id` write, no post-hoc
   kind relabel — none of these have a Lair equivalent, so they're omitted rather than invented.
   Inherits the pre-existing, disclosed `difficulty_tier=5` → tier-1-stats fallback gap in
   `spawn_config.py`'s `DIFFICULTY_TIERS` (only has entries 1-4) — not fixed, out of scope, same gap
   `check_for_boss_spawn` already has today.
3. Extended `src/observability/event_extractor.py`'s two boss-kind exclusion lists (the
   `spawn_cadence_fired` tuple and `_BOSS_KINDS` frozenset) to include `"dragonkin"`, so newly-spawned
   Lair occupants are excluded from cadence-spawn misclassification and correctly emit `boss_spawned`.
   Only the two named rollback-path (`not _push_shapers_phase2_active`) lists touched; the live
   push-shapers path is untouched.
4. Wired `check_for_lair_spawn` into `WorldDynamicsSystem.resolve_dynamics`
   (`src/engine/world_dynamics.py`) as a new "3.4b Lair Spawning" block immediately after "3.4 Boss
   Spawning", reusing the same `cadence.boss_spawn` gate (no new `SystemCadence` field). Appended
   `lair_spawn_update.entities_add` as a sixth term to the existing five-source `entities_add`
   list-concatenation in the `update.replace(...)` call — no other field touched.
5. Added `test_lair_kind_place_compiles_via_worldcompiler` to
   `tests/unit/worldbuilding/test_place_wiring.py`, mirroring `_minimal_spec()` usage exactly;
   confirms `place.kind == PlaceKind.LAIR` and `place.occupant_entity_id is None`. Did not touch
   `test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds`'s locked
   `mountain_places == []` / `place_count == 3` assertions — synthetic fixture only.
6. Added three idempotency tests to `tests/unit/world/test_world_dynamics.py`, placed directly below
   `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`:
   `test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists`,
   `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region`,
   `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied`.
7. Added `test_lair_occupant_death_does_not_dissolve_or_transform_the_lair_place` (same file) — kills
   a Lair occupant, re-invokes `check_for_lair_spawn`, then asserts `PlaceState.kind`/`prior_kind`/
   `transformed_tick` were never mutated as a side effect. Passes trivially today, proving idea 48
   (dissolution-on-death) is genuinely not built.
8. Updated `docs/world/raid_boss_camp_contract.md`: added a "Lair — Place-scoped generalization"
   paragraph under the Boss "Idempotency" subsection, and a sub-bullet under "Extension rules" §3
   noting the per-`region_id` gap is now addressed for LAIR-kind Places specifically (region-scoped
   `world_boss` mechanism unchanged by design).
9. Updated parity ledger `WORLD-085` (P0, `docs/parity_ledger/world_dynamics.yaml`) via
   `tools/parity_ledger_writer.py::write_entry` (no raw YAML edit) — `status: verified` unchanged
   (the world-boss rule itself didn't change), `v2_evidence` updated to describe the new parallel
   Place-scoped mechanism, `test_path` set to
   `tests/unit/world/test_world_dynamics.py::test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`
   (the on-point passing test for WORLD-085's literal "boss spawn" text). `WORLD-086` left untouched
   per plan.
10. Annotated the conditional `docs/world/compiler_contract.md` bullet in
    `staging_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/investigation.md`'s "Docs Requiring Update"
    section with "Resolved during implementation, condition not met" — Option A needs no new
    update-collection/schema change, so `compiler_contract.md` itself was not edited.

**Deviation from plan:** none. All 10 steps implemented as specified; architecture-reviewer's
approval had no required changes.

**Additional test coverage beyond plan.md's literal Step 3 instruction:** plan.md Step 3's Verify
note said to "locate the relevant test file... and add/extend a narrow assertion." Located
`tests/unit/observability/test_event_extractor_world_dynamics.py` (the rollback-path test file, not
`test_event_shapers_world_dynamics.py`, which exercises the separate live push-shapers path) and
added four tests there: `test_not_fired_for_lair_occupant_spawn` (spawn_cadence_fired exclusion) plus
a new `TestBossSpawned` class with `test_emitted_for_dragonkin_lair_occupant` and
`test_not_emitted_for_non_boss_kind` (covers `_BOSS_KINDS` classification, which previously had zero
rollback-path test coverage in this file for either `world_boss`/`ancient_sentinel` or `dragonkin`).

**Doc-Update phase — one additional file touched beyond plan.md's stated doc-update scope
(disclosed per CLAUDE.md/doc-updater process note):** independent verification of the two docs the
implementer updated (`docs/world/raid_boss_camp_contract.md`, `docs/parity_ledger/world_dynamics.yaml`)
confirmed both are accurate against the real diff in `src/world/boss.py`,
`src/observability/event_extractor.py`, and `src/engine/world_dynamics.py` — no changes needed there.
`docs/mechanics/05_world_evolution.md`'s dragonkin/Lair-adjacent classification row (line 412) was also
checked and confirmed still accurate and not stale: it still correctly excludes dragonkin from
City/Camp/Nest classification (unchanged by this ticket, which does not touch `CampService`
classification), and its "owned by `TCK-20260904-LAIR-ENTITY-ANCHOR`" citation follows this doc's
existing convention of citing the originating/owning ticket ID as a permanent identifier (matching the
`### Camp/Nest Classification & Nest Spread (TCK-20260904-CAMP-NEST-CLASSIFICATION)` section header's
same convention), not a "still open" status marker — investigation.md's own "Docs Requiring Update"
section (lines 191-198) had already reached this same conclusion. No edit was made to this file.

However, `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md`'s Scope item 2 ("Idea 47 — Lair")
was found stale: it described idea 47 only as a scoped-but-unbuilt idea, with no landing annotation,
while sibling item 1 ("Ideas 44 + 45 + 46") and its "World-generation note (M8)" subsection both already
carry a "**Status update, 2026-09-04:**" annotation recording that their respective tickets
(`TCK-20260904-CAMP-NEST-CLASSIFICATION`, `TCK-20260904-CAMPSTATE-PLACE-BRIDGE`) landed. This file is
listed in this ticket's own `## Related Docs` section but is not part of plan.md's 10 explicit Steps, so
per the doc-updater process note this extra edit is disclosed here rather than made silently: a matching
"**Status update, 2026-09-04:**" paragraph was added to item 2, summarizing `check_for_lair_spawn`'s
Option-A entity-property mechanism, the `cadence.boss_spawn` gate reuse, the `kind="dragonkin"`
observability-list extension, the synthetic-fixture-only content decision, and idea 48's continued
deferral — following the exact same status-update pattern the two sibling tickets already established
in this file.

**Finding flagged by doc-updater and architecture-reviewer, then fixed by the Parity phase (`docs/parity_ledger/`
is `parity-updater`'s exclusive territory, so doc-updater correctly deferred rather than editing it
itself):** `docs/parity_ledger/world_dynamics.yaml`'s **WORLD-109** entry (P1) under-described the real
exclusion set after this ticket's Step 3 added `"dragonkin"` to both the `spawn_cadence_fired` exclusion
tuple and the `_BOSS_KINDS` frozenset in `src/observability/event_extractor.py`. investigation.md (lines
234-246) explicitly flagged this exact risk before implementation, but plan.md never assigned it a step,
and it was not touched in the Step 9 parity-ledger write. **The Parity phase has since fixed this**: it
rewrote WORLD-109's `text`/`v2_evidence` (via `tools/parity_ledger_writer.py::write_entry`) to accurately
distinguish `event_extractor.py`'s rollback-path exclusion lists (now including `"dragonkin"`, confirmed
complete within that file) from `src/observability/event_shapers.py`'s separately-maintained,
live-default-path `_BOSS_KINDS`/exclusion tuple (deliberately NOT extended — out of this ticket's scope,
recorded as an open follow-up, not a Mechanics Bible divergence). See Files Changed below.

**Post-Parity data-quality defect found and fixed (orchestrator, during Verify re-pass):** the Parity
phase's `write_entry` call for WORLD-109 left its pre-existing `legacy_evidence`/`support_boundary`
fields as the literal YAML string `"None"` instead of proper `null` (confirmed via grep: these were the
only 2 such occurrences anywhere in `docs/parity_ledger/`, both on this one entry — every other `null`
field in the 133-entry file is written correctly). Harmless to `tools/parity_index.py`'s health checks
(a `build()` re-run showed no new/changed findings) but semantically wrong data. Fixed directly via a
second `write_entry` call setting both fields back to real Python `None` (confirmed the file now reads
`support_boundary: null`/`legacy_evidence: null` for this entry, matching every other entry's convention).

## Test Summary
Ran via `/home/u24desktop/Working/rpg-based-simulation/.venv/bin/python3 -m pytest` (repo's
system-level `python3` lacks `pydantic`, per prior environment notes):
- `tests/unit/world/` (all, including the 5 new Lair tests) — 338 passed alongside
  `tests/unit/core/test_place_state.py` and `tests/unit/worldbuilding/test_place_wiring.py` in the
  same combined run.
- `tests/unit/observability/test_event_extractor_world_dynamics.py` +
  `tests/unit/observability/test_event_shapers_world_dynamics.py` — 45 passed, including the 4 new
  dragonkin-classification tests.
- Confirmed unmodified passing behavior for
  `test_boss_spawn_is_idempotent_even_if_existing_boss_left_region`, `test_calamity_boss_spawn`,
  `test_world_dynamics_maturity_advancement`,
  `test_world_dynamics_folds_camp_and_calamity_world_updates_into_final_update`, and
  `test_non_camp_nest_place_kinds_do_not_construct_campstate` (all pass unmodified, per plan's Verify
  notes).
- Full pytest suite intentionally not run (Test phase's job, per instructions) — scoped sanity runs
  only.

## Files Changed
- `src/world/boss.py` — added `check_for_lair_spawn` + `PlaceKind` import (Steps 1-2)
- `src/observability/event_extractor.py` — extended `spawn_cadence_fired` exclusion tuple and
  `_BOSS_KINDS` frozenset with `"dragonkin"` (Step 3)
- `src/engine/world_dynamics.py` — wired `check_for_lair_spawn` into `resolve_dynamics` as new "3.4b"
  block, extended `entities_add` fold-in (Step 4)
- `tests/unit/worldbuilding/test_place_wiring.py` — added
  `test_lair_kind_place_compiles_via_worldcompiler` (Step 5)
- `tests/unit/world/test_world_dynamics.py` — added
  `test_lair_spawn_fills_empty_lair_place_when_no_occupant_exists`,
  `test_lair_spawn_is_idempotent_per_place_with_multiple_lairs_in_one_region`,
  `test_lair_spawn_does_not_double_spawn_when_one_of_two_lairs_already_occupied`,
  `test_lair_occupant_death_does_not_dissolve_or_transform_the_lair_place` (Steps 6-7)
- `tests/unit/observability/test_event_extractor_world_dynamics.py` — added
  `test_not_fired_for_lair_occupant_spawn` and `TestBossSpawned` class (2 tests) (Step 3 Verify,
  beyond plan.md's literal instruction — see Implementation Notes)
- `docs/world/raid_boss_camp_contract.md` — added Lair generalization paragraph + Extension rules §3
  sub-bullet (Step 8)
- `docs/parity_ledger/world_dynamics.yaml` — updated `WORLD-085` `v2_evidence`/`test_path` via
  `tools/parity_ledger_writer.py::write_entry` (Step 9); Parity phase separately rewrote `WORLD-109`'s
  `text`/`v2_evidence` to accurately describe the `event_extractor.py` rollback-path dragonkin
  additions vs. `event_shapers.py`'s unchanged live-default path (also via `write_entry`) — see
  Implementation Notes; orchestrator then fixed a `legacy_evidence`/`support_boundary` `"None"`-string
  data-quality defect on that same `WORLD-109` write via a follow-up `write_entry` call
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — added a "Status update, 2026-09-04"
  paragraph to Scope item 2 ("Idea 47 — Lair") recording this ticket's landing, matching the sibling
  tickets' existing status-update pattern in the same file. Doc-Update phase, disclosed extra edit
  outside plan.md's 10 explicit Steps — see Implementation Notes.
- `staging_artifacts/TCK-20260904-LAIR-ENTITY-ANCHOR/investigation.md` — annotated the conditional
  `compiler_contract.md` bullet as "Resolved during implementation, condition not met" (Step 10)
- `tickets/inprogress/TCK-20260904-LAIR-ENTITY-ANCHOR.md` — this file, Implementation Notes/Test
  Summary/Files Changed/Completion Summary/Status/Acceptance Criteria updated

## Completion Summary
Generalized `BossService.check_for_boss_spawn`'s region-scoped entity-property idempotency pattern to
a new, parallel `check_for_lair_spawn` method keyed per-Place (`identity.properties["lair_place_id"]`
instead of `boss_region_id`), so multiple LAIR-kind Places within one Region each get an independent
spawn slot. Wired into `WorldDynamicsSystem.resolve_dynamics` reusing the existing boss-spawn cadence
and gate values. New `kind="dragonkin"` Lair occupants required extending two observability
exclusion/classification lists in `event_extractor.py`. `PlaceState.occupant_entity_id` intentionally
stays write-never (Option A, architecture-reviewer approved) — no new apply-path plumbing was added.
Covered by a synthetic LAIR fixture test, 4 new idempotency/idea-48-boundary tests in
`test_world_dynamics.py`, and 3 new observability tests; docs and the WORLD-085 parity ledger entry
updated accordingly. Implementation phase complete; Test/Parity/Doc-Update/Verify/Finalize phases of
the standard pipeline still remain.
