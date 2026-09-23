---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Family / Kinship

**Purpose/scope.** What makes two individuals family in world-semantic terms. Does not assume
biological descent, social parenthood, adoption, partnership/marriage, household co-residence,
and lineage membership are equivalent. Only models distinctions that have causal value.

**Status.** Batch 09 (Social Relations/Family/Lineage), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-9-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## FAM-01 — Biological parentage, social parenthood, marriage/partnership, household co-residence, and lineage membership are distinct family-structural facts; none automatically implies affection, loyalty, inheritance eligibility, or legal authority

> Biological parentage, social parenthood, marriage/partnership, household co-residence, and
> lineage membership are separate family-structural facts — a subject may hold any one without
> the others (a biological parent who never raised the child; an adoptive parent with no
> biological link; spouses who are not each other's ancestor/descendant; housemates who are not
> kin). None of these facts, singly or combined, automatically implies affection, loyalty,
> inheritance eligibility, or legal authority — those remain separate facts requiring their own
> declared basis.

**Disposition: ACCEPT.** Passes the admission test: this is genuinely new content answering
this batch's own §7/§8 investigation, and it directly resolves a boundary Batch 05's own
LIFE-05 deliberately deferred rather than answered ("Biological parentage is distinct from
social/familial relationship semantics... what that provenance means socially is Family/
Lineage's own question" — a Scope Boundary in Batch 05, not a settled claim). Answering that
deferred question with a real, multi-way distinction is new content, not a restatement of
LIFE-05 itself.

**Repository evidence: SUPPORTED for biological parentage and marriage as real, structurally
independent facts; MISSING for social parenthood/adoption and household as their own tracked
facts.** `parent_a_entity_id`/`parent_b_entity_id` (`EntityState.identity`, Batch 05 evidence)
record biological parentage — checked directly, nothing else in this repository (loyalty,
affection, inheritance eligibility) is derived from or gated by these two fields.
`MarriageState` (`src/core/strategic.py`, Batch 09's own SOC-02 evidence) is a real, separate
structural fact, written independent of any biological or household relation — spouses hold no
special `parent_a/b_entity_id` relation to each other, confirming marriage and biological
parentage are genuinely independent facts already in this repository. **Confirmed MISSING**,
checked directly: no `social_parent_id`/adoption field exists anywhere on `EntityState`; no
`household_id`/co-residence field exists anywhere either — a biological parent who never
raises a child and an adoptive parent who does are, today, indistinguishable in this
repository's own state beyond the raw `parent_a/b_entity_id` fact itself.

**Scenarios:** [SL-S08](../scenarios/social-lineage-batch-09.md#sl-s08) (biological parent
without social parenting), [SL-S09](../scenarios/social-lineage-batch-09.md#sl-s09) (adoptive
parent), [SL-S11](../scenarios/social-lineage-batch-09.md#sl-s11) (kinship without affection).

---

## Inherited / Applied Foundational Rules

### Reproduction establishes a new, distinct living identity

> A reproduction process produces a genuinely new living subject, never a continuation of
> either parent's own identity — biological parentage is provenance, not identity continuity.

**Disposition: INHERITED — direct reuse of ID-04 (Batch 01) and LIFE-04 (Batch 05). This
family's own §8 explicitly states "Batch 05 already established reproduction → new identity;
Batch 09 now owns the family-side result" — the identity claim itself is not restated here,
only the family-meaning question FAM-01 above actually answers.**

**Repository evidence: SUPPORTED**, reused directly from ID-04/LIFE-04's own evidence.

**Scenarios:** none newly traced; reuses LIFE-04's own CP-S10/CP-S11-equivalent evidence
(Batch 05's own LB-S10/LB-S11) directly.

### Derived kinship conclusions must remain consistent with authoritative relationship facts, never a second duplicate truth

> A world may compute a derived kinship conclusion (e.g., "siblings" from a shared declared
> parent) without storing it as its own separately-writable fact — but if it does store one,
> that stored conclusion must never be allowed to silently disagree with the authoritative
> facts it was derived from.

**Disposition: INHERITED — direct reuse of Batch 01's OWN-03 (derived views are not duplicate
truth). This family's own §9 investigation ("kinship conclusions must remain consistent with
authoritative relationship facts... do not create duplicate durable truths that can silently
disagree") is exactly OWN-03's own claim, applied to kinship specifically — no new content.**

**Repository evidence: SUPPORTED by absence — checked directly, this repository has no
occasion yet to violate this boundary, because it does not derive or store any kinship
conclusion at all.** No `sibling`/`grandparent`/lineage-traversal function exists anywhere in
`src/` — confirmed directly via broad search. `parent_a_entity_id`/`parent_b_entity_id` are the
only stored family-structural facts; nothing computes "sibling" (shared parent) or any deeper
derived relation from them, so there is no derived-truth-vs-authoritative-fact drift risk
today, only because no derivation exists to drift. This is a **confirmed MISSING** finding
(no derived-kinship computation anywhere), recorded as evidence for this Inherited entry
rather than as its own Domain Rule, per OWN-03's own already-settled claim.

**Scenarios:** [SL-S10](../scenarios/social-lineage-batch-09.md#sl-s10) (sibling derivation).

---

## Scope / Deferred Boundaries

### Household as its own simulated system

> This family does not build a household simulator — co-residence, shared consumption, and
> shared support remain undesigned unless a real, causally-important consumer is found,
> per the batch instruction's own explicit "investigate only if current repository semantics
> make it causally important" instruction. Checked directly: no household-adjacent state or
> consumer was found (`docs/mechanics/04_strategic_cognition.md` §8 explicitly confirms "No
> household/family/dependents state is added to `MarriageState`... that belongs to a separate
> ticket"), so this remains fully deferred rather than partially designed.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.**

- **MISSING — no social parenthood/adoption tracking exists.** See FAM-01 above.
- **MISSING — no household/co-residence tracking exists.** See the Scope Boundary above.
- **MISSING — no derived-kinship computation (sibling, grandparent) exists anywhere.** See the
  Inherited OWN-03 entry above.

## Cross-domain links recorded here

- FAM-01 → Life/Body (LIFE-05, Batch 05 — the deferred boundary this Rule directly answers),
  Ownership/Possession (`ownership-possession.md`, the "family relation ≠ inheritance" half of
  this Rule's own claim, deepened in `lineage-descent.md`)
- Inherited reproduction entry → Identity (ID-04), Life/Body (LIFE-04, Batch 05)
- Inherited derived-kinship entry → State Ownership (OWN-03, Batch 01)

## Open questions carried forward

1. Whether social parenthood/adoption should gain its own tracked state is flagged for a
   future ticket, not decided here — this family confirms the *distinction* matters
   semantically (FAM-01) without requiring this repository to implement it yet.
2. Whether household/co-residence should ever gain real state is flagged, not decided, per the
   batch instruction's own explicit conditional investigation.
