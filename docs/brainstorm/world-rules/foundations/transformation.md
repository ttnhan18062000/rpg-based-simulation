---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Transformation

**Purpose/scope.** What makes a transition a *qualitative transformation* rather than an
ordinary state update. This family investigates the shape of transformation in general — it does
not define any particular domain's transformation (vampire, settlement lifecycle, species
evolution), and it explicitly preserves Batch 01's own already-settled Identity rule rather than
reopening it.

**Status.** Foundational Batch 03, first draft. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-3-ext-ai.md`); each carries this session's disposition and
repository evidence, not the original wording uncritically kept.

**Explicit non-goal, per the batch instruction.** Do not define vampire-, evolution-, or
settlement-specific transformation semantics here — those stay with Magic/supernatural,
Capability & progression, and Places/settlements & territory respectively, whenever each is
reached.

---

## TRANS-01 — A qualitative transformation requires a valid trigger, not an arbitrary update

> A transformation has a shape: a subject before → a valid trigger/precondition → the
> transformation itself → a subject after. An arbitrary state edit that happens to change a lot
> of fields at once is not automatically a transformation in this sense unless a real trigger
> condition gates it.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `EvolutionSystem.evaluate()` checks accumulated level/XP
against declared thresholds (`for threshold in [10, 25, 50]`) before applying a kind/attribute/
equipment/reward change — the transformation never fires from an arbitrary or unconditional
write.

**Scenarios:** [CTR-S13](../scenarios/foundational-batch-03.md#ctr-s13).

---

## TRANS-02 — A transformation's actual scope is whatever the domain rule declares, not a fixed bundle

> Transformation may affect classification, capabilities, constraints, relationships, resource
> behavior, or future affordances — but a given transformation touching one of these does not
> require it to touch all of them. The list is a menu of possible effects, not a mandatory
> checklist.

**Disposition: ACCEPT.**

**Repository evidence: SUPPORTED.** `EvolutionSystem`'s own transformation changes
classification (`kind`), capabilities/attributes, and equipment/reward — but does not touch
relationships or resource behavior at all. Nothing in the repository requires it to; the scope of
each transformation is whatever that specific mechanism declares.

**Scenarios:** [CTR-S13](../scenarios/foundational-batch-03.md#ctr-s13).

---

## TRANS-03 — Transformation preserves identity by default; this family does not redefine that boundary

> Per ID-03 (`identity.md`): a transformation preserves identity unless an explicit domain rule
> defines it as identity-ending or identity-creating. This family investigates what qualifies as
> a transformation at all — it explicitly does not reopen, restate with different wording, or
> add exceptions to ID-03's own default/exception boundary.

**Disposition: ACCEPT, by explicit deference — this rule's entire content is "defer to ID-03,"
per the batch instruction's own direct requirement** ("Preserve Batch 01's Identity rule").

**Repository evidence:** none newly gathered — reuses ID-03's own evidence
(`EvolutionSystem` never constructs a new entity id) without re-verifying it, since re-verifying
an already-accepted rule's evidence would duplicate work rather than add anything.

**Scenarios:** none newly traced; ID-03's own scenarios (FND-S01, FND-S02, FND-S13, FND-S14)
remain the evidence base.

---

## TRANS-04 — The accumulated condition, not the threshold-check, is the real cause of a transformation

> When a transformation is gated by a threshold (an XP total, an accumulated exposure), the
> threshold-crossing is the trigger a rule checks for — the real cause is the accumulated history
> the threshold is testing, per LIMIT-04's general principle applied here specifically.

**Disposition: ACCEPT.** This is TRANS-01 sharpened with LIMIT-04's causal-legitimacy standard,
stated once at the general level (`capacity.md`) and applied here rather than re-derived.

**Repository evidence: SUPPORTED**, reusing LIMIT-04's own evidence: `EvolutionSystem`'s
`for threshold in [10, 25, 50]` is the check, not the cause — crossing the threshold one tick
earlier or later would not itself explain the transformation; the accumulated level/XP would.

**Scenarios:** [CTR-S10](../scenarios/foundational-batch-03.md#ctr-s10) (same required counter
as LIMIT-04 — threshold crossed, required trigger/context absent, transformation does not occur).

---

## TRANS-05 — Domain-specific transformations are out of scope for this family

> `human → vampire`, `camp → settlement → ruin`, and every other specific transformation content
> belongs to the domain that owns it (Magic/supernatural, Places/settlements & territory,
> Capability & progression), not to this foundational family. This family states only the shape
> a transformation must have and the boundary conditions it must respect (TRANS-01–04,
> ID-03) — never a particular transformation's content.

**Disposition: ACCEPT, by explicit scope limitation — per the batch instruction's direct
requirement** ("Do not define vampire/evolution/settlement-specific transformations here.").

**Repository evidence:** not applicable — this rule is a scope boundary, not a claim requiring
evidence.

**Scenarios:** none; ID-03/CAUSE-02's already-recorded deferrals (human→vampire, camp→settlement
→ruin) remain the record of what's deferred and to where.

---

## Cross-domain links recorded here

- TRANS-01, TRANS-02 → Capability & progression (the future domain designing
  `EvolutionSystem`'s actual content)
- TRANS-03 → Identity (ID-03, explicit deference, not a new link — this family adds no new
  claim to Identity's own boundary)
- TRANS-04 → Capacity (LIMIT-04, reused directly), Causality (CAUSE-01)
- TRANS-05 → Magic/supernatural, Places/settlements & territory, Capability & progression
  (every domain-specific transformation this family explicitly defers)

## Open questions carried forward

None newly raised by this family — every open question a Transformation-shaped investigation
would surface (what makes `human → vampire` identity-ending; what makes `camp → settlement →
ruin` a real transformation) is already recorded under ID-03 in `identity.md`, and this family
was deliberately drafted not to duplicate that record.
