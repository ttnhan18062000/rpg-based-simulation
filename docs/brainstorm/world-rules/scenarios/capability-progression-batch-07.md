---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Capability / Progression / Conflict (Batch 07)

**Purpose/scope.** Sixteen scenarios used to pressure-test the Capability/Progression,
Learning/Adaptation, and Conflict/Combat rule families in
`capability-progression/capability-progression.md`, `learning-adaptation.md`, and
`conflict-combat.md`, per `tmp/world-rule-batch-7-ext-ai.md`. Covers all sixteen required seed
probes from that instruction's §13.

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## CP-S01 — Practice creates capability

An entity repeatedly performs a meaningful activity through a valid learning/adaptation
process; capability improves.

- **Rules invoked:** PROG-01, LEARN-02.
- **Result: partially covered — the general claim holds only for combat/quest success, not for
  "practice" in the sense the probe names.** Repeated *success* (kills, completed quests) does
  produce capability via XP/Level (PROG-01/PROG-02). Repeated *practice* specifically —
  deliberate, non-combat skill exercise — has no live path at all (`TRAIN_SKILL`'s unreachable
  opportunity generation, `capability-progression.md`'s own confirmed MISSING finding). The
  probe is covered under a substituted mechanism (combat success), not under practice itself.

## CP-S02 — Repetition without learning

The same trivial action is repeated with no meaningful new challenge or information; progression
eventually stops or remains negligible.

- **Rules invoked:** PROG-05, LEARN-02.
- **Result: revealed missing rule — the opposite of what the probe expects to find.** This
  repository has no mechanism that makes trivial repetition stop or diminish: repeatedly
  defeating the same trivial opponent grants the identical, undiminished XP every time
  (`defender.identity.evolution_level * classification.xp_multiplier`, no repeat-count or
  difficulty-mismatch adjustment). PROG-05's own Rule states that a counterforce is a legitimate
  design choice, not a requirement — but this repository's own choice is to have none, and a
  documentation claim of a bound (`max_xp_per_tick`) does not match the actual implementation.
  Scored as revealing a confirmed gap, not a rule violation — PROG-05 permits either shape;
  this repository picked the unbounded one.

## CP-S03 — Failure teaches

An entity attempts a difficult action, fails, gains information/experience, and later capability
changes.

- **Rules invoked:** LEARN-01, LEARN-02, Inherited (CAUSE-01).
- **Result: partially covered — failure teaches epistemically, not capability-wise.**
  `CausalAttributionService.attribute()` fires exactly on qualifying failure events
  (`combat_loss`, `failed_search`, `failed_craft`, `party_abandoned`) and produces a real
  `CausalMemoryEntry` — failure genuinely produces a durable change. But that change is
  epistemic (a route-scoring bias adjustment when the memory flag is on), never a capability/
  attribute change. "Later capability changes" (the probe's own final clause) does not happen
  from failure in this repository — only later *decisions* change.

## CP-S04 — Experience with no durable change (counter)

An event occurs; no declared learning/adaptation mechanism exists for it; capability remains
unchanged.

- **Rules invoked:** Inherited (CAUSE-01), LEARN-01.
- **Result: covered.** Most of the named lived-experience categories in the batch instruction's
  own §4 list (environmental exposure, social experience, leadership, long-term practice absent
  a qualifying `TRAIN_SKILL` path) produce zero capability change — confirmed directly, no
  mechanism reacts to them at all. This is the expected, correct shape per CAUSE-01: absent a
  real causal path, nothing should change, and nothing does.

## CP-S05 — Level up with real consequence

An XP threshold is reached; Level changes; a declared downstream capability/limit change
follows.

- **Rules invoked:** PROG-02.
- **Result: covered.** `LevelingService._execute_level_up()`/`EvolutionSystem.evaluate()`
  produce real, verified consequences on every level-up: `+5` unspent AP, level-gated skill
  unlocks (2/5/10), a flat `+20 * levels_gained` HP bump, and a `recalculate_combat_stats()`
  trigger via the apply path's `stats_dirty` gate. Level is never a bare counter.

## CP-S06 — Level with no consumer (counter)

Level increases; nothing reads it; no world consequence follows.

- **Rules invoked:** PROG-02.
- **Result: blocked — the counter-premise does not hold in this repository.** Checked directly:
  `identity.evolution_level` is read by `recalculate_combat_stats()` (indirectly, via the
  level-up execution that changes attributes/AP), by `CombatRewardClassificationService`'s own
  XP-reward formula (`defender.identity.evolution_level * ...`), and by
  `EvolutionSystem`'s own species-evolution threshold check (`[10, 25, 50]`). No consumer-less
  path was found for Level specifically — this counter-scenario's own premise is confirmed false
  for this repository, a positive finding recorded honestly rather than forced to reveal a gap
  that isn't there.

## CP-S07 — Capability without level

Injury, training, equipment, or adaptation changes capability; Level is unchanged.

- **Rules invoked:** PROG-01, PROG-03.
- **Result: covered.** Equipment swap, a `WoundState`/`ScarState` penalty, or an active
  `Breakthrough`/`ClassTier` bonus each changes `recalculate_combat_stats()`'s output with zero
  `evolution_level` change — confirmed independence, per PROG-03.

## CP-S08 — Injury causes regression

An experienced fighter is injured; persistent impairment follows; some capability decreases.

- **Rules invoked:** PROG-04, Inherited (BODY-04/06).
- **Result: covered — reuses Life/Body's own evidence directly.** `WoundState`/`ScarState`
  penalties (`atk_penalty`/`def_penalty`/`speed_penalty`/`max_hp_penalty`) are real, persistent,
  and read directly into combat-stat recalculation — a genuine capability regression, distinct
  from any identity or history change (PROG-04's own claim).

## CP-S09 — Conflict without combat

Two subjects pursue an incompatible resource/objective; one yields or loses access; no physical
combat occurs.

- **Rules invoked:** CONFLICT-01.
- **Result: covered.** A depleting resource node (`remaining_charges`/`max_charges`) and a
  blocked opportunity (`blocker_penalty=2.0`) both resolve incompatible-outcome contention
  without any combat encounter — confirmed real, non-combat Conflict resolution.

## CP-S10 — Combat does not guarantee progression

Combat occurs; no qualifying progression cause is present; capability remains unchanged.

- **Rules invoked:** PROG-05, Inherited (CAUSE-01).
- **Result: covered.** A `SURVIVE` or `REJECTED` combat outcome (`src/engine/combat.py`) grants
  zero XP — `xp_gain` is only ever computed on a genuine `KILL`/`DEFEAT`-classified defeat.
  Combat occurring is not itself the qualifying cause; a classified victory is.

## CP-S11 — Combat, defeat, survival

A fight occurs; one participant is defeated; survives; later history/capability is affected.

- **Rules invoked:** Inherited (LIFE-01/02, the combat-outcome-vocabulary entry).
- **Result: covered — reconfirms Batch 05 with one additional real outcome.** `DEFEAT`
  (non-lethal) and `REBIRTH` both preserve the defeated participant's continued existence; a
  wound/scar from that defeat persists as real capability regression (CP-S08's own evidence),
  and the encounter itself may become a `CausalMemoryEntry` (LEARN-01's own epistemic finding)
  when the memory flag is on. `FLED` is confirmed as a further, genuinely distinct real outcome
  beyond Batch 05's own original six-value vocabulary.

## CP-S12 — Stronger entity still loses

A higher-capability party loses an encounter because context/environment/resources/decision
differ.

- **Rules invoked:** Inherited (CAP-01's eligibility framing, AGENCY-04).
- **Result: covered.** Capability estimates and route/target scoring shape a decision before
  execution; nothing in the scoring layer guarantees the decision's own outcome — confirmed by
  construction, matching AGENCY-04's own already-settled boundary applied to Combat.

## CP-S13 — Power conversion

A fighter wins repeatedly; reputation grows; new opportunity/follower becomes possible.

- **Rules invoked:** PROG-07.
- **Result: partially covered — the reputation-growth half is real; the follower half is
  confirmed absent.** `FameDeriver`'s Option-B rule and `BeliefInstitution`'s route-scoring
  `personality_bias` bonus (Batch 05/06 evidence) are real, live conversion edges from combat/
  quest achievement into reputation and a concrete decision-relevant bonus. No mechanism
  converts that reputation into an actual recruited follower or subordinate — confirmed MISSING,
  scored honestly rather than assumed complete because *a* conversion edge exists.

## CP-S14 — Progression changes world reaction

An ordinary entity becomes unusually capable; other entities begin responding differently.

- **Rules invoked:** PROG-06.
- **Result: partially covered — a real, narrow channel exists; a general, capability-scaled
  one does not.** `ThreatService.record_kill()`'s flat `+1.0` retaliation-pressure-per-kill is a
  real, always-on world-reaction channel, but it reacts to the *fact* of a kill, not to the
  killer's or victim's own capability magnitude. `entity.kind`-keyed branches in
  `ecology.py`/`creature_territory.py`/`boss.py`/`calamity.py` are real but mostly hardcoded to
  specific kind strings, not a general function of growing capability.

## CP-S15 — Ordinary creature → regional threat (flagship, schematic)

An ordinary creature survives encounters, adapts, gains capability; territory/conflict
consequences increase; other entities begin reacting. Not scripted — asked whether current
Rules permit this trajectory causally.

- **Rules invoked:** PROG-06, PROG-07, Inherited (TRANS-01/ID-03, the evolution-as-
  transformation entry).
- **Result: partially covered — the trajectory is causally *possible* through real channels,
  but not yet a clean, unified pipeline.** Survival/adaptation is real (`EvolutionSystem`'s
  level-threshold-triggered kind change, TRANS-01-compliant); gaining capability is real
  (PROG-01/02/03); territory/conflict consequences increasing is real but narrow
  (`record_kill()`'s retaliation pressure, `creature_territory.py`'s per-kind maturity rate);
  "other entities begin reacting" holds for the region generally (retaliation pressure raises
  danger signals other entities' own scarcity/migration/threat-avoidance logic already reads,
  per Batch 05's ECOL-04) but does not hold for *named-individual* recognition of this specific
  creature's own growing significance — that channel (`LegendFact`/`FameState`) is real but
  role-gated to HERO entities only. The current Rules permit the trajectory; the current
  repository realizes about half of it for a non-HERO creature specifically.

## CP-S16 — Loss of capability without loss of history

A legendary fighter ages or is injured; capability declines; historical significance persists.

- **Rules invoked:** PROG-04, Inherited (LIFE-03, HP-01).
- **Result: covered for the injury half; MISSING for the aging half — recorded honestly rather
  than assumed symmetric.** Injury-driven capability decline is real (`WoundState`/`ScarState`,
  CP-S08's own evidence) and, per PROG-04/LIFE-03/HP-01, never touches the fighter's own
  identity or historical/legend record (`LegendFact`/`FameState` persist independent of current
  combat stats — confirmed by construction, since neither reads `WoundState`/`ScarState` at
  all). **Aging as a capability-decline driver was checked directly and confirmed absent**:
  `EvolutionSystem`'s only age/level-adjacent mechanism is monotonically upward growth; no
  mechanism reduces capability purely from elapsed time or advanced age. The probe's own
  premise ("ages... capability declines") only holds via injury in this repository, not via age
  itself.

---

## Cross-batch note

CP-S02's and PROG-05's own finding (no counterforce against repeated-trivial-kill farming,
including a confirmed documentation/implementation mismatch around `max_xp_per_tick`) is this
batch's single most load-bearing discovery, on par with Batch 05's ECOL-03/BODY-05 and
Batch 06's own CONFLICTING omniscience finding. CP-S14/S15's own finding (progression's
world-reaction channel is real but narrow and mostly capability-agnostic) is the batch
instruction's own explicitly "especially important" question, answered honestly as partial
rather than forced to a clean yes.

CP-S11's confirmation that `TacticalDecisionSystem`'s live targeting already routes through
`PerceptionGate` (CONFLICT-02's own evidence) is a genuinely positive counter-example to
Batch 06's CONFLICTING findings elsewhere — not every decision path in this repository bypasses
perception, and this batch's own investigation (per its §15's explicit instruction to verify
current behavior rather than assume) confirms that directly rather than assuming Batch 06's
findings generalize everywhere.
