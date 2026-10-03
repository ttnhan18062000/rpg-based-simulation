---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS
phase: done
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS

## Title
Author corpus-test assertions for ideas 4, 10, 13, 14, 22, 30, 33, 36/40, 39, 44, 49 — no new world authoring needed

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
M9 epic (`TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE`) child 4 of 8. Every idea in this batch's
epic-doc spec needs zero new corpus-world authoring — only an added assertion to an existing
calibration run. All underlying mechanisms are confirmed shipped (ideas 4/10/13/33 via M1's quick-wins
batch; idea 14 via M2; ideas 36/40/39/44 via M2/M4/M6; idea 22 pre-existing; idea 49 already-authored
content). Re-confirm each mechanism's real shipped shape during Investigate, not just this ticket's
citations — several of these predate this session's own recent work.

## Scope
Per the epic doc's own concrete specs:
- **Idea 4 (Unified Modification)**: `urban_political`/`simq_routing_test` (Regression-tier) — pure
  regression check, committed COMBAT-pillar scores stay within existing tolerance.
- **Ideas 10 (Heir Assignment) + 13 (Trade & Team-Up)**: compose `frontier_village_core` +
  `hero_adventurers` (16 entities, 1 region, 3 factions). Idea 10: scripted lethal hit, assert heir
  assignment + inventory transfer. Idea 13: gate 2 of 3 Heroes' mutual sentiment, assert
  `ResourceTransferIntent`/`TeamUpInvite` succeed only for the gated pair.
- **Idea 14 (Species Classification)**: `frontier_living_world` — assert `intelligence_tier` matches
  `natural_traits`, low-tier entities excluded from coming-of-age/Progression-Planner eligibility.
- **Idea 22 (Relationship Roles)**: `highland_traverse` or `frontier_living_world` — add one
  direct-field-read assertion (not score-drift) that `SocialBond.role` lands on the right
  classification after a repeated-grudge sequence (grudge >= 3.0).
- **Idea 30 (Possessions With History)**: extend `frontier_living_world`, depends on idea 13 landing
  in this same ticket first — track one `ItemInstance` through LOOT->CRAFTED->GIFT->INHERITED, assert
  `owner_history` accumulates all 4 `acquired_method` values in order.
- **Idea 33 (Marriage)**: `highland_traverse` — assert `MarriageState` transitions PROPOSED->ACCEPTED
  at `familiarity >= 0.6`.
- **Ideas 36/40 (Clan)**: `frontier_marches` — retarget existing `orc_clan_territory` content into a
  real `ClanState`, assert membership count and defection removes exactly one member.
- **Idea 39 (Affiliation Change)**: `frontier_marches` — trigger `IdentityUpdate(faction_set=...)`,
  assert `identity.faction` changes and old-faction `SocialBond` entries do NOT auto-degrade.
- **Idea 44 (Settlement Capacity)**: `hero_guild_routing` — assert `settlement_capacity` resolves
  `FULL_SETTLEMENT` for `frontier_village_core` and `NONE`/`CAMP_ONLY` for `goblin_camp` (note the
  real caveat: `goblin_camp` doesn't exercise real `CampState`/Place(kind=CAMP) machinery today since
  its content never opted into `creature_kind` — this test targets the settlement-capacity
  classification only, not Camp machinery).
- **Idea 49 (Place-Tied Crafting Materials)**: `mountain_pass.yaml` (already in `hero_guild_routing`)
  — assert a `frost_shard`-gated recipe only completes near `mountain_pass_zone`.

## Out of Scope
- Building any of these ideas' underlying mechanisms — all confirmed already shipped.
- Authoring any new corpus world — every entry in this batch reuses an existing one, by design.
- Any other item from M9's scope.

## Acceptance Criteria
- [x] All assertions above are authored and passing against the named existing corpus worlds.
- [x] No new corpus world is authored as part of this ticket — confirmed during Investigate; every
      sub-test reuses either a real existing world or a hand-seeded Unit-tier `AuthoritativeState`.
- [x] Idea 30's test lands after idea 13's, in the same ticket, per the dependency order.

## Related Tickets
- `TCK-20260824-EPIC-RPG-M9-CORPUS-TEST-COVERAGE` (parent epic)

## Related Docs
- `docs/plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md`

## Related Stored Artifacts
None yet — created by this ticket's own Investigate/Plan phases once picked up for implementation.

## Related Code Areas
- `config/simulation_quality/corpus_registry.yaml`
- `tests/simulation_quality/`

## Assumptions / Open Questions
- Each idea's exact real shipped shape (field names, thresholds) should be re-confirmed during
  Investigate — several of these ideas shipped in earlier milestones (M1/M2) not touched by this
  session's recent work, so citations here are from the original epic doc, not freshly re-verified
  line-by-line for every single one.

## Implementation Notes
Re-verified every one of the 11 sub-items' real shipped shape against code during Investigate/
Implement rather than inheriting the ticket's own citations — found and corrected 8 real premise
errors, none forced or fabricated around:
1. **Idea 13**: `TeamUpInvite` is not a real class — the real path is `ContractKind.TEAM_UP` through
   `SocialAppraisalSystem._appraise_team_up()` (`trust_score >= 0.6`).
2. **Idea 33**: the real marriage gate is the shared trust-prelude only (`trust_score < 0.2` ->
   CANCELLED), not `familiarity >= 0.6` — that figure actually belongs to idea 13's Team-Up gate in
   the same file. `MarriageState` is created directly at `ACCEPTED` in one action; there is no
   PROPOSED->ACCEPTED transition to observe.
3. **Idea 30**: `owner_history` accumulates owner IDs across transfers; `acquired_method` is
   immutable at creation and cannot "accumulate 4 values." `ItemInstanceService.maybe_create_instance()`'s
   own docstring plus a direct grep confirm zero real production callers mint or transfer
   ItemInstances today (`ENABLE_ITEM_INSTANCE_HISTORY` defaults OFF) — a fully schema-only, dormant
   mechanism, disclosed honestly rather than papered over.
4. **Idea 14**: `intelligence_tier`'s only real `src/` consumer is
   `RoleModelImitationService.compute_imitation_fidelity()` (an imitation-fidelity multiplier), not
   a coming-of-age/Progression-Planner eligibility gate.
5. **Idea 22**: a repeated grudge >= 3.0 promotes to `SocialComponent.nemesis_ids` via
   `SocialMemoryService.check_nemesis_promotion()` — `BondUpdate.role_set`/`SocialBond.role` has zero
   real production writers anywhere in `src/` (confirmed via grep), a dead field.
6. **Idea 36/40**: `orc_clan_territory.yaml` defines only a FACTION named "orc_clan", zero real
   `ClanState` content — same finding as this ticket's own immediately-prior M9 sibling
   (CORPUS-TEST-NEWLY-UNBLOCKED-IDEAS). The real party-defection trigger only degrades
   `clan_reputation`; membership removal (`ClanLifecycleService.process_leave()`) is a real, correct,
   but currently-uncalled pure function — proven directly, disclosed as built-but-not-wired.
7. **Idea 44**: `settlement_capacity`/`FULL_SETTLEMENT`/`CAMP_ONLY` do not exist anywhere in `src/` —
   the real mechanism is `PlaceKind` (idea 66). Running the real compiler further refined the epic
   doc's own caveat: `goblin_camp_conflict` DOES compile a real `Place(kind=CAMP)`, just with
   `maturity=None` (no live CampState machinery) — not "no Place at all" as the doc's text implied.
8. **Idea 49**: the real material name is `frost_shard_cluster` (not "frost_shard"), and the "gate"
   is resource-node placement/harvest availability, not a live crafting-time proximity check (no such
   check exists anywhere in `src/systems/*/crafting*.py`/`harvest*.py`).

No `src/` production code was changed — pure test-authoring, matching every other M9 sibling
ticket's own "zero new world, test-only" precedent. Every new test exercises either a real compiled
corpus world/module or a hand-seeded Unit-tier `AuthoritativeState` through a real
`Kernel.tick_once()`/`ApplyPath.apply_partial()`/pure-function call — never a mock of the logic
under test.

## Test Summary
21 new tests across 11 files, all passing. Broader regression sweep (`tests/simulation_quality/`,
`tests/unit/social/`, `tests/unit/strategic/`, `tests/unit/world/`, `tests/unit/progression/`):
1514 passed, 85 skipped, 0 failed.

## Files Changed
- `tests/simulation_quality/test_idea4_regression_coverage_confirmation.py` (new)
- `tests/simulation_quality/test_heir_inventory_transfer_corpus.py` (new)
- `tests/simulation_quality/test_team_up_trust_gate_corpus.py` (new)
- `tests/simulation_quality/test_species_intelligence_tier_corpus.py` (new)
- `tests/simulation_quality/test_relationship_role_grudge_corpus.py` (new)
- `tests/simulation_quality/test_item_owner_history_corpus.py` (new)
- `tests/simulation_quality/test_marriage_trust_gate_corpus.py` (new)
- `tests/simulation_quality/test_clan_membership_and_defection_corpus.py` (new)
- `tests/simulation_quality/test_faction_change_bond_preservation_corpus.py` (new)
- `tests/simulation_quality/test_place_kind_settlement_classification_corpus.py` (new)
- `tests/simulation_quality/test_place_tied_resource_availability_corpus.py` (new)

## Completion Summary
Authored real, regression-catching corpus-test coverage for all 11 idea groups with zero new
corpus-world authoring and zero production code changes, exactly as scoped. Found and honestly
corrected 8 real citation/premise errors along the way (wrong class names, a conflated threshold
between two sibling contract kinds, a dead relationship-role field, a dormant item-history
mechanism, and others) rather than forcing tests against mechanisms that do not exist as described —
matching this M9 batch's own now-established discipline of verifying every citation against real
code before writing an assertion.
