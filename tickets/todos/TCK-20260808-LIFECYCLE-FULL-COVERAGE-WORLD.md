---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD
phase: open
date: 2026-08-08
tags: [world, simulation-quality, corpus]
---

# TCK-20260808-LIFECYCLE-FULL-COVERAGE-WORLD

## Title
Author a large, fully-equipped "production" world exercising all 10 entity-lifecycle-phase
buckets, to separate mechanism gaps from content gaps in `phase_coverage`/`path_entropy`

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Per the user's own explicit direction: `phase_coverage` (10-bucket coverage) and `path_entropy`
(within-life event-type diversity) currently sit in a moderate 0.4-0.7 range across every real
corpus world this session's own long-run observation touched — but every world checked has a real,
content-driven **ceiling** well below the theoretical maximum. Confirmed via real data:
`wilderness_survival` only ever touches 6/10 buckets across its *entire* population (no
`ECONOMY`/`SOCIAL`/`IDENTITY`/`NARRATIVE_QUEST` content exists there at all); `urban_political`
reaches 8/10 (missing `IDENTITY`/`NARRATIVE_QUEST`). Without a world that structurally CAN reach
all 10 buckets, there is no way to tell whether a moderate `phase_coverage` score reflects a real
scoring/mechanism problem or simply reflects that no world in the corpus has ever been authored
with full content breadth.

**Real, bucket-by-bucket gap analysis** (`config/simulation_quality/entity_lifecycle_weights.yaml`
`lifecycle_phase_buckets`, cross-referenced against real corpus content this session already
mapped):

| Bucket | Real trigger events | What's needed |
|---|---|---|
| `VITALS` | biological/stamina changes | Any populated world — always reachable |
| `GROWTH_PROGRESSION` | xp_granted, level_up, skill_unlocked, trait_expressed | Real kills/quests (XP economy — see `TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX`) |
| `EXPLORATION` | movement, resource_harvested | Any populated world with resource nodes |
| `COMBAT` | combat_damage, combat_initiated, entity_killed, ... | Real hostile population (any archetype with monsters) |
| `ECONOMY` | shop_transaction, trade_executed, gold_transaction, ... | Real shop/blacksmith/merchant content (civilian settlement) |
| `SOCIAL` | social_memory_created, reputation_delta, contract_* | `ENABLE_SOCIAL_COOPERATION` + civilian population with real objectives (precedent: `highland_traverse`, `frontier_living_world`) |
| `STRATEGY_COGNITION` | strategic_goal_changed, project_started, belief_assimilated, ... | Baseline strategy system reaches some of this without flags; `belief_*` needs `ENABLE_BELIEF_ASSIMILATION`; route-specific events need `ENABLE_ADVENTURE_ROUTING` |
| `NARRATIVE_QUEST` | quest_started, quest_completed, quest_failed | Real quest content — `quest_started` likely reachable; `quest_completed` is confirmed dormant corpus-wide (see sibling ticket) — this bucket may be capped below full reachability until that's fixed |
| `IDENTITY` | entity_role_changed, entity_faction_changed | **Unconfirmed reachability** — no entity in any real data this session observed ever changed role or faction; requires investigating whether a real role/faction-change mechanic (promotion, defection, rebirth-driven role change) exists in `src/` at all before this bucket can be reached by any amount of authored content |
| `CONCLUSION_DEMOGRAPHIC` | entity_killed, demographic_mortality, demographic_birth | Real hostile population + real population dynamics (already reachable in every world checked) |

## Scope
1. **Investigate** (mandatory before Plan):
   - Confirm real reachability of `IDENTITY` bucket specifically — trace whether any code path
     ever changes `entity.identity.role` or `entity.identity.faction` post-spawn. If none exists,
     this bucket is a hard ceiling regardless of authored content — a distinct finding from the
     other 9 buckets, to be disclosed honestly rather than assumed fixable by content alone.
   - Confirm real reachability of `NARRATIVE_QUEST`'s `quest_completed` specifically, given the
     sibling ticket's own confirmed corpus-wide quest dormancy — decide whether this world should
     be authored assuming that dormancy gets fixed first, or designed to reach `quest_started`/
     `quest_failed` only until then.
   - Survey existing corpus precedent worlds for reusable module combinations
     (`frontier_marches`/`simq_scale_stress_seed42` for scale + FACTION/INFORMATION-from-inception,
     `highland_traverse`/`frontier_living_world` for `ENABLE_SOCIAL_COOPERATION`,
     `hero_guild_routing` for `ENABLE_ADVENTURE_ROUTING` at real archetype scale) — this world
     should compose/extend proven modules, not author novel content from scratch where existing
     content already serves the same purpose (matching `corpus_tier_taxonomy.md`'s own
     "check before authoring redundant content" discipline).
   - Decide real world scale — large enough for statistically meaningful per-bucket samples, but
     bounded by real, measured performance cost (this session's own 5000-tick timing data: ~250s
     for the corpus's current 2 largest worlds at 59-68 entities; a larger world should have its
     own real cost measured, not assumed safe).
2. **Plan**: design the exact module composition + feature-flag set (`ENABLE_SOCIAL_COOPERATION`,
   `ENABLE_BELIEF_ASSIMILATION`, `ENABLE_ADVENTURE_ROUTING` all ON, civilian population with
   worker/guard/merchant/blacksmith, real hostile population for COMBAT, quest content), and which
   corpus tier this world belongs to (per `corpus_tier_taxonomy.md`'s own classification order —
   likely End-to-end or Stress, given it's authored to fill a real, named coverage gap rather than
   isolate one mechanic).
3. **Implement**: author the world, compile it, verify via the real long-run observation tier
   (`make simq-long-run-lifecycle-observation --worlds <new-world>`) that `phase_coverage`
   genuinely reaches a materially higher ceiling than the existing 6-world sample — report the
   real achieved bucket count (9/10 or 10/10, honestly, not assumed) and use that result to decide
   whether the remaining gap (if any) is a content gap (this world didn't fully close it either) or
   a mechanism gap (this world has the content but the metric still doesn't reflect it).

## Out of Scope
- Fixing quest-completion dormancy or the `IDENTITY`-bucket reachability question themselves, if
  Investigate confirms either is a real, deeper mechanism gap rather than a content gap — those
  become their own follow-up tickets, not folded into this one (matching this epic's own pattern
  of narrowly-scoped children).
- Recalibrating `grade_anchors.json` for this new world unless it's promoted into the fast-tier
  calibration corpus — this world's primary purpose is long-run lifecycle observation, not SimQ
  pillar-grade regression.

## Acceptance Criteria
- [ ] investigation.md confirms real `IDENTITY`/`NARRATIVE_QUEST` reachability before authoring
      (not assumed)
- [ ] investigation.md surveys existing corpus precedent for reuse, avoiding redundant authoring
- [ ] plan.md specifies exact module composition, feature flags, and corpus tier
- [ ] World authored, compiled, and added to `config/simulation_quality/corpus_registry.yaml`
- [ ] Real long-run observation run performed on the new world; the real achieved
      `phase_coverage`/bucket-count ceiling is reported honestly (whether or not it reaches 10/10)
- [ ] `docs/simulation_quality/corpus_tier_taxonomy.md` updated with the new world's entry
- [ ] Scoped pytest passes

## Related Tickets
- TCK-20260808-ENTITY-LIFECYCLE-IMPROVEMENT-EPIC (parent epic)
- TCK-20260808-GROWTH-TRAJECTORY-STILL-NEGATIVE-POST-FIX (sibling — quest/XP dormancy bears on
  `NARRATIVE_QUEST`/`GROWTH_PROGRESSION` reachability here)
- TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP (sibling — a large, long-run world will
  likely surface more mid-run-born entities, useful cross-verification once that fix lands)
- TCK-20260808-SIMQ-LONG-RUN-LIFECYCLE-OBSERVATION-TIER (DONE — the tool this world will be
  observed through)

## Related Docs
- `config/simulation_quality/entity_lifecycle_weights.yaml` (`lifecycle_phase_buckets` — the real
  10-bucket definition this world targets)
- `docs/simulation_quality/corpus_tier_taxonomy.md`
- `docs/simulation_quality/long_run_observations/*.json` (the real 6-world ceiling data this
  ticket's own gap analysis is grounded in)

## Related Stored Artifacts
None yet.

## Related Code Areas
- `data/worlds/` (new world directory)
- `config/simulation_quality/profiles/` (new profile, feature flags)
- `config/simulation_quality/corpus_registry.yaml`
- `tools/generate_corpus_registry.py`

## Assumptions / Open Questions
- Whether `IDENTITY` is reachable by any amount of authored content, or a hard engine-level
  ceiling — not assumed; Investigate must trace real code, not guess.
- Real scale/performance cost for a larger-than-current-max world at long tick lengths — not
  assumed safe; must be measured.

## Implementation Notes
(To be filled during implementation.)

## Test Summary
(To be filled during implementation.)

## Files Changed
(To be filled during implementation.)

## Completion Summary
(To be filled during implementation.)
