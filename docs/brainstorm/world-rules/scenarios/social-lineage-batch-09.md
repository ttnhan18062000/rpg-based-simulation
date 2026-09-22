---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Scenario Bank: Social Relations / Family / Lineage (Batch 09)

**Purpose/scope.** Eighteen scenarios used to pressure-test the Social Relations, Family/
Kinship, and Lineage/Descent rule families in `social-lineage/social-relations.md`,
`family-kinship.md`, and `lineage-descent.md`, per `tmp/world-rule-batch-9-ext-ai.md`. Covers
all eighteen required seed probes from that instruction's §20.

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## SL-S01 — One-sided trust

A trusts B; B distrusts A.

- **Rules invoked:** SOC-01, SOC-02.
- **Result: covered.** `SocialBond` is a first-class *directed* record — `A.social.bonds[B]`
  and `B.social.bonds[A]` are two independent entries, neither forced to agree. Asymmetric
  social state is confirmed representable by construction, not merely permitted in theory.

## SL-S02 — Friendship through shared experience

A and B survive a dangerous event together; a declared social interpretation follows;
persistent relationship improves.

- **Rules invoked:** Inherited (CAUSE-01).
- **Result: covered.** `RelationshipService.process_update()` only ever moves `sentiment`/
  `familiarity` through an explicit `SocialUpdate` delta a real event producer supplies —
  shared survival, if a real producer emits the matching delta, is exactly this pattern; no
  code path mutates relationship state without one.

## SL-S03 — Interaction with no relationship change (counter)

A trades with B once; no declared socially meaningful consequence; relationship unchanged.

- **Rules invoked:** Inherited (CAUSE-01).
- **Result: covered.** An ordinary trade transaction (Batch 08's own Market Law) does not
  itself construct a `SocialUpdate` with a sentiment/familiarity delta — checked directly, a
  bare trade has no relationship-mutating side effect unless a separate, real social event
  producer also fires. Automatic social mutation from mere interaction is confirmed absent.

## SL-S04 — Betrayal

A trusts B; B betrays A; A learns/experiences betrayal; trust relationship changes.

- **Rules invoked:** Inherited (CAUSE-01).
- **Result: covered.** `BetrayalRecord` (`contract_id`, `betrayer_id`, `victim_id`, `severity`,
  `tick`) is a real, typed causal record appended to `SocialComponent.betrayal_records` —
  betrayal is not a bare sentiment edit but a structured event with its own provenance,
  exactly matching the causal-path requirement.

## SL-S05 — False accusation

False information causes A to believe B harmed them; hostility develops; later the truth is
discovered; hostility does not automatically disappear.

- **Rules invoked:** SOC-04.
- **Result: covered — a confirmed, honest gap in the *repair* direction, not a violation.**
  The hostility-forming half is covered by the same causal-path mechanism as SL-S04. The
  repair half: checked directly, no code path restores `sentiment`/`role` when a
  `BeliefContradictionService.detect()` event later confirms the accusation was false — the
  relationship and belief layers update independently, confirming SOC-04's own claim that
  correction requires its own separate, declared reconciliation process this repository does
  not currently implement.

## SL-S06 — Separation does not erase relationship

Friends move to different regions; no interaction for a time; relationship may persist.

- **Rules invoked:** SOC-03.
- **Result: covered.** `RelationshipService.process_update()` has no passive decay term
  anywhere on `bonds`/`sentiment`/`familiarity` — confirmed directly, and independently
  reconfirmed by `TCK-20260904-INHERITED-REPUTATION-SEED`'s own investigation. A relationship
  is stable indefinitely absent a declared mechanism that changes it, regardless of distance.

## SL-S07 — Death does not erase social history

A mentor dies; the student retains mentorship history; later choices/capability may still
reflect it.

- **Rules invoked:** SOC-03, Inherited (HP-01, LIFE-03, Batch 05).
- **Result: covered — reuses Batch 01/05's own evidence directly.**
  `LifecycleSystem._transfer_inherited_feud()`/`_seed_dying_wish()` keep a deceased subject's
  relationships causally live and referenceable; the historical relationship persists while
  the deceased party obviously cannot act on it further — exactly SOC-03's own
  historical-vs-actionable distinction.

## SL-S08 — Biological parent without social parenting

A parent produces a child; a biological relation exists; no caregiving/social-parent relation
exists.

- **Rules invoked:** FAM-01.
- **Result: partially covered.** `parent_a_entity_id`/`parent_b_entity_id` record the
  biological fact cleanly, with nothing automatically implying caregiving. But this is
  covered only by *absence* — checked directly, no social-parent/caregiving field exists at
  all for this scenario to positively confirm against; the distinction FAM-01 requires is
  representable in principle (biological ≠ social parenthood are named as separate facts) but
  this repository has no positive mechanism to represent the social-parenting side either
  way.

## SL-S09 — Adoptive parent

An adult adopts a child; social parenthood is established; biological descent is unchanged.

- **Rules invoked:** FAM-01.
- **Result: revealed missing rule.** No adoption mechanism or `social_parent_id`-equivalent
  field exists anywhere in this repository — confirmed MISSING directly. FAM-01's own
  permission (social parenthood is a legitimate, distinct family fact) is not realized by any
  mechanism today.

## SL-S10 — Sibling derivation

A and B share a declared parent; a sibling relation is derivable.

- **Rules invoked:** Inherited (OWN-03).
- **Result: revealed missing rule.** No code anywhere computes a sibling (or any other
  derived kinship) relation from shared `parent_a/b_entity_id` values — confirmed MISSING
  directly. The Inherited OWN-03 boundary this scenario probes ("derived conclusions must
  remain consistent with authoritative facts") has nothing to check against, since no
  derivation exists at all; the probe's own premise (deriving sibling status) is not
  currently exercised.

## SL-S11 — Kinship without affection

Siblings have a hostile relationship.

- **Rules invoked:** FAM-01.
- **Result: covered.** Nothing in this repository derives `sentiment`/`bonds` from
  `parent_a/b_entity_id` — a shared parent creates zero automatic effect on the siblings' own
  `SocialBond` records toward each other. Family relation is confirmed not to dictate
  attitude, consistent with FAM-01's own claim, though again confirmed by the absence of any
  coupling rather than a positive "hostile siblings" mechanism.

## SL-S12 — Lineage across generations

A has child B; B has child C; C can trace descent from A. Identity remains distinct at every
generation.

- **Rules invoked:** LIN-01, Inherited (ID-04).
- **Result: partially covered.** Each birth (`V2EntityBuilder.birth_record()`) establishes a
  genuinely new identity with real `parent_a/b_entity_id` provenance — the identity half is
  fully confirmed for every generation. The *traceability* half — can C actually be traced
  back to A programmatically — is confirmed MISSING: `parent_a_entity_id` only stores the
  immediate parent, and no traversal function exists to walk the chain further than one hop.
  The data exists to support tracing in principle (each hop is real and stored); no mechanism
  performs the trace.

## SL-S13 — Inheritance candidate

An owner dies; a descendant qualifies as heir under a declared rule; Material/Ownership
receives the candidate/trigger; property transfer occurs elsewhere.

- **Rules invoked:** Inherited (the property-transfer-remains-Ownership's-own-domain entry).
- **Result: partially covered — a real, clean boundary, with an important qualifier.**
  `LifecycleSystem._select_default_heir()` really does resolve a candidate and hand it to
  Material/Ownership's own `ResourceTransferIntent` construction, respecting the "Family
  determines eligibility, Family doesn't own property state" boundary exactly. The qualifier:
  the "descendant" framing in this probe does not hold as stated — the resolved candidate is
  whoever has the strongest social bond, which may or may not be an actual descendant at all,
  since kinship is never consulted.

## SL-S14 — Inheritance blocked

A close relative exists; a governing rule names another heir, or no inheritance path exists;
kinship alone does not transfer property.

- **Rules invoked:** Inherited (the property-transfer-remains-Ownership's-own-domain entry).
- **Result: covered, cleanly.** Since `_select_default_heir()` never reads
  `parent_a/b_entity_id` at all, a close biological relative with a weak or absent social bond
  is confirmed to lose out to an unrelated party with a strong bond, or to receive no
  candidacy at all if no bond exists — kinship alone is confirmed never sufficient to
  transfer property in this repository, exactly as this Rule requires.

## SL-S15 — Famous ancestor (flagship)

An ordinary person becomes historically significant; descendants later encounter changed
social opportunities/reactions. No automatic capability/stat bonuses.

- **Rules invoked:** LIN-02.
- **Result: partially covered — real for one generation, confirmed absent beyond it.**
  `V2EntityBuilder.birth_record()`'s reputation-seed mechanism is a real, live, declared
  channel from a parent's own `public_reputation` to a newborn child's own starting value — no
  capability/stat bonus is granted, consistent with the probe's own explicit guard. Checked
  directly: no mechanism extends this, or any comparable channel, beyond the immediate
  parent — a grandchild's or great-grandchild's own social treatment is never affected by a
  distant ancestor's own historical significance.

## SL-S16 — Family feud

Harm between individuals produces relationship consequences; descendants later inherit
knowledge/obligation/hostility only through declared mechanisms.

- **Rules invoked:** LIN-01.
- **Result: covered.** `LifecycleSystem._transfer_inherited_feud()` is exactly this: a real,
  specific, declared mechanism that transfers a feud to a resolved heir at the moment of
  death — never an automatic effect of shared lineage. Automatic inherited hatred (feud
  reaching every relative regardless of any declared transfer) is confirmed not to occur.

## SL-S17 — Social relationship changes agency

An entity receives two otherwise similar opportunities; one involves a trusted ally;
relationship affects the decision score.

- **Rules invoked:** Inherited (AGENCY-01/02, Batch 06).
- **Result: covered.** `src/systems/social_systems/appraisal.py`/`party_composition.py`/
  `src/domains/cooperation/evaluators.py` all read a candidate's own `bond.sentiment`/
  `familiarity_history` as one real input among several to a decision — relationship state is
  confirmed to influence, not bypass, the agent's own decision-making layer.

## SL-S18 — Social state with no consumer (counter)

A relationship value exists; no system reads it; no world consequence follows.

- **Rules invoked:** none directly — a repository-evidence probe, cross-referenced from
  `social-relations.md`'s own Repository Findings.
- **Result: revealed missing rule enforcement — several confirmed real instances, distinct in
  kind.** `debt_history`, `fear_history`, `salience_history`, and `place_attachment` are all
  real, written `SocialComponent` fields (`RelationshipService.process_update()` genuinely
  maintains all four) with **zero consumers anywhere outside their own write path** —
  confirmed directly. `heroism_score`/`notoriety_score` are read only by
  `src/api/presenters/state_presenter.py` — exposed for observability, never for any actual
  decision or behavior, a subtler kind of inertness (visible but not systemically consumed).
  `combat_loss_counts` has a real reader (`src/domains/combat_engagement/service.py`) but that
  entire domain is gated `ENABLE_COMBAT_ENGAGEMENT` OFF (Batch 07's own confirmed finding) — a
  doubly-inert chain. This is exactly the bookkeeping-not-depth pattern the batch instruction's
  own §19 warns against, confirmed real rather than merely hypothesized.

---

## Cross-batch note

SL-S15's finding (reputation echoes exactly one generation, no deeper) directly continues
Batch 07's own PROG-06/CP-S15 finding (progression's world-reaction channel is real but
narrow) one causal step further — the same repository, checked twice from two adjacent
angles, shows the same shape: real, working, single-hop causal channels, with no mechanism
yet built to extend them further, whether across time within one individual's own life (Batch
07) or across a generational gap (this batch).

SL-S13/S14's finding (default heir selection is bond-based, not kinship-based at all) is this
batch's own most significant discovery about how Batch 08's own confirmed CONFLICTING
property-transfer defect actually gets *fed* — the resolved candidate that then fails to
receive property (Batch 08's own finding) is, in this repository's own current design, never
guaranteed to be an actual relative in the first place. Both findings remain real and
distinct: Lineage's own eligibility-determination is confirmed clean (kinship correctly
doesn't automatically grant property); Ownership's own transfer mechanism is confirmed broken
(Batch 08); and the specific *candidate* the broken mechanism would have delivered property to,
had it worked, is a social-bond winner, not necessarily a family member.

SL-S18's four-plus confirmed-inert findings are this batch's own reconfirmation that
`SocialComponent`'s real multiplicity of tracking fields (`social-relations.md`'s own
Repository Findings) is not merely a naming-duplication risk but includes genuinely unused
state — worth an owner's attention alongside the duplication concern, not instead of it.
