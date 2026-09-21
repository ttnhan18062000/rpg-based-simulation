---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Body / Condition

**Purpose/scope.** How a living subject carries persistent bodily state that constrains or
enables future behavior — health/vitality, injury, wounds, impairment, fatigue, condition,
resistance/vulnerability. Preserves the pattern `body state → capability consequences`, never
`body state → decorative numbers only` — a wound that never affects anything is challenged as
inert bookkeeping, not assumed meaningful by its own existence.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

---

## BODY-01 — HP/vitality is a materialized abstraction, not a literal complete physical description

> HP/vitality may be canonical, materialized simulation state representing survivability or
> accumulated harmful condition, while richer wound/body state may coexist where it adds
> meaningful causal value. HP is not required to represent every physical fact about a subject
> — it is a deliberate abstraction, not a claim of biological completeness.

**Disposition: ACCEPT.** This is the explicit disposition the batch instruction required
(§3) — stated directly rather than left implicit.

**Repository evidence: SUPPORTED, by the coexistence of both layers.** `entity.combat.hp` is a
single scalar (the materialized abstraction); `WoundState`/`ScarState` (Batch 01's own
evidence) are richer, independently-tracked records with their own `atk_penalty`/
`def_penalty`/`speed_penalty`/`max_hp_penalty` fields — HP does not attempt to encode any of
that detail itself, and the richer layer exists specifically where it adds capability
consequences (BODY-04) that a bare scalar couldn't.

**Scenarios:** [LB-S03](../scenarios/life-body-batch-05.md#lb-s03) (HP zero boundary).

---

## BODY-02 — HP reaching zero triggers a real classification process, not a single automatic outcome

> Reaching zero HP does not, by itself, determine what happens next — it triggers a real
> classification (this batch's own LIFE-02 finding: `KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`),
> not one hardcoded "death" transition.

**Disposition: ACCEPT.** Directly required by the batch instruction's own "HP Zero Boundary"
probe ("what semantic transition is actually implied? Do not assume the answer in advance").

**Repository evidence: SUPPORTED**, reusing LIFE-02's own evidence: `new_hp <= 0` is the
trigger condition, but `CombatRewardClassificationService.classify_defeated_target()` and the
generation/rebirth-eligibility check determine the actual outcome — reaching zero is a
necessary condition for several different transitions, never a sufficient one for any single
predetermined result.

**Scenarios:** [LB-S03](../scenarios/life-body-batch-05.md#lb-s03).

---

## BODY-03 — HP loss and injury are related but not identical facts

> Losing HP does not necessarily mean a wound/injury record is created, and (in principle)
> injury could exist independent of HP loss. This repository's own current implementation
> produces both from the same event, which is evidence of one legitimate pairing, not proof
> that the two facts must always co-occur.

**Disposition: ACCEPT, with the coupling recorded as evidence rather than as the rule.** The
batch instruction explicitly asked this to be determined clearly rather than assumed — the
honest finding is that this repository's *current* combat path always produces both together,
but nothing in the architecture requires that pairing generally.

**Repository evidence: PARTIAL — coupled at the one production site checked, independence not
verified either way.** `CombatResolutionSystem._get_wound_infliction(attacker, defender,
damage, tick, alive)` is called alongside the same event that produces `hp_delta` — both are
derived from the same `damage` value at the same call site. Whether any path produces HP loss
without a wound (or a wound-equivalent record without HP loss) was not found in this batch's
investigation — recorded as PARTIAL, not SUPPORTED, since only the coupled case was confirmed.

**Scenarios:** [LB-S01](../scenarios/life-body-batch-05.md#lb-s01) (wounded but alive).

---

## BODY-04 — Body condition creates real capability consequences, never decorative numbers

> Wounds, impairment, and other persistent bodily state must produce a meaningful downstream
> effect on capability or behavior. A body-state field that changes but never affects anything
> is challenged as inert bookkeeping, not treated as meaningful by its own existence.

**Disposition: ACCEPT strongly.**

**Repository evidence: SUPPORTED.** `WoundState`/`ScarState`'s `atk_penalty`/`def_penalty`/
`speed_penalty`/`max_hp_penalty` fields (Batch 01's own evidence) are read directly into
combat-stat recalculation — a real, live capability consequence, not a cosmetic record.

**Scenarios:** [LB-S01](../scenarios/life-body-batch-05.md#lb-s01),
[LB-S06](../scenarios/life-body-batch-05.md#lb-s06) (persistent injury).

---

## BODY-05 — Recovery from injury/impairment requires a valid, declared recovery process

> Impairment decreasing over time must trace to a real, declared recovery mechanism (time,
> treatment, rest, or another valid process) — never spontaneous, unexplained healing.

**Disposition: ACCEPT, with a confirmed gap this batch's own investigation found — the
required mechanism doesn't merely need to be checked, it needs to be honestly reported as
absent.** The rule states what recovery must look like *if it exists*; this repository does
not yet have one for HP specifically.

**Repository evidence: MISSING, confirmed directly.** No positive HP-restoration path was
found anywhere in the engine — checked directly (`grep` for any positive `hp_delta` or
HP-increasing assignment on `combat.hp` returns nothing outside unrelated building-HP setup
code). Entities *perceive* a "healing" need (`src/cognition/need_interpretation.py`'s
`InterpretedNeed(key="healing", ...)`, triggered when self-assessed health is low) and can form
goals around it, but no mechanism exists anywhere that actually fulfills that need by
increasing HP. This is a real, confirmed gap — a perceived need with no fulfillment path,
distinct from (and arguably more concerning than) a merely-inert tracked field, since here the
world's own decision layer is asking for something the world cannot deliver.

**Scenarios:** [LB-S07](../scenarios/life-body-batch-05.md#lb-s07) (recovery — the required
counter: no spontaneous healing, and here, confirmed no healing at all).

---

## BODY-06 — Persistent injury may remain after the harmful event ends

> An impairment produced by a past harmful event may continue to affect a subject after that
> event is over — persistence is a legitimate, expected property of body condition, not a bug
> to be resolved by the harm ending.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED**, reused directly from Batch 01's ID-05/WoundState evidence —
`WoundState`/`ScarState` records persist as their own durable state, independent of whether the
originating combat encounter is still ongoing.

**Scenarios:** [LB-S06](../scenarios/life-body-batch-05.md#lb-s06).

---

## BODY-07 — Life/Body owns the bodily consequence of environmental exposure, given subject-specific protection

> When Environment (`space-environment/environment.md`'s ENV-02) establishes a real exposure
> condition, Life/Body is the domain that determines whether — given the subject's own
> protection, resistance, or immunity — that condition actually produces bodily harm. This
> answers, for the specific case of *bodily* harm, the open ownership question ENV-03
> deliberately left unresolved: Life/Body is *a* legitimate owner of this consequence (not
> necessarily the only one a future domain might add for non-bodily exposure effects).

**Disposition: ACCEPT.** This is this batch's own resolution of one of Batch 04's explicitly
carried-forward open questions — resolved here because Life/Body is the domain positioned to
answer it, not assumed in advance by Environment itself.

**Repository evidence: SUPPORTED, reusing Batch 04's own evidence from this domain's side.**
`EnvironmentService.calculate_hazard_drain()`'s immunity check
(`get_faction_semantics_service().get_hazard_immunities(faction_id)`) is exactly the
"subject-specific protection" step; the resulting drain, when nonzero, is committed via
`CombatUpdate(hp_delta=..., alive_set=...)` in `WorldDynamicsSystem.resolve_dynamics()` — a
Life/Body-relevant update path (`combat.hp`, this family's own BODY-01 abstraction), confirming
Life/Body as a real owner of this specific consequence.

**Scenarios:** [LB-S05](../scenarios/life-body-batch-05.md#lb-s05) (hazard but protected),
reuses Batch 04's SPC-S04/S05/S13 evidence directly.

---

## Cross-domain links recorded here

- BODY-01 → State Ownership (OWN-03, the derived-vs-owned distinction applied to HP vs. wound
  detail)
- BODY-02 → Causality (CAUSE-01, threshold-is-not-automatically-the-cause discipline reused),
  Capacity (LIMIT-04, directly reused)
- BODY-04, BODY-06 → Capability & progression (the future domain that designs concrete
  capability-impairment content on top of this boundary)
- BODY-05 → Agency/motivation/decision (the "healing" need's own perception/goal-formation
  side, `src/cognition/need_interpretation.py`)
- BODY-07 → Space/Environment/Movement (ENV-02, ENV-03 — this rule is this batch's own answer
  to ENV-03's deliberately-left-open question, for bodily harm specifically)

## Open questions carried forward

1. BODY-03's HP-loss/injury coupling was only confirmed at one production site
   (`_get_wound_infliction`) — whether any future mechanism (poison, disease, magic) should
   produce one without the other is not decided here.
2. BODY-05's confirmed gap (no HP recovery mechanism at all) is the most load-bearing MISSING
   finding in this family — affects any future content that wants injured entities to
   eventually recover without permanent, unrecoverable damage. Not designed here, per the
   batch instruction's own non-goal against forcing detailed wound simulation prematurely —
   but the *absence of any* recovery path, as opposed to a deliberately narrow one, is flagged
   as worth prioritizing.
3. BODY-07 answers ENV-03's open question for bodily harm specifically; it does not decide
   whether other exposure-consequence types (capability impairment without HP loss, resource
   loss from exposure) belong to Life/Body or another domain — left open for whichever future
   domain first needs to answer it.
