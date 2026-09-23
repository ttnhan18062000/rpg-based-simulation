---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Social Relations

**Purpose/scope.** What makes a social relationship a persistent world fact rather than
merely one entity's opinion about another, and what makes it materially matter. Does not
require every relationship kind (friendship, trust, hostility, rivalry, loyalty, debt,
mentorship, partnership) to exist. Applies the strict Rule-admission discipline established in
Batches 07/08's own follow-up reviews from the first draft — Rule statements below state only
target world semantics; every repository fact lives in Repository evidence/Findings.

**Status.** Batch 09 (Social Relations/Family/Lineage). First draft, then a targeted semantic
cleanup follow-up (2026-09-22, `tmp/world-rule-batch-9-followup-ext-ai.md`) that reworked
SOC-01, generalized SOC-03, reclassified SOC-04 to Inherited, and added a new Inherited entry
on reputation-reach after direct re-investigation. Structured per the normalized five-category
methodology.

---

## Domain Rules

## SOC-01 — A structural relation, a party's own belief about it, and a party's own subjective attitude toward the other are distinct kinds of fact, but not every one of them requires independent representation

> Two broad kinds of social fact exist: a **structural relation** (sibling, parent,
> spouse/partner, a formally-established mentor, a represented debtor/creditor relation, or
> another world-declared relation) and a **subjective relational state** (trust, hostility,
> affection, fear, loyalty, or another attitude one subject holds toward another). A structural
> relation may exist independently of either participant's own belief or attitude about it —
> siblings remain siblings whether or not either believes it or feels warmth toward the other.
> A directional subjective attitude such as "A trusts B" is itself simply A's own subject-owned
> state; it does not require a separate, mirrored, world-owned "trust relationship" fact to
> exist alongside it. What must remain distinct: a structural/world-social fact ≠ a party's own
> belief about that fact ≠ a party's own subjective attitude toward the other subject. No third
> canonical state is required merely for symmetry between the two parties.

**Disposition: ACCEPT (reworked 2026-09-22 per external follow-up review).** The original
draft required every relationship to decompose into five independent facts (world fact + A's
belief + B's belief + A's attitude + B's attitude) — representation-oriented language the
follow-up correctly flagged as over-specifying structure rather than stating target semantics.
This revision keeps the substantive distinction (structural fact ≠ belief ≠ attitude) while
removing the requirement that every relationship carry all of them, and without inventing a
third canonical state merely for symmetry between the two parties. Passes the admission test:
no earlier Rule states this specific structural-relation/subjective-attitude split — Batch 06's
KNOW-02/OWN-06 already establish that belief ≠ truth generally, but not this pair-relationship
structure.

**Repository evidence: SUPPORTED — this repository already exhibits both categories cleanly,
as separate real facts.** `parent_a_entity_id`/`parent_b_entity_id` (biological parentage,
Batch 05 evidence) and `MarriageState` (`src/core/strategic.py`) are real **structural
relations** — checked directly, both persist independent of either party's own sentiment or
belief; nothing in this repository derives them from, or requires them to agree with, either
party's attitude. `SocialBond` (`src/core/models/social.py`) is this repository's own real
**subjective relational state** — explicitly "a first-class *directed* relationship record":
each entity's own `social.bonds[target_id]` stores that entity's own attitude toward a target,
entirely independent of the target's own `bonds` entry about the source, with no additional
world-owned "relationship" fact required alongside either directional entry. This confirms the
Rule's own claim: structural relation and subjective attitude are both real here, genuinely
independent, and neither requires a third, mirrored fact for symmetry.

**Scenarios:** [SL-S01](../scenarios/social-lineage-batch-09.md#sl-s01) (one-sided trust),
[SL-S11](../scenarios/social-lineage-batch-09.md#sl-s11) (kinship without affection, extended
to a structural relation with opposed attitudes).

---

## SOC-02 — A relationship is reciprocal only where a world rule declares it so; storage using mirrored records does not itself create reciprocity

> Whether a relation kind is intrinsically reciprocal (siblingship, marriage, shared
> parentage, a formally-declared partnership) or directional by default (trust, debt,
> mentorship, most subjective attitudes) is a property a world rule declares for that specific
> relation — never an accident of how it happens to be stored. Two independently-writable
> records existing for a pair does not, by itself, mean the relation they represent is
> reciprocal; a single shared record does not, by itself, make a relation directional either.

**Disposition: ACCEPT (preserved, per follow-up review confirming this Rule is sound as
drafted).** Passes the admission test: no earlier Rule addresses whether relationship
reciprocity is a declared property versus a storage artifact — Batch 02's REACH-03 (reach may
be asymmetric) is a related but distinct claim about causal-affecting capability in general,
not about social relationship kinds specifically declaring their own reciprocity.

**Repository evidence: SUPPORTED, with a clean real example of each kind.** `MarriageState`
(`src/core/strategic.py`) is written to *both* parties' own `StrategicComponent.marriages` in
the same transaction on acceptance (`docs/mechanics/04_strategic_cognition.md` §8) — a
relationship kind a world rule (the Marriage Proposal Law) explicitly declares reciprocal, by
writing both sides together, not by accident. `SocialBond`'s own directional trust/sentiment
(SOC-01's own evidence) is the directional counter-example: nothing forces `A.bonds[B]` and
`B.bonds[A]` to move together, and checked directly, `RelationshipService.process_update()`
updates exactly one entity's own bond per call, never both symmetrically.

**Scenarios:** [SL-S01](../scenarios/social-lineage-batch-09.md#sl-s01).

---

## SOC-03 — Persistence, decay, rupture, and expiration of social state occur only according to declared semantics

> A relationship's persistence, decay, rupture, or expiration occurs only according to
> whatever semantics are declared for that specific relation kind — never as an unstated
> default. One relation kind may persist indefinitely through silence or distance (ordinary
> friendship); another may decay slowly through disuse; another may expire on a declared
> condition (a temporary alliance); another may terminate only through a declared event
> (marriage). A relationship whose participant has died or otherwise permanently lost the
> ability to act remains a real historical fact, distinct from a currently-actionable
> reciprocal relationship — the history is real even where the ongoing exchange is not, and
> persistence is never a function of physical proximity by itself.

**Disposition: ACCEPT (reworded 2026-09-22 per external follow-up review).** The original
phrasing ("no accidental decay") stated the permission negatively and risked reading as a
universal ban on relationship decay. This revision keeps the same underlying principle —
persistence/decay/rupture/expiration are never an unstated default, only ever a declared
semantic — stated positively so it permits every one of the concrete cases above depending on
the specific relation, rather than fixing this repository's own no-decay pattern as the only
legitimate shape. Passes the admission test: no earlier Rule addresses relationship
persistence specifically — HP-01 (historical continuity survives ordinary change) is a related
but distinct claim about not severing what happened to a *subject*, not about a *relationship*
between two subjects, or about the historical/actionable distinction once a participant can no
longer act.

**Repository evidence: SUPPORTED for the declared-semantics principle — this repository's own
current relations all happen to implement the no-decay case, which is itself one valid
instance of "declared semantics," not evidence the Rule requires it universally.**
`RelationshipService.process_update()` (`src/systems/social_systems/relationships.py`) has no
passive decay term anywhere on `bonds`/`public_reputation` — confirmed directly (also
independently confirmed by `TCK-20260904-INHERITED-REPUTATION-SEED`'s own investigation:
"`RelationshipService.process_update()` genuinely has no passive decay term anywhere on
`public_reputation`"). `LifecycleSystem._transfer_inherited_feud()`/`_seed_dying_wish()` (Batch
01/05's own evidence) keep a deceased subject's relationships causally live and referenceable
after death — the historical fact persists, while the deceased party obviously cannot act on it
further.

**Scenarios:** [SL-S06](../scenarios/social-lineage-batch-09.md#sl-s06) (separation does not
erase relationship), [SL-S07](../scenarios/social-lineage-batch-09.md#sl-s07) (death does not
erase social history).

---

## Inherited / Applied Foundational Rules

### A relationship changes only through a real, declared causal event

> A social relationship's state changes only when a real, declared event produces that change
> — not every interaction is required to change it, and it must never mutate without a real
> cause.

**Disposition: INHERITED — direct reuse of CAUSE-01. No new claim: this is CAUSE-01's own
real-causal-path requirement applied to relationship state specifically.**

**Repository evidence: SUPPORTED.** `BetrayalRecord` (`src/core/models/social.py`) is a real,
typed causal record (`contract_id`, `betrayer_id`, `victim_id`, `severity`, `tick`) — a
relationship change traces to a specific, real, recorded event, never a bare value edit.
`RelationshipService.process_update()` only ever accepts explicit, caller-supplied deltas —
checked directly, no code path mutates `bonds`/`trust_history`/`sentiment` without a real
`SocialUpdate` produced by some other, real event.

**Scenarios:** [SL-S02](../scenarios/social-lineage-batch-09.md#sl-s02) (friendship through
shared experience), [SL-S03](../scenarios/social-lineage-batch-09.md#sl-s03) (interaction with
no relationship change, counter), [SL-S04](../scenarios/social-lineage-batch-09.md#sl-s04)
(betrayal).

### A relationship materially affects behavior only through the agent's own decision-making layer, never directly

> Relationship state does not directly cause a behavior — it becomes a real input to a
> decision only by being read and weighed inside the agent's own decision-making process,
> alongside whatever else that process already weighs.

**Disposition: INHERITED — direct reuse of Batch 06's AGENCY-01/AGENCY-02 (decision stages
are causally distinct; motivation influences, never determines). No new claim: this batch's
own §6 investigation ("a real decision path is still required... reuse Batch 06 Agency")
explicitly required this reuse rather than a restatement.**

**Repository evidence: SUPPORTED, richly, across independent real consumers.**
`src/domains/cooperation/evaluators.py` reads `requester.social.familiarity_history` and
`bond.sentiment` to compute a real `trust_score` input to a cooperation decision — trust
influences, it does not by itself cause cooperation. `entity.social.nemesis_ids` is read by
`AdventureRouteGenerator` (avoidance biasing), `src/engine/cognition.py` (emotional appraisal
input), and `src/systems/social_systems/party_composition.py` (a real, documented precedence
rule: "`nemesis_ids` takes precedence over a `FRIEND` bond.role when both are set") — fear/
hostility feeds several independent decision layers as one input among others, never as a
direct behavior trigger. `src/systems/social_systems/appraisal.py` reads a candidate's own
bond toward the recruiter as one input to contract appraisal.

**Scenarios:** [SL-S17](../scenarios/social-lineage-batch-09.md#sl-s17) (social relationship
changes agency).

### Pair-specific social relationship and population-scale reputation are distinct representations

> A subject's specific relationship to one other subject and that subject's own general
> standing across a wider population are two different kinds of fact — neither is derived from
> the other, and both may diverge for the same subject simultaneously.

**Disposition: INHERITED — direct reuse of Batch 05's ECOL-01/ECOL-02 (individual and
aggregate representations are distinct; aggregate change does not automatically mutate
individual-level fact). No new claim: this batch's own §5 investigation is the same
individual/aggregate boundary ECOL-01/02 already established, instantiated for social
standing rather than population counts.**

**Repository evidence: SUPPORTED, and this batch's own investigation resolves a real,
previously-flagged open question: Batch 01's own OWN-03 finding ("reputation scalar vs.
reputation labels narrative relationship... flagged for the Social relations batch") is
resolved here.** `SocialComponent.public_reputation` (a flat `0.0–2.0` scalar, "Unified
reputation score") and `entity.social.bonds[target_id]` (a specific pair relationship) are
confirmed structurally separate fields, neither derived from the other — a feared stranger and
a trusting friend can hold entirely different `bonds` entries about the same subject while
that subject's own `public_reputation` scalar is a single shared number. **A third,
independent representation, confirmed real but write-only**: `PublicReputationProfile.labels`
(`src/core/cognition.py`, under `entity.cognition.relationships.public_reputation`) is a
qualitative label map ("reliable," "betrayer," "heroic") on the entity's own cognition state,
populated by `ReputationUpdateService.process_witnessed_event()`, called from
`src/engine/quests.py` on real witnessed events for that same entity — confirmed live at the
write side, but checked directly during this follow-up, `.labels` has **zero readers anywhere**
outside its own write path (not even `src/api/presenters/state_presenter.py`, which exposes
only the `public_reputation` scalar). This resolves OWN-03's own carried-forward question:
`public_reputation` (numeric scalar) and `PublicReputationProfile.labels` (qualitative labels)
are two legitimately separate, real, independently-owned fields, neither a duplicate of the
other, exactly as OWN-03's own original flag anticipated — a genuine naming collision around
the word "reputation," not a semantic violation. The labels field's own inertness is recorded
as a fresh Repository Finding below, not folded into this resolution.

**Scenarios:** none newly traced; this Inherited entry's own evidence resolves Batch 01's
OWN-03 open question directly.

### Correcting the information behind a social change does not itself restore what changed; restoration needs its own causal process

> Correcting the belief that caused a social change does not retroactively erase the social
> consequences already produced — a relationship's own current state persists through the
> belief's correction unless a separate, declared reconciliation process changes it.
> Restoration, where it happens at all, requires its own valid causal process, exactly as any
> other change to social state does.

**Disposition: INHERITED (reclassified from a Domain Rule during the 2026-09-22 follow-up
review — originally drafted as SOC-04).** The follow-up correctly tested whether this adds
genuinely new content beyond combining Rules already established elsewhere, and it does not:
SOC-03 above (persistence/decay/restoration occur only according to declared semantics —
silence, or a belief simply being corrected, is not itself a declared reconciliation event) and
CAUSE-01 (any change requires a real, declared causal event — restoration is a change like any
other, so it needs its own cause) together already require exactly this outcome. Batch 06's
KNOW-02 separately established that a *belief* does not automatically re-sync with corrected
truth; this entry's own remaining claim — that a *relationship*, once changed, doesn't either —
turns out to be SOC-03's own declared-semantics requirement applied to the specific case where
the "event" in question is a correction, not a distinct third principle. Per the follow-up's
own instruction not to preserve the Rule count artificially, this is moved rather than kept as
a Domain Rule.

**Repository evidence: SUPPORTED, by the shape of the only real repair mechanism found.**
`RelationshipService.process_update()` only ever moves `sentiment`/`familiarity` through
explicit deltas the caller supplies (`SocialUpdate.sentiment_delta`/`familiarity_delta`) — no
code path detects "the belief behind this sentiment change was corrected" and reverses it
automatically. Checked directly: no mechanism was found that restores a relationship's own
`sentiment`/`role` when a contradicting `BeliefContradictionService.detect()` event fires
(Batch 06 evidence) — the relationship layer and the belief layer are confirmed to update
independently, with no automatic reconciliation wired between them.

**Scenarios:** [SL-S05](../scenarios/social-lineage-batch-09.md#sl-s05) (false accusation).

### Reputation is real world/social state; whether another subject may act on it still requires a declared information/perception channel, same as any other fact

> A subject's own public reputation existing as a real, authoritative world/social fact does
> not by itself mean every other subject automatically knows it — a fact's own availability and
> another subject's own knowledge of that fact remain separate requirements, exactly as
> Perception/Knowledge (Batch 06) already requires for any world fact. A reputation may be
> widely available in principle, but another subject's own use of it still requires declared
> social/information semantics connecting the two.

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01 (perception is bounded by
declared constraints, default of partiality) and KNOW-01 (certainty permitted where relevant,
≠ truth), applied to reputation-reach specifically, per this follow-up's own §7 investigation
(re-investigating a question the original draft explicitly left unchecked). No new claim
beyond instantiating an already-settled boundary for this specific kind of fact.**

**Repository evidence: CONFLICTING — every consumer checked reads reputation as directly,
globally available truth; no perception/knowledge-mediated channel gates it anywhere.**
Checked directly: `SocialAppraisalSystem.appraise_contract()` (`src/systems/social_systems/
appraisal.py`) reads `source_entity.social.public_reputation` straight off the *other* party's
own authoritative state to compute `public_trust`, for an evaluating entity with **no prior
`bond` at all** (a stranger) — no `PerceptionGate.can_perceive()` call, no knowledge_model
lookup, no information-transfer event of any kind gates this read. `ShopService.buy_item()`
(`src/town/shop.py`) and its price-hardening counterpart in `src/engine/shop.py` both call
`apply_reputation_discount(..., entity.social.public_reputation)` — the shop system reads the
*customer's* own authoritative reputation directly, again with no perception gate. The same
`appraise_contract()` call also blends in `state.clans[clan_id].clan_reputation` for
guilt-by-association trust priors, the same ungated pattern one level up. Every reputation
consumer found treats `public_reputation` as instantly, universally available — none of them
implement "this entity previously observed, was told of, or otherwise received a report of
that reputation." This is the same class of finding as Batch 06's own CONFLICTING
`ResourceOpportunityProvider`/`HarvestScorer` reads (raw world state read with no perception
gate), now confirmed for reputation specifically. Cross-referenced in depth from
`lineage-descent.md`'s own LIN-02 evidence, where this same gap collapses two causal steps this
follow-up's own §8 requires kept distinct.

**Scenarios:** [SL-S15](../scenarios/social-lineage-batch-09.md#sl-s15) (extended — famous
ancestor, uninformed stranger).

---

## Scope / Deferred Boundaries

### Concrete relationship-formation content

> This family states the causal-path requirement for relationship formation/change (Inherited,
> above) but does not design the concrete catalog of qualifying events, thresholds, or
> magnitude formulas for every relationship kind — that remains implementation-level content,
> per this family's own scope.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.** The Rules above state
what this family's own target semantics require and permit; the findings below report where
this repository's own current implementation does or does not realize them.

- **CONFLICTING — reputation-reach is ungated, confirmed via direct re-investigation.** See the
  new reputation-reach Inherited entry above. Every checked reputation consumer
  (`SocialAppraisalSystem.appraise_contract()`, `ShopService`'s discount path) reads another
  subject's `public_reputation` directly, with no perception/knowledge-mediated channel — a
  stranger reacts identically to someone with genuine history. This is the batch's own new
  CONFLICTING finding, superseding the original draft's "not independently investigated" note.
- **A real duplication risk, not a duplicate-truth violation — worth naming.**
  `SocialComponent` carries at least three parallel per-target-entity tracking structures for
  overlapping hostility/trust concepts: the older per-dict fields (`trust_history`,
  `familiarity_history`, `debt_history`, `fear_history`, `grudge_history`,
  `combat_loss_counts`, `salience_history`), the newer first-class `bonds: Dict[int,
  SocialBond]` (with its own `RelationshipRole` classification, explicitly documented as
  "Independent of nemesis_ids/grudge_history"), and `nemesis_ids` (a promoted subset of
  `grudge_history`). `src/systems/social_systems/party_composition.py` documents a real,
  already-resolved precedence rule between `nemesis_ids` and `bonds.role`, confirming this is
  an actively-managed multiplicity, not an accidental drift — but it remains a real
  multiplicity a future author should be aware of before adding a fourth tracking field.
- **MISSING (consumer) — `PublicReputationProfile.labels` is write-only.** Confirmed during
  this follow-up: `ReputationUpdateService.process_witnessed_event()` writes it from
  `src/engine/quests.py`, but nothing anywhere reads `.labels` — not even the API presenter,
  which exposes only the numeric `public_reputation` scalar. A real, live write path with zero
  consumers, distinct from (and additional to) the SL-S18 findings below.
- **SUPPORTED — reputation seeds transgenerationally for exactly one hop, confirmed real and
  live.** `V2EntityBuilder.birth_record()` seeds a newborn's own `SocialComponent.
  public_reputation` from the weighted average of both parents' own `public_reputation` at
  birth (`TCK-20260904-INHERITED-REPUTATION-SEED`) — "a starting echo," naturally swamped by
  the child's own subsequent actions since no decay logic exists or is needed. This is real
  evidence for `social-lineage/lineage-descent.md`'s own LIN-02, cross-referenced there rather
  than duplicated.
- **PARTIAL — betrayal is a real, structured event; the "grudge" side is richly consumed, but
  no automatic reconciliation exists.** See the correcting-information-behind-a-change entry
  above (originally SOC-04).

## Cross-domain links recorded here

- SOC-01, SOC-02 → Perception/Knowledge (Batch 06's KNOW-02, OWN-06), Reach (REACH-03,
  related but distinct)
- SOC-03 → History/Provenance (HP-01, related but distinct), Identity (LIFE-03, Batch 05)
- Inherited causal-path entry → Causality (CAUSE-01)
- Inherited decision-layer entry → Agency/Decision (AGENCY-01/02, Batch 06)
- Inherited reputation-representations entry → Ecology/Population (ECOL-01/02, Batch 05),
  State Ownership (OWN-03, Batch 01 — this entry's own resolution of that carried-forward open
  question)
- Inherited correcting-information entry (originally SOC-04) → Causality (CAUSE-01), this
  family's own SOC-03, Perception/Knowledge (Batch 06's KNOW-02)
- Inherited reputation-reach entry → Perception/Knowledge (Batch 06's PERC-01, KNOW-01),
  Lineage/Descent (`lineage-descent.md`'s LIN-02, the two-causal-steps finding)

## Open questions carried forward

1. Whether the three parallel hostility/trust tracking structures on `SocialComponent` should
   ever be consolidated is a real implementation question, not decided here.
2. Whether relationship repair/reconciliation should ever gain a real automatic mechanism tied
   to belief-contradiction correction (confirmed gap, above) is flagged for a future ticket,
   not decided here.
3. Whether reputation reads should ever gain a real perception/knowledge-mediated gate
   (confirmed absent, above) before being wired to further decision systems is flagged for a
   future ticket, not decided here — this follow-up confirms the gap is real, not how to close
   it.
4. Whether `PublicReputationProfile.labels` should gain a real consumer or be removed is
   flagged, not decided here.
