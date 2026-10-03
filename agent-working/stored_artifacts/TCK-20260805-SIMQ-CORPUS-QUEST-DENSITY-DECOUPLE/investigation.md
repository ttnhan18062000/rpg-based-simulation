---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE
artifact_type: investigation
tags: [simulation-quality, world, progression, corpus, calibration]
---

# investigation.md — TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE

## Current Behavior (file:line refs)

Given the sibling gap-1 and gap-2 tickets both found their target gap already closed and
undocumented (`crowded_frontier`, `resource_dense_basin`), this ticket verified gap #5 against
real corpus data before authoring anything, rather than assuming the ticket's premise was still
accurate.

## Verification (real corpus data)

Computed real quest_count/entity_count ratio from every `data/worlds/*/world_compile_report.json`:

| World | Entities | Quests | Ratio |
|---|---|---|---|
| `unit_information_density`/`unit_information_source`/`unit_selfmodel_pilot` | 16 | 3 | 0.188 (lowest) |
| `frontier_extended` | 59 | 25 | 0.424 |
| `wilderness_survival` | 11 | 7 | **0.636 (highest, incidental)** |

Unlike gaps #1/#2, **no per-world table entry claims to close gap #5** — confirmed via grep, 0
hits for "fills gap 5"/"gap 5". `wilderness_survival`'s 0.636 ratio is real but incidental: its
own composition (`forest_deep_ecology` + `wolf_den_near_forest` + `undead_battlefield` +
`survivor_camp_shelter`) was authored as a "no settlement, high danger ecology" survival scenario
— the gap text's own framing ("no world *deliberately* decouples these axes") is still accurate.
Gap #5 is genuinely open, unlike gaps #1/#2.

## World Design

**First draft** (frontier_village_core + mountain_pass + river_crossing + forest_deep_ecology):
13 entities, 7 quests, ratio 0.538 — **rejected**: lower than `wilderness_survival`'s existing
incidental 0.636, so it would not have added new corpus coverage despite being deliberately
authored.

**Final composition** (`ruins_mystery_quest` + `mountain_pass` + `river_crossing` +
`forest_deep_ecology`): `ruins_mystery_quest` is standalone (no `requires:`, confirmed via direct
read), contributes only 6 entities (`undead_battlefield_patrol` population) and 2
`quest_definitions`. The 3 terrain/ecology modules each declare `populations: []` (confirmed via
direct read of all 19 world modules' `populations:` fields) but still contribute
`quest_definitions` (2 + 1 + 1 = 4). Combined: **6 entities, 6 quest_definitions, ratio 1.0** —
genuinely and clearly beyond the corpus's prior incidental maximum.

**Pre-existing content issue found, not introduced by this ticket:** `river_crossing`'s
`survey_river_route` quest requires `required_location_tags: ["wilderness", "river"]`, but its own
region (`river_ford`) has no `tags:` field declared — confirmed this exact warning already fires
for the existing, shipped `highland_traverse` world (which also composes `river_crossing`), via a
direct compile. Not fixed here — a shared-module content bug affecting other worlds too, out of
this ticket's scope.

## Docs Requiring Update
- `docs/simulation_quality/corpus_tier_taxonomy.md`: gap #5 marked CLOSED in the "Named
  scale-diversity gaps" section, and a new per-world table row added for `quest_dense_frontier`.

## Parity Ledger Overlap
None.

## Prior Work
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` — authored `crowded_frontier`/`resource_dense_basin`
  (gaps #1/#2), the precedent pattern this ticket follows for a genuinely-needed stress-tier world.
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`,
  `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE` (this session) — found their respective
  gaps already closed; this ticket's verification-first approach is a direct application of that
  lesson, and it found a genuinely different (still-open) result.

## Risks and Open Questions
None outstanding. Both the "gap is still open" finding and the final world's ratio improvement
were verified against real compile-report data, not assumed.
