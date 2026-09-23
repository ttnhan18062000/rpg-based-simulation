---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
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

---

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

> A combat encounter resolves into one of several distinct outcomes — kill, non-lethal defeat,
> rebirth, permanent death, mutual survival, rejection, or withdrawal — never a binary
> victory/death pair.

**Disposition: INHERITED — direct reuse of Batch 05's LIFE-01/LIFE-02, which already fully
established this exact claim ("incapacitated ≠ dead," a real classification process, not one
predetermined outcome). This batch's own contribution is confirming the vocabulary is
*richer* than Batch 05 traced, not restating the claim.**

**Repository evidence: SUPPORTED, with one additional confirmed outcome beyond Batch 05's own
evidence.** `src/engine/combat.py`'s real `outcome_kind` values: `KILL`/`DEFEAT`/`REBIRTH`/
`PERMADEATH`/`SURVIVE`/`REJECTED`. A further real, separately-produced outcome —
`FLED` (`src/engine/movement.py`'s `combat_escape="EVASIVE_SUCCESS"` property update) —
confirms withdrawal is a genuine seventh category, not merely combat resolving to one of the six
`CombatUpdate.outcome_kind` values. **Confirmed MISSING**, checked directly: no surrender,
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
- **MISSING — no surrender, capture, or forced-displacement combat outcome exists.** See the
  inherited combat-outcome-vocabulary entry above.
- **MISSING — no non-combat Conflict superclass or contest-resolution mechanism is named as
  such.** Resource contention resolves through Batch 03/05's own RES-*/ECOL-04 mechanisms, not
  a dedicated "Conflict" abstraction — consistent with the Scope Boundary above, not a gap this
  family needed to fill.

## Cross-domain links recorded here

- CONFLICT-01 → Resource (RES-*, Batch 03), Ecology/Population (ECOL-04, Batch 05)
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
