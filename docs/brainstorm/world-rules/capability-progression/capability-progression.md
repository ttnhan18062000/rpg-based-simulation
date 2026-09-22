---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Capability / Progression

**Purpose/scope.** What capabilities living entities actually acquire, lose, improve, combine,
or transform over time, and what makes an entity meaningfully different because of what it has
lived through. Foundational Capability (Batch 03's CAP-01–05: eligibility to attempt/produce a
transition) is not restated here — this family investigates the acquisition/loss mechanics
foundational Capability deliberately left open. Does not require one universal capability
representation.

**Status.** Batch 07 (Capability/Progression/Conflict), drafted 2026-09-22, revised the same
day per a follow-up Rule-admission and semantic cleanup
(`tmp/world-rule-batch-7-followup-ext-ai.md`): PROG-01/02/05/06 rewritten to remove
repository-evaluation language ("checked," "verified," "this repository has N mechanisms")
from their own Rule statements — that language now lives only in Repository Findings/Evidence;
PROG-04 reclassified from a Domain Rule to Inherited, since its distinctness claim is fully
covered by combining Identity/History-Provenance/Body-Condition Rules already established, not
genuinely new progression-specific content. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-7-ext-ai.md`); each carries this session's disposition and
repository evidence. Structured per the normalized five-category methodology established in
Batch 05/06's admission-discipline passes — only genuinely new or domain-refined semantics
receive a local Rule ID.

---

## Domain Rules

## PROG-01 — Capability acquisition and loss occur through declared causal mechanisms; different mechanisms may coexist without being unified into one progression system

> Capability acquisition and loss occur through declared causal mechanisms, and different
> mechanisms may coexist without being unified into one progression system.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — the Rule's own quoted
statement now states only the semantic core; the specific count and identity of this
repository's own mechanisms moved to Repository evidence, where a repository fact belongs.**
Passes the admission test: no earlier Rule states that capability acquisition/loss must trace
to a declared mechanism *and* that multiple, non-unified mechanisms are legitimate — CAP-01–05
(Batch 03) establish eligibility semantics, not acquisition/loss plurality.

**Repository evidence: SUPPORTED, by real plurality.** At least five independent, non-unified
mechanisms exist in this repository: (1) XP/Level → `LevelingService._execute_level_up()`
grants `+5` Attribute Points and level-gated skill unlocks for `EntityRole.HERO`; (2) direct
attribute deltas (`vitality`/`strength`/`endurance`, scaled by `entity.aptitude`) for non-HERO
entities on the *same* level-up event (`EvolutionSystem.evaluate()`) — a role-differentiated
mechanism, not one path; (3) equipment (`recalculate_combat_stats()` Step 2 — atk/def/hp/
evasion bonuses from equipped, non-broken items); (4) `BreakthroughService`/`ClassTierService`
registries (ad hoc attribute bonuses, `apply_bonuses()`); (5) `WoundState`/`ScarState`
(Batch 01/05's own evidence — persistent capability *penalties* from injury). None of these
mechanisms is required to route through any other; a future capability-affecting mechanism may
add a sixth without touching the other five — this is this repository's own current instance
of the Rule's own permissive claim, not the claim itself.

**Scenarios:** [CP-S01](../scenarios/capability-progression-batch-07.md#cp-s01) (practice
creates capability), [CP-S07](../scenarios/capability-progression-batch-07.md#cp-s07)
(capability without level), [CP-S17](../scenarios/capability-progression-batch-07.md#cp-s17)
(non-combat lived experience, added per 2026-09-22 follow-up).

---

## PROG-02 — XP and Level are materialized abstractions whose meaning comes from their declared world consequences

> XP and Level are materialized abstractions whose meaning comes from their declared world
> consequences; neither substitutes for the underlying capability/history it represents.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — restated as a semantic claim
about what gives XP/Level their meaning, removing the original wording's "must be checked
against the repository's own implementation" framing, which described a verification
discipline rather than a world semantic.** Passes the admission test: this states XP/Level's
own representational status — a domain-specific claim distinct from BODY-01's analogous claim
about HP (a different subject, not reused here), and not addressed by any earlier Rule.

**Repository evidence: SUPPORTED — checked directly, with a real downstream consequence
confirmed.** `identity.evolution_points`/`identity.evolution_level` are real `AuthoritativeState`
fields, granted only via the conservation path (`IdentityUpdate(evolution_points_delta=...)`,
`source_kind="COMBAT"` or `"QUEST"`). A level-up is not inert: it grants `+5` unspent AP, unlocks
level-gated skills (2/5/10), adds a flat `+20 * levels_gained` HP bump
(`EvolutionSystem.evaluate()`), and triggers `recalculate_combat_stats()` (the apply path's own
`stats_dirty` gate) — a real, verified downstream consequence, not an assumed one.

**Scenarios:** [CP-S05](../scenarios/capability-progression-batch-07.md#cp-s05) (level up with
real consequence), [CP-S06](../scenarios/capability-progression-batch-07.md#cp-s06) (level with
no consumer, counter).

---

## PROG-03 — Capability and Level are independent axes; neither implies the other

> Capability may change without Level changing (equipment, injury, breakthroughs, class tier),
> and Level increasing does not automatically grant every possible capability improvement
> (unspent AP sits inert until spent; skill unlocks are fixed and sparse, not proportional to
> what was actually practiced).

**Disposition: ACCEPT.** Passes the admission test: this states the specific bidirectional
independence claim the batch instruction's own §3 required checked — no earlier Rule addresses
the Capability/Level relationship.

**Repository evidence: SUPPORTED, in both directions.** Capability-without-Level: equipment
swap, a `WoundState`/`ScarState` penalty, or an active `Breakthrough`/`ClassTier` bonus each
changes `recalculate_combat_stats()`'s output with zero `evolution_level` change. Level-without-
proportional-capability: `unspent_ap` accumulates but grants nothing until an explicit
`execute_allocate_ap` action spends it (PROG-067 gate) — a level-up alone does not retroactively
improve stats beyond its own fixed `+20 HP`/skill-unlock grant.

**Scenarios:** [CP-S07](../scenarios/capability-progression-batch-07.md#cp-s07).

---

## PROG-05 — Repeatable accumulation/progression sources must declare their scaling, limiting, or counterforce semantics; unlimited repeatability must not arise accidentally

> Repeatable accumulation/progression sources must declare their scaling, limiting, or
> counterforce semantics; unlimited repeatability must not arise accidentally. This does not
> require equilibrium or guaranteed diminishing returns — a mechanism may legitimately declare
> no limiting effect at all — but that must be a stated design choice, not a silent default no
> one decided.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — restated so the Rule requires
a *declared* scaling/limiting/counterforce stance (which may legitimately be "none"), rather
than requiring a counterforce to exist or be verified against behavior.** The original wording
("must be verified against real behavior, not assumed present") described a verification
discipline, not a world semantic; this revision keeps the semantic core (unlimited
repeatability must be a stated choice, not an accident) while moving the verification act
itself to Repository evidence. The batch instruction explicitly required challenging
farming/exploit-like loops — the honest finding, now recorded purely as evidence, is that this
repository's combat-XP source declares no scaling/limiting/counterforce stance at all — an
accidental default, not a stated one.

**Repository Finding: MISSING, confirmed directly — the most load-bearing finding in this
family.** `xp_gain = defender.identity.evolution_level * classification.xp_multiplier`
(`CombatRewardClassificationService`, `src/engine/combat.py`) is a pure function of the
*defeated target's* level and role-based multiplier — it reads nothing about how many times
this specific attacker has defeated this specific (or same-kind) opponent before, nothing about
the attacker's own relative capability, and nothing about difficulty mismatch. Repeatedly
defeating the same trivial, already-mastered opponent grants the identical, undiminished XP
reward every time. Checked directly for any diminishing-returns, repeat-kill-count, or
per-tick-cap logic anywhere in `src/progression/`, `src/engine/combat.py`, or
`src/engine/evolution.py` — none exists. **Documentation/implementation mismatch, disclosed
here rather than silently corrected:** `docs/engine/supported_progression_surface_phase5.md`
claims "Entity progression is bounded by `max_xp_per_tick` (engine contract)" — no
`max_xp_per_tick` symbol, constant, or check exists anywhere in `src/`. This is a doc claiming a
bound that the implementation does not have, not a Rule Catalog finding about repository
behavior violating a target semantic — flagged so a future reader is not misled by the doc's
own claim.

**Scenarios:** [CP-S02](../scenarios/capability-progression-batch-07.md#cp-s02) (repetition
without learning), [CP-S10](../scenarios/capability-progression-batch-07.md#cp-s10) (combat
does not guarantee progression, counter-adjacent).

---

## PROG-06 — Progression may change how the world reacts to an individual through declared causal channels

> Progression may change how the world reacts to an individual through declared causal
> channels — a subject becoming more capable, or changing kind through growth, is permitted to
> produce real, observable changes in how the surrounding world responds to it, wherever a
> real channel connects the two.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — restated as the semantic
permission itself, removing the original wording's "this family checks that it does rather
than assuming it" framing, which described this session's own verification act rather than a
world semantic.** The batch instruction's own flagship scenario ("Ordinary Creature → Regional
Threat") is exactly what this Rule states is permitted; whether this repository's own current
channels realize it fully is a Repository Finding (below), not part of the Rule's own claim.

**Repository evidence: PARTIAL, checked directly against two independent real channels.**
(1) `ThreatService.record_kill()` (`src/world/threat.py`) raises a region's
`retaliation_pressure` by a flat `+1.0` per kill — a real, general, always-on world-reaction
channel, but capability-agnostic: it does not scale with the killed (or killing) entity's own
level, kind, or significance, only with the raw fact that a kill occurred in that region.
`ThreatService.process_threat_evolution()` further ties peaceful-state trauma decay to the
absence of a live `entity.kind == "world_boss"` — a real, if narrowly kind-string-keyed, example
of an evolved/special kind mattering to regional dynamics. (2) `entity.kind` (mutated by
`EvolutionSystem._get_evolved_kind()` on level-threshold crossing) is read broadly across
`src/world/ecology.py`, `src/world/creature_territory.py` (`CreatureTerritoryService`'s
per-kind territory-maturity rate), `src/world/boss.py`, and `src/world/calamity.py` — but
mostly through hardcoded kind-string branches rather than a general function of the entity's
own capability magnitude. **What is confirmed MISSING**: no mechanism tracks a non-HERO,
individually-evolved entity's own growing significance the way `LegendFact`/`FameState`
(Batch 05/06 evidence) tracks a HERO's fame from `entity_death`/`quest_completed` events — that
individual-significance-tracking channel is real but role-gated to HERO entities specifically,
not a general "any entity that becomes unusually capable is tracked and reacted to by name"
mechanism. The batch instruction's own flagship trajectory (ordinary creature → survives →
adapts → gains capability → territory/conflict consequences increase → other entities react) is
therefore causally *possible* through the retaliation-pressure/kind-branching channels, but not
yet realized as a clean, capability-scaled, individual-tracking pipeline for ordinary creatures.

**Scenarios:** [CP-S13](../scenarios/capability-progression-batch-07.md#cp-s13) (power
conversion), [CP-S14](../scenarios/capability-progression-batch-07.md#cp-s14) (progression
changes world reaction), [CP-S15](../scenarios/capability-progression-batch-07.md#cp-s15)
(ordinary creature → regional threat, flagship — deepened 2026-09-22 to explicitly distinguish
generic kind/threat reaction from reaction to this specific historied individual).

---

## PROG-07 — Different forms of effective power do not automatically convert into each other; each conversion edge requires its own real, declared mechanism

> Power is plural (physical, informational, economic, social, political, institutional,
> territorial, magical) — this family does not introduce one universal `Power` stat. A concrete
> conversion edge (e.g., combat victory → reputation) is only real where a specific mechanism
> implements it; the existence of one edge does not imply any other edge exists.

**Disposition: ACCEPT.** Passes the admission test: this states the plurality-of-power and
conversion-edge-specificity design principle the batch instruction's own §6 required — no
earlier Rule addresses power conversion.

**Repository evidence: SUPPORTED for one real edge (combat → fame); MISSING for the batch
instruction's own named example (fame → followers).** `FameDeriver`'s Option-B event rule
credits fame from a HERO's `entity_death` or `quest_completed` `NarrativeLedgerEntry` —
combat/quest achievement converting into a real, durable `FameState`/`LegendFact` is a genuine,
implemented conversion edge (Batch 05/06 evidence). That fame further converts into a real
`personality_bias` route-scoring bonus via `BeliefInstitution` (clan-level reverence,
Batch 05/06 evidence) — a second real edge, though a route-scoring nudge rather than literal
followers. **Checked directly: no mechanism converts fame/reputation into actual recruited
followers, subordinates, or any concrete social-capital grant** — the specific example the batch
instruction itself named ("fighter wins repeatedly → reputation grows → new opportunity/
follower becomes possible") is only half-real in this repository: the reputation-growth half is
real; the follower-grant half is confirmed absent.

**Scenarios:** [CP-S13](../scenarios/capability-progression-batch-07.md#cp-s13).

---

## Inherited / Applied Foundational Rules

### Capability loss/regression is distinct from identity loss and history erasure (PROG-04)

> A subject may durably lose capability (injury, equipment loss/breakage, a spent or reverted
> breakthrough) without that touching its own identity or historical record. Capability loss,
> identity loss, and history erasure are three separate facts, never conflated.

**Disposition: INHERITED — reclassified 2026-09-22 per follow-up review, from a Domain Rule
(originally drafted as PROG-04) to this Inherited entry.** The distinctness claim is fully
covered by combining Identity/History-Provenance/Body-Condition Rules already established:
Batch 05's LIFE-03/HP-01 (death/identity ends action, never identity or history) and Batch 01/
05's BODY-04/BODY-06 (injury durably reduces capability, a separate owned fact) jointly already
establish everything this claim needs — capability can degrade (BODY-04/06) without that
touching identity or history (LIFE-03/HP-01). No genuinely new progression-specific semantic
content survives once those two boundaries are combined; the importance of the distinction is
not, by itself, a reason to keep a local Rule ID for it.

**Repository evidence: SUPPORTED for capability loss via injury and equipment; MISSING for
several other named loss categories.** `WoundState`/`ScarState` penalties (Batch 01/05
evidence) and equipment breaking (`durability <= 0` zeroing its stat contribution on the next
recalculation) are both real, confirmed capability-loss paths that touch neither identity nor
history. **Confirmed MISSING**, checked directly: no skill-decay-from-disuse mechanism exists
(a learned skill, once unlocked, is never removed or weakened by lack of use); no mechanism
reduces capability from "lost social access" (out of this family's own scope — Social relations'
own concern). Aging as a capability-loss driver was not found either — `EvolutionSystem`'s own
level-gated growth is the only age-adjacent mechanism, and it is monotonically upward, never a
decline.

**Scenarios:** [CP-S08](../scenarios/capability-progression-batch-07.md#cp-s08) (injury causes
regression), [CP-S16](../scenarios/capability-progression-batch-07.md#cp-s16) (loss of
capability without loss of history).

### Foundational Capability (eligibility) is distinct from acquisition/loss mechanics

> Being mechanically eligible to attempt or produce a transition (foundational Capability) is a
> separate fact from how a subject actually gains, loses, or improves that eligibility over
> time.

**Disposition: INHERITED — direct reuse of CAP-01–05 (Batch 03). This family's own scope
statement (§1 of the batch instruction) explicitly requires not restating foundational
Capability; every Domain Rule above investigates acquisition/loss mechanics CAP-01–05
deliberately left open, never eligibility semantics themselves.**

**Repository evidence: SUPPORTED**, reused directly from Batch 03's own CAP-01–05 evidence.

**Scenarios:** none newly traced; reuses Batch 03's own evidence directly.

### A durable capability consequence requires a real causal path, independent of an event's narrative label

> A lived-experience event producing a durable capability change must trace to a real cause —
> not to nothing, and not to an arbitrary "event happened → stat bonus" label.

**Disposition: INHERITED — direct reuse of CAUSE-01. The batch instruction's own §4 warning
("avoid: event happened → arbitrary stat bonus, without a meaningful bridge") is exactly
CAUSE-01's own real-causal-path requirement, applied to Progression specifically; no new claim
is added by restating it here.**

**Repository evidence: SUPPORTED**, reused directly: every real capability-affecting mechanism
this family found (XP grant, attribute delta, equipment change, wound/scar penalty,
breakthrough/class-tier bonus) traces to a real, typed `*Update` producer — never a raw,
unexplained field edit.

**Scenarios:** [CP-S03](../scenarios/capability-progression-batch-07.md#cp-s03) (failure
teaches), [CP-S04](../scenarios/capability-progression-batch-07.md#cp-s04) (experience with no
durable change, counter).

### Capability does not guarantee success

> Being mechanically capable of an action is a necessary, not sufficient, condition for
> succeeding at it — context, decision, and circumstance may still produce failure regardless
> of capability.

**Disposition: INHERITED — direct reuse of CAP-01's own eligibility framing ("eligibility to
attempt/produce a transition," never a success guarantee) and Batch 06's AGENCY-04 (decision
validity ≠ execution outcome). No new claim: this is the Combat/Progression-specific
instantiation of an already-settled boundary.**

**Repository evidence: SUPPORTED**, reused directly from CAP-01/AGENCY-04's own evidence, plus
this family's own confirmation that `AdventureRouteScorer`'s scoring and `TacticalDecisionSystem`'s
target selection both complete before any execution outcome is known — capability/confidence
inputs shape the decision, never the result.

**Scenarios:** [CP-S12](../scenarios/capability-progression-batch-07.md#cp-s12) (stronger
entity still loses).

### Injury/scars are a real, persistent capability-reducing mechanism

> A persistent wound or scar reduces real, live combat capability (attack/defense/speed/max-HP
> penalties read directly into stat recalculation), not merely a cosmetic record.

**Disposition: INHERITED — direct reuse of Batch 01/05's BODY-04/BODY-06. No new claim: this
family's own PROG-04 entry (above, itself Inherited) cites this as one of capability loss's
real, confirmed instances, but the underlying mechanism and its ownership were already fully
established.**

**Repository evidence: SUPPORTED**, reused directly from BODY-04/BODY-06's own evidence.

**Scenarios:** [CP-S08](../scenarios/capability-progression-batch-07.md#cp-s08).

### Ordinary progression-driven transformation is a valid instance of Transformation's own trigger requirement

> A creature transforming into a "sufficiently adapted" form of itself through ordinary growth
> (a level threshold, an accumulated milestone) is a concrete, valid instance of Transformation's
> own requirement that every transformation trace to a real, declared trigger — not a new kind
> of transformation semantics.

**Disposition: INHERITED — direct reuse of TRANS-01 (Batch 03) and ID-03's default+exception
slot (Batch 01). Per the batch instruction's own §12 explicit guidance, major supernatural
transformation (human → vampire) stays with Magic; this entry only confirms that
progression-driven kind-change is TRANS-01's own principle at work, not a new Rule.**

**Repository evidence: SUPPORTED.** `EvolutionSystem._get_evolved_kind()` maps a real,
declared level-threshold trigger (`[10, 25, 50]`, crossed via `IdentityUpdate`) to a new
`entity.kind` (`GOBLIN → GOBLIN_WARRIOR → ORC_SCOUT`, `WOLF → DIRE_WOLF`, `HERO → LEGEND_HERO`,
or a generic numeric-suffix increment) — a real, TRANS-01-compliant transformation, gated on a
real trigger, never an unconditional or arbitrary kind edit.

**Scenarios:** none newly traced; the transformation itself is folded into
[CP-S14](../scenarios/capability-progression-batch-07.md#cp-s14)'s and
[CP-S15](../scenarios/capability-progression-batch-07.md#cp-s15)'s own evidence.

---

## Scope / Deferred Boundaries

### Major supernatural transformation stays with Magic

> Progression-driven transformation covered here is ordinary creature-to-adapted-creature
> growth (EvolutionSystem's own kind-mapping). Major supernatural transformation (human →
> vampire, or comparable qualitative species change driven by magical rather than ordinary
> causes) is not designed here, per the batch instruction's own explicit deferral.

**Disposition: SCOPE BOUNDARY.**

### Later-domain power-conversion chains

> This family confirms that *some* conversion edges (combat → fame, fame → route-scoring bias)
> exist and are real, and that others (fame → followers) do not — but it does not design the
> economic, social, political, institutional, territorial, or magical conversion chains
> themselves. Those remain with their own future domain batches.

**Disposition: SCOPE BOUNDARY.**

### Universal progression architecture

> This family does not introduce implementation concepts such as `UniversalProgressionSystem`,
> `BasePower`, `GenericExperience`, or `UniversalSkill`. The conceptual progression grammar
> (State → Experience → Accumulation → Adaptation/Learning → Capability → Power → Conversion →
> Influence → World Reaction → Transformation) is shared design vocabulary, not a required
> implementation pipeline — domain implementation remains specific, per the batch instruction's
> own explicit instruction.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **MISSING — no counterforce against repeated-trivial-kill farming.** See PROG-05 above, the
  most load-bearing finding in this family, including the documentation/implementation mismatch
  around `max_xp_per_tick`.
- **INERT/OFF — the Breakthrough-granting mechanism is never invoked in production.**
  `BreakthroughService.apply_bonuses()` is real, live, and wired into `get_effective_stats()`,
  but nothing in production/gameplay code ever constructs
  `IdentityUpdate(breakthroughs_add=[...])` to actually grant one — confirmed via
  `TCK-20260808-TRAIT-EXPRESSED-PRODUCER-INVESTIGATION`, cited directly in
  `docs/mechanics/attribute_progression_contract.md`. The application path is fully wired; the
  granting path has no live producer outside tests.
- **MISSING — practice/training as a capability-improvement path is unreachable.**
  `RouteFamily.TRAIN_SKILL` exists as an enum value and maps to `ObjectiveKind.REACH_LOCATION`
  in `ObjectiveIntentResolver`, but `AdventureRouteGenerator.generate()`'s own `kind_map` and
  structural-default branches (Batch 06 evidence) never produce a `TRAIN_SKILL` opportunity —
  confirmed directly. Even if reached, arriving at a training location was not found to grant
  any skill or attribute change. Practice, as the batch instruction's own §5 investigates it, is
  a declared route family with no live path to ever fire.
- **MISSING — no capability-improving mechanism exists for most named lived-experience
  categories.** Checked directly against the batch instruction's own §4 list: repeated
  non-combat success/failure, near-death survival (beyond `REBIRTH`'s own generation increment,
  which is a lifecycle fact, not a capability grant), environmental exposure, social experience,
  leadership, and long-term practice all produce no capability change anywhere in this
  repository. Only combat/quest XP and injury/scars durably change capability.
- **MISSING — no combat outcome beyond kill/defeat/survive/withdrawal exists.** Confirmed real
  `outcome_kind` values: `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`/`SURVIVE`/`REJECTED`
  (`src/engine/combat.py`), plus a real, separately-produced `FLED` (withdrawal,
  `src/engine/movement.py`'s `combat_escape="EVASIVE_SUCCESS"`). No surrender, capture, or
  forced-displacement-as-a-combat-outcome exists. `src/world/displacement.py` exists but is a
  calamity-driven, World-Evolution-domain population-relocation mechanism, unrelated to combat
  defeat — a naming near-collision worth flagging, not a semantic overlap.
- **MISSING — fame does not convert into followers.** See PROG-07 above.
- **PARTIAL — progression's world-reaction channel is real but narrow and mostly
  capability-agnostic.** See PROG-06 above — the most important finding the batch instruction
  itself flagged as critical.

## Cross-domain links recorded here

- PROG-01 → Capability (CAP-01–05, inherited above), Life/Body (BODY-04/06, inherited above)
- PROG-02, PROG-03 → State Ownership (OWN-01, the authoritative-field pattern), Perception/
  Knowledge (Batch 06's own "materialized abstraction" framing precedent, BODY-01, analogous
  but not reused)
- PROG-04 (now Inherited) → Identity/History (LIFE-03, HP-01), Body/Condition (BODY-04/06)
- PROG-05 → Causality (CAUSE-01, the general real-causal-path requirement this Rule's own
  counterforce question sits alongside without restating)
- PROG-06 → Ecology/Population (ECOL-03/04, Batch 05 — the individual↔aggregate causal-loop
  pattern this Rule's own finding echoes at a different scale), History/Provenance (fame/legend
  tracking)
- PROG-07 → Social relations (deferred conversion chains), History/Provenance (`FameState`/
  `LegendFact`, `BeliefInstitution`)

## Open questions carried forward

1. Whether a counterforce (diminishing returns, risk/difficulty scaling, or a real per-tick
   cap) should be added to combat XP rewards is a real design/implementation question, not
   decided here — flagged as the most load-bearing gap in this family.
2. Whether the `max_xp_per_tick` documentation claim should be implemented, or the doc corrected
   to match current behavior, is not decided here.
3. Whether `TRAIN_SKILL` should gain a real opportunity producer, and what it should actually
   grant on arrival, is a real design question for a future ticket — not decided here.
4. Whether an ordinary (non-HERO) entity's individually-growing significance should gain its own
   tracking mechanism (parallel to `LegendFact`/`FameState`'s HERO-only scope), closing PROG-06's
   own confirmed gap, is flagged for a future batch or ticket, most plausibly Social relations
   or a later Ecology/population-focused pass.
5. Whether fame/reputation should gain a real follower/recruitment conversion edge is flagged
   for Social relations, not decided here.
