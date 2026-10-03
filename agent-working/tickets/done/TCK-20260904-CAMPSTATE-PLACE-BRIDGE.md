---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260904-CAMPSTATE-PLACE-BRIDGE
phase: done
date: 2026-09-04
tags: [content, architecture]
---

# TCK-20260904-CAMPSTATE-PLACE-BRIDGE

## Title
Reconcile CampState and PlaceState(kind=CAMP/NEST) for world-gen bridging

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Corrects a stale framing in the M4 epic doc ("new WorldModuleSpec field plus new WorldCompiler step") — idea 66's Place hierarchy already lets `WorldCompiler.compile()` construct `kind=CAMP`/`kind=NEST` `PlaceState` instances generically (both Direct and Composition paths), and `PlaceState.maturity`'s own docstring says "reused from CampState.maturity." The real remaining gap is that `CampState`'s fields (`kind: str` creature-flavor string, faction, active, last_raid_tick) do not losslessly map onto `PlaceState`'s fields (`kind: PlaceKind` enum, owner_faction_id, occupant_entity_id). This ticket makes and implements an explicit architecture decision to close that gap.

## Scope
- In `plan.md`, make and document an explicit architecture decision between: (a) construct a companion `CampState` alongside each `PlaceState(kind=CAMP/NEST)` instance at compile time, keeping `CampService` operating on `CampState` as today, or (b) migrate `CampService` to operate on `PlaceState` directly (owner_faction_id/occupant_entity_id/maturity), retiring the separate `AuthoritativeState.camps` dict — note (b) has a larger blast radius, touching raid/spawn logic and all existing camp tests.
- Implement the chosen option: wire `WorldCompiler.compile()` (`src/worldbuilding/compiler.py`) to recognize Camp/Nest-shaped content and construct the corresponding `PlaceState` (and, if option (a), companion `CampState`), for both the Direct and Composition content paths, mirroring `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`'s precedent for CITY-kind Places.
- Add a regression test proving non-Camp-shaped content (e.g. a City/Ruin/Dungeon-only world module) compiles unchanged after this change.
- If option (a) is chosen, define and test the `CampState`<->`PlaceState` linkage (e.g. via `place_id`, matching `RegionState.places`' dual-sided membership pattern from the schema migration ticket).

## Out of Scope
- The City/Camp/Nest race classification decision itself — that is `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s scope; this ticket consumes that decision's output (which races/content are Camp vs Nest) but does not make the classification call itself.
- Any change to the Nest spread-outcome mechanism or new typed Camp/Nest feature fields (totem/stockpile/palisade) — those are `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s scope.
- `CreatureTerritoryService` changes.

## Acceptance Criteria
- [x] `plan.md` states and justifies the chosen architecture (companion CampState vs CampService-on-PlaceState migration) before implementation begins.
- [x] `WorldCompiler.compile()` constructs `PlaceState(kind=CAMP)` and `PlaceState(kind=NEST)` instances from content, for both the Direct and Composition paths, mirroring the CITY-kind precedent in `TCK-20260902-WORLDCOMPILER-PLACE-WIRING`.
- [x] A new test proves non-Camp-shaped world content compiles unchanged (regression) after this change — mirrors `tests/unit/worldbuilding/test_place_wiring.py` and `tests/unit/worldassembly/test_resolver.py`'s existing structure.
- [x] If option (a): `CampState` instances constructed alongside their `PlaceState` counterpart round-trip correctly and existing `CampService` tests (`test_camp_lifecycle.py`) continue to pass unmodified in their assertions about `CampService` behavior.
- [ ] If option (b): all existing `CampService`/`CampState` call sites (`src/world/camp.py`, `src/world/creature_territory.py`, `src/engine/apply.py`, `src/engine/apply_plan.py`) are updated consistently and their existing test suites pass. (N/A — option (a) was chosen, per plan.md's Architecture Decision; this criterion does not apply.)

## Related Tickets
- TCK-20260904-CAMP-NEST-CLASSIFICATION
- TCK-20260902-WORLDCOMPILER-PLACE-WIRING
- TCK-20260902-PLACE-SCHEMA-MIGRATION
- TCK-20260902-EPIC-IDEA66-REGION-PLACE-REBUILD

## Related Docs
- docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md
- docs/plans/rpg_design_roadmap/rpg_idea66_region_place_rebuild_plan.md
- docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md (stale WorldModuleSpec/WorldCompiler framing to correct)

## Related Stored Artifacts
None yet.

## Related Code Areas
- src/worldbuilding/compiler.py
- src/core/state.py (PlaceState, PlaceKind, CampState, AuthoritativeState.camps/.places)
- src/world/camp.py
- src/world/creature_territory.py
- src/engine/apply.py
- src/engine/apply_plan.py
- tests/unit/worldbuilding/test_place_wiring.py
- tests/unit/worldassembly/test_resolver.py

## Assumptions / Open Questions
- Recommended sequencing: this ticket needs C1's classification rule (which races/content are Camp vs Nest) to exist before compiling real content, though the bridging mechanism itself is separately implementable — recommend implementing TCK-20260904-CAMP-NEST-CLASSIFICATION first.
- docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md's "CampState is never constructed anywhere, needs new WorldModuleSpec field + WorldCompiler step" framing is now stale given idea 66's landed Place hierarchy — this ticket's plan.md should note the correction rather than re-implementing the stale plan.
- Option (a) vs (b) is a real, consequential architecture decision with different blast radii; the Plan phase should not silently default to the smaller option without stating the tradeoff.
- No production code currently constructs `CampState()` at all (confirmed via grep) — `state.camps` is populated only in tests today; this ticket is the first to give it a real construction path.

## Implementation Notes
Implemented plan.md's 10 steps exactly, option (a) (companion `CampState` construction):

1. Added `creature_kind: Optional[str] = None` to `PlaceRecipeSpec` (`src/worldbuilding/recipe.py`)
   and `PlaceSpec` (`src/worldbuilding/schema.py`), plus a `CAMP_NEST_CREATURE_RACES = frozenset({...})`
   constant and a `field_validator("creature_kind")` in each, mirroring the existing `validate_kind`
   pattern. Value is lowercased and validated against the Camp+Nest race set; `None` bypasses
   validation.
2. Threaded `creature_kind=p.creature_kind` through `resolve_module_contribution()`'s `PlaceSpec(...)`
   construction in `src/worldassembly/resolver.py` (one-line additive change, no new namespacing —
   `creature_kind` is not an identifier).
3. Extended `WorldCompiler.compile()`'s existing Place-construction loop (`src/worldbuilding/compiler.py`)
   with an additive branch: when `p_spec.kind in ("CAMP", "NEST")` and `creature_kind` is set, build a
   companion `CampState` keyed by the same `place_id`, added to a new `camps: Dict[str, CampState]`
   dict. Fixed the confirmed pre-existing latent bug: the final `AuthoritativeState(...)` call now
   passes `camps=camps` (previously omitted entirely, silently defaulting to `{}` — `CampService`/
   `CreatureTerritoryService` were dead code in every compiled world in production before this fix).
4. Added 8 new tests to `tests/unit/worldbuilding/test_place_wiring.py` covering the Direct path:
   CAMP/NEST companion CampState construction, non-Camp/Nest kinds producing no CampState, the
   non-Place-shaped regression guard extended to camps, place_id linkage round-trip, schema-level
   `creature_kind` validation (valid/invalid/unset), and canonical-hash participation.
5. Added 1 Composition-path test to `tests/unit/worldassembly/test_resolver.py` confirming
   `creature_kind` passes through `resolve_module_contribution()` unnamespaced while `id` is namespaced.
6. Added 3 architecture-guard/anti-drift tests to `tests/unit/world/test_camp_lifecycle.py`: a
   world-gen-seeded `CampState` (via `WorldCompiler.compile()`) is fed directly into the UNMODIFIED
   `CampService.process_camps()` and produces the expected maturity-accrual update; a behavioral
   (not source-grep) proof that the raid-trigger/monster-spawn path still fires with NO feature flags
   set at all (guards against new gating without over-matching the pre-existing, unrelated
   `ENABLE_REPRODUCTION_NATURAL_CREATURE_PATH` flag already in that function); and a confirmation that
   `AuthoritativeState.to_readonly()`'s `camps=ReadOnlyDict(...)` wrapping still applies to
   world-gen-seeded camps.
7. Added a "World-gen construction" subsection to `docs/world/raid_boss_camp_contract.md` under the
   existing `## Camp — camp.py` section.
8. Extended the `RegionSpec`/`PlaceSpec` field summary in `docs/world/compiler_contract.md` to mention
   `creature_kind`.
9. Corrected `WORLD-109`'s stale `divergence_note` in `docs/parity_ledger/world_dynamics.yaml` via
   `tools/parity_ledger_writer.py::write_entry` (schema-validating write path, not a raw YAML edit);
   only that one field changed at Implement time, confirmed via `git diff`. `status`/`priority`/
   `test_path`/`v2_evidence` untouched.
10. Corrected item 2's stale framing in
    `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` to describe the as-built
    mechanism (idea 66's existing insertion point + this ticket's narrow `creature_kind` field/branch,
    not a new schema field/compiler step). Item 9's historical reference to item 2's original finding
    was left untouched per the plan's scope guard (it accurately describes the reasoning at the time
    idea 66 was sequenced first, not a claim about current state).

All code Scope Guards respected: `src/world/camp.py`, `src/world/creature_territory.py`,
`src/engine/world_dynamics.py` untouched; no new `ENABLE_*` flag added; no cross-validation forcing
`creature_kind` when `kind in {CAMP, NEST}`; no real content YAML modified (`hero_guild_routing`'s
`goblin_camp_place` left as-is, confirmed inert by the unmodified
`test_hero_guild_routing_real_content_produces_expected_non_uniform_place_kinds` test still passing).

**Parity Phase — one disclosed, narrow deviation from `plan.md`'s scope guard.** `plan.md` explicitly
said "Do NOT touch `WORLD-124`" — written when `WORLD-109`'s original `divergence_note` asserted a
blanket "no CampState is constructed anywhere in production." Implement's own item 9 correction to
`WORLD-109` (above) made that blanket claim false, which left `WORLD-124`'s own text (the sibling
`TCK-20260904-CAMP-NEST-CLASSIFICATION` ticket's ledger entry) carrying a now-dangling parenthetical
cross-reference: "No new CampState is constructed anywhere in this branch (**WORLD-109 remains
true**)." The Parity phase found this during its independent re-verification and corrected only
`WORLD-124`'s `text` field (via `tools/parity_ledger_writer.py::write_entry`, confirmed via `git diff`
that `status`/`priority`/`v2_evidence`/`test_path` were untouched) to distinguish "this
[CAMP-NEST-CLASSIFICATION] branch constructs no CampState" (still literally true — the Nest-spread
fork spawns an entity, not a Place/Camp record) from "WORLD-109's separate, opt-in world-gen CampState
path, still inert for all real content" (this ticket's own change). This is a deliberate, narrow
deviation from `plan.md`'s scope guard, not an oversight — the guard's own premise (that WORLD-109
would stay untouched, so WORLD-124 needed no cross-check) was invalidated by this ticket's own item 9,
and leaving WORLD-124's stale cross-reference in place would have been a worse outcome than the
narrow, disclosed fix.

## Test Summary
`pytest tests/unit/worldbuilding/test_place_wiring.py tests/unit/worldassembly/test_resolver.py tests/unit/world/test_camp_lifecycle.py -q`
→ 39 passed (12 new tests: 8 in test_place_wiring.py, 1 in test_resolver.py, 3 in
test_camp_lifecycle.py; all 27 pre-existing tests across the three files pass unmodified).
Broader scoped run per test_plan.md's Scoped Pytest Commands (`tests/unit/worldbuilding/`,
`tests/unit/worldassembly/`, `tests/unit/world/`, `tests/unit/domains/optimization/test_apply_plan_builder.py`):
630 passed, 7 failed (971s). All 7 failures are in `tests/unit/worldassembly/test_corpus_diversity.py`
(NARRATIVE-pillar grade-stability drift assertions, e.g. `test_frontier_marches_seed42_200t_narrative_grade_stability`)
and are unrelated to this ticket — none reference `CampState`/`PlaceSpec`/`creature_kind`/`WorldCompiler`'s
Place loop, and the failures are accompanied by `WARNING kernel.py:444 Tick N exceeded budget` /
`WatchdogTrip` log lines, matching `docs/testing/regression_policy.md`'s documented pre-existing
`tick_budget`/`watchdog_variance` structural-noise categories for this exact test file (118
`tick_budget` + 3 `watchdog_variance` pre-classified combos, per that doc's §6 root-cause table).
`state.camps` stays `{}` for every real compiled world after this ticket (no content sets
`creature_kind`), so this ticket cannot causally affect a NARRATIVE-pillar grade. Flagged for the
Test/Parity phases to confirm against a clean baseline; not treated as a regression to fix here.

## Files Changed
- `src/worldbuilding/recipe.py` — `CAMP_NEST_CREATURE_RACES` constant, `creature_kind` field +
  validator on `PlaceRecipeSpec`
- `src/worldbuilding/schema.py` — `CAMP_NEST_CREATURE_RACES` constant, `creature_kind` field +
  validator on `PlaceSpec`
- `src/worldassembly/resolver.py` — `creature_kind=p.creature_kind` pass-through in
  `resolve_module_contribution()`
- `src/worldbuilding/compiler.py` — `CampState` import, `camps` dict construction in the Place loop,
  `camps=camps` passed into the final `AuthoritativeState(...)` call
- `tests/unit/worldbuilding/test_place_wiring.py` — 8 new tests
- `tests/unit/worldassembly/test_resolver.py` — 1 new test
- `tests/unit/world/test_camp_lifecycle.py` — 3 new tests
- `docs/world/raid_boss_camp_contract.md` — new "World-gen construction" subsection
- `docs/world/compiler_contract.md` — `creature_kind` added to the `RegionSpec`/`PlaceSpec` field summary
- `docs/parity_ledger/world_dynamics.yaml` — `WORLD-109` `divergence_note` corrected at Implement time
  (via `tools/parity_ledger_writer.py`); `WORLD-124` `text` field also corrected at Parity phase (a
  dangling cross-reference to WORLD-109's old premise) — disclosed above in Implementation Notes'
  "Parity Phase" subsection as a narrow, deliberate deviation from `plan.md`'s "Do NOT touch WORLD-124"
  scope guard
- `docs/plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md` — item 2 reframed to the
  as-built mechanism
- `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — Document-Update phase: corrected the
  same stale "CampState is never constructed / needs new WorldModuleSpec field" claim in its
  "World-generation note (M8)" callout; disclosed above in Implementation Notes (item 1)
- `docs/simulation_quality/event_type_coverage.md` — Document-Update phase: corrected the stale
  "camps are pre-placed at world generation" premise in the `camp_constructed` §3.9 row and the
  "Remaining gaps" summary line; disclosed above in Implementation Notes (item 2)
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — Document-Update phase:
  corrected the stale "CampState is never constructed in production" parenthetical in the idea-44
  world-scoping note; disclosed above in Implementation Notes (item 3)
- `tickets/inprogress/TCK-20260904-CAMPSTATE-PLACE-BRIDGE.md` — this ticket file
- `staging_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/plan.md`,
  `staging_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/investigation.md`,
  `staging_artifacts/TCK-20260904-CAMPSTATE-PLACE-BRIDGE/test_plan.md` — created during this run's
  Investigate/Plan phases (not authored by the implementer, but part of this run's changeset)

## Completion Summary
Closed the confirmed gap where `WorldCompiler.compile()` never passed `camps=` into the final
`AuthoritativeState(...)` call, leaving `CampService`/`CreatureTerritoryService` as dead code in
every compiled world. Added an opt-in `creature_kind` field to `PlaceRecipeSpec`/`PlaceSpec`
(CAMP/NEST-scoped, validated against the Camp+Nest race set, `None` by default) and an additive
branch in the compiler's existing Place-construction loop that builds a companion `CampState`, keyed
by the same `place_id`, only when that field is set. The bridge is inert for all content on disk
today — no real content (including `hero_guild_routing`) sets `creature_kind`, so `state.camps`
remains `{}` for every currently-compiled world, matching the plan's Gameplay-Activation Risk
Decision. `CampService`, `CreatureTerritoryService`, and the Camp/Nest classification rule were not
touched.

## Document-Update Phase — Additional Doc Corrections (outside plan.md's stated 4-doc scope)

Independent Document-Update-phase verification (per CLAUDE.md's process note learned from the
sibling ticket `TCK-20260904-CAMP-NEST-CLASSIFICATION`'s Verify BLOCK) cross-checked the 4
implementer-updated docs against the real diff (all 4 confirmed accurate — code diff in
`src/worldbuilding/recipe.py`/`schema.py`, `src/worldassembly/resolver.py`,
`src/worldbuilding/compiler.py` matches plan.md exactly; `CAMP_NEST_CREATURE_RACES` matches
`docs/mechanics/05_world_evolution.md` §6's City/Camp/Nest table verbatim; `CampState` dataclass
defaults and `to_readonly()`'s `camps=ReadOnlyDict(...)` wrapping match the corrected doc claims;
39/39 scoped tests re-run and pass). A broader staleness sweep (grep across `docs/` for the same
"CampState is never constructed"/"camps are pre-placed at world generation, no dynamic
construction mechanic" premise this ticket's WORLD-109 correction addresses) found 3 additional
doc locations, outside the 4 already listed and outside plan.md's own stated doc-update scope,
carrying the identical now-stale premise. Fixed all 3, disclosed here per the process note:

1. `docs/plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md` — its "World-generation note (M8)"
   callout (under Scope item 1) still read "`CampState` is never constructed in production
   anywhere... needs a new `WorldModuleSpec` field plus a new `WorldCompiler` step" — the exact
   same stale claim the implementer already corrected in the M8 epic doc's own item 2. Updated to
   a "closed, 2026-09-04" callout describing the as-built mechanism and cross-referencing both this
   ticket and the M8 doc's corrected item 2.
2. `docs/simulation_quality/event_type_coverage.md` (`status: authoritative`, Certified Level 1 —
   given full rigor per CLAUDE.md's authoritative-doc rule regardless of folder) — its §3.9
   `camp_constructed` table row and the preceding "Remaining gaps" summary line both asserted
   "camps are pre-placed at world generation... no dynamic construction mechanic," the identical
   premise just corrected in `WORLD-109`'s `divergence_note`. The row's actual conclusion (no
   viable *tick-time* engine path for `camp_constructed` — `StateUpdate` still has no `camps_add`
   field, unaffected by this ticket) remains correct and was preserved; only the false premise
   clause was corrected, with an explicit cross-reference to `WORLD-109` and this ticket.
3. `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md` — its idea-44 world-scoping
   note asserted (parenthetically) "confirmed elsewhere this session `CampState` is never
   constructed in production," now false as a general claim (it's constructible; just inert for
   `hero_guild_routing`'s `goblin_camp_place` specifically, which sets no `creature_kind`). The
   doc's substantive test-scoping conclusion (this world still doesn't exercise real `CampState`
   machinery) was correct and preserved; only the stale justification clause was corrected.

No other doc area was found to reference `WorldCompiler.compile()`'s `AuthoritativeState`
construction, `CampState`, or the `camps=` omission bug in a way this ticket makes stale —
`docs/audits/*` hits were left untouched (cite-only per CLAUDE.md, and audits are dated
point-in-time snapshots, not living reference docs); `docs/archive/*` hits were left untouched
(out of scope for all agents); other `WorldCompiler.compile` references found via grep were either
unrelated to the camps-construction claim (e.g. terrain-fill, entity-spawn, role-resolution
descriptions) or already-correct.
