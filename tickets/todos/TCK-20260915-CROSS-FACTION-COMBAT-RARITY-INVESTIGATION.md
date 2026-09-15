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

## Test Summary
_(none yet)_

## Files Changed
_(none yet)_

## Completion Summary
_(not started)_
