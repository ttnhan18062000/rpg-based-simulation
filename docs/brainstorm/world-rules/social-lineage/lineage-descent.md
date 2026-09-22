---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Lineage / Descent

**Purpose/scope.** How ancestry persists across generations and creates historical continuity
without merging individual identities, and how it may create later social opportunities/
constraints only through real causal paths. Does not solve political succession (who becomes
king, who inherits office) — that remains Politics/Institutions.

**Status.** Batch 09 (Social Relations/Family/Lineage), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-9-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology.

---

## Domain Rules

## LIN-01 — Lineage membership conveys nothing automatically; each potential inheritance requires its own declared transfer mechanism

> Lineage/ancestral continuity persists across generations without merging the distinct
> identities of ancestor and descendant. Membership in a shared lineage — belonging to the
> same family line — conveys nothing by itself: relationships, claims, objects, reputation,
> obligations, and traits each require their own real, declared transfer mechanism to reach a
> descendant. A close relative existing is not, by itself, a transfer.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states that lineage
membership itself is causally inert — CAUSE-01 already requires any specific transfer to trace
to a real cause, but does not itself state the domain-specific claim that shared lineage is
never that cause on its own. This is directly required by this batch's own §10 ("nothing
should transfer merely because two entities belong to the same lineage") and §16's family-feud
warning ("descendants later inherit knowledge/obligation/hostility only through declared
mechanisms").

**Repository evidence: SUPPORTED, by real, clean per-item examples of exactly this
discipline.** `LifecycleSystem._transfer_inherited_feud()`/`_seed_dying_wish()` (Batch 01/05
evidence) are specific, real, declared per-mechanism transfers — a feud reaches an heir only
because a named function explicitly transfers it at the moment of death, never because the
heir simply shares a lineage with the deceased. `V2EntityBuilder.birth_record()`'s
reputation-seed mechanism (below, LIN-02's own evidence) is a second real, declared,
per-mechanism transfer — reputation moves from parent to child only through this one specific,
named write, not automatically from any general "family" fact. Object/property inheritance
(Batch 08's own PROP-02-adjacent Inherited entry) is a third: property transfer is confirmed to
require its own resolved-heir mechanism, entirely separate from Lineage's own domain.

**Scenarios:** [SL-S12](../scenarios/social-lineage-batch-09.md#sl-s12) (lineage across
generations), [SL-S16](../scenarios/social-lineage-batch-09.md#sl-s16) (family feud).

---

## LIN-02 — An ancestor's own historical significance may affect a descendant's later social treatment only through a real, declared causal channel

> An ancestor's own accumulated significance, reputation, or notoriety may causally affect how
> a descendant is later socially treated — but only through a real, declared channel connecting
> the two specifically. Lineage existing, by itself, does not make a descendant's treatment
> reflect an ancestor's own significance; a real mechanism must carry that effect across the
> generational gap.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states that transgenerational
social-significance propagation requires its own declared channel — Batch 07's PROG-06
(progression may change world reaction through declared channels) is a related but distinct
claim about one individual's *own* progression affecting reaction to *that same individual*;
this Rule is about propagation *across a generational gap*, a different causal question. This
is the batch instruction's own flagship investigation (§11, §21 — "Famous Ancestor," continuing
Batch 07's own ordinary-individual-significance question one generation further).

**Repository evidence: SUPPORTED for exactly one generational hop; MISSING for any deeper
multi-generation propagation — checked directly, not assumed symmetric with the single-hop
case.** `V2EntityBuilder.birth_record()` seeds a newborn's own `SocialComponent.
public_reputation` from the weighted average of both parents' own `public_reputation` at the
moment of birth (`TCK-20260904-INHERITED-REPUTATION-SEED`, confirmed real and live) — "a
starting echo... not a full inheritance," naturally swamped by the child's own subsequent
actions since `RelationshipService.process_update()` has no passive decay term at all. This is
a real, declared, one-hop transgenerational significance channel — exactly what this Rule
requires, realized for parent→child specifically. **Checked directly: no mechanism propagates
significance any deeper** — a grandchild's own reputation is never seeded from a grandparent's;
`LegendFact`/`FameState` (Batch 05/06/07 evidence, HERO-scoped fame from `entity_death`/
`quest_completed` events) has no lineage-awareness at all — nothing reads a HERO's own
descendants' identity to extend fame's effect to them. The flagship trajectory this batch was
asked to probe (an ordinary ancestor's notable life producing changed social treatment for
distant descendants) is therefore realized only at the shallowest possible depth (one
generation) and not at all beyond it.

**Scenarios:** [SL-S15](../scenarios/social-lineage-batch-09.md#sl-s15) (famous ancestor,
flagship).

---

## Inherited / Applied Foundational Rules

### Identity remains distinct at every generation

> A descendant's own identity is never a continuation of an ancestor's — each generation
> establishes a genuinely new, separate identity, however many generations removed.

**Disposition: INHERITED — direct reuse of ID-04 (Batch 01), cross-referenced from
`family-kinship.md`'s own identical entry. No new claim beyond that file's own citation — this
entry exists so Lineage's own multi-generation claim (LIN-01) is read against the same
identity-distinctness discipline, without duplicating the rationale.**

**Repository evidence: SUPPORTED**, reused directly — see `family-kinship.md`'s own fuller
evidence for this same inherited entry.

**Scenarios:** [SL-S12](../scenarios/social-lineage-batch-09.md#sl-s12).

### Property transfer remains Ownership's own domain, never Family/Lineage's

> Family/Lineage may determine who is eligible as a successor and under what priority its own
> rules declare — but it never owns the resulting property relation itself, which stays with
> whichever domain owns durable property state.

**Disposition: INHERITED — direct reuse of Batch 08's own reclassified Inherited entry
(originally drafted as PROP-02; itself a reuse of Batch 01's OWN-01/OWN-02). This batch's own
§13 states the boundary explicitly ("Family determines eligibility ≠ Family owns property
state... Property transfer remains Material/Ownership") — restating an already-settled
boundary from its own vantage point, not new content.**

**Repository evidence: CONFLICTING for the property-transfer half, confirmed by Batch 08's own
investigation and reconfirmed rather than re-investigated here; SUPPORTED for the
eligibility-determination half, a new finding this batch's own investigation adds.**
`LifecycleSystem._select_default_heir()` (`src/systems/lifecycle_systems/lifecycle.py`) is the
real, live eligibility-determination mechanism — but checked directly, it selects purely by
**social bond strength** (`score = 0.6 * bond.familiarity + 0.4 * ((bond.sentiment + 1.0) /
2.0)`), never reading `parent_a_entity_id`/`parent_b_entity_id` or any other kinship fact at
all. This is a real, clean confirmation that this Rule's own boundary holds correctly in this
repository — kinship does not automatically determine, or even factor into, the default
eligibility determination — but it also means this repository's current "default heir" concept
is not, in fact, a *family*-eligibility mechanism at all; it is a *relationship-bond*
eligibility mechanism that happens to serve the same downstream slot. The property-transfer
half remains Batch 08's own confirmed CONFLICTING finding (the `source_kind="CHEST"` resolver
gap) — cross-referenced, not re-investigated.

**Scenarios:** [SL-S13](../scenarios/social-lineage-batch-09.md#sl-s13) (inheritance
candidate), [SL-S14](../scenarios/social-lineage-batch-09.md#sl-s14) (inheritance blocked).

---

## Scope / Deferred Boundaries

### Political succession

> This family supplies parentage, descent, lineage, and kinship as real inputs — it does not
> decide who becomes king, who inherits political office, or what makes sovereignty
> legitimate. Those remain Politics/Institutions' own future domain, per the batch
> instruction's own explicit deferral.

**Disposition: SCOPE BOUNDARY.**

### Law, custom, or wills overriding simple kinship-based inheritance

> This family does not design how law, custom, wills, or institutions might override a simple
> kinship-based (or, per this repository's own current mechanism, bond-based) succession
> determination — that remains deferred to future Law/Crime and Politics/Institutions domains.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions.**

- **A significant, notable finding: this repository's own "default heir" mechanism is a
  relationship-bond mechanism, not a kinship mechanism.** See the Inherited property-transfer
  entry above. This is not a violation of any Rule (kinship correctly does not automatically
  transfer property, per this same entry) — but it means a future reader should not assume
  `_select_default_heir()` implements anything like "nearest living relative"; it implements
  "whoever this entity has the strongest social bond with," which may or may not be a relative
  at all.
- **SUPPORTED, but shallow — reputation echoes exactly one generation, no deeper.** See LIN-02
  above.
- **Cross-referenced from Batch 08**: the property-transfer resolver gap
  (`source_kind="CHEST"` unhandled by `src/core/conservation.py`) remains CONFLICTING,
  unaffected by anything this batch investigated — Lineage's own eligibility-determination
  half is unaffected by that defect and is evaluated separately above.

## Cross-domain links recorded here

- LIN-01 → Causality (CAUSE-01), Ownership/Possession (`ownership-possession.md`'s own
  Inherited entry, reused above), Family/Kinship (`family-kinship.md`'s FAM-01)
- LIN-02 → Capability/Progression (`capability-progression.md`'s PROG-06, Batch 07 — the
  same-generation analogue of this Rule's own transgenerational claim), History/Provenance
  (`FameState`/`LegendFact`, confirmed lineage-unaware)
- Inherited identity entry → Identity (ID-04), `family-kinship.md` (cross-reference, not
  duplicated)
- Inherited property-transfer entry → State Ownership (OWN-01, OWN-02, Batch 01), Objects/
  Ownership (`material-economy/ownership-possession.md`, Batch 08)

## Open questions carried forward

1. Whether a real kinship-aware heir-priority option should be added alongside (or instead of)
   the current bond-based default is flagged for a future ticket — not decided here.
2. Whether reputation/significance propagation should ever extend beyond one generation is
   flagged, not decided here.
3. Whether Politics/Institutions, once reached, should consume parentage/lineage/kinship facts
   this family supplies for legitimate-succession content is flagged for that future batch —
   not pre-decided here.
