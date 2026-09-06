---
status: active
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS
date: 2026-09-06
---

# Test Plan: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS

## Regression Surface
No existing tests are modified. `tests/simulation_quality/`, `tests/unit/social/`,
`tests/unit/strategic/` must all continue passing unmodified.

## New Tests Required (one file per idea-group, all under `tests/simulation_quality/`)
1. `test_idea4_regression_coverage_confirmation.py` — asserts `grade_anchors.json` already has a
   COMBAT entry for `urban_political_seed42_200t` and `simq_routing_test_seed42_500t` (citation
   test, not a new mechanism proof).
2. `test_heir_inventory_transfer_corpus.py` (idea 10) — hand-seeded death-with-heir scenario,
   real `Kernel.tick_once()`, assert inventory items transfer to the heir.
3. `test_team_up_trust_gate_corpus.py` (idea 13) — hand-seeded entities at varied trust levels,
   real `execute_team_up`/`appraise_contract()` call, assert accept above 0.6 trust / cancel below.
4. `test_species_intelligence_tier_corpus.py` (idea 14) — real compiled world content, assert
   `intelligence_tier` matches `natural_traits` containing `tool_user`.
5. `test_relationship_role_grudge_corpus.py` (idea 22) — repeated-grudge sequence, assert
   `SocialBond.role` lands on the correct classification.
6. `test_item_owner_history_corpus.py` (idea 30) — one `ItemInstance` tracked through
   LOOT->CRAFTED->GIFT->INHERITED, assert `owner_history`/`acquired_method` sequence.
7. `test_marriage_trust_gate_corpus.py` (idea 33, corrected) — assert `MarriageState` is created at
   `ACCEPTED` when trust passes the real shared prelude, and is NOT created when trust is hostile
   (a real regression-catching negative-path assertion).
8. `test_clan_membership_and_defection_corpus.py` (idea 36/40, hand-seeded per correction) —
   2 Clans of 4 members, assert membership count and that defection removes exactly one member.
9. `test_faction_change_bond_preservation_corpus.py` (idea 39) — real `faction_set` mutation,
   assert `identity.faction` changes and `SocialBond` entries are untouched.
10. `test_place_kind_settlement_classification_corpus.py` (idea 44, corrected) — real
    `hero_guild_routing` compiled world, assert `PlaceKind.CITY` for `frontier_village_core`'s
    region and no live `CampState`/`Place(kind=CAMP)` for `goblin_camp`'s region.
11. `test_place_tied_resource_availability_corpus.py` (idea 49, corrected) — real `mountain_pass`
    module compiled content, assert `frost_shard` is only obtainable via a `mountain_pass_zone`
    resource node.

## Scoped Pytest Commands
`.venv/bin/python3 -m pytest tests/simulation_quality/test_idea4_regression_coverage_confirmation.py tests/simulation_quality/test_heir_inventory_transfer_corpus.py tests/simulation_quality/test_team_up_trust_gate_corpus.py tests/simulation_quality/test_species_intelligence_tier_corpus.py tests/simulation_quality/test_relationship_role_grudge_corpus.py tests/simulation_quality/test_item_owner_history_corpus.py tests/simulation_quality/test_marriage_trust_gate_corpus.py tests/simulation_quality/test_clan_membership_and_defection_corpus.py tests/simulation_quality/test_faction_change_bond_preservation_corpus.py tests/simulation_quality/test_place_kind_settlement_classification_corpus.py tests/simulation_quality/test_place_tied_resource_availability_corpus.py -v`

## Anti-Drift Test Guards
Every assertion must be regression-catching (fails if the underlying mechanism breaks), never a
tautology or a bare "no exception raised" smoke check.
