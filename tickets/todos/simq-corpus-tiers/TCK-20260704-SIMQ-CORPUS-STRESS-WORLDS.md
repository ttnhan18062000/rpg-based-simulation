---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS
phase: open
date: 2026-07-04T12:17:33Z
tags: [simulation-quality, world, corpus, calibration]
---

# TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS

## Title
Author new stress-tier worlds filling the corpus's identified scale-diversity gaps

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 found that scale
diversity across the existing 10 worlds is incidental (a byproduct of module composition for other
reasons), not deliberate, and named specific combinations "NOT currently represented":
- Large faction count (6-9) combined with a small entity/region footprint (today, faction density
  and world size move together — the 6-9-faction worlds are also the largest)
- High resource-node density with a small map (today's densest world, `frontier_extended`, is also
  the largest by region count — nothing tests a small map saturated with resources, or the inverse)
- FACTION/INFORMATION/self-model content combined with a large-scale population (the only world
  with any Pattern-6 content, `urban_political`, is mid-scale — 30 entities/3 regions — there is no
  data point at `frontier_extended`'s scale, 56 entities/10 regions)

This ticket authors new stress-tier worlds filling these gaps, per the taxonomy
`TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC` defines.

## Scope
1. Author **at minimum** the following, per the task's explicit minimum:
   (a) **A many-factions/small-map world**: comparable in entity/region footprint to the smallest
       existing worlds (`wilderness_survival` 11/4, `sandbox_world` 18/3) but with 6-9 distinct
       populated factions (matching the density of `frontier_living_world`/`generated_frontier_3_42`/
       `frontier_extended`) crammed into that small footprint.
   (b) **A sparse-resources/large-map world, OR a resource-saturated/small-map world** — whichever
       this ticket's own investigation phase judges more valuable given available catalog content
       (both fill the same identified gap from opposite directions; pick one and justify the choice
       in Implementation Notes).
   (c) **A world combining FACTION/INFORMATION content with a large-scale population** — comparable
       to `frontier_extended`'s scale (56 entities/10 regions), with `faction_tension_overrides`
       and `information_source_profiles`/`pending_information_responses` seeded (bespoke to this
       world's archetype, following the same per-world judgment discipline as
       `TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION`) — the first data point for how these
       mechanics behave at large scale.
2. For each new world: compile, verify 0 warnings, verify population stability (>=60% alive floor)
   through 200-300 ticks, run a 3-seed calibration matrix, add grade-anchor entries.
3. Use the `distinct_populated_factions` metric from `TCK-20260704-SIMQ-CORPUS-SCALE-METRIC` (if
   landed) to numerically confirm world (a) actually achieves 6-9 populated factions in a small
   footprint — do not rely on eyeballing the world.yaml content.
4. Update `docs/simulation_quality/eval_matrix_results.md` with the new worlds' grade tables, tagged
   as stress-tier.
5. Run `make evaluate --dry-run` (0 regressions on pre-existing corpus) and
   `make knowledge-index-update` if docs changed.

## Out of Scope
- Any changes to the 9 existing non-routing worlds' AGENCY grade — stress-tier worlds this ticket
  authors are new worlds, not modifications reversing the AGENCY-DA ruling
- Quest-density-vs-entity-count decoupling (investigation.md §2's fourth named gap) — this ticket's
  minimum scope is the 3 gaps explicitly listed in Scope item 1; the quest-density gap may be picked
  up in a future ticket if judged valuable, but is not required here
- Fixing any pillar scoring/emission bug discovered while authoring these worlds — file a follow-up
  ticket

## Acceptance Criteria
- [ ] A many-factions/small-map world exists: entity/region footprint comparable to
      `wilderness_survival`/`sandbox_world`, with 6-9 distinct populated factions confirmed
      (numerically, via the scale metric if available)
- [ ] Either a sparse-resources/large-map world or a resource-saturated/small-map world exists, with
      the choice justified in Implementation Notes
- [ ] A large-scale (comparable to `frontier_extended`) world exists with bespoke
      `faction_tension_overrides` and `information_source_profiles`/`pending_information_responses`
      content
- [ ] All 3 new worlds compile with 0 warnings and are verified population-stable (>=60% alive
      floor) through 200-300 ticks
- [ ] All 3 new worlds have 3-seed grade-anchor entries
- [ ] `docs/simulation_quality/eval_matrix_results.md` updated with stress-tier grade tables
- [ ] `make evaluate --dry-run` exits 0 with 0 regressions

## Related Tickets
- TCK-20260704-SIMQ-CORPUS-TIERS-EPIC (parent epic)
- TCK-20260704-SIMQ-CORPUS-TAXONOMY-DOC — defines stress-tier criteria these worlds must meet
- TCK-20260704-SIMQ-CORPUS-SCALE-METRIC — used to numerically verify the many-factions/small-map
  world's faction density
- TCK-20260704-SIMQ-CORPUS-E2E-CONTENT-EXPANSION — sibling content-authoring discipline (per-world
  judgment, not copy-paste) that the large-scale FACTION/INFORMATION world in this ticket should
  follow
- TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS — precedent for compile/verify/anchor workflow

## Related Docs
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/investigation.md` §2 ("Combinations NOT
  currently represented" — all 4 named gaps, 3 of which this ticket addresses)
- `docs/simulation_quality/eval_matrix_results.md`
- `docs/guides/content_authoring.md`

## Related Stored Artifacts
- `staging_artifacts/EPIC-SCOPE-full-feature-world-coverage/` — source investigation
- `stored_artifacts/TCK-20260703-SIMQ-UPLIFT3-WORLD-CORPUS/` — compile/verify/anchor workflow
  reference

## Related Code Areas
- `data/worlds/` — 3 new world directories
- `data/content/world_modules/` — existing modules to compose from (prefer reuse over new module
  authoring where possible, per investigation.md §3's low-risk framing for content-only changes)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- UQ-1: Should these 3 worlds be built primarily from existing catalog modules
  (`data/content/world_modules/`), or does filling the "many-factions/small-map" gap specifically
  require new module content (since no existing module combination currently produces that
  shape, per investigation.md §2)? Investigate available existing modules first; only author new
  module content if no existing combination can achieve the target shape.
- UQ-2: For gap (b) (sparse-resources/large-map vs. resource-saturated/small-map) — this ticket
  explicitly defers the choice to the implementer's investigation phase, per the task's own framing
  ("whichever the implementer's investigation phase judges more valuable"). Document the reasoning
  for whichever is chosen.

## Implementation Notes
(to be filled during implementation)

## Test Summary
(to be filled during implementation)

## Files Changed
(to be filled during implementation)

## Completion Summary
(to be filled on done)
