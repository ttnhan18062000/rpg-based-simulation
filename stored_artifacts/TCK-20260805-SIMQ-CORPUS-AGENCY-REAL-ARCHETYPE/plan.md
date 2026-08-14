---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE
artifact_type: plan
tags: [simulation-quality, world, adventure, corpus, calibration]
---

# plan.md — TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE

## Ordered Steps

1. **Verify gap #4 against real corpus data and content**, per the ticket's own flagged open
   question — compared `hero_guild_routing`'s scale (31 entities/4 regions/10 quests/5 factions)
   against real Unit-tier peers (16-18/1-3/3-6/3) and End-to-end peers (`urban_political`,
   `dungeon_crawl`), and directly verified its composed content includes real economic/social
   modules (`frontier_village_core`'s shop/blacksmith/trade content).
2. **No new world authored** — `hero_guild_routing` already substantially exceeds every real
   Unit-tier world's scale and matches/exceeds End-to-end peers; authoring a new world would
   duplicate its already-established role.
3. **Correct `corpus_tier_taxonomy.md`**: mark gap #4 CLOSED in the gap-list section, and update
   `hero_guild_routing`'s own per-world table entry to explicitly acknowledge its dual role
   (Unit-tier test-suite isolation + gap-4 real-archetype closure), not just the isolation framing.
   - Files: `docs/simulation_quality/corpus_tier_taxonomy.md`.
4. **Fill this ticket's Completion Summary**, noting the now-moot ECONOMY-ticket motivation
   alongside the independent scale/content finding.

## Scope Guards

- Do NOT author a new world — confirmed unnecessary via direct scale/content comparison.
- Do NOT reclassify `hero_guild_routing`'s formal tier label away from "Unit" — it still correctly
  describes the world's role in the test suite (isolating `ENABLE_ADVENTURE_ROUTING`); this ticket
  only adds an acknowledgment of its additional real-archetype role, not a tier change.
- Do NOT touch `hero_guild_routing`'s own `world.yaml` or anchors — correct, already-committed.

## Dependency Map

Step 3 depends on step 1's finding. No other dependencies.

## Acceptance Criteria Map

- AC1 (new world with routing on, classified as genuine archetype) → **not met, deliberately** —
  found `hero_guild_routing` already satisfies this; investigation.md documents the evidence.
- AC2 (classified in corpus_tier_taxonomy.md, citing gap #4 closure) → Step 3, applied to
  `hero_guild_routing`'s existing entry instead of a new one.
- AC3 (anchors committed, tests pass) → N/A, no new anchors; existing regression suite verified
  unaffected.
- AC4 (ECONOMY ticket cross-referenced with new substrate) → N/A — that ticket already closed
  without needing new substrate, independent of this ticket's own finding.

No unresolved questions requiring human review.
