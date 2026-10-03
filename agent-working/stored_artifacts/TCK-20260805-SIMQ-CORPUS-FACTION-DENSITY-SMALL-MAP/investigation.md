---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP
artifact_type: investigation
tags: [simulation-quality, world, faction, corpus, calibration]
---

# investigation.md — TCK-20260805-SIMQ-CORPUS-FACTION-DENSITY-SMALL-MAP

## Current Behavior (file:line refs)

The ticket's premise, from `docs/simulation_quality/corpus_tier_taxonomy.md`'s "Named
scale-diversity gaps" section (gap #1, before correction): "No world combines a high
distinct-faction count (6-9) with a small map — faction density and world size currently move
together."

**This premise was false at the time this ticket was filed, and the doc itself already
contradicted it.** `corpus_tier_taxonomy.md`'s own per-world table (line 141, unchanged) already
documented: `crowded_frontier` | Stress | 38 entities, 4 regions — **fills gap 1 (many-factions/
small-map)**: 6 distinct populated factions in a 4-region footprint (`TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS`).

## Verification (not trusting either doc section at face value)

Directly compiled 3 worlds via `WorldCompiler.compile()` (not just reading declared `factions:`
lists, which — confirmed separately in this investigation — routinely list a faction with no
archetype actually assigned to it, e.g. `moon_cult_ruins` declares `moon_cult` but only
`arcane_circle` archetypes are ever populated):

| World | Real populated factions (via `entity.properties["faction_id"]`) | Regions | Entities |
|---|---|---|---|
| `crowded_frontier` | 6: town_council, merchant_league, bandit_company, goblin_warband, hero_guild, orc_clan | 4 | 38 |
| `generated_frontier_3_42` | 7: town_council, merchant_league, bandit_company, goblin_warband, arcane_circle, wild_beast_pack, orc_clan | 6 | 44 |
| (this ticket's draft `faction_dense_frontier`, built then reverted) | 7: town_council, merchant_league, goblin_warband, arcane_circle, wild_beast_pack, orc_clan, swamp_tribe | 6 | 44 |

Both `crowded_frontier` (6 factions) and `generated_frontier_3_42` (7 factions) sit squarely
within the gap's own stated 6-9 target range, on maps at least as small as any "small map" world
in the corpus. **Gap #1, as literally stated, is already closed — twice over.**

A draft world was authored, resolved, compiled, and calibrated (3 seeds, 200t) before this
verification step caught the redundancy — its aggregate footprint (44 entities, 6 regions, 7
factions) turned out **identical to `generated_frontier_3_42`'s**, just with a different specific
faction mix (swamp_tribe instead of bandit_company). Adding a 3rd world with no marginal coverage
beyond what 2 existing worlds already provide would be padding the corpus, not closing a real gap
— directly contrary to this session's own established guidance (corpus-breadth expansion
deprioritized relative to fixing/verifying real signals, `docs/audits/D20_simq_quality_status_review.md`).
The draft world, its 3 anchor entries, and the accompanying test-file edits were reverted before
commit — no trace remains in the tracked corpus.

## Root Cause

`corpus_tier_taxonomy.md`'s "Named scale-diversity gaps" section (list, near the bottom of the
doc) was never updated when `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` closed gap #1 — even though
the same document's own per-world table, a few dozen lines earlier, already recorded the closure
correctly. Two sections of the same doc disagreed with each other, and this ticket was filed
citing the stale section without cross-checking the other.

## Docs Requiring Update
- `docs/simulation_quality/corpus_tier_taxonomy.md`: gap #1 in the "Named scale-diversity gaps"
  list marked CLOSED, citing both `crowded_frontier` and `generated_frontier_3_42`, explaining the
  staleness and why no new world was authored.

## Parity Ledger Overlap
None.

## Prior Work
- `TCK-20260704-SIMQ-CORPUS-STRESS-WORLDS` — authored `crowded_frontier`, which already closed
  this gap (correctly documented in the per-world table, just not in the gap-list section).
- `TCK-20260707-SIMQ-GENERATED-FRONTIER-BASELINE-ANCHORS` — authored `generated_frontier_3_42`,
  which also independently closes this gap (not documented as such anywhere, since it wasn't
  authored with that framing).

## Risks and Open Questions
None outstanding. The finding is conclusive and independently verified via a real compile, not
just a doc reading.
