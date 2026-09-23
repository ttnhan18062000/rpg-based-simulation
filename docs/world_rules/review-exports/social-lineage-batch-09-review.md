---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
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

## Follow-up revision summary (2026-09-22)

A targeted semantic cleanup follow-up (`tmp/world-rule-batch-9-followup-ext-ai.md`) was applied
directly to the canonical files, not merely to this export:

1. **SOC-01 reworked.** Removed the requirement that every relationship decompose into five
   independent facts (world fact + A's belief + B's belief + A's attitude + B's attitude).
   Replaced with a two-category distinction — structural relation vs. subjective relational
   state — that keeps the same underlying separation (fact ≠ belief ≠ attitude) without the
   representation-oriented over-specification, and without inventing a third canonical state
   merely for symmetry.
2. **SOC-02 preserved as drafted**, with clarifying examples (siblingship as a reciprocal
   structural relation, ordinary trust as directional by default).
3. **SOC-03 generalized.** Reworded from a negative "no accidental decay" framing to a positive
   "persistence, decay, rupture, and expiration occur only according to declared semantics"
   framing, so the Rule permits per-relation decay/expiration rather than fixing this
   repository's own no-decay pattern as universal law.
4. **SOC-04 reclassified to Inherited** (originally a Domain Rule). Re-examined against the
   admission test and found to add no content beyond combining SOC-03 (declared-semantics
   persistence) and CAUSE-01 (any change needs a real cause) — moved rather than kept for the
   sake of preserving the Rule count, per the follow-up's own explicit instruction.
5. **LIN-01 narrowed.** Reworded from "conveys nothing automatically" (too broad — it obviously
   conveys at least the declared ancestry fact itself) to "conveys only the consequences
   explicitly defined for that lineage relationship."
6. **LIN-02's repository evidence separated more cleanly from its target semantics**, with an
   explicit statement that the confirmed one-generation depth must not be read as this Rule's
   own desired model.
7. **Reputation/recognition reach was re-investigated directly** (the original draft had left
   this explicitly unchecked). Result: **CONFLICTING** — every reputation consumer checked
   reads `public_reputation` as globally available truth with no perception/knowledge-mediated
   gate. Recorded as a new Inherited entry (reusing Batch 06's PERC-01/KNOW-01) in
   `social-relations.md`, with supporting evidence duplicated into `lineage-descent.md`'s own
   LIN-02.
8. **Inherited reputation clarified into two causal steps** (ancestor significance →
   descendant's own social starting condition, vs. another subject learning of that ancestry
   and changing treatment because of it) — confirmed **collapsed** in this repository: the
   second step does not exist as its own information-mediated event; it is substituted by the
   same ungated global read found in #7.
9. **Two focused probes added**, extended onto existing scenarios rather than as new IDs, per
   the follow-up's own preference: SL-S11 (structural relation, opposed attitudes) and SL-S15
   (famous parent, uninformed stranger — which revealed a contradiction).
10. **Six repository findings preserved prominently** per the follow-up's own explicit list,
    now collected together in `lineage-descent.md`'s own Repository Findings section.

Net effect on counts: genuine Domain Rules **7 → 6** (SOC-04 reclassified); Inherited entries
**7 → 9** (SOC-04 reclassified in, plus one wholly new reputation-reach entry); Scope
Boundaries unchanged at **4**; total catalog entries **18 → 19**.

## Canonical files included

- `social-lineage/social-relations.md` (SOC-01–03; SOC-04 now Inherited)
- `social-lineage/family-kinship.md` (FAM-01 — unaffected by this follow-up)
- `social-lineage/lineage-descent.md` (LIN-01–02)
- `scenarios/social-lineage-batch-09.md` (SL-S01–S18, SL-S11/SL-S15 extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 19 total
catalog entries break down as:

- **6 genuine Domain Rules**: SOC-01, SOC-02, SOC-03; FAM-01; LIN-01, LIN-02.
- **9 Inherited/Applied Foundational Rules**: in `social-relations.md` — a relationship
  changes only through a real causal event (CAUSE-01), a relationship affects behavior only
  through the decision layer (Batch 06's AGENCY-01/02), pair-specific relationship ≠
  population-scale reputation (Batch 05's ECOL-01/02, resolving Batch 01's own OWN-03 open
  question), correcting information behind a change ≠ automatic restoration (originally
  SOC-04; CAUSE-01 + SOC-03 + Batch 06's KNOW-02), reputation-reach requires a declared
  information/perception channel (Batch 06's PERC-01/KNOW-01, new this follow-up); in
  `family-kinship.md` — reproduction establishes a new identity (ID-04, Batch 05's LIFE-04),
  derived kinship must remain consistent with authoritative facts (Batch 01's OWN-03); in
  `lineage-descent.md` — identity remains distinct at every generation (ID-04), property
  transfer remains Ownership's own domain (Batch 08's own reclassified entry, itself
  OWN-01/OWN-02).
- **4 Scope/Deferred Boundaries**: concrete relationship-formation content, in
  `social-relations.md`; household as its own simulated system, in `family-kinship.md`;
  political succession, law/custom/wills overriding kinship-based inheritance, in
  `lineage-descent.md`.

**Genuine new-Rule count for this batch: 6.** **Inherited/reused foundation count: 9 entries,
citing CAUSE-01, ID-04, OWN-01, OWN-02, OWN-03, ECOL-01, ECOL-02, and Batch 06's PERC-01,
KNOW-01, KNOW-02, AGENCY-01, AGENCY-02.**

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| SOC-01 | Domain Rule | Structural Relation ≠ Belief ≠ Attitude (two categories, not five facts) | Reworked 2026-09-22 to remove the five-fact decomposition requirement. | Accepted (revised) |
| SOC-02 | Domain Rule | Reciprocity Is Declared, Not a Storage Accident | Siblingship/marriage declared-reciprocal; trust directional by default. | Accepted |
| SOC-03 | Domain Rule | Persistence/Decay/Expiration Occur Only Per Declared Semantics | Generalized 2026-09-22 from a negative "no accidental decay" framing. | Accepted (revised) |
| ~~SOC-04~~ | *(reclassified)* | *(was: Belief Correction ≠ Automatic Relationship Restoration)* | Moved to Inherited — fully covered by SOC-03 + CAUSE-01 + KNOW-02. | Reclassified (see Inherited) |
| FAM-01 | Domain Rule | Family-Structural Facts Are Distinct From Each Other and From Affection/Inheritance | Resolves Batch 05's LIFE-05 deferred boundary. | Accepted (several sub-facts confirmed MISSING) |
| LIN-01 | Domain Rule | Lineage Conveys Only Its Own Declared Consequences | Narrowed 2026-09-22 from "conveys nothing automatically." | Accepted (revised) |
| LIN-02 | Domain Rule | Ancestor Significance → Descendant Treatment Only Via a Real Channel | One-generation reputation echo confirmed; the further "another subject learns of it" step confirmed collapsed into an ungated read, not a genuine second causal stage. | Accepted (confirmed shallow and collapsed) |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| A relationship changes only through a real causal event | CAUSE-01 | `social-relations.md` |
| A relationship affects behavior only through the decision layer | AGENCY-01, AGENCY-02 (Batch 06) | `social-relations.md` |
| Pair-specific relationship ≠ population-scale reputation | ECOL-01, ECOL-02 (Batch 05); resolves OWN-03 (Batch 01) | `social-relations.md` |
| Correcting information behind a change ≠ automatic restoration *(originally SOC-04)* | CAUSE-01, this family's own SOC-03, KNOW-02 (Batch 06) | `social-relations.md` |
| Reputation-reach requires a declared information/perception channel *(new, this follow-up)* | PERC-01, KNOW-01 (Batch 06) | `social-relations.md` |
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
| SL-S05 | False Accusation | false belief → hostility → truth discovered → not auto-restored | Social Relations (inherited, originally SOC-04) | Covered |
| SL-S06 | Separation Does Not Erase Relationship | distance → no interaction → persists | Social Relations | Covered |
| SL-S07 | Death Does Not Erase Social History | mentor dies → history retained | Social Relations (inherited) | Covered |
| SL-S08 | Biological Parent Without Social Parenting | biological relation, no caregiving | Family/Kinship | Partial |
| SL-S09 | Adoptive Parent | social parenthood, biological unchanged | Family/Kinship | Revealed gap |
| SL-S10 | Sibling Derivation | shared parent → derivable sibling relation | Family/Kinship (inherited) | Revealed gap |
| SL-S11 | Kinship Without Affection / Structural Relation, Opposed Attitudes | siblings, hostile relationship; extended — trust vs. hate, opposed | Family/Kinship, Social Relations | Covered |
| SL-S12 | Lineage Across Generations | A→B→C, distinct identities, traceable descent | Lineage/Descent (inherited) | Partial |
| SL-S13 | Inheritance Candidate | descendant qualifies → Ownership receives trigger | Lineage/Descent (inherited) | Partial |
| SL-S14 | Inheritance Blocked | close relative ≠ automatic transfer | Lineage/Descent (inherited) | Covered |
| SL-S15 | Famous Ancestor (flagship) / Famous Parent, Uninformed Stranger | ordinary → significant → descendants' treatment changes; extended — stranger must not react as informed | Lineage/Descent, Social Relations (reputation-reach) | Partial + revealed contradiction (extended clause) |
| SL-S16 | Family Feud | harm → consequences → descendants inherit only via declared mechanism | Lineage/Descent | Covered |
| SL-S17 | Social Relationship Changes Agency | trusted ally → decision score affected | Social Relations (inherited) | Covered |
| SL-S18 | Social State With No Consumer (counter) | relationship value → no reader → no consequence | (repository-evidence probe) | Revealed missing rule enforcement |

## Coverage Summary

**Social Relations**
- structural relation ≠ belief ≠ attitude (two categories) — SL-S01, SL-S11 (extended)
- causal-path requirement for relationship change — SL-S02, SL-S03, SL-S04
- correcting information behind a change ≠ automatic restoration — SL-S05
- persistence independent of interaction/proximity/actionability, per declared semantics —
  SL-S06, SL-S07
- relationship materially affects decisions via the decision layer — SL-S17
- reputation-reach is ungated (new finding, this follow-up) — SL-S15 (extended clause)

**Family/Kinship**
- family-structural fact distinctness — SL-S08, SL-S09, SL-S11
- derived kinship vs. authoritative facts — SL-S10

**Lineage/Descent**
- lineage membership conveys only its own declared consequences — SL-S13, SL-S14, SL-S16
- identity distinct across generations, traceability — SL-S12
- ancestor significance → descendant treatment via a real channel, confirmed shallow and
  confirmed collapsed with the reputation-reach gap — SL-S15

## Deferred Semantics

- Concrete relationship-formation-event content (specific magnitudes, thresholds) is not
  designed here.
- Household as its own simulated system stays deferred, per direct confirmation no causally-
  important consumer exists.
- Political succession (who becomes king, who inherits office, sovereignty legitimacy) stays
  with Politics/Institutions.
- Law/custom/wills overriding kinship- or bond-based inheritance stays deferred.
- Whether reputation reads should ever gain a real perception/knowledge-mediated gate (the
  confirmed CONFLICTING finding, this follow-up) is not designed here — only confirmed as a
  real gap.

## Cross-domain findings

- Social Relations ↔ State Ownership (Batch 01): the reputation-representations Inherited
  entry directly resolves OWN-03's own carried-forward open question (reputation scalar vs.
  reputation labels) — confirmed as two legitimately separate, real, independently-owned
  fields (`SocialComponent.public_reputation`, `PublicReputationProfile.labels`), neither a
  duplicate of the other, though `.labels` is itself confirmed write-only.
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
- Social Relations / Lineage-Descent ↔ Perception/Knowledge (Batch 06): **new this
  follow-up.** Reputation-reach was re-investigated directly and found CONFLICTING with
  Batch 06's own PERC-01/KNOW-01 — every checked consumer (`SocialAppraisalSystem.
  appraise_contract()`, `ShopService`'s discount path) reads another subject's
  `public_reputation` as instantly, globally available truth, never through a
  perception/knowledge-mediated channel. This directly collapses the two causal steps LIN-02's
  own boundary requires kept distinct (ancestor significance → descendant's own starting
  condition, vs. another subject learning of that ancestry and reacting because of it).

**Explicit call-out — genuine Domain Rule count:** **6** (was 7 before this follow-up
reclassified SOC-04).

**Explicit call-out — whether subjective attitudes require any separate world-owned
relationship fact:** **No.** Per revised SOC-01: a directional subjective attitude (e.g. "A
trusts B") is itself simply A's own subject-owned state; it does not require a separate,
mirrored, world-owned relationship fact to exist alongside it. `SocialBond`'s own directional
records confirm this by construction — a structural relation (sibling, marriage) may exist
independently of attitude, but ordinary attitudes do not themselves require a third,
world-owned fact for symmetry.

**Explicit call-out — whether relationships may be asymmetric:** **Yes, confirmed by
construction.** `A.social.bonds[B]` and `B.social.bonds[A]` are independent records; nothing
forces them to agree. Extended and reconfirmed via SL-S11's own opposed-attitudes probe
(trust one direction, hate the other, alongside one shared structural fact).

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

**Explicit call-out — whether reputation consumers respect subject-local information
boundaries:** **No — confirmed CONFLICTING, re-investigated directly this follow-up.**
`SocialAppraisalSystem.appraise_contract()` reads a target entity's `public_reputation`
directly for an evaluating entity with no prior bond (a stranger), with no
`PerceptionGate.can_perceive()` call and no knowledge_model lookup of any kind.
`ShopService.buy_item()`/`src/engine/shop.py`'s price-hardening path read the *customer's* own
`public_reputation` the same way. Reputation exists as real world/social state, but nothing
gates another subject's own use of it behind a declared information/perception channel — the
same class of finding as Batch 06's own CONFLICTING `ResourceOpportunityProvider` finding.

**Explicit call-out — whether inherited reputation is social state, information, or both
through separate causal stages:** **Both in principle, but confirmed collapsed into one stage
in this repository, not kept separate.** LIN-02's own birth-seed mechanism is real world/social
*state* (a direct data write from parent to child at birth) — that stage is genuinely real and
distinct from information/perception. But the *second* stage this Rule's own boundary
requires — another specific subject learning of that ancestry/significance and reacting
because of it — does not exist as its own information-mediated event; it is substituted by the
same ungated `public_reputation` read found in the reputation-reach finding above. The two
causal stages are conceptually distinct (and this Rule's own text keeps them distinct) but
this repository's own implementation only realizes the first as a genuine causal stage; the
second is not a stage at all, only an unconditional global read.

**Explicit call-out — which social/family state is causally inert:** `debt_history`,
`fear_history`, `salience_history`, `place_attachment` (zero consumers anywhere);
`PublicReputationProfile.labels` (write-only, zero readers, confirmed this follow-up);
`heroism_score`/`notoriety_score` (presenter-only, never a behavioral consumer);
`combat_loss_counts` (a real reader gated behind the INERT/OFF `combat_engagement` domain).

**Explicit call-out — whether an ordinary non-HERO individual can become socially significant
by name:** **Sharpened, not newly resolved — the same partial answer Batch 07 already found,
now confirmed unchanged and further clarified as ungated rather than information-mediated.** A
parent's own reputation does seed a child's own starting standing (LIN-02, real and live) — a
genuine, if shallow, individual-history → starting-condition chain. But `LegendFact`/
`FameState`'s own individual-significance tracking remains role-gated to HERO entities only
(Batch 07's own confirmed finding, unchanged by this batch's own investigation), and this
follow-up's own reputation-reach investigation confirms that whatever "recognition" does occur
for a non-HERO individual is never mediated by another subject actually learning that
individual's own history — it is always a direct, ungated read of a shared numeric value.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction Batch 06/07/08 established.
**These are repository/implementation facts, not World Rule decisions.**

**CONFLICTING (1 finding, new this follow-up):**
1. Reputation-reach is ungated. Every checked reputation consumer
   (`SocialAppraisalSystem.appraise_contract()`, `ShopService.buy_item()`, `src/engine/
   shop.py`'s price-hardening path) reads another subject's `public_reputation` (and, in
   `appraise_contract()`, a clan's `clan_reputation`) directly, with no
   perception/knowledge-mediated channel — a total stranger reacts identically to someone with
   genuine prior history with the target. This directly collapses the two causal stages
   LIN-02's own boundary requires kept distinct. Superseding the original draft's own
   "not independently investigated" note.

**INERT/OFF (1 finding, reconfirmed):**
2. `combat_loss_counts` has a real reader gated behind Batch 07's own confirmed-OFF
   `combat_engagement` domain.

**MISSING (6 findings):**
3. No social parenthood/adoption tracking exists.
4. No household/co-residence tracking exists.
5. No derived-kinship computation (sibling, grandparent, lineage-traversal) exists anywhere.
6. No reputation/significance propagation beyond one generation exists.
7. `debt_history`, `fear_history`, `salience_history`, `place_attachment` have zero
   consumers anywhere outside their own write path.
8. `PublicReputationProfile.labels` (`entity.cognition.relationships.public_reputation.
   labels`) is written by `ReputationUpdateService.process_witnessed_event()` but has zero
   readers anywhere — confirmed this follow-up, distinct from the scalar's own CONFLICTING
   finding above.

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
9. This repository's own default heir-eligibility mechanism (`_select_default_heir()`) is a
   social-bond mechanism, not a kinship mechanism — it never reads `parent_a/b_entity_id` at
   all. Not a violation of any Rule (kinship correctly does not automatically grant
   eligibility, per LIN-01/the Inherited property-transfer entry) — but a real, notable fact a
   future reader should know before assuming "default heir" means "nearest relative." The
   misleading name and the semantically-correct behavior are separate concerns, per this
   follow-up's own explicit instruction not to treat the one as evidence against the other.

Key evidence, all confirmed by direct code/doc inspection: `src/core/models/social.py`,
`src/core/state.py`, `src/systems/social_systems/{relationships,appraisal,party_composition,
memory,clan_lifecycle}.py`, `src/systems/lifecycle_systems/lifecycle.py`,
`src/systems/economy_systems/reputation_discount.py`, `src/town/shop.py`,
`src/engine/shop.py`, `src/domains/cooperation/evaluators.py`,
`src/domains/commitment/reputation.py`, `src/core/cognition.py`, `src/engine/quests.py`,
`src/core/builder.py`, `src/world/reproduction_humanoid.py`,
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
- Whether the four confirmed-unread `SocialComponent` fields, plus
  `PublicReputationProfile.labels`, should be wired to a real consumer or removed.
- Whether reputation reads should gain a real perception/knowledge-mediated gate before any
  further decision system is wired to consult them — the new CONFLICTING finding this
  follow-up confirms, not decides.

## Candidate disposition

Seven Domain Rules were originally drafted across three families (4 Social Relations, 1
Family/Kinship, 2 Lineage/Descent); this follow-up reclassified one (SOC-04) to Inherited after
re-testing it against the admission discipline, leaving **6 accepted Domain Rules, 1
reclassified, 0 rejected, 0 split, 0 merged.** No target rule count was set in advance. Nine
entries are now Inherited/Applied Foundational Rules (7 original + 1 reclassified + 1 new
reputation-reach entry) and four remain Scope/Deferred Boundaries — none required a new Rule
ID beyond the original seven.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/social-lineage-batch-09-report.md` (local review report, not part of this catalog).

---

> **BATCH 09 (SOCIAL RELATIONS / FAMILY / LINEAGE) — PASS, READY TO FREEZE.**

All required artifacts exist and are current: three rule-family files (6 genuine Domain
Rules; 19 total catalog entries), one scenario file (18 scenarios, two extended in place per
this follow-up's own two focused probes, covering all eighteen original required seed probes
plus both follow-up probes), this review export with all required sections plus every
explicitly-required call-out, and a local disposition report. No contradiction was found
against any prior batch's own Rules. This follow-up's own targeted semantic cleanup resolved
every one of its eleven numbered items: SOC-01 reworked to remove over-specified structure;
SOC-02 preserved; SOC-03 generalized to a positive declared-semantics framing; SOC-04
reclassified after failing the admission test on stricter re-examination; LIN-01 narrowed;
LIN-02's evidence cleanly separated from its target semantics with an explicit anti-endorsement
note; reputation/recognition reach re-investigated and confirmed CONFLICTING; inherited
reputation's two causal steps clarified and confirmed collapsed; two focused probes added by
extension rather than new IDs; six repository findings preserved prominently; and this export
fully regenerated. The target semantics remain coherent throughout this revision — no
reclassification or reword introduced a gap between what a Rule's own quoted text claims and
what its evidence supports.

Batch 10 (Organizations / Institutions / Politics / Law) has no instruction file yet in
`tmp/` at the time of this freeze — unlike the transition from Batch 08 to Batch 09, where
`tmp/world-rule-batch-9-ext-ai.md` already existed when Batch 08's own follow-up said to
proceed. Per this Catalog's own discipline against guessing at content the user has not yet
supplied, Batch 10 does not begin until its own instruction file is provided.
