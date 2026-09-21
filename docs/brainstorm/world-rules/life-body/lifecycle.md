---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Lifecycle

**Purpose/scope.** What makes a living subject alive, inactive/incapacitated, dying, dead,
reproduced, or otherwise changed in lifecycle state. Kinship, inheritance, dynasty, and family
role remain for Family/Lineage — this family establishes only that reproduction creates a new
living identity, never who that identity is to anyone socially.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

---

## LIFE-01 — Active participation and permanent lifecycle termination are distinct facts

> Whether a subject is currently an active participant (able to act, engage, be targeted as
> ongoing) and whether it has permanently ended its lifecycle (true death) are two separately
> tracked facts, not one. A subject may lose active-participant status without that being
> permanent.

**Disposition: ACCEPT.** This is the core distinction the batch instruction most explicitly
required ("incapacitated ≠ dead").

**Repository evidence: SUPPORTED, and unusually precisely.** `combat.alive` is set `False` at
`new_hp <= 0` uniformly, regardless of ultimate fate. Whether that fate is final is a separate
field entirely: `LifecycleUpdate.is_permadeath_set` (only ever set `True` under a specific
classification path) is the true, final-death marker — matching Batch 01's own ID-05 finding
("Dead subject as historical reference — `active=False`, `is_permadeath_set=True`"). The two
fields are never conflated in the same write.

**Scenarios:** [LB-S02](../scenarios/life-body-batch-05.md#lb-s02) (defeated but not dead),
[LB-S03](../scenarios/life-body-batch-05.md#lb-s03) (HP zero boundary).

---

## LIFE-02 — Incapacitation/defeat does not necessarily mean death

> A subject losing active-participant status (being defeated, incapacitated) does not, by
> itself, entail permanent lifecycle termination. A real classification process may route a
> defeat toward continued existence (in a reduced or altered state) rather than toward death.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, and this is a genuinely rich instance.**
`CombatResolutionSystem`'s outcome classification (`src/engine/combat.py`) does not stop at
"alive/not alive" — it further classifies `KILL`, `DEFEAT` (explicitly non-lethal, e.g. for
`EntityRole.HERO`, where `is_lethal` is forced `False`), `REBIRTH` (when
`classification.rebirth_eligible` and `defender.lifecycle.generation < 4` — `generation_delta=1`,
identity continues), and only `PERMADEATH` (rebirth exhausted, `generation >= 4`) as truly
final. Losing a fight and permanently dying are architecturally distinct outcomes here, not
merely different labels for the same event.

**Scenarios:** [LB-S01](../scenarios/life-body-batch-05.md#lb-s01) (wounded but alive),
[LB-S02](../scenarios/life-body-batch-05.md#lb-s02) (defeated but not dead).

---

## LIFE-03 — Death terminates active participation; it does not delete identity or history

> A subject's permanent death ends its ability to act, but its identity and historical record
> remain real and referenceable. This restates ID-05 and HP-01 at this family's own point of
> use — no new claim.

**Disposition: ACCEPT, by explicit reuse.**

**Repository evidence:** none newly gathered — reuses ID-05's own evidence
(`_transfer_inherited_feud()`, `_seed_dying_wish()`, `CorpseState` as a distinct object)
directly.

**Scenarios:** [LB-S16](../scenarios/life-body-batch-05.md#lb-s16) (death with persistent
history).

---

## LIFE-04 — Reproduction establishes a new, distinct living identity

> A reproduction process, given valid parent(s), produces a genuinely new living subject —
> never a continuation of a parent's own identity, even where the new subject carries real
> provenance (biological parentage) from them. This restates ID-04, applied to Lifecycle
> specifically, and deliberately does not decide family role, surname, inheritance, dynastic
> legitimacy, or social parenthood — those remain for Family/Lineage and Social domains.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `V2EntityBuilder.birth_record()` constructs a genuinely new
`entity_id` and records `parent_a_entity_id`/`parent_b_entity_id` as provenance, never as
identity — reused directly from Batch 01's ID-04 finding. This batch does not add new evidence;
it confirms the finding still holds when read from Lifecycle's own vantage point.

**Scenarios:** [LB-S10](../scenarios/life-body-batch-05.md#lb-s10) (birth creates new identity),
[LB-S11](../scenarios/life-body-batch-05.md#lb-s11) (parent ≠ child identity, counter).

---

## LIFE-05 — Biological parentage is distinct from social/familial relationship semantics

> Being a biological parent does not, by itself, establish family role, surname, inheritance
> rights, dynastic legitimacy, or any other social/familial meaning. This family states only
> that reproduction has occurred and who provided provenance; what that provenance *means*
> socially is Family/Lineage's own question.

**Disposition: ACCEPT, by explicit scope limitation — per the batch instruction's direct
requirement.**

**Repository evidence:** not applicable — this rule is a scope boundary. `parent_a_entity_id`/
`parent_b_entity_id` exist and are populated (LIFE-04's evidence); nothing in this repository
currently attaches social meaning to them, which is consistent with this boundary rather than a
gap this family needs to fill.

**Scenarios:** none; the boundary is enforced by omission (no social-meaning content exists to
check against yet).

---

## LIFE-06 — Lifecycle transitions require a valid triggering process, not an arbitrary change

> A lifecycle transition (an age-stage change, a generation/rebirth increment) requires a real,
> declared trigger — never an arbitrary or unconditional state edit. This restates TRANS-01 for
> lifecycle specifically.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED, reusing evidence gathered for an adjacent purpose across two
prior batches.** `LifeStageService.get_stage_for_age()`'s declared age thresholds (Batch 02's
TIME-05 evidence) and `CombatResolutionSystem`'s `generation_delta`/rebirth-eligibility
classification (LIFE-02's own evidence) both gate their respective transitions on a real,
checkable condition — never an unconditional write.

**Scenarios:** none newly traced; reuses LIFE-02's and Batch 02's TIME-05 evidence directly.

---

## Cross-domain links recorded here

- LIFE-01, LIFE-02 → Identity (ID-05), History/Provenance (HP-01), State Ownership
  (the alive/permadeath field separation is itself an OWN-01 instance — one authoritative
  source per fact, not one field trying to mean two things)
- LIFE-03 → Identity (ID-05), History/Provenance (HP-01), explicit reuse
- LIFE-04, LIFE-05 → Identity (ID-04), Family/lineage & succession (deferred family-meaning
  content), Social relations & identity
- LIFE-06 → Transformation (TRANS-01), Time (TIME-05)

## Open questions carried forward

1. `DEFEAT` (non-lethal, non-rebirth-eligible) as a final `outcome_kind` was found in the code
   but not confirmed to actually occur in practice for any currently-classified entity kind —
   whether it is a live, reachable outcome or a vestigial label was not resolved this batch.
   Flagged, not decided.
2. LIFE-05's boundary is currently enforced by the absence of any social-meaning content — this
   is correct for now, but should be re-checked once Family/Lineage is actually designed, to
   confirm that content doesn't quietly attach social meaning to `parent_a/b_entity_id`
   directly rather than through its own declared mechanism.
