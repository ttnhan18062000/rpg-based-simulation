---
status: active
layer: world
authority: P1
audience: agent
ticket_id: TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION
phase: open
date: 2026-09-15
tags: [world, faction, combat]
---

# TCK-20260915-CROSS-FACTION-COMBAT-RARITY-INVESTIGATION

## Title
Cross-faction hostile interaction never occurs at all in most sampled corpus worlds — a real
system (faction sentiment) fed by nothing, not merely a reachability threshold problem; same
shape as the lair-trauma and calamity-intensity findings this week

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
While closing `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY`, sampled `pairwise_tension`
(the real, directed per-faction-pair tension driven exclusively by cross-faction
`SocialBondUpdate`s — see `src/domains/faction/sentiment.py`) across 4000-6000 ticks in 4 real
corpus worlds. Result: **3 of 4 worlds (`crowded_frontier`, `quest_dense_frontier`,
`urban_political`) show `pairwise_tension` at exactly `0.0` for every faction pair, the entire
run.** Not low — zero. No cross-faction hostile interaction happens at all. Only
`frontier_living_world` shows any real cross-faction combat in the sampled window.

This is a different, larger class of problem than a tuned threshold being slightly out of reach
(that's `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY`'s own scope, which found
`frontier_living_world`'s real interaction volume falls short of the `HOSTILE` threshold by a
tuning-sized margin). Here, in most of the corpus, the mechanism has **nothing to run on at
all** — the same shape as two other findings this week: the Lair region sitting at exactly `0.0`
trauma because it never sees combat
(`TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES`), and calamity intensity never leaving `0.0`
because its producer never fires (`TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES`). A
system that works, fed by nothing.

**A concrete, puzzling data point to start from**: `crowded_frontier`'s own world spec describes
itself as "a single frontier settlement pressed on three sides by a bandit-controlled road, a
goblin war-camp, and an orc clan's stronghold — six distinct factions contest a footprint no
larger than the corpus's smallest worlds" (`data/worlds/crowded_frontier/world.yaml`) — composed
from `bandit_road_trade_pressure`, `goblin_camp_conflict`, and `orc_clan_territory`, three
explicitly conflict-themed modules, arguably a denser hostile composition than
`frontier_living_world`'s own five module set. Yet it shows zero cross-faction interaction across
4000 ticks, while `frontier_living_world` (same three of those modules, plus others) shows real
combat between `bandit_company` and `wild_beast_pack`/`goblin_warband`. Composition density alone
does not explain the difference.

**A second, separately-flagged anomaly worth carrying into this investigation**: `urban_political`'s
own real `SocialBondUpdate` sample (from this same closing ticket's earlier diagnostic) showed
680 real nonzero interactions, **100% same-faction** — including two `hero_guild` heroes fighting
each other, two `merchant_league` merchants fighting each other. That may be a related
targeting/posture defect (entities preferentially engaging same-faction targets over real
cross-faction ones) rather than a pure "no cross-faction entities nearby" explanation — was
explicitly flagged as out of scope for the sentiment build and never investigated.

## Scope
- **Investigation first — do not assume the answer.** Determine, with real evidence, why
  cross-faction hostile interaction occurs in `frontier_living_world` but not in
  `crowded_frontier`, `quest_dense_frontier`, or `urban_political`, checking at minimum:
  1. **Spatial separation**: are opposing-faction entities ever actually co-located/in combat
     range in the worlds that show zero interaction? Compare region/spawn layouts.
  2. **Targeting/posture logic**: does combat engagement (`src/engine/combat.py` and whatever
     selects a target) have any bias toward same-faction or nearest-entity-regardless-of-faction
     targeting that would explain `urban_political`'s 100%-same-faction sample? This may be the
     `urban_political`-specific piece of the puzzle, distinct from the "nobody nearby" explanation
     that might apply to `quest_dense_frontier` (population-minimal by design, see its own world
     spec description — likely a poor sample for this question, single-faction-dominant by
     construction; note this and don't over-generalize from it).
  3. **Faction/species composition per world**: which real factions are actually represented with
     living entities in each world, at what population, and do any two hostile-by-module-intent
     factions ever have entities within combat range simultaneously.
  4. **Spawn timing/attrition**: does one side of a would-be cross-faction conflict get wiped out,
     disperse, or never spawn before the other side could engage it?
  - Sample more worlds than these 4 before generalizing a root cause — this is exactly the
    "check more than one world before concluding" discipline this same arc's investigations have
    repeatedly needed.
- Determine whether this is one root cause or several independent ones (spatial vs. targeting vs.
  population) — the `urban_political` same-faction-combat anomaly may be entirely separate from
  the `crowded_frontier`/`quest_dense_frontier` zero-interaction finding.
- If a real, scoped fix is found, propose it for peer review before building — this affects
  combat/targeting broadly, not just the faction subsystem.

## Out of Scope
- The `HOSTILE` threshold tuning question itself (`FACTION_SCALE_FACTOR`, decay) —
  `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY`'s own scope, closed separately.
- Building or changing the faction sentiment mechanism itself.
- The military-strength/`WAR` reachability driver — depends on this finding but is its own,
  separately-scoped initiative.

## Acceptance Criteria
- A real, evidence-backed explanation (not assumption) for why most sampled corpus worlds show
  zero cross-faction hostile interaction, checked across more than the 4 worlds sampled so far.
- A determination of whether this is a targeting/posture defect, a spatial/spawn-layout property
  of specific world content, a population/attrition issue, or some combination — stated plainly,
  not left ambiguous.
- If a fix is warranted, it is scoped and reviewed before being built.

## Related Tickets
- `TCK-20260915-SENTIMENT-HOSTILE-THRESHOLD-REACHABILITY` (sibling — the threshold-tuning half of
  the same underlying investigation; this ticket is the "nothing to run on" half, split out per
  peer's explicit direction not to chase it inside the threshold ticket)
- `TCK-20260914-FACTION-WAR-DECLARATION-DESIGN-QUESTION` (parent — built faction sentiment,
  surfaced both findings)
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (same shape: a system fed by nothing)
- `TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES` (same shape: a system fed by nothing)
- `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION` (filed from this
  investigation's own candidate-3 findings — `CombatEngagementPhase`'s entire tactical decision has
  zero downstream consumers)
- `TCK-20260915-COMBAT-ENGAGEMENT-4X-MEASUREMENT-NO-LONGER-REPRODUCES` (filed alongside it — the
  original 4.1x combat-volume claim used to justify enabling this feature does not reproduce today)
- `TCK-20260915-SENSORY-FILTER-SALIENCY-USES-LEGACY-FACTION-ENUM` (candidate 4, found here, filed
  separately — a real bug, measured to be a minor contributor not the primary blocker)
- `TCK-20260915-WORLDBUILDING-DANGLING-REGION-REFERENCE-SILENT-FALLTHROUGH` (found during the
  static composition comparison — `merchant_caravan`'s `preferred_regions` references a region no
  module defines; filed as its own class-level defect)
- `TCK-20260915-WORLDBUILDING-DUPLICATE-REGION-ID-ACROSS-MODULES` (found in the same trace — two
  modules composed into `frontier_living_world` both define a region named `"hometown"` with
  different bounds; filed separately)

## Related Docs
- `docs/plans/rpg_design_roadmap/faction_war_drivers_proposal.md` (§3.2 — the sentiment mechanism
  this finding is about)

## Related Stored Artifacts
_(none yet — filed as a finding, not yet investigated)_

## Related Code Areas
- `src/domains/faction/sentiment.py` (`FactionSentimentService.derive_from_bond_updates` — reads
  real `SocialBondUpdate`s; the mechanism with nothing to run on)
- `src/engine/combat.py` (real `SocialBondUpdate` producer on a hit — candidate site for a
  targeting/posture investigation)
- `data/worlds/crowded_frontier/world.yaml`, `data/worlds/frontier_living_world/world.yaml`,
  `data/worlds/urban_political/world.yaml`, `data/worlds/quest_dense_frontier/world.yaml` (world
  composition comparison)

## Assumptions / Open Questions
- Not yet known whether `quest_dense_frontier`'s zero-interaction result is even a real instance
  of this problem (it is deliberately population-minimal, likely single-faction-dominant by
  design) or a false positive that shouldn't be weighted the same as `crowded_frontier`'s.
- **Population/density scale, directly tested and weighed against**: `frontier_living_world`
  (lower density than `crowded_frontier`) produces 28x more real combat, not less — this doesn't
  fully rule out scale as *a* factor (the metropolis scenario's own 1000-entity, ~58% cross-faction
  finding is still real), but it rules out density/population alone as *the* explanation for
  `crowded_frontier`'s own near-zero rate. The module/species-composition lead (candidate 5, above)
  is now the stronger open thread.
- The decisive next step: compare `crowded_frontier`'s and `frontier_living_world`'s specific
  hostile-module content definitions for a real, disclosed behavioral difference (aggression
  parameters, patrol/wander AI, species-specific combat propensity) — not yet done.
- **Tested directly (2026-09-15) whether real combat is predator/wildlife-driven rather than
  faction-political**: of `frontier_living_world`'s 57 real attacks, checked each pairing's real
  `alignment_bucket` (`data/content/social/factions.yaml`). `wild_beast_pack` is explicitly
  catalogued `alignment_bucket: "wild"` ("Territorial animal groups. Contextual threat, not
  enemy-by-race"); `merchant_league` is `"neutral"` ("economic_actor"); `goblin_warband` is
  `"invader"` ("challenger"). Of the 57: **11 (19%) are `wild_beast_pack` vs `bandit_company`
  (wildlife-driven) — but 46 (81%) are `merchant_league` vs `goblin_warband`, two organized,
  non-wild factions.** The hypothesis as stated ("beasts attack things; factions don't attack
  each other") **does not hold** — the large majority of real attacks in this world's own sample
  are between organized factions, not wildlife. `crowded_frontier`'s own (much smaller) sample —
  `merchant_league` vs `bandit_company`, both organized, `bandit_company`'s own roster has no
  wildlife at all — is consistent with this: where real combat does occur, in both worlds sampled
  so far, it's predominantly faction-vs-faction, with wildlife as a real but minority contributor.
- Whether the exact same "real combat is universally rare in this world, any faction" pattern
  (candidate 5's finding) holds in `quest_dense_frontier` and `urban_political` too, or whether
  those worlds have their own distinct explanation — not yet checked.

## Implementation Notes
**2026-09-15, investigation in progress — two of peer's three candidate hypotheses directly
falsified with evidence, third one narrowed to a specific gap, not yet root-caused to
completion.**

**Candidate 1 (circular hostile-diplomatic-state loop) — checked, real but not the blocker for
the pairs that matter.** `combat_engagement/phase.py`'s `_consider()` filters spatial candidates
through `FactionSemanticsService.is_hostile_compat(actor_faction, target_faction, rel_context)`
(`src/content_semantics/faction.py`) before an actor will even evaluate a target — this reads
**static catalog content** (`alignment_bucket` per faction, `data/content/social/factions.yaml`;
pairwise `faction_relationships.yaml` entries with authored `hostility` axes; `perspectives.yaml`),
**not** `DiplomaticState`/sentiment/`pairwise_tension` at all. Confirmed the fallback rule
(`is_hostile()`) makes any pair where *neither* faction is bucketed `"invader"` structurally
unable to ever be flagged hostile absent an explicit catalog relationship entry — a real, if
narrower, circularity than the one peer asked about (a `DiplomaticState`-based loop does not
exist here; a static-catalog-coverage gap does). But checked the actual catalog data for
`crowded_frontier`'s factions (`bandit_company`/`goblin_warband`: `invader`; `orc_clan`:
`rival`; `hero_guild`/`town_council`: `defender`) and found **real, authored relationship
entries with `hostility: "high"` between exactly these pairs** (e.g. `orc_to_goblin`,
`bandit_company`/`hero_guild`, etc.), which `RelationProjectionService.project_relation()`
(`src/content_semantics/relation.py:126-129`) correctly projects to `label="enemy"` →
`is_hostile_compat()` returns `True`. **So the pairs that should fight in `crowded_frontier` ARE
classified as hostile by the game's own content.** This candidate is not what's blocking that
world.

**Candidate 2 (spatial separation) — directly measured, falsified for `crowded_frontier`.**
Instrumented `crowded_frontier` (2000 ticks, seed 42), sampling every 50 ticks: real hostile
faction pairs are found spatially in range (within `combat_engagement`'s own 10.0-unit radius)
**320 times**, across 7 distinct real hostile pairs (`bandit_company`/`merchant_league`,
`goblin_warband`/`hero_guild`, `bandit_company`/`goblin_warband`, `bandit_company`/`town_council`,
`goblin_warband`/`merchant_league`, `bandit_company`/`hero_guild`, `goblin_warband`/`town_council`).
Entities of opposing, hostile-classified factions are not failing to meet each other. This
candidate is also not what's blocking `crowded_frontier`.

**Candidate 3 (posture/targeting logic, live since `ENABLE_COMBAT_ENGAGEMENT`) — narrowed, not yet
fully traced.** Sampled the final `last_combat_posture` distribution across all entities in the
same run: `{'retreat': 12, 'avoid': 2, 'probe': 2, 'engage': 6, 'watch': 1}`. Two things follow:
1. `retreat`/`avoid` dominate (14 of 23, ~61%) — `CombatEngagementDecisionService.evaluate()`'s
   risk assessment (peer's own suspicion: "entities now assess threats before engaging... could
   plausibly make them less likely to start fights they'd lose") is a real, live, and plausible
   suppressor of engagement even when a hostile target is correctly identified in range.
2. **But `engage` is chosen 6 times, not zero** — and yet zero cross-faction `pairwise_tension`
   was ever recorded in this same world/run (per the sibling ticket's own probe). This means the
   break is not fully explained by risk-averse posture selection alone: either (a) an `engage`
   posture doesn't reliably reach a real damage-dealing hit by the time downstream action-routing
   /combat resolution runs (target moved, died, or the intent got dropped/overridden somewhere in
   `PostureIntentResolver` → action routing → `src/engine/combat.py`), or (b) `engage` is being
   chosen but resolving against a target that turns out not to produce a nonzero
   `SocialBondUpdate` for some other reason. **Not yet traced to a conclusion** — the next
   concrete step is following one specific `engage`-postured actor's intent through action routing
   into `combat.py`'s resolution to see exactly where (if anywhere) it stops short of a real hit.

**Not yet checked**: `urban_political`'s own separately-flagged same-faction-combat anomaly (100%
same-faction in the earlier sample) — still open, may or may not share a root cause with the
`crowded_frontier` finding above; the mechanisms investigated here (`is_hostile_compat`, spatial
range) both explicitly *exclude* same-faction pairs by construction, so that anomaly needs its own
trace through target-selection order, not just hostility classification.

**2026-09-15, candidate 4 (`SensoryFilter.filter_saliency`'s legacy-enum hostility scoring) —
found via code read, then directly measured and falsified as the primary blocker.**
`SensoryFilter.filter_saliency` (`src/engine/cognition.py:44`) scores hostility via
`ent.identity.faction != subject.identity.faction` — the raw, 4-value legacy `Faction` enum field,
not `EntityIdentityResolver`'s resolved `faction_id`. Confirmed by direct probe against real
`crowded_frontier` entities: the legacy enum collapses `bandit_company`, `goblin_warband`, and
`orc_clan` (3 genuinely distinct, mutually-hostile real factions, confirmed hostile by candidate 1's
own catalog check) into a single `Faction.MONSTER_HORDE` bucket, so the `!=` check — and the +200/
+500-nemesis/+grudge saliency bonus that depends on it — never fires between them. This traces to
the same root `EntityIdentityResolver.resolve()` was built to work around
(`TCK-20260809-COMBAT-HOSTILE-PAIRS-NEVER-ENGAGE`'s own fix never touched this consumer, since
`filter_saliency` reads the raw field directly rather than going through the resolver).

**Directly measured whether this actually drops real hostile targets from the saliency cut in
practice** (2000-tick instrumented run, `crowded_frontier`, comparing the raw pre-saliency neighbor
set against the post-`max_targets=5` result every tick a real hostile target was present): of 617
ticks where a real hostile target existed in range, it survived the saliency cut **614 times
(99.5%)** and was dropped only **3 times (0.5%)**. **This candidate is a real, independently
disclosable correctness bug, but not the operative blocker for this investigation** — worlds this
small rarely have more than `max_targets=5` real neighbors in range at once, so the missing
hostility bonus almost never changes which entities make the cut. Filed as its own small, scoped
finding rather than pursued further here (see Related Tickets) — the search for the real blocker
continues, now with confirmation that hostile targets DO reach `tactical.py`'s own (correctly-
resolved) hostiles-loop in the overwhelming majority of real opportunities.

**2026-09-15, candidate 5 (attack legality gate) — traced, and the finding reframes the
investigation's own question.** Instrumented `LegalityServiceV2.verify_attack_legality()`
directly (2000 ticks, `crowded_frontier`, seed 42): **212 calls total, 117 legal (55%)**. The 95
illegal results split `OUT_OF_RANGE` (17) and `FRIENDLY_FIRE_ILLEGAL` (78) — and the
`FRIENDLY_FIRE_ILLEGAL` cases, cross-checked against `EntityIdentityResolver`-resolved real
faction identity, are **exclusively between the allied "defender" factions**
(`hero_guild`/`town_council`/`merchant_league` pairs) — entities of factions that are not supposed
to fight being correctly blocked, not a bug. None involve the real hostile trio
(`bandit_company`/`goblin_warband`/`orc_clan`). **Directly falsifies a specific hypothesis raised
while tracing this**: `verify_attack_legality`'s own `if not has_clean:` fallback path compares the
same raw legacy `Faction` enum `SensoryFilter` was found to misuse (candidate 4, above) — a
plausible mechanism for exactly this kind of false block. Checked directly: in all 78
`FRIENDLY_FIRE_ILLEGAL` results, the legacy-enum comparison was `False` (i.e. never the reason the
function returned illegal) — that specific fallback path was not what triggered any of these.
Ruled out with evidence, not assumed.

**The more consequential finding**: separately instrumented real `CombatActions.execute_attack()`
calls (the actual damage-dealing execution, same function traced throughout this arc's
combat-engagement work) over the same 2000-tick run. **Only 2 real attacks occurred, total,
across all factions** — and the 2 that did occur were cross-faction (`merchant_league` vs
`bandit_company`). Given 117 verify_attack_legality calls found a legal target, but only 2 real
attacks executed, there is a large gap between "a legal attack decision exists" and "a real attack
executes" that this session's own tracing did not fully close: an attempt to correlate individual
`evaluate_entity_intent` calls against their own `verify_attack_legality` sub-calls produced
wildly inconsistent counts between two otherwise-identical instrumented runs (212 vs 1), most
likely because `_phase_collection()` runs entity "thought" evaluation **concurrently**
(`docs/engine/kernel.md`'s own documented pipeline), which makes a shared-mutable-state probe
(the technique used here) inherently unreliable for this specific correlation — not evidence of a
real system bug, but a limitation of this investigation's own probe methodology this session,
disclosed rather than presented as a false conclusion.

**Reframes the investigation's own question**: this data suggests the right framing may not be
"cross-faction combat is specifically blocked" so much as "**real combat of any kind is
exceedingly rare in this 38-entity world**" — 2 real attacks in 2000 ticks, full stop, regardless
of faction pairing.

**The population-scale hypothesis was the natural next thing to test — and a real, direct
comparison complicates it rather than confirming it.** No existing corpus world offers a clean
"same composition, 10x population" test (the closest, `simq_scale_stress_seed42`, is 68 entities
across 13 regions — *lower* density per region than `crowded_frontier`, not a clean scale-up). So
instead, ran the identical probe (`CombatActions.execute_attack()`, 2000 ticks, seed 42) against
`frontier_living_world` — the one corpus world already known to show real cross-faction combat —
for a real, apples-to-apples comparison:

| World | Entities | Regions | Entities/region | Real `execute_attack()` calls / 2000 ticks |
|---|---|---|---|---|
| `crowded_frontier` | 38 | 4 | 9.5 | **2** |
| `frontier_living_world` | 46 | 7 | 6.6 | **57** |

`frontier_living_world` has *fewer* entities per region than `crowded_frontier` (lower density,
not higher) yet produces **28x more real combat**. **This directly weighs against pure population/
density as the explanation** — if anything, the lower-density world fights more. The real attacking
pairs in `frontier_living_world` (`wild_beast_pack` vs `bandit_company`, `merchant_league` vs
`goblin_warband`) include `wild_beast_pack`, a faction that does not exist at all in
`crowded_frontier`'s roster — pointing toward **module/composition-specific differences** (which
hostile content modules are present, and their own AI aggression/patrol parameters) as a stronger
candidate than raw scale. Not yet traced to a specific mechanism — the next concrete step is
comparing `crowded_frontier`'s and `frontier_living_world`'s specific hostile-module definitions
(`data/content/social/` and whatever governs `wild_beast_pack`'s own behavior) for a real,
disclosed difference, rather than assuming population scale is the answer just because it was the
most recently proposed lead.

**2026-09-15, new lead from `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`'s
own measurement — a strong discriminator for this investigation, not yet followed up here.**
That ticket's reference scenario (`build_metropolis_state`, 1000 entities, seed 42) found **100%
of real attacks are cross-faction, zero same-faction**, both before and after its gate — a sharp
contrast with this ticket's own `crowded_frontier`/`quest_dense_frontier` corpus-world samples,
where cross-faction `pairwise_tension` was flat zero despite hostile pairs being spatially present.
**This means cross-faction combat is not universally rare — it's world-specific**: something about
`build_metropolis_state`'s own generation (likely its faction/entity distribution, spatial density,
or how many distinct factions it seeds relative to population) produces a world where essentially
all real combat is cross-faction, while the SimQ corpus worlds this ticket has been sampling
produce close to none. This is a genuine third axis, distinct from the three candidates traced
above (catalog hostility coverage, spatial separation, posture/targeting) — it suggests the answer
may be as much about *which worlds get sampled* as about any one mechanism inside
`combat_engagement`. Not yet investigated: what specifically differs between
`build_metropolis_state`'s world generation and the SimQ corpus profiles' own world-building path
(entity count, faction count, spatial layout, faction assignment logic) that would explain this gap.

**2026-09-15, the one bounded attempt (peer's explicit final scope): static world-spec comparison
of `merchant_league`'s own composition between the two worlds — no instrumentation, no runs.**
`merchant_league` is the one faction present as a real, meaningful combatant in both worlds'
samples, so it's the natural pivot. Traced its composition end to end via the content catalog:

- **`crowded_frontier`'s only source of `merchant_league` entities**: the `merchant_caravan`
  population (`data/content/entities/populations.yaml`), pulled in via the
  `bandit_road_trade_pressure` module (present in both worlds). `merchant_caravan`'s own
  `preferred_regions: ["trade_road", "hometown"]` — but **no module in either world's composition
  defines a region literally named `"trade_road"`** (`bandit_road_trade_pressure` itself defines
  `"bandit_road"`, a different id). This reference falls through to `merchant_caravan`'s second
  preference, `"hometown"` — specifically `frontier_village_core`'s own `"hometown"` region,
  `grid_bounds: [10, 10, 40, 40]`, the far corner of the map.
- **`frontier_living_world` has a second, additional source**: the `trading_company_hub` module
  (present only here, not in `crowded_frontier`'s module list at all), which defines its **own**
  region also literally named `"hometown"` — but with completely different bounds,
  `grid_bounds: [45, 10, 80, 45]` — and an explicit `population_recipes` entry spawning 3
  `merchant_league` entities directly into it (`spawn_region: "hometown"`).
- **The bounds matter concretely**: `bandit_road_trade_pressure`'s own hostile region
  (`"bandit_road"`) is `[40, 40, 100, 60]` and `goblin_camp_conflict`'s (`"goblin_camp"`, present
  in both worlds) is `[95, 20, 125, 55]`. `frontier_village_core`'s `"hometown"` (`[10,10,40,40]`)
  barely touches `bandit_road`'s edge and sits far from `goblin_camp`. `trading_company_hub`'s own
  `"hometown"` (`[45,10,80,45]`) **overlaps `bandit_road`'s x-range directly and sits much closer
  to `goblin_camp`.** If `frontier_living_world`'s merchants spawn into this second, closer
  `"hometown"` instance — plausible given `trading_company_hub` is the later-composed module and
  explicitly targets `spawn_region: "hometown"` for its own population — that alone would explain
  materially more real spatial overlap with hostile territory than `crowded_frontier`'s
  single-source, far-corner placement.
- **A genuine remaining ambiguity, not chased further per the explicit scope cap**: two modules
  in the same world composition both defining a region literally named `"hometown"` with different
  bounds is itself worth naming — it's unclear from the specs alone whether the compiler keeps
  both as distinct regions, merges them, or has one silently override the other for entities from
  *both* modules (which would mean `frontier_village_core`'s own villagers, not just
  `trading_company_hub`'s merchants, get relocated). Confirming which happens requires either
  reading the world-compiler's own region-merge logic or one instrumented run — explicitly not
  done here, per the cap on this investigation's remaining budget.

**This is a real, static, well-evidenced structural difference — a plausible, disclosed mechanism,
not a confirmed root cause.** It was not verified with a live re-run (deliberately, per peer's
explicit "static comparison only, then stop" instruction), so it should be read as the strongest
remaining lead for whoever picks this up next, not as a closed finding.

**Investigation paused here, per peer's explicit scope cap** ("one bounded attempt, then park
regardless of outcome"). Six candidates traced and falsified with real evidence (catalog hostility
coverage, spatial separation, posture/targeting write-only-ness, the saliency legacy-enum bug, the
attack-legality gate, the predator-driven-combat hypothesis), and one plausible structural
mechanism identified via static comparison but not yet verified live. This narrows the problem
space substantially for a future pass without claiming a fix or a fully confirmed root cause.

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
**Investigation paused (not closed), per explicit scope cap.** Not resolved to a fix — deliberately
stopped short of one. Real progress: six candidate root causes traced and falsified with direct
evidence (catalog hostility coverage was correct; spatial separation was not the blocker; the
posture/targeting break was resolved by identifying `combat_engagement`'s write-only-ness in the
sibling ticket; a real legacy-Faction-enum bug in `SensoryFilter.filter_saliency` was found and
filed, measured to have only 0.5% practical impact; the attack-legality gate mostly passes for
real hostile pairs and its illegal results are correctly-blocked allied friendly-fire, not a bug;
and a specific "predator-driven, not faction-driven" hypothesis was tested against real data and
rejected — 81% of real combat in the comparison world is faction-vs-faction). One plausible,
evidence-backed structural mechanism was identified via a purely static world-spec comparison
(differing region composition for `merchant_league` between the two worlds, driven by
`crowded_frontier` lacking the `trading_company_hub` module) but was not verified with a live
run. Whoever picks this up next starts from a narrow, evidenced position rather than the original
broad question.
