---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA
phase: done
date: 2026-10-05
tags: [world, investigation]
---

# TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA

## Title
Split `frontier_living_world`'s deaths by contested zone and by killer/victim ecology, to decide
whether `near_forest` and `wolf_den` sit at 0.0 trauma because the region lookup shadows them, because
`bandit_road`'s 20-tile-wide rectangle claims den ground, or because no fighting happens there at all

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
**This is the measurement that should have preceded the overlap ruling, and it is filed before the rule
it tests.** The planner ruled a resolution rule (smallest-area-containing region) on an unmeasured
premise of nesting; Lane B implemented it and the measurement refuted the premise. The replacement rule
(authored precedence, recommended by `rpg-designer` as draft `LOC-08`) must not be built on a second
unmeasured premise — namely that resolution is why `near_forest` and `wolf_den` hold 0.0 trauma.

**What is already established** (Lane B, `frontier_living_world`, 10000 ticks, seed 42, smallest-area
rule implemented): `near_forest` and `wolf_den` are at **0.0 trauma**; `bandit_road` is credited **121**
deaths and `goblin_camp` **118**; credited-to-no-region fell 23 -> 16; `hometown` 7 -> 12 via the
inclusive-edge fix. Trauma crosses the 50 instability threshold in two regions (`goblin_camp` tick 5211,
`bandit_road` tick 5317, both ~110 by tick 10000).

**Verified geometry** (`data/content/world_modules/`, planner-checked):

**Corrected 2026-10-05.** An earlier revision of this ticket listed five regions and claimed no pair
was nested. `frontier_living_world` has **eight** regions, and one pair **is** nested. The full table,
measured from `data/worlds/frontier_living_world/resolved/world.resolved.yaml` at main `544b1d341`
with bounds inclusive on both ends:

| region | bounds | area |
|---|---|---|
| `hometown` | `[10,10,40,40]` | 961 |
| `bandit_road` | `[40,40,100,60]` | 1281 |
| `goblin_camp` | `[95,20,125,55]` | 1116 |
| `old_mine` | `[20,60,60,105]` | 1886 |
| `trading_hometown` | `[45,10,80,45]` | 1296 |
| `haunted_battlefield` | `[120,20,160,60]` | 1681 |
| `near_forest` | `[45,10,90,55]` | 2116 |
| `wolf_den` | `[70,30,105,70]` | 1476 |

Contested tile counts: `trading_hometown`∩`near_forest` **1296 (fully nested)**,
`bandit_road`∩`near_forest` 736, `bandit_road`∩`wolf_den` 651, `near_forest`∩`wolf_den` 546,
`goblin_camp`∩`wolf_den` 286, `bandit_road`∩`trading_hometown` 216,
`goblin_camp`∩`haunted_battlefield` 216, `bandit_road`∩`goblin_camp` 96,
`trading_hometown`∩`wolf_den` 176, `bandit_road`∩`old_mine` 21.

**`trading_hometown` (1296 tiles) sits fully inside `near_forest` (2116).** Under the smallest-area
rule in force, `near_forest` owns only **200 of its 2116 tiles** and `wolf_den` **525 of 1476**.

**Overlap is not rare**: 15 of 24 resolved corpus worlds have overlapping regions, 14 beyond 1-tile
edge artifacts (planner-verified over all `data/worlds/*/resolved/world.resolved.yaml`).
`generated_frontier_3_42`, which Lane B measured as nearly overlap-free, is the **exception**, not a
representative second sample.

**The three hypotheses this ticket discriminates**, per `rpg-designer`'s brief:
- **(H1) Resolution shadows them.** Deaths occur in contested zones and are credited to the road. Then
  the precedence declaration is what matters.
- **(H2) The geometry is the defect.** The road's 121 deaths are concentrated in `road ∩ den` / triple
  and are mostly wolf-ecology kills. Then the road is mis-crediting den bloodshed and the fix is
  **content** (narrow the rectangle), not a precedence flip.
- **(H3) Neither.** `near_forest`/`wolf_den` have ~0 deaths **even in their uncontested zones**. Then
  the fighting happens elsewhere, 0.0 trauma is not a lookup question, and neither the rule nor the
  geometry matters for trauma. This would also mean the overlap work must not be cited as a trauma fix.
- **(H4) `near_forest` barely exists as an answer.** Added 2026-10-05 by `rpg-designer`:
  `trading_hometown` is **fully nested** inside `near_forest` and takes 1296 of its 2116 tiles, leaving
  it only 200 owned tiles. Its 0.0 trauma may then be neither shadowing-by-road nor absence-of-fighting
  but simple arithmetic — almost no point resolves to it. **This is the hypothesis a nesting rule (draft
  `LOC-08` clause 3a, contained-region-wins) would fix with no content edits**, and it is the one the
  earlier five-region table made invisible. The split **must report `trading_hometown` as its own zone**
  or H4 cannot be distinguished from H1.

H3 is the outcome that would most change what we do next, so the measurement must be able to show it.

## Scope
1. On `origin/main` with the region-lookup unification landed, run `frontier_living_world`, 10000 ticks,
   seed 42, and **record every death's position**.
2. Classify each death into: uncontested `bandit_road`; `road ∩ near_forest`; `road ∩ wolf_den`; triple
   (`road ∩ forest ∩ den`); `near_forest ∩ wolf_den`; uncontested `near_forest`; uncontested `wolf_den`;
   `goblin_camp ∩ wolf_den`; uncontested `goblin_camp`; **`trading_hometown` (the nested town), both its
   own uncontested interior and `trading_hometown ∩ near_forest`**; credited-to-no-region. Report counts
   per zone. **The `trading_hometown` zones are required, not optional** — without them H4 is
   indistinguishable from H1.
3. For each zone also record **killer and victim faction / ecology**, so "wolves killing travellers on
   den ground credited to the road" is distinguishable from "bandits killing travellers on the road".
4. State which hypothesis the data supports, **including H3**, and say so even if it means the overlap
   work has no bearing on trauma.
5. Report each region's **owned-tile share** under the rule in force, so a region owning zero tiles is
   visible as such (`rpg-designer`'s refutation condition 3).
6. Re-run on at least one other corpus world with overlapping regions, so the conclusion is not
   single-world. If `generated_frontier_3_42` is used, fix the probe watch list first — it previously
   named regions that world lacks and crashed.

## Out of Scope
- **Choosing or implementing the precedence rule.** That is owner decision 13, pending. This ticket
  informs it and must not pre-empt it.
- Changing `bandit_road`'s bounds. If H2 holds, the content fix is a separate ticket under the
  feature-freeze discipline (memo row 7), not this one.
- The trauma-to-panic mapping (`TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE`,
  P0, blocked on ratification).
- Terrain paint. Whether paint order follows the same precedence is part of decision 13.

## Acceptance Criteria
- [x] Death positions recorded and classified into every zone listed in scope 2, with counts (`investigation.md`, zone table; every zone listed has a row, the unlisted-zero ones as an explicit zero row).
- [x] Killer/victim ecology recorded per zone.
- [x] Verdict: H3 for own ground (zero deaths on uncontested `near_forest`, `wolf_den` and the `trading_hometown` interior, in all five worlds measured); H1 narrowly (every death inside `near_forest`, `wolf_den`, `trading_hometown` lies in a zone shared with `bandit_road` and is credited to it, but they are hazard deaths at a few spawn tiles); H2 not supported; H4 not separable from H3. Stated outright: the overlap work is not a trauma fix for fighting.
- [x] Per-region owned-tile share reported (`geometry.jsonl`, all 24 worlds).
- [x] Second and further overlapping worlds measured: `frontier_extended`, `simq_scale_stress_seed42`, `hero_guild_routing`, `lifecycle_full_coverage_world`. `quest_dense_frontier` failed at kernel construction (artifact-manifest JSON decode error) and was not investigated.
- [x] The probe is committed with a README under this ticket's stored artifacts.
- [x] Reported to the planner before owner decision 13; the result also produced `TCK-20261005-REGIONAL-TRAUMA-IS-PRODUCED-BY-A-BOSS-RESPAWN-AND-HAZARD-DEATH-LOOP-NOT-BY-FIGHTING`.

## Related Tickets
- `TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER` — the lookup unification; this ticket
  tests the premise behind its successor rule.
- `TCK-20261005-HAZARD-GROWTH-CAPPED-BELOW-EVERY-AUTHORED-COMBAT-REGION` — sequenced after the overlap
  work for the same reason (changing region credit changes which regions reach trauma 50); this
  measurement tells us whether that sequencing matters.
- `TCK-20261005-REGIONAL-TRAUMA-FED-INTO-PANIC-AS-IF-NORMALISED-MAKES-EVERYONE-FLEE` — P0, consumes
  per-region trauma; its observed flee rate needs re-measuring once membership is unified.

## Related Docs
- `docs/mechanics/06_worldbuilding_foundation.md` :32 (the false "strictly disjoint, enforced" claim)
  and :37 (declaration order as the terrain priority mechanism).
- `docs/mechanics/regional_sovereignty.md` — region boundaries.
- The world-rule catalog's `LOC-01` (one answer per subject) and `LOC-03` (containment is declared, not
  an incidental consequence of coordinates overlapping) — the rule constraints `rpg-designer` cited.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261005-REGION-OVERLAP-VALIDATION-FLAG-HAS-NO-READER/probes/`
  (with README) — Lane B's existing probes. **Extend these rather than writing new ones**; they already
  record credited deaths per region, so this ticket adds position classification and ecology, not a new
  harness.

## Related Code Areas
- `src/core/region_resolution.py::resolve_region_among` — the unified resolution point.
- `src/world/transformation.py:79-82` — `replace(region, kind=next_kind)`, the runtime `kind` rewrite
  that rules out keying precedence on type/kind.
- `src/worldbuilding/compiler.py:476` — `kind=r_spec.type.upper()`.
- `data/content/world_modules/wolf_den_near_forest.yaml:24-31` — the documented terrain-fill precedence
  that currently contradicts the lookup's.

## Assumptions / Open Questions
- **Lane.** Lane B (`rpg-implementer-2`), world domain. Measurement only; no `src/` behaviour change
  expected, so no holds requested beyond its existing ones.
- **Planner observation, corrected 2026-10-05 — do not spend measurement time on this.** `bandit_road`
  is declared twice with different type *and* geometry: `road` `[40,40,100,60]` in
  `bandit_road_trade_pressure.yaml`, `wilderness` `[50,30,85,60]` in `scalable_bandit_camp.yaml`. I first
  read this as a latent precedence conflict. **It is not, and `rpg-designer` was right to correct it.**
  Verified: the two modules are never composed together (`bandit_road_trade_pressure` is in
  `crowded_frontier`, `generated_frontier_3_42`, `frontier_extended`, `frontier_living_world`,
  `frontier_marches`, `simq_scale_stress_seed42`, `urban_political`; `scalable_bandit_camp` only in
  `dungeon_crawl`), and a duplicate region id inside one world already aborts assembly
  (`src/worldbuilding/schema.py:320-327`, `validate_unique_identifiers`, "Duplicate region ID found").
  So these are **two different regions sharing a name across worlds** — an identity smell worth
  recording, not a conflict to resolve. **No scope item follows from it**; it is noted here only so a
  later reader does not rediscover it and draw the conclusion I drew.
  The reason precedence must still be reconciled at **composition** level is different and stronger:
  precedence is a relation between *pairs*, and regions from different modules only meet inside a
  composition, so a module cannot rank itself against neighbours it cannot see.
- Open: whether death position is already recorded in the event stream, or whether the probe must add
  it. Check before building instrumentation.

## Implementation Notes
Measurement only; no `src/` change. Probes extended (not a new harness) per the ticket. All runs under `audit_mode` with `max_tick_budget_ms=1e9`; `frontier_living_world` run twice, byte-identical. Primary base `54c31ee73`. Full findings in `agent-working/stored_artifacts/TCK-20261005-CONTESTED-ZONE-DEATH-SPLIT-DECIDES-WHETHER-OVERLAP-OR-GEOMETRY-CAUSES-ZERO-TRAUMA/investigation.md`.

## Test Summary
No behaviour changed, so no new tests. Controls: byte-identical repeat run; geometry matches the planner's tile table; death rows come from the update the kernel commits, so `credited` agrees with the trauma writer.

## Files Changed
Stored artifacts and probes only (`probes/zones.py`, `geometry.py`, `analyse.py`, `contamination.py`, outputs, `plan.md`, `investigation.md`, `test_plan.md`).

## Completion Summary
The deaths on `frontier_living_world` are not fights: 232 of 233 are hazard drain, 158 of them world bosses dying at spawn tiles. Own-ground zones have zero deaths; every death inside `near_forest`, `wolf_den` and `trading_hometown` is in a zone shared with `bandit_road` and credited to it. All three `haunted_battlefield` author-call pairs show 100% `undead_remnants` dying to the other region's hazard (24 deaths, five worlds); `old_mine`/`sacred_grove`/`deep_forest` had zero deaths, so no evidence. The finding led to the boss-loop P0. No precedence rule chosen (owner decision 13).

