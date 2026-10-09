---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-10-09"
---

# World Rule Family: Conflict / Combat

**Purpose/scope.** What constitutes an opposed interaction where subjects pursue incompatible
outcomes, and the domain semantics of physical combat specifically. Treats Conflict as broader
than Combat; does not force every conflict through Combat, and does not create a universal
conflict-resolution framework merely to support every imaginable contest. Reuses rather than
redefines Capability, Authority, Reach, Cost, and Life/Body.

**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same
day per a follow-up Rule-admission and semantic cleanup
(`tmp/world-rule-batch-7-followup-ext-ai.md`): CONFLICT-02 reclassified from a Domain Rule to
Inherited — the semantic requirement that decisions must respect subject-local perception/
knowledge is already fully established by Batch 06 (PERC-01, KNOW-01, AGENCY-01, AGENCY-02);
that live combat targeting correctly uses `PerceptionGate` is real, valuable Repository
evidence supporting that already-established boundary, not a new Conflict-specific semantic
claim. CONFLICT-01 survives the same re-examination unchanged. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-7-ext-ai.md`); each carries this session's
disposition and repository evidence. Structured per the normalized five-category methodology
established in Batch 05/06's admission-discipline passes.

---

## Domain Rules

## CONFLICT-01 — Conflict is broader than Combat; not every opposed interaction resolves through physical combat

> An opposed interaction (subjects pursuing incompatible outcomes) may resolve through
> resource/opportunity contention, forced yielding, or displacement — without any physical
> combat encounter occurring. Combat is one Conflict-resolution mechanism this repository
> implements, not the only legitimate shape Conflict may take.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule names Conflict as its own
category distinct from Combat — this is genuinely new content directly required by the batch
instruction's own §7.

**Repository evidence: SUPPORTED, via real non-combat contention mechanisms.** Two entities
competing for the same scarce resource node resolve their incompatible outcomes without
combat: `ResourceOpportunityProvider`'s reward scaling by `remaining_charges`/`max_charges`
(Batch 06 evidence) means whichever entity depletes a node first genuinely reduces what the
other can still gain — a real, resolved incompatible-outcome interaction with no fight. An
opportunity blocked by insufficient resources (`blocker_penalty=2.0`, Batch 06's AGENCY-01
evidence) is a subject losing access to a contested outcome through resource insufficiency, not
combat. `ECOL-04`'s own regional-scarcity/migration feedback (Batch 05 evidence) is a further
real instance: subjects contending for the same limited regional resources, resolved through
migration/yielding, never a fight.

**Scenarios:** [CP-S09](../scenarios/capability-progression-batch-07.md#cp-s09) (conflict
without combat).

## CONFLICT-03 — Permission to attack is symmetric between two parties; whether a party starts a fight is its own decision

> Whether one subject may attack another is a fact about the pair, and it holds in both
> directions: if A may attack B, then B may attack A. Permission is not intent. A "contextual
> threat" (a creature that is dangerous when intruded on or provoked, not an enemy by race)
> differs from an enemy in when it CHOOSES to fight, which belongs to its own decision-making
> layer (AGENCY-02). It never differs in whether it is ALLOWED to fight back or strike first.

**Amendment, who is a threat or a quarry comes from appraisal, not faction (decided by the owner
directly, 2026-10-09; rows 47 and 49 of the memo):**

> Every creature judges another from what it perceives: the other's size and apparent strength,
> whether one could eat the other, and its own hunger and condition. That appraisal decides
> hunting, fleeing and wariness for every kind. A hungry creature may hunt one whose body its
> diet can eat and which it judges it can overcome, whatever their factions. A creature is wary
> of one that could eat and overcome it, keeping its distance and staying alert, and flees one
> that approaches, stalks or chases it. Hunger is never read by the other side: a wolf lying
> still or walking past draws wariness, not panic. Faction enmity remains an additional, social
> reason for people-kinds to fight (war, feud), on top of the appraisal, not instead of it.

- **Why:** decision 46 (roles from properties). Today "hostile" is a faction verdict
  (`src/engine/hostility.py:41-66`, `is_hostile_compat`; `src/ai/goals/scorers_support.py:18`).
  A hare could flee a wolf only if their factions were declared enemies, and a wolf could not
  hunt a hare of its own wild faction (this Rule's same-faction refusal).
- **Shape (Lane A, relayed by rpg-planner):** a relation between two creatures adds PREDATION (a
  is hungry, a's diet can eat b's body, a judges it can overcome b, a perceives b) and DANGER (b
  could eat and overcome a, and a perceives b; the response scales with what b is doing). The
  threat terms (AGENCY-07, CONFLICT-04, decision 32) read any relation.
- **Engineering, not this Rule:** how "can overcome" is estimated (today `apparent_power` reads
  the opponent's true stats, `src/domains/combat_engagement/power.py:58`, which KNOW-02 objects
  to), the wariness distance, and how approach or stalking is perceived.
- **Alternatives not taken:** appraisal only, with faction dropped as a reason to fight; faction
  hostility kept as the main gate with a narrow hunting exception; prey fearing only a
  hungry-looking predator; prey fleeing any predator on sight.
- **Evidence: CONFLICTING** until Lane A's hunting batch lands.

**Disposition: ACCEPT — decided by world-rule-catalog-design under owner delegation, 2026-10-06**
(row 18 of `docs/plans/systemic_world/owner_decision_memo.md`; the owner confirmed the
delegation directly the same day). Passes the admission test: no earlier Rule said whether
attack permission may be one-way. The number CONFLICT-02 is retired (that entry was reclassified
to Inherited).
- **Why symmetric:** legality answers "may", and the decision layer answers "will". One-way
  permission makes the target a creature that can be attacked but can never answer, which no
  fiction of "contextual threat" intends. It would also hide intent inside a permission check,
  where the decision layer (AGENCY-01/02) can neither weigh it nor show it.
- **Alternatives not taken:** keep one-way legality for wild creatures (today's accident);
  make wild creatures non-hostile both ways (removes them as a threat entirely).
- **Contextual engagement (attack when intruded on or provoked) is feature work,** parked by
  memo row 7. Until it exists, a wild creature's decision layer engages like any other hostile,
  as the spawned kinds already do on the `MONSTER_HORDE` bucket.

**How a pair's permission is resolved: declared hostility decides, and missing data declares
nothing.** Decided by world-rule-catalog-design under owner delegation, 2026-10-06 (memo row 18).
A faction "declares" when the catalog holds a perspective or a relationship row for it.
1. **Both factions declare:** attack is permitted in both directions if either side declares the
   other hostile.
2. **Exactly one faction declares:** that side's verdict decides both directions.
3. **Neither declares:** the legacy fallback applies, which is already symmetric (only an attack on
   one's own faction is refused).
- **Why:** the permissive fallback (with no catalog data, only the same-faction check applies) is
  not a judgement that two parties are enemies; it is the absence of any judgement. Letting that
  absence override the other side's declared peace would make "no data" mean "at war".
- **Consequence for `neutral` (no catalog data):** hero ↔ neutral is refused in both directions.
  `hero_guild`'s perspective does not declare neutral hostile, and neutral declares nothing. A
  neutral subject is not at war with the defenders. It remains exposed to invaders, whose declared
  data makes them hostile to it.
  - The existing pin (`test_legality_faction_mutation`: a hero may not attack an entity that
    defected to NEUTRAL) stands.
  - The change is that a neutral subject may no longer attack a hero.
- **Alternatives not taken:** union in every case (would let heroes attack neutrals and revise the
  pin); a stated NEUTRAL exception to symmetry (unneeded, since the general rule already settles it).
- **Measured at the decision:** Lane B's either-side rule over 16 factions × engaged/not (512
  directed verdicts) flipped 16 to legal and none to illegal (10 `wild_beast_pack` pairs and 6
  non-wild reverses), and left 58 asymmetric on the neutral and legacy-fallback side. Clause 2
  resolves those 58.
- **Measured as implemented** (all three clauses, DEV-016 in
  `docs/guidelines/intentional_divergences.md`): of the 512 directed verdicts, 108 were asymmetric
  before and **0** after. 16 flipped illegal→legal, and 15 flipped legal→illegal; every one of the
  15 is a pair where exactly one side declares (clause 2). On the corpus (24 worlds, seed 42,
  10,000 ticks, `audit_mode`, tick budget off, before vs after on one tree, base `7254a558c`):
  - live neutral→hero attacks lost: 0;
  - the only lost direction with corpus events is town_council→swamp_tribe (`swamp_border_world`,
    8→0);
  - attacks by a `wild_beast_pack` attacker rose from 81 to 184.

**Repository evidence: SUPPORTED since #395 (`7aa6f997b`, 2026-10-07).** Previously
CONFLICTING: legality was one-way for catalog-wild factions. hero→wild was legal, while wild→hero
returned `FRIENDLY_FIRE_ILLEGAL` through `FactionSemanticsService.is_hostile_compat`, because the
catalog hostility law makes only "invader" factions hostile and `wild_beast_pack`'s alignment is
"wild". That affected 85 compiled `wild_beast_pack` entities across 13 corpus worlds.
- **Now:** `verify_attack_legality` (`src/engine/legality.py`) resolves each pair by the three
  clauses above. The implemented text is DEV-016 (`docs/guidelines/intentional_divergences.md`)
  and Bible 02's Friendly-Fire Law (`docs/mechanics/02_combat_laws.md`, "permission is symmetric,
  CONFLICT-03"), with parity entry COMB-334 (`docs/parity_ledger/combat_movement.yaml`, verified).
- **Pinned by:**
  - `tests/unit/world/test_spawn_monster_catalog_faction.py`: both directions for spawned wolf,
    bear and golem; clauses 1, 2 and 3; the legacy-fallback pin;
  - `tests/unit/engine/test_legality_faction_mutation.py` (unchanged).
- **The spawn mapping is complete:** wolf, slime, bear, harpy and golem now spawn as
  `wild_beast_pack` (#395), closing the gap the owner held open on 2026-10-06 (memo row 18).
- **Ticket:** `TCK-20261006-WILD-BEAST-PACK-LEGALITY-IS-ONE-WAY-HERO-CAN-ATTACK-IT-IT-CANNOT-ATTACK-HERO`.
- **Still open, recorded rather than resolved:** "contextual" engagement (attack when intruded on or
  provoked) is feature work parked by memo row 7. A wild creature's decision layer still engages
  like any other hostile.

**Scenarios:** none traced in the catalog's scenario files yet. The behaviour is pinned by the
tests above: a hero may attack a spawned wolf, the wolf may attack the hero, and hero↔neutral is
refused both ways.

---

## CONFLICT-04 — A fighter stands its ground between blows; leaving an engagement is a decision, and it has a cost

> A subject fighting an adjacent opponent, and meaning to keep fighting, stays where it is
> between its blows. Being unable to strike yet is a reason to wait, not to move. Stepping away
> from an adjacent hostile is a decision to leave the engagement: flight under AGENCY-07, or a
> goal that outranks the fight. It pays the disengagement cost. Nothing mechanical, such as a
> timer or the lack of a "wait" action, may turn into a step.

**Disposition: ACCEPT — decided by rpg-designer, direction confirmed by the owner, 2026-10-08**
(row 28 of `docs/plans/systemic_world/owner_decision_memo.md`). Applies AGENCY-01/02 to melee:
a step is an action the subject chooses, so it needs a reason the subject holds. Passes the
admission test: no earlier Rule said what a fighter does while it cannot strike, and the
disengagement cost (an opportunity attack, `docs/combat/combat_movement_overhaul_spec.md`)
was declared without any Rule on when a fighter accepts it.
- **No free repositioning:** adjacency is orthogonal (MOV-07), so every step from a tile
  beside a hostile leaves its reach. A "repositioning step that does not provoke" does not
  exist; a step away is always a disengagement. A fighter that can withdraw without the cost
  needs a declared ability for it (the EVASIVE retreat that skips the attack today is one).
- **What still moves a fighter:** flight from a present threat (AGENCY-07, which already counts
  an adjacent hostile for a cautious subject), the panic retreat at low health, pursuit of a
  target that is not adjacent, or a goal that genuinely outranks the fight. A pressing need does
  not: SURV-07 keeps a present threat above it.
- **A long exchange of blows is not a stalemate.** The stall breaker exists for chase and kite
  loops (COMB-274..276). While a perceived hostile stands adjacent and the subject is fighting
  it, the breaker does not send the subject wandering.
- **Engineering, not this Rule:** how holding is represented (a typed hold or guard action, not
  an empty step); preferring an adjacent hostile the subject is engaged with as its target; the
  stall counter's bookkeeping.
- **Amendment, a hostile stepping into reach is noticed and decided (decided by the owner
  directly, 2026-10-08; row 32 of the memo):** when a perceived hostile the subject is not
  fighting comes to stand adjacent to it, because the subject walked up or the hostile came
  close, the subject decides on it then. It may fight, step away, wait, or keep walking and pay
  the disengagement cost knowingly. A committed walk does not carry it past a hostile it never
  noticed, and nothing freezes it in place until a routine decision comes round.
  - **Measured at the decision** (Lane A, relayed; 5 seeds x 3 worlds, crowded / living /
    urban). Opportunity-attack hits per run:
    - base: 185 / 158 / 87;
    - steps away blocked from an engaged hostile only: 180 / 123 / 65;
    - steps away blocked from any adjacent hostile: 14 / 37 / 8.

    Deaths stay within 1 SD in every arm. The any-adjacent movement block froze subjects for
    700 to 1,570 entity-ticks per run, up to 219 ticks beside a hostile they never decided
    about, so a freeze at the movement layer is the alternative not taken. About 90 percent of
    what remains after the engaged-only block is this case.
  - **Engineering, not this Rule:** how the event reaches the decision layer (an event-driven
    re-decision touches scheduling), and its cadence. This is feature work with its own ticket.
  - **Evidence: SUPPORTED since #457 (`edda25490`, 2026-10-09), with one disclosed gap.**
    Implemented by
    `TCK-20261008-A-SUBJECT-NOTICES-AN-UNENGAGED-HOSTILE-COMING-ADJACENT-AND-DECIDES-DECISION-32`
    (Lane A); divergence 2.95, parity COMB-343.
    - **The wake:** the scheduler wakes the brain of a subject holding no action, with an
      unengaged perceived hostile orthogonally adjacent, every 2 ticks ahead of its cadence. The
      decision follows the subject's own combat-engagement verdict: avoid steps away, watch
      holds (a typed `HOLD`, reason `WATCH_HOSTILE`), and other verdicts go to the tactical pass.
    - **Pinned by** `tests/mechanic_scenarios/test_decision32_notice_and_decide.py` (control arm,
      and the invariant that no two-tick adjacency episode ends without a decision).
    - **Measured** (pinned, seeds 42-46, 1500 ticks; crowded / living / urban):
      - opportunity-attack hits: 196.0 / 140.2 / 77.4 to 63.8 / 94.6 / 40.2;
      - DEFEAT deaths: 14.2 / 15.2 / 6.2 to 6.6 / 8.0 / 5.4;
      - total deaths: 28.6 / 33.0 / 17.4 to 21.2 / 29.8 / 17.2;
      - adjacency episodes ending with no decision: about 80 percent before, none after;
      - of the woken decisions, about half are fights (54 / 55 / 52 percent); WATCH is 21.6 /
        15.4 / 13.8 per run; AVOID 15.2 / 10.4 / 8.6.
    - **Disclosed gap:** keep walking (IGNORE) never fires, because the posture service never
      returns it for these pairs (`TCK-20261009-IGNORE-POSTURE-IS-NEVER-PRODUCED-SO-KEEP-WALKING-CANNOT-FIRE-DECISION-32`).
      Under decisions 47 and 49 the appraisal replaces faction hostility as the trigger in the
      hunting batch.
  - **Two follow-up rulings (owner, directly, 2026-10-09, on Lane A's per-world split):** a WATCH
    posture means stand and observe, as a typed wait. It does not mean fight, because the router
    withholds the attack under WATCH, so the subject would "fight on paper" and strike nothing.
    "Keep walking and pay knowingly" (IGNORE) is built but unreachable today, because the posture
    service never returns IGNORE for these pairs. That is accepted for now and disclosed;
    making it reachable is a later combat_engagement ticket.
- **Alternatives not taken:** back off between blows and re-close (today's behaviour, made
  intentional: one free hit per swing for no reason the fiction holds); hold only when winning
  (duplicates AGENCY-07's OUTMATCHED term, and a losing fighter has no better tile to step to).

**Repository evidence: SUPPORTED since #439 (`86b77abca`, 2026-10-08), with one disclosed gap.**
Implemented by `TCK-20261008-A-FIGHTER-HOLDS-BETWEEN-BLOWS-CONFLICT-04` (Lane A).
- **The hold:** with the target adjacent and only readiness missing, the decision is a queued
  ATTACK with reason `HOLD_BETWEEN_BLOWS` (`src/engine/tactical_hold.py`). There is no step and
  no opportunity attack, and the swing lands at readiness 100. PURSUE applies only to a target
  that is not adjacent, and target choice ranks an adjacent hostile first. Divergence 2.86
  (Intentional Gameplay Change), parity COMB-339.
- **The stall breaker:** every ATTACK or SKILL emission, the held swing included, sets the
  counter to 0, and the breaker is skipped while the target is adjacent. Divergence 2.87 (Bug
  Fix), parity COMB-340.
- **Waiting is not a capability gap:** a queued action rejected only for readiness writes no
  capability blocker. Divergence 2.88 (Bug Fix), parity COMB-341.
- **Text:** Bible 02 §7 and the tactical contract §5 (`docs/engine/contracts/tactical_contract.md`).
- **Pinned by** the kernel scenarios CP-S18 and CP-S19
  (`tests/mechanic_scenarios/test_conflict04_fighter_holds_between_blows.py`). Each has its
  control arm, and both main arms fail on pre-merge main. They pass in CI (#439's run, in the
  "Perf / cert / arena" lane) and locally on `86b77abca` (4 passed). Unit tests are in
  `tests/unit/combat/test_anti_stalemate.py`.
- **Measured** (Lane A, relayed; seeds 42 to 46, 1,500 ticks, governor pinned NORMAL,
  `dcfe5de4d` vs the branch; `crowded_frontier` / `frontier_living_world` / `urban_political`):
  - holds per run: 0.6 / 0.4 / 1.6, none at HP under 15 percent, and no death after a hold;
  - `STALEMATE_BREAK` decisions: 0 in both arms;
  - total deaths: 36.4 to 36.0, 43.0 to 44.2, 23.4 to 21.6, all inside 1 SD.
  The effect is small because the "decided at contact" class this Rule governs was small. Most
  opportunity-attack hits come from held moves and from the "neither" class (moving with no
  move task), which are engine defects outside this Rule. Hits per run went 179.4 to 185.2,
  151.8 to 158.0 and 90.2 to 85.0.
- **Disclosed gap (2.86):** while a fighter holds, it is not re-decided until the swing lands
  or the task is released (`OUT_OF_RANGE`, `TARGET_INCAPACITATED`). So for up to one readiness
  refill it cannot choose to leave, though the Rule says leaving is a decision it may take. An
  already-queued ATTACK behaved the same before. Measured as a no-op (0 holds at low HP, 0
  deaths after a hold). If that stops holding, the fix is to re-decide a holding fighter when a
  present-threat term changes (AGENCY-07), not to drop the hold.

**At the movement layer, SUPPORTED since #446 (`28e29ed2e`, 2026-10-08):**
- **The rule:** an entity beside an engaged, perceived hostile takes no step from a stored or
  reaffirmed navigation target. Only a decision this tick moves it, and a blocked held move is
  released to the brain. Divergence 2.89 (Bug Fix), parity COMB-342.
- **Pinned by** `tests/mechanic_scenarios/test_conflict04_movement_layer.py` (with a control arm)
  and `tests/unit/engine/test_engaged_adjacent_hostile_takes_no_stored_step.py`.
- **Measured** (pinned, seeds 42 to 46, 1500 ticks, `d671868bb` to the branch; crowded / living
  / urban):
  - opportunity-attack hits: 185.2 / 158.0 / 87.4 to 162.0 / 128.4 / 72.0;
  - held-move hits: 102.4 / 92.6 / 40.6 to 61.2 / 46.8 / 18.2;
  - total deaths: unchanged within 1 SD.
- **What remains:** the hits left are against adjacent hostiles that are perceived but not
  engaged. That is decision 32's case (notice and decide), in Lane A's next batch.
- **Also in #446:** a chokepoint hold is a typed success that ends its task, not an
  `UNSUPPORTED_ACTION` (divergence 2.90, parity COMB-015). This is a reporting fix with no
  change to the trajectory.

**Previously CONFLICTING, traced by Lane A on main `753f98ea9`** (relayed by rpg-planner, seeds
42 to 46, 3 worlds; kept as found).
- **Who takes the free hits:** 83 to 98 percent of opportunity-attack swings land on a victim
  standing beside its attacker. Split by what the victim was doing on that tick (per world):
  - decided a move: 4 to 5 percent;
  - continuing a move already under way: 41 / 37 / 19 percent;
  - neither (an ENTITY_ACT task, no decision, yet it still moved): 55 / 59 / 77 percent.
- **Stepping between blows:** `TacticalDecisionSystem` emits ATTACK or SKILL only when
  `is_attack_legal`, which needs readiness 100 (Bible 02 §7). Otherwise it emits PURSUE toward
  the target even when the target is already adjacent (`src/engine/tactical.py:739-829`). The
  opportunity attack fires on any successful step from an engaged tile
  (`src/engine/movement.py`, `LegalityServiceV2.get_engaged_hostiles`).
- **The stall breaker in melee:** once `stale_ticks` exceeds 10, the subject wanders before any
  attack branch, even when adjacent (`src/engine/tactical.py:506-517`). The SKILL, ATTACK and
  pursuit payloads add to `stale_ticks` on every swing or step (`:772`, `:788`, `:817`), although the tactical contract's trigger is
  "without a target change or outcome" (`docs/engine/contracts/tactical_contract.md` §5). That
  half is a defect against the existing contract.
- **Non-cautious subjects have no way out but a step:** the safety retreat needs
  `safety_pressure` above 0.75, and no branch treats "adjacent and being struck" as a reason to
  hold.
- **Separate engine defect, not this Rule:** the largest class above, subjects that move with
  no move task at all (rpg-planner is filing it).

**Scenarios:** [CP-S18](../scenarios/capability-progression-batch-07.md#cp-s18) (a fighter
holds between blows; a cautious control flees and pays the cost) and
[CP-S19](../scenarios/capability-progression-batch-07.md#cp-s19) (a long exchange of blows is not
a stalemate; a two-tile control still trips the breaker). Both are kernel-level tests since
#439, and both are covered.

---

## Inherited / Applied Foundational Rules

### Conflict/combat decisions must respect subject-local perception/knowledge, never an omniscient shortcut (originally drafted as CONFLICT-02)

> Assessing how dangerous an opponent is (estimation) and deciding whether that danger is worth
> heeding (consideration/risk tolerance) are two separate causal stages, and neither may be
> satisfied by reading another entity's hidden, unperceived state directly — both must route
> through the same subject-local Perception/Knowledge layer.

**Disposition: INHERITED — reclassified 2026-09-22 per follow-up review, from a Domain Rule
(originally drafted as CONFLICT-02) to this Inherited entry.** The semantic requirement itself
is already fully established by Batch 06: PERC-01/KNOW-01 already state that perception and
belief are bounded, subject-local facts a decision must route through, and AGENCY-01/AGENCY-02
already state that a decision's stages (including estimation-adjacent "wanting"/"choosing")
are causally distinct and never satisfied by omniscient access. The estimation/consideration
framing this entry adds is a restatement of that same boundary in Combat's own vocabulary, not
a new semantic claim — the batch instruction's own §15 (Agency integration) asked this batch to
*verify* the boundary holds for Conflict/Combat specifically, which is exactly what Repository
evidence is for, not grounds for a second Rule stating what Batch 06 already requires.

**Repository evidence: SUPPORTED for both halves, with one confirmed live counter-example to
Batch 06's own CONFLICTING findings — checked directly, not assumed from old evidence.**
**Estimation ≠ consideration**: `docs/mechanics/04_strategic_cognition.md` §13.4 states this
law directly ("a wolf is not bad at sensing that a human is dangerous... it charges anyway. That
is low *consideration*, not poor *estimation*") and cites `EngagementRiskEvaluator`'s own real
separation (`caution = 1.0 - bravery`; the estimate's own accuracy is untouched by bravery;
bravery only changes `risk_score`, which changes the resulting `CombatPosture`) — a concrete
instance of AGENCY-02's own already-established "influence, not determination" claim. **
Perception-gated engagement, confirmed live**: `TacticalDecisionSystem.evaluate_entity_intent()`
(`src/engine/tactical.py`) builds its `hostiles` candidate list by calling
`PerceptionGate.can_perceive(entity, get_entity_signals(n), {"distance": ...})` for every
neighbor *before* that neighbor becomes eligible as a target at all — the comment at the call
site states the law directly: "Perception gate: entity can only engage targets it can detect."
This is a genuine, live, positive counter-example to Batch 06's own two confirmed CONFLICTING
findings (`ResourceOpportunityProvider`, `HarvestScorer`) — not every decision path bypasses
perception; Combat's own live targeting path does not. **What remains INERT/OFF, not
CONFLICTING**: the richer, declared `OpponentPerceptionService`/`CombatLearning` power-
estimation pipeline (true power → apparent power → observer's estimate, §13.2–13.3) is real,
specified in detail, and "most of it already exists, unreachable" — gated behind
`ENABLE_COMBAT_ENGAGEMENT`, default OFF, never run in a real corpus profile. The live targeting
path above uses a simpler, ad hoc capability estimate (`CapabilityEstimateService`, Batch 06
evidence) instead — real and perception-gated for *which* targets are eligible, but not the
richer true/apparent/estimate power pipeline for *how dangerous* each one is judged to be.

**Scenarios:** [CP-S11](../scenarios/capability-progression-batch-07.md#cp-s11) (combat, defeat,
survival), [CP-S12](../scenarios/capability-progression-batch-07.md#cp-s12) (stronger entity
still loses).

### Combat outcomes form a real, differentiated vocabulary; victory ≠ kill and defeat ≠ death

> A combat encounter resolves into one of several distinct outcomes — for example kill,
> defeat (which need not mean death; LIFE-02), mutual survival, rejection, or withdrawal —
> never a binary victory/death pair. (Example list revised 2026-10-01: it no longer names
> specific mechanisms; the former `REBIRTH`/`PERMADEATH` outcomes were retired.)

**Disposition: INHERITED — direct reuse of Batch 05's LIFE-01/LIFE-02, which already fully
established this exact claim ("incapacitated ≠ dead," a real classification process, not one
predetermined outcome). This batch's own contribution is confirming the vocabulary is
*richer* than Batch 05 traced, not restating the claim.**

**Repository evidence: PARTIAL (revised 2026-10-01).** "Victory ≠ kill" is SUPPORTED:
`src/engine/combat.py`'s real `outcome_kind` values are `KILL`/`DEFEAT`/`SURVIVE`/`REJECTED`,
plus a separately-produced `FLED` (`src/engine/movement.py`'s
`combat_escape="EVASIVE_SUCCESS"`), so an encounter can end without anyone dying. "Defeat ≠
death" is permitted, not currently realised, inherited from LIFE-02's own status: terminal
`DEFEAT` is now a recorded, classified death (`death_reason` `DEFEAT`). The former `REBIRTH`/
`PERMADEATH` outcomes were retired as an undeclared resurrection
(`TCK-20261001-RETIRE-HERO-REBIRTH-UNDECLARED-RESURRECTION`; see STR-02). **Confirmed MISSING**, checked directly: no surrender,
capture, or forced-displacement-as-a-combat-outcome exists (`src/world/displacement.py` is an
unrelated, calamity-driven World-Evolution mechanism, not a combat outcome — flagged as a
naming near-collision, not a semantic overlap).

**Scenarios:** [CP-S11](../scenarios/capability-progression-batch-07.md#cp-s11).

### Combat produces events; Life/Body owns the resulting bodily consequence

> Combat is a producer of triggering events (an attack, a defeat), never the owner of the
> bodily harm that results — Life/Body owns that consequence regardless of producer.

**Disposition: INHERITED — direct reuse of Batch 05's BODY-07 and Batch 01's OWN-02. The batch
instruction's own §8 states this exact boundary explicitly ("Combat produces causes/events.
Life/Body owns bodily consequences") — restating it as a new Rule would duplicate, not refine,
already-settled content.**

**Repository evidence: SUPPORTED**, reused directly from BODY-07's own evidence.

**Scenarios:** none newly traced; reuses BODY-07's own evidence directly.

### Capability does not guarantee a favorable conflict outcome

> A higher-capability party may still lose an encounter — context, environment, resources, and
> decision quality may all still produce an unfavorable outcome for the nominally stronger
> side.

**Disposition: INHERITED — direct reuse of CAP-01's eligibility framing and Batch 06's
AGENCY-04, restated at Combat's own point of use per `capability-progression.md`'s own
identical entry. No new claim beyond that file's own citation.**

**Repository evidence: SUPPORTED**, reused directly — see `capability-progression.md`'s fuller
evidence for this same inherited entry.

**Scenarios:** [CP-S12](../scenarios/capability-progression-batch-07.md#cp-s12).

---

## Scope / Deferred Boundaries

### Universal conflict-resolution framework

> This family does not build a universal Conflict-resolution framework covering every
> imaginable contest type (competition, chase, coercion, territorial dispute as their own named
> mechanisms) — only Combat and the resource-contention examples CONFLICT-01 already cites are
> checked here, per the batch instruction's own explicit "do not create a universal
> conflict-resolution framework merely to support every imaginable contest" instruction.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **SUPPORTED — a genuine, positive, live counter-example to Batch 06's own CONFLICTING
  findings.** `TacticalDecisionSystem`'s hostile-candidate gathering routes through
  `PerceptionGate.can_perceive()` before any neighbor becomes target-eligible. See the
  Inherited perception/knowledge entry above (originally drafted as CONFLICT-02). This directly
  satisfies the batch instruction's own §15 requirement to verify current behavior rather than
  assume old findings hold everywhere.
- **INERT/OFF — the richer declared power-estimation pipeline (`combat_engagement` domain)
  never runs in production.** `OpponentPerceptionService`/`CombatLearning`/
  `EngagementRiskEvaluator` are real, detailed, specified in
  `docs/mechanics/04_strategic_cognition.md` §13, and gated behind `ENABLE_COMBAT_ENGAGEMENT`
  (default OFF) — "most of it already exists, unreachable," per that section's own explicit
  admission. No durable storage for `OpponentModel` exists on `EntityState` at all yet.
  Additionally, a live minor fallback risk: the gate call at `tactical.py`'s own call site is
  wrapped in `try/except Exception: pass` — a gate failure fails open (permissive), not closed;
  worth noting as a real, if narrow, robustness gap rather than a semantic violation.
  **Superseded note (2026-09-24):** `ENABLE_COMBAT_ENGAGEMENT` flipped to default ON via
  `TCK-20260914-COMBAT-ENGAGEMENT-PERCEIVED-POWER` (PR #190, `1e075b807`), predating this file's
  own `last_verified` date above — the INERT/OFF characterization no longer reflects live state.
  This Repository Finding is a point-in-time snapshot, not continuously re-verified; the
  Semantic Control Plane's ongoing M3 triage stream
  (`TCK-20260924-M3-TERRITORY-COMBAT-FINDING-TRIAGE`) is the current source of truth for
  `combat_engagement`'s realization status.
- **MISSING — no surrender, capture, or forced-displacement combat outcome exists.** See the
  inherited combat-outcome-vocabulary entry above.
- **MISSING — no non-combat Conflict superclass or contest-resolution mechanism is named as
  such.** Resource contention resolves through Batch 03/05's own RES-*/ECOL-04 mechanisms, not
  a dedicated "Conflict" abstraction — consistent with the Scope Boundary above, not a gap this
  family needed to fill.

## Cross-domain links recorded here

- CONFLICT-01 → Resource (RES-*, Batch 03), Ecology/Population (ECOL-04, Batch 05)
- CONFLICT-03 → Agency/Decision (AGENCY-01/02, Batch 06: intent lives in the decision layer),
  Organizations / factions (`organizations.md`; the faction catalog's hostility law)
- CONFLICT-04 → Agency/Decision (AGENCY-01/02/07, Batch 06: a step is a chosen action; flight
  is the decided way out), Movement/Navigation (MOV-07: orthogonal adjacency), Survival
  (SURV-07: a present threat outranks a need)
- Inherited perception/knowledge entry (formerly CONFLICT-02) → Perception (PERC-01, KNOW-01,
  Batch 06), Agency/Decision (AGENCY-01/02, Batch 06), Capability/Progression
  (`capability-progression.md`, the same ad hoc `CapabilityEstimateService` finding)
- Inherited combat-outcome entry → Life/Body (LIFE-01/02, Batch 05)
- Inherited bodily-consequence entry → Life/Body (BODY-07, Batch 05), State Ownership (OWN-02,
  Batch 01)

## Open questions carried forward

1. Whether the declared `combat_engagement` domain (§13 of `04_strategic_cognition.md`) should
   be turned on (`ENABLE_COMBAT_ENGAGEMENT`) is a rollout decision, not a semantic one — not
   decided here.
2. Whether the `try/except Exception: pass` permissive fallback around the live perception-gate
   call in `tactical.py` should instead fail closed is a real, small implementation question —
   flagged, not decided.
3. Whether surrender/capture/forced-displacement should become real combat outcomes is flagged
   for a future batch or ticket, not decided here.
4. Whether a dedicated non-combat Conflict-resolution mechanism (beyond resource contention)
   should ever be built is flagged, not decided — CONFLICT-01's own evidence shows the boundary
   is real without one.
