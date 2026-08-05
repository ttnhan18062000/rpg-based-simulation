---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE
phase: open
date: 2026-08-05
tags: [simulation-quality, world, adventure, corpus, calibration]
---

# TCK-20260805-SIMQ-CORPUS-AGENCY-REAL-ARCHETYPE

## Title
Author a routing-capable (AGENCY-active) world that is a real gameplay archetype, not a purpose-built calibration fixture

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
`docs/simulation_quality/corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" (gap #4) notes the
only `ENABLE_ADVENTURE_ROUTING`-active world in the corpus, `simq_routing_test`, is a purpose-built
minimal-calibration fixture, not a coherent gameplay archetype (hero_guild_routing also runs
routing, but per this session's own investigation is itself closer to a routing-focused fixture
than a broad archetype — the investigation phase should confirm/dispute this and decide what "real
archetype" means precisely here). No world exists that is both a genuine end-to-end-tier gameplay
scenario *and* has routing genuinely active by default.

**Directly relevant to already-open work:** `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`
needs real, non-synthetic entity situations to determine whether `AdventureRouteScorer`'s craft/buy
selection bias is a miscalibration or a correct reflection of archetype incentives (per that
ticket's investigation-first scope and the explicit caution against forcing unrealistic routes). A
world built specifically to be a coherent, realistic, routing-active archetype would give that
investigation a much better substrate than the current purpose-built fixtures.

Note (2026-08-05): filed as backlog per the same corpus-breadth-deprioritization rationale as its
siblings, but flagged higher within that backlog given the direct connection to the already-open
ECONOMY investigation above.

## Scope
- Author a new end-to-end-tier world with `ENABLE_ADVENTURE_ROUTING` on by default, composed as a
  genuine, coherent gameplay scenario (not a minimal calibration fixture) — e.g. a settled region
  with real economic/social content where entities plausibly have reason to adventure, craft, buy,
  and trade as part of ordinary life, not just a routing-isolation test.
- Classify and register per `corpus_tier_taxonomy.md`'s decision tree (end-to-end tier, since it
  represents a coherent scenario rather than isolating one mechanic or filling a narrow scale gap).
- Calibrate and commit anchors.
- Update `corpus_tier_taxonomy.md`'s gap #4 entry to closed, citing this ticket.

## Out of Scope
- The other 3 named scale-diversity gaps — sibling tickets, independent.
- `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS`'s own investigation and any scoring
  changes — this ticket only provides better corpus substrate for that investigation, it does not
  perform or preempt it.
- Reopening `ENABLE_ADVENTURE_ROUTING`'s DA-ruled default for the corpus at large (Factor 1 from
  the ECONOMY ticket) — this world opts routing on for itself specifically, which is a normal
  per-world content decision already supported (`hero_guild_routing`, `simq_routing_test` both do
  this today), not a change to the flag's global default.

## Acceptance Criteria
1. New world exists with `ENABLE_ADVENTURE_ROUTING` on, classified as a genuine end-to-end
   archetype (justified in `plan.md` against what distinguishes it from `simq_routing_test`'s
   fixture framing).
2. World is classified and documented in `corpus_tier_taxonomy.md`, citing gap #4's closure.
3. Anchors committed and `test_grade_regression.py` passes for the new world.
4. `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS` is updated (via a comment/cross-reference,
   not a scope change) to note this new world is available as investigation substrate, if that
   ticket hasn't already closed by the time this one lands.

## Related Tickets
- `TCK-20260704-SIMQ-CORPUS-TIERS-EPIC` — parent epic that identified this gap.
- `TCK-20260805-SIMQ-ECONOMY-ADVENTURE-ROUTE-SCORER-BIAS` — direct beneficiary of this world; soft
  relationship only, neither ticket blocks the other.
- `TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP`,
  `TCK-20260805-SIMQ-CORPUS-RESOURCE-DENSITY-DECOUPLE`,
  `TCK-20260805-SIMQ-CORPUS-QUEST-DENSITY-DECOUPLE` — sibling tickets, mutually independent.

## Related Docs
- `docs/simulation_quality/corpus_tier_taxonomy.md` — "Named scale-diversity gaps" §, gap #4.
- `docs/simulation_quality/extension_points.md` §1 (World breadth).

## Related Stored Artifacts
None yet — standard tier, staging artifacts to be created at Scope.

## Related Code Areas
- `data/worlds/` (new world directory)
- `tests/simulation_quality/fixtures/grade_anchors.json`

## Assumptions / Open Questions
- What precisely distinguishes a "real archetype" from a "purpose-built fixture" for this axis is
  not pinned down here — the investigation phase must define and justify the distinction, including
  confirming or disputing whether `hero_guild_routing` already partially satisfies this gap.

## Implementation Notes
(fill during implementation)

## Test Summary
(fill during implementation)

## Files Changed
(fill during implementation)

## Completion Summary
(fill during implementation)
