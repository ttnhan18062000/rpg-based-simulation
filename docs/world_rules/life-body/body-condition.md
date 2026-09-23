---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
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

**Normalized 2026-09-22** per external-reviewer instruction on Rule admission discipline
(`tmp/world-rule-batch-5-normalization-ext-ai.md`): entries separated into Domain Rules and
Inherited/Applied Foundational Rules. No entry was removed, no evidence discarded, no ID
renumbered. Of the seven original BODY-* entries, **six (BODY-01, BODY-03, BODY-04, BODY-05,
BODY-06, BODY-07) are genuine Domain Rules; one (BODY-02) is an Inherited/Applied Foundational
Rule** — it restates this same batch's own LIFE-02 finding at the HP-zero-boundary level
without adding a new constraint beyond it.

---

## Domain Rules

## BODY-01 — HP/vitality is a materialized abstraction, not a literal complete physical description

> HP/vitality may be canonical, materialized simulation state representing survivability or
> accumulated harmful condition, while richer wound/body state may coexist where it adds
> meaningful causal value. HP is not required to represent every physical fact about a subject
> — it is a deliberate abstraction, not a claim of biological completeness.

**Disposition: ACCEPT.** This is the explicit disposition the batch instruction required
(§3) — stated directly rather than left implicit. Passes the admission test: no earlier Rule
states HP's own representational status.

**Repository evidence: SUPPORTED, by the coexistence of both layers.** `entity.combat.hp` is a
single scalar (the materialized abstraction); `WoundState`/`ScarState` (Batch 01's own
evidence) are richer, independently-tracked records with their own `atk_penalty`/
`def_penalty`/`speed_penalty`/`max_hp_penalty` fields — HP does not attempt to encode any of
that detail itself, and the richer layer exists specifically where it adds capability
consequences (BODY-04) that a bare scalar couldn't.

**Scenarios:** [LB-S03](../scenarios/life-body-batch-05.md#lb-s03) (HP zero boundary).

---

## BODY-03 — HP loss and injury are related but not identical facts

> Losing HP does not necessarily mean a wound/injury record is created, and (in principle)
> injury could exist independent of HP loss. This repository's own current implementation
> produces both from the same event, which is evidence of one legitimate pairing, not proof
> that the two facts must always co-occur.

**Disposition: ACCEPT, with the coupling recorded as evidence rather than as the rule.** The
batch instruction explicitly asked this to be determined clearly rather than assumed — the
honest finding is that this repository's *current* combat path always produces both together,
but nothing in the architecture requires that pairing generally. Passes the admission test: no
earlier Rule distinguishes HP loss from injury as separable facts.

**Repository evidence (Repository Finding): PARTIAL — coupled at the one production site
checked, independence not verified either way.** `CombatResolutionSystem._get_wound_infliction
(attacker, defender, damage, tick, alive)` is called alongside the same event that produces
`hp_delta` — both are derived from the same `damage` value at the same call site. Whether any
path produces HP loss without a wound (or a wound-equivalent record without HP loss) was not
found in this batch's investigation — recorded as PARTIAL, not SUPPORTED, since only the
coupled case was confirmed. This is a repository fact about the current implementation, not the
Rule's own claim (the Rule claims the two facts are distinguishable in principle; it does not
claim this repository already exercises that distinction).

**Scenarios:** [LB-S01](../scenarios/life-body-batch-05.md#lb-s01) (wounded but alive).

---

## BODY-04 — Body condition creates real capability consequences, never decorative numbers

> Wounds, impairment, and other persistent bodily state must produce a meaningful downstream
> effect on capability or behavior. A body-state field that changes but never affects anything
> is challenged as inert bookkeeping, not treated as meaningful by its own existence.

**Disposition: ACCEPT strongly.** Passes the admission test as a standing modeling constraint
specific to Body/Condition — no earlier Rule requires this.

**Repository evidence: SUPPORTED.** `WoundState`/`ScarState`'s `atk_penalty`/`def_penalty`/
`speed_penalty`/`max_hp_penalty` fields (Batch 01's own evidence) are read directly into
combat-stat recalculation — a real, live capability consequence, not a cosmetic record.

**Scenarios:** [LB-S01](../scenarios/life-body-batch-05.md#lb-s01),
[LB-S06](../scenarios/life-body-batch-05.md#lb-s06) (persistent injury).

---

## BODY-05 — Recovery from injury/impairment requires a valid, declared recovery process

> Impairment decreasing over time must trace to a real, declared recovery mechanism (time,
> treatment, rest, or another valid process) — never spontaneous, unexplained healing. This is
> the Rule's own semantic principle, target-state-independent of whether this repository
> currently implements any such mechanism.

**Disposition: ACCEPT.** The rule states what recovery must look like *if it exists*; whether
this repository currently has one is a separate, Repository Finding-level question (below), not
part of the Rule's own claim. Passes the admission test: no earlier Rule states a recovery
discipline.

**Repository Finding: MISSING, confirmed directly.** No positive HP-restoration path was found
anywhere in the engine — checked directly (`grep` for any positive `hp_delta` or HP-increasing
assignment on `combat.hp` returns nothing outside unrelated building-HP setup code). Entities
*perceive* a "healing" need (`src/cognition/need_interpretation.py`'s `InterpretedNeed(
key="healing", ...)`, triggered when self-assessed health is low) and can form goals around it,
but no mechanism exists anywhere that actually fulfills that need by increasing HP. This is a
real, confirmed gap — a perceived need with no fulfillment path, distinct from (and arguably
more concerning than) a merely-inert tracked field, since here the world's own decision layer is
asking for something the world cannot deliver. This finding is a fact about the current
repository, not a restatement of the Rule itself; the Rule (recovery must trace to a declared
process) remains a standing constraint on any future recovery mechanism, whenever one is built.

**Scenarios:** [LB-S07](../scenarios/life-body-batch-05.md#lb-s07) (recovery — the required
counter: no spontaneous healing, and here, confirmed no healing at all).

---

## BODY-06 — Persistent injury may remain after the harmful event ends

> An impairment produced by a past harmful event may continue to affect a subject after that
> event is over — persistence is a legitimate, expected property of body condition, not a bug
> to be resolved by the harm ending.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states this persistence
property for bodily impairment specifically (History/Provenance's HP-01 covers identity/history
persistence, a different subject).

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
answer it, not assumed in advance by Environment itself. Passes the admission test: this is new
domain-refined content, not a restatement of ENV-02/ENV-03 (which deliberately left this
question open rather than answering it).

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

## Inherited / Applied Foundational Rules

### BODY-02 — HP reaching zero triggers a real classification process, not a single automatic outcome

> Reaching zero HP does not, by itself, determine what happens next — it triggers a real
> classification (`KILL`/`DEFEAT`/`REBIRTH`/`PERMADEATH`), not one hardcoded "death" transition.

**Disposition: INHERITED — direct reuse of this same batch's own LIFE-02 finding, restated at
the HP-zero-boundary level. Reclassified 2026-09-22 (normalization pass): the original draft
explicitly cited this as "this batch's own LIFE-02 finding"; the admission test treats this as
reconfirmation, not a new constraint — HP-02's own framing (the trigger condition) adds no
semantics LIFE-02 does not already state.** Kept here because the batch instruction's own "HP
Zero Boundary" probe specifically required checking this at the HP level, not because the claim
itself is new.

**Repository evidence: SUPPORTED**, reusing LIFE-02's own evidence: `new_hp <= 0` is the
trigger condition, but `CombatRewardClassificationService.classify_defeated_target()` and the
generation/rebirth-eligibility check determine the actual outcome — reaching zero is a
necessary condition for several different transitions, never a sufficient one for any single
predetermined result.

**Scenarios:** [LB-S03](../scenarios/life-body-batch-05.md#lb-s03).

---

## Repository Findings (significant, cross-referenced)

- **BODY-05's confirmed absence of any HP recovery mechanism** — no positive `hp_delta` path
  exists anywhere in the engine; entities can perceive a "healing" need with no fulfillment
  path. The most load-bearing finding in this family. See BODY-05 above for full evidence.
- **BODY-03's HP-loss/injury coupling** — confirmed only at one production site
  (`_get_wound_infliction`), independence from HP loss not verified either way. See BODY-03
  above.

## Cross-domain links recorded here

- BODY-01 → State Ownership (OWN-03, the derived-vs-owned distinction applied to HP vs. wound
  detail)
- BODY-02 (inherited) → Causality (CAUSE-01, threshold-is-not-automatically-the-cause discipline
  reused), Capacity (LIMIT-04, directly reused), Lifecycle (LIFE-02, direct source)
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
