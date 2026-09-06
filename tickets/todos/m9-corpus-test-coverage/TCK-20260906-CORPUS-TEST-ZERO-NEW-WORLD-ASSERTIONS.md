---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS
phase: open
date: 2026-09-06
tags: [testing, simulation-quality, corpus]
---

# TCK-20260906-CORPUS-TEST-ZERO-NEW-WORLD-ASSERTIONS

## Title
Author corpus-test assertions for ideas 4, 10, 13, 14, 22, 30, 33, 36/40, 39, 44, 49 — no new world authoring needed

## Status
OPEN

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
- [ ] All assertions above are authored and passing against the named existing corpus worlds.
- [ ] No new corpus world is authored as part of this ticket — confirm during Investigate that each
      target world still matches its described composition before writing the assertion.
- [ ] Idea 30's ticket depends on idea 13's assertion landing first within this same ticket (or is
      confirmed independently satisfiable if idea 13 already has separate coverage).

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

## Test Summary

## Files Changed

## Completion Summary
