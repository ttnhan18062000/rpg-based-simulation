# Core RPG Feature Review

Date: 2026-08-27  
Evidence baseline: repository `HEAD` `2af384ff`, inspected with the then-current working tree  
Scope: existing RPG mechanics, proposed RPG feature ideas, and the M1-M9 RPG plans  
Constraint: this document is an independent review; it does not modify or supersede the existing brainstorm or plan documents

## Executive judgment

The project already has a strong simulation engine and a credible RPG substrate. Combat decisions and resolution, character needs, goal selection, equipment, inventory conservation, faction relationships, quests, campaign persistence, and Chronicle/history generation are real systems rather than design placeholders.

What it does not yet have is a comparably strong **life-path layer**. Characters can act, fight, acquire resources, and level, but most do not yet become meaningfully different because of the life they lived. Numeric progression is largely linear; AP allocation is not reached by normal behavior; class and archetype remain fixed; wounds do not complete their heal/scar lifecycle; marriage, reproduction, coming of age, direct social invitations, affiliation changes, and place-based identity are absent or incomplete.

The best new ideas correctly target that gap. The roadmap's strategic direction is therefore sound, but its milestone structure needs refinement before M2-M6 are ticketed:

- Idea 66 (Region contains Places) should be resolved before place, city-ownership, Camp/Nest/Lair, or place-transition work.
- M3's written build order contradicts its own dependencies: Coming of Age is listed first despite depending on Reproduction's birth record.
- M6 contains conflicting sequencing language for Affiliation versus Drifting Loyalty.
- M7 treats SimQ integration as a late sweep when event emission and observer legibility should also be acceptance criteria of each feature ticket.
- Several high-value features depend on dormant substrates (`CultureDeriver`, self-model/belief phases, information execution) that currently have no single prerequisite owner.

The recommended center of gravity is: **fix lifecycle correctness, enable real build divergence, establish the shared species/life-stage/population foundations, then advance Place architecture and voluntary family/social choice in parallel before closing the loop into legacy and history.**

## What counts as a core RPG feature

For this review, a core RPG feature must materially affect at least one of these player-observable questions:

1. **Who is this character?** Attributes, race/species, class, occupation, personality, relationships, home, lineage.
2. **What can this character choose?** Goals, tactical posture, build path, affiliation, companions, commitments.
3. **How does experience change the character?** Levels, skills, wounds, habits, expertise, aging, reputation, beliefs.
4. **What does the world remember?** Death, succession, borders, changed places, local reputation, Chronicle, myth.
5. **How do systems collide?** Combat affects relationships; history affects ambition; family affects politics; place affects crafting and identity.
6. **Can an observer understand why it happened?** Internal correctness alone is insufficient for an observed emergent-world RPG.

Infrastructure, schema cleanup, flags, tests, and observability remain necessary, but they are supporting work unless they directly unlock one of these outcomes.

## Existing RPG feature assessment

### Combat and action — strongest existing pillar

Current strengths:

- Deterministic fractional-armor damage resolution.
- High ground, flanking, surrounding, cover, exhaustion, Frozen/shatter, and bond-synergy modifiers.
- Tactical target selection, cover-seeking, guarding, kiting, interception, bracketing, leash behavior, and anti-stalemate logic.
- Equipment durability and broken-slot consequences.
- Readiness-based action pacing and weight/agility-sensitive movement cost.
- Hero rebirth generations and intended final permadeath.

Core gaps:

- `readiness_speed` is structurally present but uniform, so builds do not currently change action frequency.
- The richer pre-combat `CombatPosture` assessment is gated off and does not yet shape normal engagement.
- Wounds inflict a flat live penalty; severity-scaled mechanics are disconnected; healing and scar formation have no production path.
- Final permadeath is structurally broken: combat emits `PERMADEATH`, while lifecycle deactivation recognizes only `KILL`.

Judgment: do not add more combat breadth yet. Finish the consequence chain already implied by readiness, subjective engagement, wounds, scars, and permadeath. Combat is deep enough; its incomplete transitions are now more damaging than a missing attack type.

Relevant plans: [M1 Quick Wins](../../plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md), especially ideas 15, 17, and 29. The permadeath defect is not cleanly owned by the current milestone tickets and deserves its own focused repair ticket.

### Progression and character identity — live but too linear

Current strengths:

- Nine core attributes feed combat stats, stamina, movement cost, tactical role, and cognition capacity.
- XP curve, level cap 99, level-up execution, +5 AP grants, skill gates, evolution stages, equipment bonuses, passive skill bonuses, and trait bonuses are implemented.
- Race/archetype composition provides meaningful initial differentiation.
- Occupation affects routine, crafting eligibility, movement priority, conflict response, and mortality rules.

Core gaps:

- AP allocation has a valid apply path but is not normally selected/reached.
- Same-class characters follow essentially the same numeric path.
- Class/archetype is fixed after spawn; no specialization or earned branch point exists.
- Only three fixed level-gated skill unlocks create little long-run build identity.
- Genetics/aptitude and breakthrough machinery exist but are neutral, orphaned, or incomplete in normal play.
- Personality is assigned at creation rather than shaped by lived events.

Judgment: this is the highest-value core-RPG gap. Before adding large social/world systems, the project should make two initially similar characters diverge through choices and consequences.

Highest-value ideas:

- Idea 3 — apply real breakthrough bonuses.
- Idea 11 — true build diversity.
- Idea 20 — life-stage transitions.
- Idea 23 — earned habits.
- Idea 26 — expertise earned through living.
- Idea 29 — injury that changes later behavior.
- Idea 34 — coming-of-age choice, once birth/life-stage prerequisites exist.

Relevant plans: [M1](../../plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md), [M2 Foundational Systems](../../plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md), and [M3 Family/Species](../../plans/rpg_design_roadmap/rpg_m3_family_species_epic.md).

### Cognition, goals, and memory — excellent architecture, fragmented activation

Current strengths:

- Survival, biological, social, and economic goal priorities.
- Bounded candidate gathering/scoring, cognitive slice limits, and interruption resistance.
- Leads, blockers, obligations, projects, objectives, and actions form a real intent hierarchy.
- Perception is salience-ranked and capacity-limited.
- Beliefs can decay or be contradicted; public reputation and private social bonds affect decisions.
- Campaign social memory carries some consequences across episodes.

Core gaps:

- The live strategic engine, gated `SelfModelBundle` path, and orphaned `core/cognition.py::SelfModel` family are distinct systems with confusingly similar names.
- Several cognition/belief/information phases are disabled by default.
- Multiple memory representations do not form one coherent character-learning loop.
- Rich emotion, causal memory, information sourcing, deception response, and multi-step planning are built partially or fully but have no normal producer/consumer chain.
- Internal state is not consistently surfaced to an observer as an understandable reason for behavior.

Judgment: consolidate and activate before adding another cognition representation. The core question is not “can the engine represent another mental fact?” but “does one lived event change a later choice through one legible path?”

Highest-value ideas:

- Idea 5 — subjective capability affects engagement.
- Idea 8 — explicitly prune or finish the orphaned cognition schema.
- Idea 12 — contradiction detection in the live Leads path.
- Idea 25 — secrets/selective disclosure, only after belief/information activation.
- Idea 26 — causal memory feeding route choice.
- Idea 41 — information hubs, only after conversation and information execution work.

### Relationships, groups, and politics — good state, weak voluntary interaction

Current strengths:

- Directed sentiment, familiarity, trust, grudges, fear, rival/nemesis classification, and public reputation.
- Contract appraisal can accept or refuse based on trust and betrayal history.
- Party formation, leader succession, factions, diplomacy, war, sieges, and war exhaustion exist.
- Affiliation influences combat/action legality.

Core gaps:

- Characters cannot normally initiate a real conversation, direct gift/trade, or explicit team-up invitation with independent acceptance/refusal.
- Relationship roles remain scores rather than durable social meanings such as mentor, spouse, dependent, or rival.
- Affiliation has an apply path but no lived change path.
- Clan/institution membership spanning territorial boundaries is absent.
- Marriage, parentage, dependents, and succession selection do not form a lifecycle.
- Reputation is global rather than local to a place/faction audience.

Judgment: the next social work should reuse existing interaction layers deliberately, without prematurely forcing every social act into one universal state machine:

1. **Appraisal policy** — `SocialAppraisalSystem.appraise_contract()` is the existing accept/refuse precedent. M1 idea 13 can extract/reuse its trust/affection policy for eligible interactions.
2. **Proposal lifecycle** — Contracts provide an offer/accept shape. M3 idea 33 (Marriage) should be the first feature to prove whether that lifecycle can be generalized safely; conversation, team-up, and Clan entry may reuse it only where their cancellation, expiry, and reciprocity semantics actually match.
3. **Authoritative outcome** — each accepted interaction still emits its own domain-specific `StateUpdate` through the pipeline. Trade, group membership, marriage, and affiliation must not share a generic mutation path merely because they share an appraisal or handshake pattern.

Highest-value ideas:

- Idea 13 — voluntary interaction gate for conversation/trade/team-up.
- Idea 22 — relationship roles, but only with named consumers.
- Idea 33 — marriage as a concrete two-party commitment.
- Ideas 36/40 — Clan state and lifecycle.
- Idea 39 — affiliation change path.
- Idea 60 — local reputation before inherited/organizational reputation expands the current global field.

### Economy, equipment, crafting, and quests — robust invariants, thin content/interconnection

Current strengths:

- Atomic resource conservation, inventory slot/weight limits, harvesting, regeneration, shops, liquidity, reputation discounts, crafting gates, auto-equip, quests, guild intel, and home storage.
- Economic action is already connected to character goals and resource availability.

Core gaps:

- Direct entity-to-entity transfer does not exist.
- Crafting is mechanically sound but uses very little reachable content.
- Rich recipe/material catalogs are duplicated or orphaned from the live crafting path.
- Materials are not yet strong reasons to explore particular places or branch an evolution.
- Ordinary death does not leave a modeled economic vacancy.

Judgment: preserve the conservation law and avoid economy rewrites. The valuable work is connective: direct social exchange, place-tied materials, reachable recipe content, material-gated transformation, and visible economic consequences of death.

Highest-value ideas:

- Idea 13 — direct trade/gifting.
- Idea 24 — personal economy/material ambition, after its motivation dependency is real.
- Idea 49 — connect exploration to crafting materials.
- Idea 50 — material-gated evolution branch.
- Idea 64 — the economic “empty chair” left by a death.

### World, places, species, and history — broad simulation, shallow topology

Current strengths:

- Regions, factions, territory, diplomacy, cultures, campaigns, Chronicle/history, disasters, bosses, threat escalation, world compilation, and scenario composition.
- Camp lifecycle code and demographic cohort code already exist, although normal worlds do not seed the required state.

Core gaps:

- City and Region are conflated; points of interest are flat sibling regions rather than Places inside Regions.
- Camp/Nest/Lair/Ruin/Dungeon do not share a coherent place model.
- Species have strong per-entity starting definitions but no collective population/relationship state and limited species-specific psychology.
- Places do not retain transformation/ownership history.
- Chronicle records history, but history only partially feeds back into belief, ambition, religion, or identity.

Judgment: idea 66 is the architectural foundation for this entire branch. Building City ownership, Camps, Nests, Lairs, place transitions, local reputation, home/exile, or refugees against the flat model first creates avoidable rework.

Highest-value ideas:

- Idea 14 — species classification, expanded beyond one intelligence scalar into behavioral eligibility.
- Idea 37 — race relations, with careful content/balance design.
- Idea 44 — settlement capacity distinct from intelligence.
- Idea 48 — place-type transitions.
- Idea 57 — history creates future behavior.
- Idea 59 — home/exile/return.
- Idea 62 — remembered history diverges from recorded history.
- Idea 63 — belief grows around real history.
- Idea 66 — Region contains typed Places.

## New feature idea triage

### Tier A — complete or repair existing core loops first

These are not glamorous, but they turn already-present mechanics into trustworthy RPG behavior:

1. Fix final permadeath deactivation and succession triggering.
2. Decide and apply rollout-flag policy for cognition, engagement, belief, and information phases.
3. Make AP allocation reachable or explicitly remove it as an intended live behavior.
4. Complete the wound -> heal/scar -> tactical adaptation chain.
5. Apply breakthrough bonuses and wire causal memory to a real decision consumer.
6. Seed demographic cohorts if downstream birth/settlement plans continue to depend on them.

### Tier B — make individual lives diverge

1. Build diversity (11).
2. Species classification with real behavioral consequences (14).
3. Life-stage transitions (20).
4. Earned habits/expertise (23/26).
5. Injury-driven adaptation (29).
6. Coming of age (34), after birth and life-stage foundations.

This tier most directly fixes the current RPG weakness: characters have rich state but too few irreversible, earned branch points.

### Tier C — establish voluntary social and family life

1. Shared appraisal policy from M1 idea 13, followed by a reusable proposal lifecycle proven by Marriage where appropriate; authoritative outcomes remain domain-specific.
2. Relationship roles with real behavior consumers (22).
3. Marriage (33), reproduction (32), dependents (31), then coming of age (34).
4. Affiliation change (39) and Clan lifecycle (40).

### Tier D — restructure the world around meaningful places

1. Region/Place model (66).
2. Settlement capacity and species eligibility (44/14).
3. Camp/Nest/Lair/Ruin/Dungeon placement (45-48 as reshaped by 66).
4. Place-tied crafting/evolution (49/50).
5. City ownership and expansion (35/51/52) against the settled place model.

### Tier E — make consequences outlive their origin

1. Local reputation (60).
2. Inherited reputation/feuds and dying wishes (53/55/58).
3. Chronicle distortion and living legend feedback (62 -> 57).
4. Emergent belief/religion (63).
5. Home, exile, political drift, and refugees (39 -> 56 -> 59/65).

## Review of the current plans

### M1 — useful, but separate correctness from feature value

M1's 20-idea scope produced 21 tickets for 19 ideas; idea 16 required no behavior-change ticket. The batch is valuable, but it mixes four different kinds of work:

- Correctness repairs: wound mechanics, town center, route count.
- Activation/governance: flags, orphan wiring, AP reachability.
- Core-RPG improvements: heirs, life stages, relationship roles, causal memory.
- Scope-only decisions: secrets and personal economy.

Recommendation: retain the ticket sequence as the workflow authority, but review/execute M1 in lanes. Correctness and activation should establish stable foundations before feature-facing tickets depend on them. Add the permadeath repair to the correctness lane rather than waiting for a later milestone.

### M2 — too broad; idea 66 must precede its world-facing half

M2 combines entity progression, cognition cleanup, species classification, relationships, world demographics, sovereignty, Clans, race relations, and place transitions. Calling all 16 ideas mutually independent is no longer sufficient once idea 66 is considered.

Recommendation: split M2 conceptually into:

1. **Entity foundation:** 2, 4, 5, 8, 11, 14, 23, 27, 28, 30.
2. **Independent institution/species foundation:** 36 and 37. Clan shape and race relations do not depend on the Place model.
3. **Population foundation:** 43. Population seeding is useful regardless of the final Place representation.
4. **Place-dependent foundation:** 35 and 48. Resolve idea 66 before these are ticketed.
5. **Interaction capability:** 6. Reuse M1 idea 13's appraisal policy where appropriate; do not absorb teaching's authoritative behavior into a generic interaction mutation.

Resolve idea 66 before ticketing 35 and 48. Do not block 36, 37, or 43 on the Place migration.

### M3 — direction is excellent; written build order is inconsistent

The plan lists Coming of Age first while stating that it needs idea 32's birth record. It lists Reproduction fourth, followed by the population feedback loop. That is not an executable dependency order.

Recommended order:

1. Idea 33 — establish marriage/proposal state if marriage remains a reproduction gate.
2. Idea 32 — birth event and persistent parentage.
3. Idea 38 — close the individual-birth/aggregate-population feedback loop immediately after, or atomically with, idea 32. Do not expose repeated births before the pressure signal incorporates them.
4. Idea 31 — make a born child a dependent and connect succession responsibility.
5. Idea 34 — coming-of-age transition and branching archetype/class choice.

M1 idea 20 and M2 ideas 14/43 remain external prerequisites. Because Reproduction has the worst cost/risk profile in the scorecard, splitting it into its own epic remains sensible.

### M4 — currently two or three epics hiding in one milestone

M4 combines place ecology, Clan lifecycle, information hubs, crafting/evolution materials, national expansion, settlement personality, and economic vacancy. Idea 66 also subsumes or reshapes 45-47.

Recommendation: separate the milestone into branches, and apply the idea 66 gate only to tickets whose authoritative state actually uses Place identity or containment:

- **Place-shaped ecology and settlements:** 44-47 and 61. Resolve idea 66 first.
- **Material exploration and national expansion:** 49-50 and 51-52. Decide at ticket scope whether each outcome targets a Place; only that Place-shaped portion inherits the idea 66 gate.
- **Institutions and economic signals:** 40, 41, and 64. These retain their own Clan-lifecycle, information-activation, and vacancy-signal prerequisites; they are not globally blocked on idea 66.

Do not extend dormant `CultureDeriver` behavior independently in ideas 56, 57, 61, and 62. Give that shared substrate one prerequisite ticket and one owner.

### M5 — good consolidation, but it needs two explicit dependency chains

The plan already recognizes that local reputation changes the state shape written by inherited and organizational reputation. It also recognizes that belief depends on history/fame.

Recommended internal ordering:

- Reputation branch: 60 -> 53/54.
- Death/lineage branch: 55+58 after Reproduction, heir assignment, and death dispatch are real.
- History/belief branch: 62 -> 57 -> 63.

These branches can proceed independently once their external prerequisites are met; treating them as one linear six-ticket milestone would add unnecessary blocking.

### M6 — valuable late-game chain, but sequencing text conflicts

The plan's acceptance signal says `39 -> 56 -> 59/65`, while its Idea 56 description says Drifting Loyalty should land before or alongside Idea 39. The implementation dependency should be explicit:

- Idea 39 first establishes the authoritative affiliation mutation path.
- Idea 56 then derives a gradual political signal that can request/use that path.
- Ideas 59/65 add personal place identity and displacement consequences.

If design intent instead requires Drift to exist before affiliation can ever change, then idea 39 must be split into “mutation primitive” first and “voluntary change trigger” later. The current wording tries to use both interpretations.

### M7 — retain the final audit, move feature obligations earlier

A consolidated SimQ audit after M1-M6 is useful. It should not be the first time a feature gets an event and observability design.

Recommendation: every feature ticket that introduces behavior should already require:

- Its authoritative state update/event.
- A scenario that causes it to fire.
- A SimQ mapping or explicit exclusion.
- An observer-facing surfacing path or explicit reason none is needed.

M7 should then verify completeness and calibration, not retrofit missing event contracts after six milestones ship.

### M8/M9 — treat as readiness gates, not distant follow-ups

World compilation and corpus reachability decide whether a “finished” feature can appear in any real run. Their findings should be consumed while individual M2-M6 tickets are scoped.

Idea 66 is the strongest example: its world-schema migration and grade-anchor blast radius belong in the feature's own Definition of Done, even if M8/M9 retain oversight.

## Recommended revised program shape

This is a review recommendation, not a request to rewrite the existing plans immediately.

1. **R0 — Core correctness and activation**
   - Permadeath, wounds/scars, town targeting, rollout flags, AP reachability, orphan decisions.
2. **R1 — Shared entity foundations and individual divergence**
   - Breakthroughs, build diversity, species eligibility, life stages, population seeding, habits/expertise, subjective engagement.
3. **R2A — Place architecture**
   - Idea 66, sovereignty boundary, settlement/place kinds.
4. **R2B — Voluntary social/family life, parallel with R2A once shared prerequisites clear**
   - Shared appraisal policy, Marriage-proven proposal lifecycle, relationship roles, birth plus its population-feedback safety loop, dependents, coming of age.
5. **R3 — Institutions, ecology, and material ambition**
   - Clans, Camps/Nests/Lairs, information hubs, place materials, evolution branches, expansion.
6. **R4 — Legacy, memory, and political identity**
   - Local/inherited reputation, feuds, dying wishes, distorted history, belief, home/exile/refugees.
7. **Continuous acceptance, plus final audit**
   - Corpus reachability, SimQ mapping, determinism, and observer legibility during each ticket; M7/M9 remain final completeness audits.

## Plan updates worth making before implementation

This review does not apply these changes.

1. Update M1 status to reflect the existing 21-ticket batch and add/associate the permadeath repair.
2. Give idea 66 formal prerequisite ownership before M2 ideas 35/48 or M4 tickets that use Place identity or containment are created; do not apply it to unrelated institution work.
3. Correct M3's internal order so Reproduction precedes Coming of Age.
4. Resolve M6's Affiliation/Drift sequencing contradiction.
5. Create one prerequisite owner for `CultureDeriver`/`CulturalBiasApplicator` activation.
6. Assign interaction-layer ownership: M1 idea 13 owns shared appraisal policy; M3 idea 33 tests/generalizes the proposal lifecycle; each consuming feature owns its domain-specific authoritative update.
7. Require per-feature event, corpus, SimQ, and observer-legibility acceptance; keep M7/M9 as final audits.
8. When child tickets are created, separate player-visible feature scope from cleanup/governance work so prioritization does not confuse low-cost maintenance with core RPG depth.

## Final priority recommendation

If the objective is to make the simulation feel substantially more like a living RPG, the next major feature should not be religion, refugees, another combat mechanic, or a large performance change.

The highest-leverage sequence is:

1. Stabilize the existing lifecycle and activation paths.
2. Make progression and behavior diverge between individuals.
3. Establish shared species/life-stage/population foundations.
4. In parallel, build the Region/Place branch and the voluntary social/family branch; neither is a product or technical prerequisite for the other once their shared foundations are ready.
5. Let those lives feed local reputation, history, belief, and politics.

That sequence turns the engine's existing breadth into connected character stories. It also follows the creative direction's strongest rule: new mechanics should create intersections that other systems can stumble into, rather than isolated content that only demonstrates itself.

## Source map

- [`The Unwritten World`](../the_unwritten_world.html)
- [`RPG Feature Atlas`](../rpg_feature_atlas.html)
- [`RPG Schema Registry`](../rpg_expected_schemas.html)
- [`Simulation Wiring Map`](../rpg_simulation_wiring_map.html)
- [`Design Merit Scorecard`](../design_merit_scorecard.html)
- [`RPG Design Roadmap`](../../plans/rpg_design_roadmap/rpg_design_roadmap.md)
- [`M1`](../../plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md), [`M2`](../../plans/rpg_design_roadmap/rpg_m2_foundational_systems_epic.md), [`M3`](../../plans/rpg_design_roadmap/rpg_m3_family_species_epic.md), [`M4`](../../plans/rpg_design_roadmap/rpg_m4_beyond_city_epic.md), [`M5`](../../plans/rpg_design_roadmap/rpg_m5_memory_reputation_epic.md), [`M6`](../../plans/rpg_design_roadmap/rpg_m6_political_identity_epic.md), [`M7`](../../plans/rpg_design_roadmap/rpg_m7_simq_pillar_integration_epic.md), [`M8`](../../plans/rpg_design_roadmap/rpg_m8_world_corpus_generation_epic.md), [`M9`](../../plans/rpg_design_roadmap/rpg_m9_corpus_test_coverage_epic.md)
