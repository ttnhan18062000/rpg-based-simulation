---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Social Relations

**Purpose/scope.** What makes a social relationship a persistent world fact rather than
merely one entity's opinion about another, and what makes it materially matter. Does not
require every relationship kind (friendship, trust, hostility, rivalry, loyalty, debt,
mentorship, partnership) to exist. Applies the strict Rule-admission discipline established in
Batches 07/08's own follow-up reviews from the first draft — Rule statements below state only
target world semantics; every repository fact lives in Repository evidence/Findings.

**Status.** Batch 09 (Social Relations/Family/Lineage), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-9-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## SOC-01 — A relationship, each party's own belief about it, and each party's own attitude toward the other are up to five independent facts

> A social relationship (a real world fact between two subjects) is distinct from subject A's
> own belief about that relationship, from subject B's own belief about it, from A's own
> attitude toward B, and from B's own attitude toward A. All five may exist simultaneously and
> may disagree with one another — siblings may share a real, world-owned kinship fact while A
> believes B betrayed them and B still trusts A, with none of these facts required to
> reconcile automatically.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states this specific
five-way distinctness for a pair relationship — Batch 06's KNOW-02/OWN-06 already establish
that belief ≠ truth generally, but not the specific multi-party structure (two independent
beliefs, two independent attitudes, one world fact) a *relationship* requires.

**Repository evidence: SUPPORTED for the world-fact/belief separation as an architectural
pattern; PARTIAL for whether all five facts are independently trackable in practice.**
`SocialBond` (`src/core/models/social.py`) is explicitly "a first-class *directed*
relationship record" — each entity's own `social.bonds: Dict[target_id, SocialBond]` stores
that entity's own view (familiarity, sentiment, role) toward a target, independently of the
target's own `bonds` entry about the source. Checked directly: entity A's bond toward B and
entity B's bond toward A are two structurally separate records, confirming the
world-relationship/A's-view/B's-view distinctness is real for at least the "attitude" layer.
This repository does not additionally track a *world-owned*, subject-independent relationship
fact distinct from both parties' own bond records — "the relationship" as experienced by this
repository *is* the pair of directional bonds, not a third, separate authoritative fact.

**Scenarios:** [SL-S01](../scenarios/social-lineage-batch-09.md#sl-s01) (one-sided trust).

---

## SOC-02 — A relationship is reciprocal only where a world rule declares it so; storage using mirrored records does not itself create reciprocity

> Whether a relationship is intrinsically reciprocal (marriage, siblinghood, shared parentage)
> or directional (trust, debt, mentorship) is a property a world rule declares for that
> relationship kind — never an accident of how the relationship happens to be stored. Two
> independently-writable records existing for a pair does not, by itself, mean the relationship
> they represent is reciprocal.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule addresses whether
relationship reciprocity is a declared property versus a storage artifact — Batch 02's REACH-03
(reach may be asymmetric) is a related but distinct claim about causal-affecting capability in
general, not about social relationship kinds specifically declaring their own reciprocity.

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

## SOC-03 — A relationship's persistence is independent of continued interaction, physical proximity, or a participant's own continued ability to act

> A relationship does not decay merely from elapsed time or physical separation absent a
> declared mechanism that changes it — a relationship may remain stable indefinitely through
> silence or distance. A relationship whose participant has died or otherwise permanently lost
> the ability to act remains a real historical fact, distinct from a currently-actionable
> reciprocal relationship — the history is real; the ongoing exchange is not.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule addresses relationship
persistence specifically — HP-01 (historical continuity survives ordinary change) is a related
but distinct claim about not severing what happened to a *subject*, not about a *relationship*
between two subjects remaining stable absent a decay mechanism, or about the historical/
actionable distinction once a participant can no longer act.

**Repository evidence: SUPPORTED for no-accidental-decay; SUPPORTED for historical
persistence after death, reusing Batch 01/05's own evidence.** `RelationshipService.
process_update()` (`src/systems/social_systems/relationships.py`) has no passive decay term
anywhere on `bonds`/`public_reputation` — confirmed directly (also independently confirmed by
`TCK-20260904-INHERITED-REPUTATION-SEED`'s own investigation: "`RelationshipService.
process_update()` genuinely has no passive decay term anywhere on `public_reputation`").
`LifecycleSystem._transfer_inherited_feud()`/`_seed_dying_wish()` (Batch 01/05's own evidence)
keep a deceased subject's relationships causally live and referenceable after death — the
historical fact persists, while the deceased party obviously cannot act on it further.

**Scenarios:** [SL-S06](../scenarios/social-lineage-batch-09.md#sl-s06) (separation does not
erase relationship), [SL-S07](../scenarios/social-lineage-batch-09.md#sl-s07) (death does not
erase social history).

---

## SOC-04 — A relationship's current state does not automatically re-derive itself when the belief that changed it is later corrected

> Damaging a relationship through a (possibly false) belief-driven event, and later correcting
> that belief, are not mirror-image operations — a relationship's own current state persists
> through the belief's own correction unless a separate, declared reconciliation process
> changes it. The relationship has its own lived history, not merely a live reflection of the
> currently-held belief that most recently touched it.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule addresses this specific
asymmetry. Batch 06's KNOW-02 states that a belief itself does not automatically re-sync with
changing world truth; this Rule states the further, distinct claim that a *relationship*
already changed by an earlier (possibly false) belief does not automatically re-sync either,
once that belief is corrected — a second-order persistence claim, not a restatement of KNOW-02.

**Repository evidence: SUPPORTED, by the shape of the only real repair mechanism found.**
`RelationshipService.process_update()` only ever moves `sentiment`/`familiarity` through
explicit deltas the caller supplies (`SocialUpdate.sentiment_delta`/`familiarity_delta`) — no
code path detects "the belief behind this sentiment change was corrected" and reverses it
automatically. Checked directly: no mechanism was found that restores a relationship's own
`sentiment`/`role` when a contradicting `BeliefContradictionService.detect()` event fires
(Batch 06 evidence) — the relationship layer and the belief layer are confirmed to update
independently, with no automatic reconciliation wired between them.

**Scenarios:** [SL-S05](../scenarios/social-lineage-batch-09.md#sl-s05) (false accusation).

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
independent representation, confirmed real and live**: `PublicReputationProfile.labels`
(`src/core/cognition.py`, under `RelationshipModel`) is a qualitative label map ("reliable,"
"betrayer," "heroic") populated by `ReputationUpdateService.process_witnessed_event()`, called
from `src/engine/quests.py` on real witnessed events — confirmed live, not dormant. This
resolves OWN-03's own carried-forward question: `public_reputation` (numeric scalar) and
`PublicReputationProfile.labels` (qualitative labels) are two legitimately separate, real,
independently-owned fields, neither a duplicate of the other, exactly as OWN-03's own original
flag anticipated — a genuine naming collision around the word "reputation," not a semantic
violation.

**Scenarios:** none newly traced; this Inherited entry's own evidence resolves Batch 01's
OWN-03 open question directly.

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
- **SUPPORTED — reputation seeds transgenerationally for exactly one hop, confirmed real and
  live.** `V2EntityBuilder.birth_record()` seeds a newborn's own `SocialComponent.
  public_reputation` from the weighted average of both parents' own `public_reputation` at
  birth (`TCK-20260904-INHERITED-REPUTATION-SEED`) — "a starting echo," naturally swamped by
  the child's own subsequent actions since no decay logic exists or is needed. This is real
  evidence for `social-lineage/lineage-descent.md`'s own LIN-02, cross-referenced there rather
  than duplicated.
- **PARTIAL — betrayal is a real, structured event; the "grudge" side is richly consumed, but
  no automatic reconciliation exists.** See SOC-04 above.

## Cross-domain links recorded here

- SOC-01, SOC-02 → Perception/Knowledge (Batch 06's KNOW-02, OWN-06), Reach (REACH-03,
  related but distinct)
- SOC-03 → History/Provenance (HP-01, related but distinct), Identity (LIFE-03, Batch 05)
- SOC-04 → Perception/Knowledge (Batch 06's KNOW-02, the belief-side half of this Rule's own
  claim)
- Inherited causal-path entry → Causality (CAUSE-01)
- Inherited decision-layer entry → Agency/Decision (AGENCY-01/02, Batch 06)
- Inherited reputation entry → Ecology/Population (ECOL-01/02, Batch 05), State Ownership
  (OWN-03, Batch 01 — this entry's own resolution of that carried-forward open question)

## Open questions carried forward

1. Whether the three parallel hostility/trust tracking structures on `SocialComponent` should
   ever be consolidated is a real implementation question, not decided here.
2. Whether relationship repair/reconciliation should ever gain a real automatic mechanism tied
   to belief-contradiction correction (SOC-04's own confirmed gap) is flagged for a future
   ticket, not decided here.
