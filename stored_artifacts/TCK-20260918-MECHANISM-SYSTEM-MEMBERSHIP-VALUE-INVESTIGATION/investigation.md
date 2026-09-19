---
status: active
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION
artifact_type: investigation
tags: [architecture, documentation, investigation]
---

# Investigation — TCK-20260918-MECHANISM-SYSTEM-MEMBERSHIP-VALUE-INVESTIGATION

## Required reading done first: what a bad grouping looks like

`TCK-20260917-MECHANISM-SYSTEM-TIER-FEASIBILITY-INVESTIGATION` derived 4 candidate systems by
`depends_on`-ancestor traversal and found all 4 unusable: `combat` (partial fit — missing
`tactical_decision`, the single most intuitive member, because a correct edge removal deleted it
from the derived set); `progression` (mostly `combat`'s own 8 members plus `xp_leveling` — a
person who knows the simulation would call this "combat, plus leveling," not progression);
`economy` (n=2, missing trade/services/harvesting/buildings — the real domain is far larger than
one root's ancestors reach); `social` (two plausible roots gave 4 and 17 members with almost no
overlap — "pick a root" is not a well-posed instruction). This ticket does **declared**, not
derived, membership, so none of those specific failures apply mechanically — but the underlying
lesson carries: a grouping can look plausible and still be wrong in a way only checking against
real registry data exposes. §3 below applies that same discipline to declared membership.

## §1 — The broad pass

Assigned all 93 mechanisms to 7 broad systems, coverage-first (large groupings first, splitting
deferred). Full assignment script and raw output:
`/tmp/claude-1000/.../scratchpad/membership_pass.py` (not committed — throwaway per this ticket's
own explicit scope). Vocabulary arrived at: **combat, progression, cognition, social, faction,
economy, world**.

**Sanity check against the ticket's own worked example**: the ticket's Request Summary states
progression is 15 mechanisms. This pass's own `progression` assignment — done independently,
before re-reading that number — also produced exactly 15: `attributes_biology`, `derived_stats`,
`race_archetype`, `class_assignment`, `personality`, `build_diversity`, `aging_death`,
`succession`, `genetics_aptitude`, `evolution`, `xp_leveling`, `breakthrough_bonuses`,
`entity_role`, `readiness_speed_scaling`, `progression_conversion`. That match is real evidence
this session's judgment tracks the ticket author's, not a coincidence forced after the fact —
`skill_unlocks` was the one candidate considered and deliberately placed in `combat` instead
(skill *unlocking* is a leveling-adjacent event, but the skill itself is a combat capability; the
15-count would have been 16 with it included, so excluding it is what makes the numbers agree).

### Full membership

**combat (7)**: `action_pacing_readiness`, `combat_engagement`, `combat_resolution`,
`movement`*, `skill_unlocks`, `status_effects`, `tactical_decision`

**progression (15)**: `aging_death`, `attributes_biology`, `breakthrough_bonuses`,
`build_diversity`, `class_assignment`, `derived_stats`, `entity_role`, `evolution`,
`genetics_aptitude`, `personality`*, `progression_conversion`, `race_archetype`,
`readiness_speed_scaling`, `succession`, `xp_leveling`

**cognition (21)**: `adventure_routing`*, `belief_cycle`, `causal_spatial_memory`,
`cognition_capacity_fatigue`, `committed_intentions`, `concern_intake`,
`declared_cognition_schema`, `emotion`, `goal_hierarchy`, `information_trust_deception`,
`knowledge_model`, `motivation_doctrine`, `perception`, `personality`*,
`quest_generation_sourcing`*, `self_model`, `strategic_intelligence_core`,
`strategic_learning_bias`, `strategic_redirection`, `temporal_pressure`, `trauma`

**social (12)**: `affection_relationship_bonds`, `commitment_betrayal`,
`commitment_pressure_consequences`, `conversation`, `cooperation`, `entity_trade`*, `fame`*,
`group_coordination`, `guilds`*, `interaction_channeling`, `party_formation`, `team_up`

**faction (13)**: `betrayal_siege_war`, `clan`, `country_lifecycle`,
`cross_episode_grief_nemesis`, `cross_episode_social_consequences`, `diplomacy`, `guilds`*,
`race_collective_force`, `regional_sovereignty`*, `reputation`, `settlement_capacity_axis`,
`social_contracts`, `social_memory`

**economy (8)**: `building_sabotage`, `buildings`, `crafting`, `entity_trade`*,
`equipment_scoring`, `inventory_trade_conservation`, `resource_harvesting`, `town_services`

**world (25)**: `adventure_routing`*, `belief_institution`, `calamity_intensity`, `camp`,
`campaigns`, `chronicle`, `city`, `cultural_drift`, `demographic_cohort_cycle`,
`event_interpretation`, `fame`*, `fidelity_drift`, `gods_pantheon_blessings`, `lair`, `movement`*,
`narrative_memory`, `nest`, `opportunity_rumor_seeds`, `quest_generation_sourcing`*,
`quest_reward_distribution`, `regional_sovereignty`*, `regional_trauma`,
`ruins_mines_battlefields`, `world_boss_spawn`, `world_generation`

`*` = multi-system membership (8 mechanisms, listed once per system they belong to).

## §2 — Shape, reported honestly

**How many systems did full coverage require?** 7: `combat`, `progression`, `cognition`,
`social`, `faction`, `economy`, `world`. All 93 mechanisms are covered — confirmed by direct
set-difference against the loaded registry (`missing` = empty set), not eyeballed.

**How many mechanisms genuinely belong to more than one?** **8 of 93 (8.6%)**:
`movement` (combat + world — real dual use: the dominant real-combat driver per this arc's own
`resolve_multi_attack()` measurements, and also plain travel/pathing with no combat involved),
`personality` (progression + cognition — an identity stat that is also a real behavioral input to
`combat_engagement` and strategic decision-making), `adventure_routing` (cognition + world —
routing decisions consuming world-generated quest content), `entity_trade` (social + economy — a
trade interaction is simultaneously a social act and an economic transfer), `guilds` (social +
faction — an entity-scale grouping that behaves like a mini-faction), `regional_sovereignty`
(world + faction — region ownership is inherently a faction-politics fact), `fame` (world +
social — a world-legible reputation-adjacent stat, distinct from faction-level `reputation`),
`quest_generation_sourcing` (world + cognition — world-authored content that `adventure_routing`
consumes as a decision input).

**8.6% is a real minority, not "almost none."** It's low enough that a single-valued `system`
field with these 8 as a documented, small exception list would likely be cheaper to maintain than
a full many-to-many relational schema — but it isn't low enough to pretend the exceptions don't
exist. This is a genuine simplification candidate for the foundation ticket to weigh, not a clear
"go many-to-many" or "go single-valued" verdict on its own.

**How many resist assignment entirely?** **Zero.** No mechanism in the 93 needed an `unassigned`
bucket — every one of them, including the more infrastructure-flavored ones
(`declared_cognition_schema`, `committed_intentions`, `strategic_redirection`, `concern_intake`,
`narrative_memory`), had a real, defensible home once `cognition` and `world` were drawn broadly
enough. This is itself informative: it suggests 7 systems drawn at this width are wide enough
that "no home" isn't a real failure mode at this granularity — the risk this design should
actually worry about is over-broad buckets (`cognition` and `world` are 21 and 25 members
respectively, the two largest), not gaps.

## §3 — The value test (three systems, chosen for domain diversity, not `progression` itself)

**Methodology note, not in the ticket's literal text but necessary for an honest answer**: a raw
per-system rate (e.g., "77% unverified") is exactly the kind of fact the per-mechanism table
already shows, one row at a time — it only becomes a synthesis the table doesn't hand you for
free once it's compared against a baseline. So every rate below is checked against the
whole-registry baseline, computed the same way: **69/93 (74%) unverified, 28/93 (30%) have a real
`implemented_by` code citation.**

### combat (7 members)
- State: 5 `done`, 2 `partial`. Verdict: 3 `observed`, 3 `unverified`, 1 `contradicted`
  (`tactical_decision`). **Unverified rate: 3/7 = 43% — below the 74% baseline.**
  **`implemented_by` rate: 0/7 = 0% — well below the 30% baseline.**
- Internal `depends_on` edges: 2 (`combat_resolution → movement`,
  `combat_resolution → status_effects`) — a small, coherent internal structure.
- **What the grouping reveals**: combat is *better-verified than the corpus average* (43% vs.
  74% unverified) yet has *zero* real code-citation bindings, the only one of the three test
  systems at 0%. And the one `contradicted` verdict in the set is `tactical_decision` — the
  system's own decision-maker — sitting directly next to `combat_resolution`/`combat_engagement`,
  both `observed`. Read together: this system's *execution* mechanisms are verified working, but
  its own *decision* mechanism is verified **not** doing what it's supposed to (this arc's own
  finding: the `ATTACK`-intent path is dormant, with `movement`'s opportunity-attack mechanic
  actually driving nearly all real combat instead) — and none of it has a recorded code citation
  despite being the most heavily-exercised real gameplay mechanism this arc measured.
- **Could this have been read off the per-mechanism table without the grouping?** **No.** Each
  individual fact (this row is `contradicted`, that row has no `implemented_by`) is visible
  per-row, but the *combination* — busiest real system, better-than-average verification, zero
  code-binding, and a decision/execution split — requires deliberately collecting these 7 ids and
  computing two rates against a baseline. A reader scanning 93 alphabetized rows would not notice
  combat's 0% `implemented_by` rate is an outlier without first knowing which 7 rows to compare.
  **Verdict: YES, clears the bar.**

### faction (13 members)
- State: 7 `done`, 3 `gap`, 2 `partial`, 1 `skeleton`. Verdict: 10 `unverified`, 3 `observed`.
  **Unverified rate: 10/13 = 77% — statistically indistinguishable from the 74% baseline.**
  **`implemented_by` rate: 3/13 = 23% — close to the 30% baseline, not a meaningful gap.**
- 3 `gap`-state members (`clan`, `race_collective_force`, `settlement_capacity_axis`); 2 of those
  3 are the registry's own documented `KNOWN PLACEHOLDER` cases (`layer: faction` assigned as "the
  nearest organizational tier a real implementation would likely live in," per
  `registries/mechanisms.yaml`'s own header comment — not a citation-backed placement).
- Internal `depends_on` edges: 2 — thin, but not zero.
- **What the grouping reveals**: in isolation, "77% unverified" and "3 of 13 not yet built"
  sound like real findings. Checked against baseline, they aren't — this system tracks the
  corpus-wide average almost exactly on both axes. The one genuinely interesting fact (2 of the
  3 `gap` members are known-placeholder layer guesses) is **already stated in the registry's own
  global header**, not something the grouping surfaces — grouping only localizes an
  already-documented fact to "these 2 specific placeholders happen to both land in what I'm
  calling `faction`," which is a much smaller contribution than it first appeared.
- **Could this have been read off the per-mechanism table without the grouping?** **Yes, mostly.**
  The rates aren't distinguishing, and the one real finding was already written down elsewhere.
  **Verdict: NO — does not clear the bar, once checked honestly against baseline.** This is
  exactly the "two of three" honesty check the ticket's own Scope anticipated.

### economy (8 members)
- State: 5 `done`, 1 `partial`, 1 `gap` (`entity_trade`), 1 `orphan` (`resource_harvesting`).
  Verdict: **8/8 = 100% unverified — 26 points above the 74% baseline, the maximum possible gap.**
  **`implemented_by` rate: 1/8 = 13% — 17 points below the 30% baseline.**
- Internal `depends_on` edges: 4, and a real, sensible structure —
  `crafting → inventory_trade_conservation`, `equipment_scoring → inventory_trade_conservation`,
  `building_sabotage → buildings`, `town_services → buildings` — unlike the prior derived-economy
  candidate (`TCK-20260917-...FEASIBILITY-INVESTIGATION`'s n=2 failure), this declared set is both
  larger and internally coherent.
- **What the grouping reveals**: an entire, real, 8-mechanism gameplay domain — production,
  trade, crafting, buildings, upkeep — has **never once been checked with a real instrument**,
  and only one of its eight mechanisms has a recorded code citation. That is a genuinely
  surprising, actionable fact once you know it's a coherent domain rather than 8 scattered rows.
- **Could this have been read off the per-mechanism table without the grouping?** **No** — same
  reasoning as combat, and the gap here is even larger (100% vs. baseline 74%, the single most
  extreme number in either test system). **Verdict: YES, clears the bar — the strongest result of
  the three, and it reaches the same caliber of finding as the ticket's own progression benchmark
  (unverified ratio, binding ratio both cited there too).**

### Summary: 2 of 3 clear the bar
`combat` and `economy` produced real, baseline-checked findings a per-mechanism scan would not
surface unassisted. `faction` did not, once its raw percentages were checked against the
corpus-wide average rather than reported in isolation. **This is not a failure of the exercise —
it's the honest result the ticket's own Scope explicitly asked for** ("if two of three produce
nothing a reader wouldn't already see, say so"), and it surfaces a real design implication: **the
value only shows up when a rate is compared against a baseline, not when it's reported raw.** A
rollup view that just prints "77% unverified" per system, without a baseline column, would
mislead a reader into thinking `faction` is worse than average when it is not.

## §4 — Cost estimate

- **Initial cost**: hand-assigning membership on 93 mechanisms, done once, ~30-45 minutes of
  judgment-call work (this session's own time for the full pass, including the 8 multi-membership
  decisions, which took noticeably longer per-mechanism than the 85 single-membership ones).
- **Marginal cost per new mechanism**: one judgment call, likely a few minutes given the
  vocabulary already exists — cheap in isolation, but non-zero and easy to defer/forget without a
  process hook (this ticket builds no validator, so nothing would catch a new mechanism landing
  with no membership assigned).
- **Re-assignment cost on mechanism splits**: real and not rare — `TCK-20260917-MECHANISM-
  IDENTITY-RULES-AND-CHANGE-TAXONOMY` produced 4 splits from 9 cases reviewed (a ~44% split rate
  among reviewed candidates). Each split requires re-deciding membership for both resulting
  mechanisms, not just copying the parent's assignment forward — a split can separate concerns
  that belonged to different systems (this investigation's own combat/progression cases show
  `skill_unlocks` and `xp_leveling` are adjacent-but-distinct despite both being "leveling-ish,"
  exactly the kind of judgment a split would force a second time).
- **Judgment-without-code-reading risk (Assumption #2 from the ticket)**: mostly resolved
  favorably in this pass — the large majority of the 93 mechanisms were assignable from their
  `id`/atlas description alone, without opening implementation files. The 8 multi-membership
  cases were the exception: each required recalling or checking a real behavioral fact (e.g.
  `movement`'s real role in triggering `resolve_multi_attack()`, from this arc's own prior
  investigation) rather than being inferable from the name alone. If most future mechanisms are
  single-membership (as 85/93 = 91% were here), the cost stays low; if a mechanism resembles one
  of the 8 multi-membership cases, expect it to cost meaningfully more than a single judgment call.

## §5 — Recommendation

**Proceed, with one required change to the foundation's own design (not a "do not build").**

The value test passed 2 of 3 (`combat`, `economy`), including one result (`economy`) that
matches the caliber of the ticket's own progression benchmark. That is real signal, not noise —
unlike the prior derived-membership investigation, where the underlying design itself was broken
and every candidate failed for a *structural* reason (wrong root, unaudited edges, roots not
unique). Here the one failure (`faction`) failed for a *measurement* reason (raw percentages
without a baseline look informative when they aren't), which is fixable in how the foundation
presents membership, not evidence the whole approach is unsound.

**The required change**: any rollup or review view built on top of declared membership must
report per-system rates **against the whole-registry baseline**, not in isolation — this
investigation's own `faction` case shows a raw rate alone actively misleads (77% reads as bad
until you learn the average is 74%). This is a small addition to whatever the foundation/rollup
ticket already plans to build, not new scope.

**On multi-membership**: 8.6% is real but small. The foundation ticket should weigh a
single-valued `system` field with a short, explicit exception list for these 8 cases against a
full many-to-many schema — the former is very likely cheaper to build and maintain for a
minority this size, but that trade-off is child 2's own decision to make with its own foundation
constraints in view, not settled here.

**On cost**: the ~44% split rate found by the identity-rules ticket means membership will need
real re-review on a recurring basis, not a one-time cost. Whoever owns the foundation should plan
for that as an ongoing maintenance line, not a sunk setup cost.
