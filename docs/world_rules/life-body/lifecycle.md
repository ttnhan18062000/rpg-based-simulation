---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Lifecycle

**Purpose/scope.** What makes a living subject alive, inactive/incapacitated, dying, dead,
reproduced, or otherwise changed in lifecycle state. Kinship, inheritance, dynasty, and family
role remain for Family/Lineage — this family establishes only that reproduction creates a new
living identity, never who that identity is to anyone socially.

**Status.** Batch 05 (Life/Body/Survival/Ecology), first draft. Candidates below originated as
external-reviewer hypotheses (`tmp/world-rule-batch-5-ext-ai.md`); each carries this session's
disposition and repository evidence, not the original wording uncritically kept.

**Normalized 2026-09-22** per external-reviewer instruction on Rule admission discipline
(`tmp/world-rule-batch-5-normalization-ext-ai.md`): entries below are separated into Domain
Rules (new local IDs — genuinely new or domain-refined semantic constraints), Inherited /
Applied Foundational Rules (direct reuse/reconfirmation of an existing Rule ID, no new claim),
and Scope / Deferred Boundaries. No entry was removed, no evidence discarded, and no ID was
renumbered — reclassification only changes which section an existing ID lives under and updates
its Disposition line to say so. Of the six original LIFE-* entries, **two (LIFE-01, LIFE-02)
are genuine Domain Rules; three (LIFE-03, LIFE-04, LIFE-06) are Inherited/Applied Foundational
Rules; one (LIFE-05) is a Scope/Deferred Boundary.**

---

## Domain Rules

## LIFE-01 — Active participation and permanent lifecycle termination are distinct facts

> Whether a subject is currently an active participant (able to act, engage, be targeted as
> ongoing) and whether it has permanently ended its lifecycle (true death) are two separately
> tracked facts, not one. A subject may lose active-participant status without that being
> permanent.

**Disposition: ACCEPT.** This is the core distinction the batch instruction most explicitly
required ("incapacitated ≠ dead"). Passes the admission test: this is a domain-refined
semantic constraint (the alive/permadeath field separation stated as a general lifecycle law),
not a restatement of an existing Rule ID under a new name.

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

**Disposition: ACCEPT.** Passes the admission test: this refines LIFE-01's distinction into an
operational claim about *how* a defeat resolves (a real classification process, not a binary),
which no earlier Rule ID already states.

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

## Inherited / Applied Foundational Rules

Direct reuse or reconfirmation of an already-accepted Rule ID at Lifecycle's own point of use.
Per the admission test ("reconfirmation of an earlier Rule → reference, not a new Rule"), these
carry no new local Rule ID. Content, evidence, and scenario links are unchanged from the
original draft — only the categorization and the Disposition line changed.

### LIFE-03 — Death terminates active participation; it does not delete identity or history

> A subject's permanent death ends its ability to act, but its identity and historical record
> remain real and referenceable.

**Disposition: INHERITED — direct reuse of ID-05 and HP-01 at this family's own point of use.
Reclassified 2026-09-22 (normalization pass): the original draft already stated "no new claim";
the admission test confirms this belongs here rather than in Domain Rules.**

**Repository evidence:** none newly gathered — reuses ID-05's own evidence
(`_transfer_inherited_feud()`, `_seed_dying_wish()`, `CorpseState` as a distinct object)
directly.

**Scenarios:** [LB-S16](../scenarios/life-body-batch-05.md#lb-s16) (death with persistent
history).

### LIFE-04 — Reproduction establishes a new, distinct living identity

> A reproduction process, given valid parent(s), produces a genuinely new living subject —
> never a continuation of a parent's own identity, even where the new subject carries real
> provenance (biological parentage) from them.

**Disposition: INHERITED — direct reuse of ID-04, applied to Lifecycle specifically.
Reclassified 2026-09-22 (normalization pass): the claim itself adds no constraint beyond ID-04's
own; the family-role/surname/inheritance/dynastic-legitimacy boundary this entry also names is
recorded separately below under Scope / Deferred Boundaries (LIFE-05), not folded into this
Inherited entry.**

**Repository evidence: SUPPORTED.** `V2EntityBuilder.birth_record()` constructs a genuinely new
`entity_id` and records `parent_a_entity_id`/`parent_b_entity_id` as provenance, never as
identity — reused directly from Batch 01's ID-04 finding. This batch does not add new evidence;
it confirms the finding still holds when read from Lifecycle's own vantage point.

**Scenarios:** [LB-S10](../scenarios/life-body-batch-05.md#lb-s10) (birth creates new identity),
[LB-S11](../scenarios/life-body-batch-05.md#lb-s11) (parent ≠ child identity, counter).

### LIFE-06 — Lifecycle transitions require a valid triggering process, not an arbitrary change

> A lifecycle transition (an age-stage change, a generation/rebirth increment) requires a real,
> declared trigger — never an arbitrary or unconditional state edit.

**Disposition: INHERITED — direct reuse of TRANS-01 for lifecycle specifically. Reclassified
2026-09-22 (normalization pass): restates an existing Rule at a new point of use without
refining its semantics.**

**Repository evidence: SUPPORTED, reusing evidence gathered for an adjacent purpose across two
prior batches.** `LifeStageService.get_stage_for_age()`'s declared age thresholds (Batch 02's
TIME-05 evidence) and `CombatResolutionSystem`'s `generation_delta`/rebirth-eligibility
classification (LIFE-02's own evidence) both gate their respective transitions on a real,
checkable condition — never an unconditional write.

**Scenarios:** none newly traced; reuses LIFE-02's and Batch 02's TIME-05 evidence directly.

---

## Scope / Deferred Boundaries

### LIFE-05 — Biological parentage is distinct from social/familial relationship semantics

> Being a biological parent does not, by itself, establish family role, surname, inheritance
> rights, dynastic legitimacy, or any other social/familial meaning. This family states only
> that reproduction has occurred and who provided provenance; what that provenance *means*
> socially is Family/Lineage's own question.

**Disposition: SCOPE BOUNDARY — explicit deferral to Family/Lineage, per the batch
instruction's direct requirement.** Not a Domain Rule: it makes no claim about target world
semantics itself, only about which future domain owns a claim not yet made.

**Repository evidence:** not applicable — this is a scope boundary, not a semantic claim.
`parent_a_entity_id`/`parent_b_entity_id` exist and are populated (LIFE-04's evidence); nothing
in this repository currently attaches social meaning to them, which is consistent with this
boundary rather than a gap this family needs to fill.

**Scenarios:** none; the boundary is enforced by omission (no social-meaning content exists to
check against yet).

---

## Cross-domain links recorded here

- LIFE-01, LIFE-02 → Identity (ID-05), History/Provenance (HP-01), State Ownership
  (the alive/permadeath field separation is itself an OWN-01 instance — one authoritative
  source per fact, not one field trying to mean two things)
- LIFE-03 (inherited) → Identity (ID-05), History/Provenance (HP-01), explicit reuse
- LIFE-04 (inherited), LIFE-05 (scope boundary) → Identity (ID-04), Family/lineage & succession
  (deferred family-meaning content), Social relations & identity
- LIFE-06 (inherited) → Transformation (TRANS-01), Time (TIME-05)

## Open questions carried forward

1. `DEFEAT` (non-lethal, non-rebirth-eligible) as a final `outcome_kind` was found in the code
   but not confirmed to actually occur in practice for any currently-classified entity kind —
   whether it is a live, reachable outcome or a vestigial label was not resolved this batch.
   Flagged, not decided.
2. LIFE-05's boundary is currently enforced by the absence of any social-meaning content — this
   is correct for now, but should be re-checked once Family/Lineage is actually designed, to
   confirm that content doesn't quietly attach social meaning to `parent_a/b_entity_id`
   directly rather than through its own declared mechanism.
