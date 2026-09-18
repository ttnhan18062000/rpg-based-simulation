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
- `TCK-20260918-EPIC-PROGRESSION-STARVATION-CHAIN` — groups this ticket with 4 others that together
  measured one causal chain (incidental combat → few kills → XP never accumulates → no level-ups →
  `stats_dirty` never fires); see that epic's own `SEQUENCE.md` for why child 1
  (`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION`) is sequenced to resume this
  investigation, not the other way around
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
- `TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES` (sibling instance of the same pattern —
  see that ticket's own "Named finding" section for the general statement: mechanics whose
  preconditions depend on world geometry that nothing validates)
- `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION` (2026-08, closed — independently found
  `resolve_attack()`: 0 real calls in 2000-tick runs, for an unrelated reason (rebirth reachability);
  the 2026-09-17 addendum above is the third independent confirmation of the same fact)
- `TCK-20260915-COMBAT-GATE-DOWNSTREAM-STARVATION-FACTION-AND-BOSS-GATE` (open, P2 — its own Scope
  item 1 asked for exactly the gate-effect measurement in the 2026-09-17 addendum above; cites this
  ticket's own measurement rather than duplicating it, per the "one place defines the fact" rule)
- `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS` (closed — the progression
  investigation whose own resumption led back to this ticket)

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

## Addendum — 2026-09-17, resumed per user decision (progression-defect thread), a 7th candidate
## checked and a new, sharper finding

**Context**: resumed after `TCK-20260916-DERIVED-COMBAT-STAT-RECALCULATION-UNOBSERVED-IN-CORPUS`
(closed) found progression XP never crosses a level threshold in these same three worlds
(`crowded_frontier`, `quest_dense_frontier`, `hero_guild_routing`) due to real combat being too
rare — this ticket's own investigation is the most likely upstream cause. Peer raised a 7th
candidate not previously checked: `TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`
(closed same day as this investigation was paused) built a real posture-veto gate that cuts real
attacks 57.3% overall / 58.1% cross-faction on the `metropolis` reference scenario — could this
epic's own gate be starving the thing it was built to regulate?

**Candidate 7 (the posture-veto gate) — checked directly, falsified, for a stronger reason than
initially suspected.** Peer's own back-of-envelope math already argued against it: the pre-gate
baseline on `crowded_frontier` (candidate 5, above) was 2 real attacks in 2000 ticks, so a gate
that removes at most those 2 cannot be *the* cause of near-zero combat there. Direct measurement
confirms this and goes further. Ran the same gate ON/OFF A/B the closed gate ticket used
(`ENABLE_COMBAT_ENGAGEMENT` toggled via `state.feature_flags`, the corrected toggle mechanism —
not the silently-ignored `Kernel(flags=...)` dict), instrumenting real
`CombatActions.execute_attack()` calls, on `metropolis` (1000 entities, 30 ticks: 5 warmup + 25
sample, matching the closed ticket's own convention) alongside `crowded_frontier`,
`quest_dense_frontier`, `hero_guild_routing` (2000 ticks each) in the same run, reported per-world
per peer's explicit instruction (never aggregated — metropolis and a 38-entity corpus world tell
completely different stories):

| World | Entities | Ticks | Gate OFF (total / cross-faction) | Gate ON (total / cross-faction) |
|---|---|---|---|---|
| `metropolis` | 1000 | 30 | 2310 / 2310 | 1027 / 1027 |
| `crowded_frontier` | 38 | 2000 | 0 / 0 | 0 / 0 |
| `quest_dense_frontier` | 9 | 2000 | 0 / 0 | 0 / 0 |
| `hero_guild_routing` | 35 | 2000 | 5 / 5 | 0 / 0 |

`metropolis` reproduces the closed gate ticket's own direction (real, large reduction; 100%
cross-faction matching its own finding). All three corpus worlds show at most 5
`execute_attack()` calls in 2000 ticks in *either* gate state — the gate genuinely has no
measurable effect on these worlds, confirming peer's hypothesis.

**But the reconciliation with this investigation's own progression-defect context revealed
something sharper than "the gate doesn't matter here."** The progression ticket separately found
10 real kills in `crowded_frontier` over 1000 ticks (instrumented via
`CombatRewardClassificationService.classify_defeated_target`, not `execute_attack()`) — a real
discrepancy against this ticket's own 0-`execute_attack()`-calls reading that had to be resolved,
not glossed over, per this arc's own standing discipline. Direct reconciliation (wrapping
`CombatResolutionSystem.resolve_attack()`, `resolve_opportunity_attack()`, and
`resolve_multi_attack()` separately, plus `execute_attack()`, in one run, 1000 ticks each, gate at
its real default ON):

| World | `execute_attack`/`resolve_attack` calls | `resolve_multi_attack` calls |
|---|---|---|
| `crowded_frontier` | 2 | **181** |
| `quest_dense_frontier` | 0 | 0 |
| `hero_guild_routing` | 0 | **2177** |

**Almost all real combat resolution in these worlds runs through `resolve_multi_attack()` —
`movement.py`'s opportunity-attack mechanic, triggered on disengagement/pursuit — not through
`resolve_attack()`, the decision-driven path reached via `TacticalDecisionSystem` →
`ActionRouter.execute_action()` → `CombatActions.execute_attack()`.** The posture-veto gate lives
exclusively in `ActionRouter.execute_action()`'s `ATTACK`/`SKILL` dispatch (see
`src/engine/domain/action_router.py:76-105`) — `movement.py`'s opportunity-attack call site
(`src/engine/movement.py:240`, calling `CombatResolutionSystem.resolve_multi_attack()` directly)
never routes through `ActionRouter` at all, so the gate structurally cannot touch it. This is a
**stronger** falsification of the gate-starvation hypothesis than the arithmetic alone: it's not
just that the gate's own effect is small relative to an already-thin baseline — the gate doesn't
apply to the mechanism producing the overwhelming majority of these worlds' real combat, full
stop. (Reward construction for a kill is present in `resolve_multi_attack()` too — ported there by
`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION` specifically because it observed the
same "`resolve_attack()`: 0 real calls" fact for a different reason years earlier — so opportunity
kills do correctly grant XP; this is not a second wiring gap on top of the first.)

**This is a third, independent confirmation of the same underlying fact, now triangulated from
three unrelated investigations**: `TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`
(2026-08) found `resolve_attack()` has 0 real calls in 2000-tick runs while investigating rebirth
reachability; this investigation's own candidate 5 (2026-09-15) independently found only 2 real
`execute_attack()` calls in 2000 ticks on `crowded_frontier` while investigating combat rarity; and
this addendum (2026-09-17) confirms it again while investigating the veto gate, and additionally
identifies `resolve_multi_attack()` as the actual dominant real-combat mechanism filling that gap.
**The sharpened open question this investigation should hand to whoever picks it up next is no
longer "why is cross-faction combat rare" in the abstract — it is specifically "why does
`TacticalDecisionSystem`'s own decision-driven `ATTACK`-intent path essentially never fire in these
corpus worlds, leaving nearly all real combat to the incidental opportunity-attack mechanic
instead."** That is a decision/scoring-layer question (`tactical.py` or whatever selects/queues an
`ATTACK` task), not a hostility-catalog, spatial, or gate question — all three of which this
investigation's own six earlier candidates, plus this 7th one, have now checked and ruled out or
narrowed as primary causes.

**Not chased further here, per "measure, trace, report, don't fix in the same pass"** — this
finding is substantial enough to warrant its own scoped follow-up rather than open-ended
continuation inside an already-large investigation.

## Addendum — 2026-09-19, resumed per user decision relayed by peer, reframed to "why does the
## decision layer never see the enemies the movement layer is already attacking" — root cause
## found and measured, not yet fixed

**Context**: resumed directly from
`TCK-20260917-TACTICAL-ATTACK-PATH-NEVER-FIRES-INVESTIGATION` (closed 2026-09-18), which found
`hostiles` non-empty in **0 of 1130** real `evaluate_entity_intent` calls across
`crowded_frontier`/`quest_dense_frontier`/`hero_guild_routing`, while the incidental
opportunity-attack mechanic (`resolve_multi_attack()`, reached via `movement.py`) fires 181-2177
times per 1000-2000 ticks in the same worlds (per this ticket's own 2026-09-17 addendum). Peer's
own framing: "the rarity question isn't 'why is combat rare' — it's 'why does the decision layer
never see the enemies the movement layer is already attacking?'" — with three specific checks.

**Check 1 — what actually populates `hostiles`.** Traced `TacticalDecisionSystem.evaluate_entity_
intent`'s hostiles-loop (`src/engine/tactical.py:182-226`) directly: for each perception-filtered
`neighbor`, alive+active, passing `PerceptionGate.can_perceive()`, a neighbor is appended to
`hostiles` only if `FactionSemanticsService.is_hostile_compat(src_faction_id, tgt_faction_id,
RelationContext(...))` returns `True`. `is_hostile_compat()` (`src/content_semantics/faction.py:
159-206`) is fully catalog-driven: it first checks for a real authored `faction_relationships.yaml`
entry or a `perspectives.yaml` projection between the two real content-faction IDs (not the raw
legacy 4-value `Faction` enum), classifying via `RelationProjectionService.project_relation()`'s
`enemy`/`threat`/`intruder` labels; only when neither exists does it fall back to the generic
`alignment_bucket` rule (`invader` hostile to all non-invaders). This confirms and extends this
ticket's own 2026-09-15 candidate-1 finding: the decision layer's hostility source is real,
catalog-authored per-pair data, not a coarse bucket check.

**Check 2 — is that source ever true in these worlds.** Yes, directly confirmed by re-reading
`data/content/social/factions.yaml`: `goblin_warband` (`alignment_bucket: invader`) and
`orc_clan` (`alignment_bucket: rival`) are two real, distinct catalog factions — exactly the
"weaker_rival_fear" pairing peer named — and this ticket's own earlier candidate-1 pass already
found real authored `hostility: "high"` relationship entries between comparable pairs
(`bandit_company`/`hero_guild`, `orc_to_goblin`, etc.) in `crowded_frontier`'s own roster. The
decision layer's hostility source is not empty of real content — it has real hostile pairs to
find, when a `neighbor` of the right faction is actually in `neighbors` and passes perception.

**Check 3 — does the opportunity-attack path consult the same source, and if not, does that
account for the gap.** **No — and this is the decisive finding, measured directly, not inferred.**
`movement.py`'s opportunity-attack trigger (`src/engine/movement.py:232-242`) reads
`engaged_hostiles` from `LegalityServiceV2.get_engaged_hostiles_at_pos()`
(`src/engine/legality.py:517-559`), which determines hostility as `my_faction != other.identity.
faction` — the **raw legacy 4-value `Faction` enum** (`HERO_GUILD`/`MONSTER_HORDE`/
`TOWN_COUNCIL`/`NEUTRAL`), the same field previously found misused by `SensoryFilter.filter_
saliency` (this ticket's own candidate 4) — never calling `is_hostile_compat()`, `FactionSemantics
Service`, or any catalog data at all. Confirmed by direct catalog read that this collapses
genuinely distinct, catalog-authored-hostile factions into the same bucket:
`goblin_warband.legacy_engine_bucket = "MONSTER_HORDE"` and `orc_clan.legacy_engine_bucket =
"MONSTER_HORDE"` — identical — so `get_engaged_hostiles_at_pos()` can **never** flag them as
engaged against each other, no matter how hostile the real catalog says they are, because the
raw-enum check only ever distinguishes across the 4 legacy buckets, never within one.

**Measured directly, not just reasoned about**: instrumented
`LegalityServiceV2.get_engaged_hostiles_at_pos()` to independently re-classify every real adjacent
occupant pair it evaluates via `is_hostile_compat()` on the side, over real 2000-tick runs
(`WorldCompiler.compile()`, `LocalSequentialExecutor`, seed 42):

| World | Total pair-checks | Both agree hostile | Both agree not-hostile | **Legacy says hostile, catalog says NOT** (false-positive engagement) | **Catalog says hostile, legacy says NOT** (blocked real rivalry) |
|---|---|---|---|---|---|
| `crowded_frontier` | 21366 | 982 | 19787 | **506** | **91** |
| `hero_guild_routing` | 20254 | 78 | 17556 | **2620** | 0 |
| `quest_dense_frontier` | 1022 | 0 | 1022 | 0 | 0 |

The two sources disagree on a large share of exactly the pairs that matter (where either source
says "hostile" at all): in `crowded_frontier`, 506 of 1488 legacy-triggered pairs (34%) are
between factions the real catalog does **not** consider hostile (`hero_guild`/`merchant_league`,
`hero_guild`/`town_council`, `goblin_warband`/`merchant_league`, `merchant_league`/`town_council`
— friendly/neutral factions engaging each other under the raw-enum test alone); in
`hero_guild_routing` it is far more extreme — **2620 of 2698 legacy-triggered pairs (97%) are
not real catalog hostility at all.** The reverse direction is real too, if smaller in this sample:
`crowded_frontier`'s 91 `catalog_only` cases are exclusively `(bandit_company, goblin_warband)` —
a real, specific authored relationship (both catalogued `alignment_bucket: invader`, so the
generic bucket-vs-bucket fallback rule alone would not make them hostile either; the real
authored `faction_relationships.yaml`/perspective entry between them is what `is_hostile_compat()`
picks up) that the legacy-enum path can never see because both factions share
`legacy_engine_bucket: "MONSTER_HORDE"`.

**This is the whole answer, exactly as peer's framing predicted, and now with numbers**: the
opportunity-attack path (`resolve_multi_attack()`, the mechanic actually producing 181-2177 real
combat resolutions per 1000-2000 ticks in these worlds) is driven almost entirely by a coarse,
catalog-blind legacy-enum comparison that both over-triggers (friendly/neutral factions fighting
each other because they happen to sit in different legacy buckets — the dominant effect measured
here, 506-2620 spurious engagements) and under-triggers (real catalog-authored rivalries within
the same legacy bucket, like `bandit_company`/`goblin_warband` or the `goblin_warband`/`orc_clan`
pairing peer named, structurally unable to ever engage via this path). Meanwhile the
decision-driven `ATTACK` path, which *does* consult the real catalog correctly, essentially never
fires at all (0-2 per 2000 ticks, per the closed tactical-attack-path investigation) — so almost
none of the real combat volume in these worlds is governed by the game's own authored hostility
model. The two findings compose: it is not just that the decision layer rarely runs — when the
mechanic that *does* run frequently decides who fights, it is consulting a different, much
cruder, and demonstrably wrong-in-both-directions notion of "hostile" than the one the content
catalog actually defines.

**Not fixed in this pass, per this ticket's own Scope** ("if a real, scoped fix is found, propose
it for peer review before building — this affects combat/targeting broadly, not just the faction
subsystem") — `LegalityServiceV2.get_engaged_hostiles_at_pos()` is a shared legality primitive with
its own call sites beyond the opportunity-attack trigger (e.g. the `skip_oa`/escape-tag logic in
the same function, and `get_engaged_hostiles_at_pos` at `movement.py:100` for hypothetical-position
checks during pathing), so swapping its hostility test for `is_hostile_compat()` needs a scoped
follow-up, not a same-pass edit. Filed as the concrete next step for whoever picks this up.

## Completion Summary
**Investigation still paused (not closed).** Real progress across two sessions: six candidate root
causes traced and falsified with direct evidence in the original 2026-09-15 pass (catalog
hostility coverage was correct; spatial separation was not the blocker; the posture/targeting
break was resolved by identifying `combat_engagement`'s write-only-ness in the sibling ticket; a
real legacy-Faction-enum bug in `SensoryFilter.filter_saliency` was found and filed, measured to
have only 0.5% practical impact; the attack-legality gate mostly passes for real hostile pairs and
its illegal results are correctly-blocked allied friendly-fire, not a bug; and a specific
"predator-driven, not faction-driven" hypothesis was tested against real data and rejected). One
plausible, evidence-backed structural mechanism was identified via a purely static world-spec
comparison (differing region composition for `merchant_league`) but was not verified live.

A 7th candidate (2026-09-17): whether the newly-built posture-veto gate
(`TCK-20260915-COMBAT-ENGAGEMENT-POSTURE-NEVER-WIRED-TO-EXECUTION`) is itself starving real
combat — **falsified**, and more decisively than expected: the gate only governs the
decision-driven `ATTACK`-intent path, which these three corpus worlds essentially never use in the
first place (0-2 calls per 1000-2000 ticks); almost all their real combat runs through the
ungated, incidental opportunity-attack mechanic (`resolve_multi_attack()`, 181-2177 calls per 1000
ticks). This reframes the investigation's own open question from "why is combat rare" to the more
precise "why does the decision-driven `ATTACK` path essentially never fire, leaving real combat to
an incidental movement-triggered mechanic" — corroborated by a third, independent prior
investigation (`TCK-20260808-LIFE-ARC-REBIRTH-REACHABILITY-INVESTIGATION`) that found the same
`resolve_attack(): 0 real calls` fact from a different angle in 2026-08. Whoever picks this up next
starts from an even narrower, triply-evidenced position.
