---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 09 (Social Relations / Family / Lineage)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The sixth domain-facing (Milestone B) batch — how interactions between individuals become
persistent social relationships, family structure, and lineage history that later affect what
those individuals and their descendants can experience. Three rule families: Social
Relations, Family/Kinship, Lineage/Descent. Files live under `social-lineage/`, per the batch
instruction's own directory suggestion. Built directly with the strict Rule-admission
discipline Batches 07/08's own follow-up reviews established, applied from the first draft.

## Canonical files included

- `social-lineage/social-relations.md` (SOC-01–04)
- `social-lineage/family-kinship.md` (FAM-01)
- `social-lineage/lineage-descent.md` (LIN-01–02)
- `scenarios/social-lineage-batch-09.md` (SL-S01–S18)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 18 total
catalog entries break down as:

- **7 genuine Domain Rules**: SOC-01, SOC-02, SOC-03, SOC-04; FAM-01; LIN-01, LIN-02.
- **7 Inherited/Applied Foundational Rules**: in `social-relations.md` — a relationship
  changes only through a real causal event (CAUSE-01), a relationship affects behavior only
  through the decision layer (Batch 06's AGENCY-01/02), pair-specific relationship ≠
  population-scale reputation (Batch 05's ECOL-01/02, resolving Batch 01's own OWN-03 open
  question); in `family-kinship.md` — reproduction establishes a new identity (ID-04,
  Batch 05's LIFE-04), derived kinship must remain consistent with authoritative facts
  (OWN-04's sibling — Batch 01's OWN-03); in `lineage-descent.md` — identity remains distinct
  at every generation (ID-04), property transfer remains Ownership's own domain (Batch 08's
  own reclassified entry, itself OWN-01/OWN-02).
- **4 Scope/Deferred Boundaries**: concrete relationship-formation content, in
  `social-relations.md`; household as its own simulated system, in `family-kinship.md`;
  political succession, law/custom/wills overriding kinship-based inheritance, in
  `lineage-descent.md`.

**Genuine new-Rule count for this batch: 7.** **Inherited/reused foundation count: 7 entries,
citing CAUSE-01, ID-04, OWN-01, OWN-02, OWN-03, ECOL-01, ECOL-02, and Batch 06's AGENCY-01/
AGENCY-02.**

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| SOC-01 | Domain Rule | Relationship ≠ Either Party's Belief or Attitude | Up to five independent facts for one pair. | Accepted (PARTIAL — only the attitude layer is separately tracked) |
| SOC-02 | Domain Rule | Reciprocity Is Declared, Not a Storage Accident | Marriage is declared-reciprocal; trust is directional by default. | Accepted |
| SOC-03 | Domain Rule | Persistence ≠ Interaction/Proximity/Actionability | No accidental decay; historical ≠ currently-actionable. | Accepted |
| SOC-04 | Domain Rule | Belief Correction ≠ Automatic Relationship Restoration | The relationship has its own lived history. | Accepted (confirmed real gap) |
| FAM-01 | Domain Rule | Family-Structural Facts Are Distinct From Each Other and From Affection/Inheritance | Resolves Batch 05's LIFE-05 deferred boundary. | Accepted (several sub-facts confirmed MISSING) |
| LIN-01 | Domain Rule | Lineage Membership Conveys Nothing Automatically | Each inheritance needs its own declared mechanism. | Accepted |
| LIN-02 | Domain Rule | Ancestor Significance → Descendant Treatment Only Via a Real Channel | One-generation reputation echo confirmed; deeper propagation confirmed absent. | Accepted (confirmed shallow) |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| A relationship changes only through a real causal event | CAUSE-01 | `social-relations.md` |
| A relationship affects behavior only through the decision layer | AGENCY-01, AGENCY-02 (Batch 06) | `social-relations.md` |
| Pair-specific relationship ≠ population-scale reputation | ECOL-01, ECOL-02 (Batch 05); resolves OWN-03 (Batch 01) | `social-relations.md` |
| Reproduction establishes a new, distinct identity | ID-04, LIFE-04 (Batch 05) | `family-kinship.md` |
| Derived kinship must remain consistent with authoritative facts | OWN-03 (Batch 01) | `family-kinship.md` |
| Identity remains distinct at every generation | ID-04 | `lineage-descent.md` |
| Property transfer remains Ownership's own domain | OWN-01, OWN-02 (Batch 01); Batch 08's own reclassified entry | `lineage-descent.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| SL-S01 | One-Sided Trust | A trusts B, B distrusts A | Social Relations | Covered |
| SL-S02 | Friendship Through Shared Experience | survive together → declared consequence → improves | Social Relations (inherited) | Covered |
| SL-S03 | Interaction With No Relationship Change (counter) | trade once → no declared consequence → unchanged | Social Relations (inherited) | Covered |
| SL-S04 | Betrayal | trust → betrayal → trust changes | Social Relations (inherited) | Covered |
| SL-S05 | False Accusation | false belief → hostility → truth discovered → not auto-restored | Social Relations | Covered |
| SL-S06 | Separation Does Not Erase Relationship | distance → no interaction → persists | Social Relations | Covered |
| SL-S07 | Death Does Not Erase Social History | mentor dies → history retained | Social Relations (inherited) | Covered |
| SL-S08 | Biological Parent Without Social Parenting | biological relation, no caregiving | Family/Kinship | Partial |
| SL-S09 | Adoptive Parent | social parenthood, biological unchanged | Family/Kinship | Revealed gap |
| SL-S10 | Sibling Derivation | shared parent → derivable sibling relation | Family/Kinship (inherited) | Revealed gap |
| SL-S11 | Kinship Without Affection | siblings, hostile relationship | Family/Kinship | Covered |
| SL-S12 | Lineage Across Generations | A→B→C, distinct identities, traceable descent | Lineage/Descent (inherited) | Partial |
| SL-S13 | Inheritance Candidate | descendant qualifies → Ownership receives trigger | Lineage/Descent (inherited) | Partial |
| SL-S14 | Inheritance Blocked | close relative ≠ automatic transfer | Lineage/Descent (inherited) | Covered |
| SL-S15 | Famous Ancestor (flagship) | ordinary → significant → descendants' treatment changes | Lineage/Descent | Partial |
| SL-S16 | Family Feud | harm → consequences → descendants inherit only via declared mechanism | Lineage/Descent | Covered |
| SL-S17 | Social Relationship Changes Agency | trusted ally → decision score affected | Social Relations (inherited) | Covered |
| SL-S18 | Social State With No Consumer (counter) | relationship value → no reader → no consequence | (repository-evidence probe) | Revealed missing rule enforcement |

## Coverage Summary

**Social Relations**
- world fact ≠ belief ≠ attitude, directional storage — SL-S01
- causal-path requirement for relationship change — SL-S02, SL-S03, SL-S04
- belief-correction ≠ relationship restoration — SL-S05
- persistence independent of interaction/proximity/actionability — SL-S06, SL-S07
- relationship materially affects decisions via the decision layer — SL-S17

**Family/Kinship**
- family-structural fact distinctness — SL-S08, SL-S09, SL-S11
- derived kinship vs. authoritative facts — SL-S10

**Lineage/Descent**
- lineage membership conveys nothing automatically — SL-S13, SL-S14, SL-S16
- identity distinct across generations, traceability — SL-S12
- ancestor significance → descendant treatment via a real channel — SL-S15

## Deferred Semantics

- Concrete relationship-formation-event content (specific magnitudes, thresholds) is not
  designed here.
- Household as its own simulated system stays deferred, per direct confirmation no causally-
  important consumer exists.
- Political succession (who becomes king, who inherits office, sovereignty legitimacy) stays
  with Politics/Institutions.
- Law/custom/wills overriding kinship- or bond-based inheritance stays deferred.

## Cross-domain findings

- Social Relations ↔ State Ownership (Batch 01): the reputation Inherited entry directly
  resolves OWN-03's own carried-forward open question (reputation scalar vs. reputation
  labels) — confirmed as two legitimately separate, real, independently-owned fields
  (`SocialComponent.public_reputation`, `PublicReputationProfile.labels`), neither a
  duplicate of the other.
- Family/Kinship ↔ Life/Body (Batch 05): FAM-01 directly answers LIFE-05's own deferred
  boundary ("what provenance means socially is Family/Lineage's own question") — the first
  time in this Catalog a Scope Boundary named in one batch is actually resolved by the batch
  it was deferred to, by name.
- Lineage/Descent ↔ Capability/Progression (Batch 07): LIN-02's own confirmed-shallow finding
  (reputation echoes exactly one generation) is the direct continuation of PROG-06/CP-S15's
  own finding (progression's world-reaction channel is real but narrow) — the same repository
  pattern, checked twice from adjacent angles a batch apart.
- Lineage/Descent ↔ Objects/Ownership (Batch 08): the property-transfer Inherited entry
  surfaces a genuinely new, significant finding even while reusing an old Rule — this
  repository's own default heir-eligibility mechanism is bond-based, not kinship-based,
  meaning the candidate Batch 08's own confirmed-broken resolver would have (if it worked)
  transferred property to is not guaranteed to be an actual relative.

**Explicit call-out — genuine Domain Rule count:** **7.**

**Explicit call-out — relationship vs. belief/attitude semantics:** Confirmed distinct by
construction (`SocialBond` is explicitly directional) for the attitude layer; this repository
does not additionally track a third, world-owned relationship fact separate from both
parties' own bond records — "the relationship" *is* the pair of directional bonds here, a
PARTIAL rather than full five-way realization of SOC-01's own permission.

**Explicit call-out — whether relationships may be asymmetric:** **Yes, confirmed by
construction.** `A.social.bonds[B]` and `B.social.bonds[A]` are independent records; nothing
forces them to agree.

**Explicit call-out — whether social state materially changes decisions:** **Yes, confirmed,
richly.** `cooperation/evaluators.py`, `party_composition.py`, `appraisal.py`, and
`nemesis_ids`'s several real consumers all read relationship state as one weighted input
among others.

**Explicit call-out — whether biological/social parenthood are distinguished:** **Distinct in
principle (FAM-01); social parenthood has no positive mechanism of its own to distinguish
against — confirmed MISSING, not merely undesigned.**

**Explicit call-out — whether lineage traversal is real:** **No.** `parent_a/b_entity_id`
stores exactly one hop; no sibling/grandparent/ancestor-traversal function exists anywhere.

**Explicit call-out — whether kinship improperly implies inheritance:** **No — confirmed
correctly absent.** `_select_default_heir()` never reads kinship fields at all; kinship alone
never transfers property in this repository.

**Explicit call-out — whether inheritance candidate selection integrates cleanly with
Batch 08:** **Structurally cleanly (the eligibility/ownership boundary holds exactly as
declared) — but with an important substantive caveat.** The candidate handed to Batch 08's
own (confirmed broken) property-transfer mechanism is a social-bond winner, not a
kinship-determined heir — the two batches' own mechanisms connect correctly at the boundary,
but the boundary crossing carries a candidate this batch's own investigation shows is not
what "heir" would ordinarily suggest.

**Explicit call-out — whether dead entities retain social/historical consequence:** **Yes,
confirmed**, reusing Batch 01/05's own `_transfer_inherited_feud()`/`_seed_dying_wish()`
evidence directly.

**Explicit call-out — whether reputation/recognition obeys information reach:** Not
independently re-investigated this batch beyond what Batch 06 already established
(`PERC-01`/`KNOW-02`) — `public_reputation`'s own transgenerational seed (LIN-02) is a direct
data-write at birth, not an information-propagation event, so Batch 06's own reach/perception
boundary does not directly apply to it; this is noted as an open question rather than a
confirmed finding.

**Explicit call-out — which social/family state is causally inert:** `debt_history`,
`fear_history`, `salience_history`, `place_attachment` (zero consumers anywhere);
`heroism_score`/`notoriety_score` (presenter-only, never a behavioral consumer);
`combat_loss_counts` (a real reader gated behind the INERT/OFF `combat_engagement` domain).

**Explicit call-out — whether an ordinary non-HERO individual can become socially significant
by name:** **Sharpened, not newly resolved — the same partial answer Batch 07 already found,
now confirmed unchanged one generation later.** A parent's own reputation does seed a child's
own starting standing (LIN-02, real and live) — a genuine, if shallow, individual-history →
named-recognition → limited world-reaction chain. But `LegendFact`/`FameState`'s own
individual-significance tracking remains role-gated to HERO entities only (Batch 07's own
confirmed finding, unchanged by this batch's own investigation) — an ordinary non-HERO
individual's own growing reputation is real and does echo to a child, but is not "recognition
by name" in the sense of other entities identifying and reacting to that specific individual's
own history, only a numeric seed value.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07/08 established.
**These are repository/implementation facts, not World Rule decisions.**

**No new CONFLICTING finding was identified in this batch's own new territory.** Batch 08's
own CONFLICTING finding (the heirloom-transfer resolver gap) is cross-referenced, not
re-classified, since this batch's own investigation of the *eligibility* side found it clean.

**INERT/OFF (1 finding, reconfirmed):**
1. `combat_loss_counts` has a real reader gated behind Batch 07's own confirmed-OFF
   `combat_engagement` domain.

**MISSING (5 findings):**
2. No social parenthood/adoption tracking exists.
3. No household/co-residence tracking exists.
4. No derived-kinship computation (sibling, grandparent, lineage-traversal) exists anywhere.
5. No reputation/significance propagation beyond one generation exists.
6. `debt_history`, `fear_history`, `salience_history`, `place_attachment` have zero
   consumers anywhere outside their own write path.

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
7. This repository's own default heir-eligibility mechanism (`_select_default_heir()`) is a
   social-bond mechanism, not a kinship mechanism — it never reads `parent_a/b_entity_id` at
   all. Not a violation of any Rule (kinship correctly does not automatically grant
   eligibility, per LIN-01/the Inherited property-transfer entry) — but a real, notable fact a
   future reader should know before assuming "default heir" means "nearest relative."

Key evidence, all confirmed by direct code/doc inspection: `src/core/models/social.py`,
`src/core/state.py`, `src/systems/social_systems/{relationships,appraisal,party_composition,
memory}.py`, `src/systems/lifecycle_systems/lifecycle.py`, `src/domains/cooperation/
evaluators.py`, `src/domains/commitment/reputation.py`, `src/core/cognition.py`,
`src/engine/quests.py`, `src/core/builder.py`, `src/world/reproduction_humanoid.py`,
`src/systems/world_systems/generator.py`, `docs/mechanics/04_strategic_cognition.md` §8
(Marriage Proposal Law), `TCK-20260824-DEFAULT-HEIR-ASSIGNMENT`,
`TCK-20260904-INHERITED-REPUTATION-SEED`.

## Owner-attention decisions

- Whether the three parallel hostility/trust tracking structures on `SocialComponent` should
  be consolidated.
- Whether a real kinship-aware heir-priority option should be added alongside the current
  bond-based default.
- Whether social parenthood/adoption and household should ever gain real tracked state.
- Whether reputation/significance propagation should ever extend beyond one generation.
- Whether the four confirmed-unread `SocialComponent` fields should be wired to a real
  consumer or removed.

## Candidate disposition

Seven Domain Rules were drafted across three families (4 Social Relations, 1 Family/Kinship,
2 Lineage/Descent) — **all 7 accepted, 0 rejected, 0 split, 0 merged.** No target rule count
was set in advance. Seven further entries were identified as Inherited/Applied Foundational
Rules and four as Scope/Deferred Boundaries — none required a new Rule ID.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/social-lineage-batch-09-report.md` (local review report, not part of this catalog).

---

> **BATCH 09 (SOCIAL RELATIONS / FAMILY / LINEAGE) READY FOR HIGH-LEVEL EXTERNAL REVIEW.**

All required artifacts exist: three rule-family files (7 genuine Domain Rules; 18 total
catalog entries), one scenario file (18 scenarios covering all eighteen required seed probes),
this review export with all required sections plus every explicitly-required call-out, and a
local disposition report. No contradiction was found against any prior batch. This batch's own
genuinely new material is concentrated in one clean resolution of a long-carried-forward open
question (OWN-03's reputation-scalar-vs-labels naming collision), one clean resolution of a
deferred Scope Boundary (LIFE-05's family-meaning question), and one significant, notable
finding about how this repository's own default heir mechanism actually works (bond-based, not
kinship-based) — rather than a uniform spread of small findings. All fourteen of the batch
instruction's own stop-condition checklist items are satisfied: relationship state and subject
belief are distinct; asymmetric social relations are permitted and confirmed real; relationship
change requires a real causal path; social state has meaningful downstream consumers for most
tracked fields, with several confirmed inert; biological and social parenthood are not
collapsed, though social parenthood has no positive mechanism; kinship/lineage preserve
distinct identities across generations; kinship does not automatically imply affection/
loyalty; kinship does not automatically transfer property or authority, confirmed cleanly;
inheritance integrates cleanly with Batch 08's ownership semantics at the structural boundary,
with a substantive caveat about the candidate's own nature; death preserves relevant
relationship/history consequences; false/stale information can create real social
consequences that do not auto-correct; lineage can create later opportunities/constraints
through a real, if shallow, path; ordinary-individual social significance has been probed and
found partially realized; inert or omniscient social mechanisms are identified; genuine Rules
remain separated from evidence/findings.

Do not begin Batch 10 (Organizations / Institutions / Politics / Law) until this batch
receives high-level review.
