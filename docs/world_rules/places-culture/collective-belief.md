---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Collective Belief

**Purpose/scope.** Collective or socially-organized belief (religious tradition, shared myth,
institutional doctrine, folk belief, collective historical narrative) as distinct from any
individual's own belief and from objective world truth; the boundary between social/religious
belief and supernatural mechanism, which this family does not decide; and how a place, object,
or event may become sacred through cultural interpretation alone. Does not decide Magic/
supernatural truth or mechanism — that remains Batch 12's own future domain.

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 11B (Culture/Collective Belief), first draft, per
`tmp/world-rule-batch-11-ext-ai.md`.

---

## Domain Rules

## BEL-01 — Collective or socially-organized belief is distinct from any individual's own belief and from objective world truth; it may exist with no institution ever declaring it; it may be false and still produce real individual or institutional behavior; and correcting it does not automatically undo consequences already caused

> A religious tradition, shared myth, institutional doctrine, folk belief, or collective
> historical narrative is its own kind of fact — distinct from any single individual's own
> private belief (Batch 06's own individual belief machinery), and distinct from objective
> world truth. Collective belief may exist purely as a shared social pattern with no
> institution ever formally declaring it (a folk myth a whole community holds without any
> governing body), which distinguishes this Rule from Batch 10's own LAW-02 (institutional
> record ≠ world truth ≠ individual belief) — that Rule requires an institution; this one does
> not. A collective belief may be false (a false historical story, an incorrect cosmology, a
> myth, propaganda) and still produce real behavior from individuals or institutions that hold
> it; correcting the belief afterward does not automatically undo whatever real consequences
> it already caused, exactly as this Catalog's own already-established belief/relationship
> persistence pattern requires (Batch 06's KNOW-02, Batch 09's own correcting-information
> Inherited entry).

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is genuinely broader than
Batch 10's own LAW-02 — the "no institution required" case (a purely social, uninstitutional
shared myth) is the specific new content this Rule adds beyond LAW-02's own institution-scoped
claim, alongside applying it to *collective* belief specifically rather than one institution's
own record.

**Repository evidence: PARTIAL, for the institution-backed half only; MISSING for the
institution-free half (narrowed 2026-09-22 per external follow-up review).**
`BeliefInstitution`/`BeliefInstitutionCarryForward` (`src/domains/belief_institution/model.py`,
"idea 63, Belief Grows Around Real History") is a real, per-(clan, origin-event) collective
belief record, explicitly documented as "a genuinely third, population-scale concept" distinct
from the per-entity `BeliefEntry` (tactical belief) and `KnowledgeFact` (settled individual
knowledge) — a genuinely positive structural match for this Rule's own individual/collective
distinctness, at the design-intent level, but only for the case this Rule requires an
institution *not* be present for at all: `BeliefInstitution` is, by its own design, keyed to a
specific `clan_id` — it is a promising carrier for institution-backed doctrine/belief, and it
may participate in culturally or religiously grounded significance (this file's own
reclassified sacredness entry, originally BEL-03), but it does not cover, and is not
evidence for, this Rule's own broader
institution-*free* permission (a folk myth no clan or institution ever declares). `belief_
strength` is derived from a real Chronicle event (the legendary subject's own fame), confirming
collective belief grounded in real history rather than fabricated from nothing, for the
institution-backed case specifically. The mechanism itself is explicitly documented as having
"no live caller yet... built, not yet visible in play" — currently INERT/OFF rather than
CONFLICTING or fully SUPPORTED, for that same institution-backed case. For the institution-
free case, no candidate mechanism of any kind was found — confirmed MISSING, not merely
INERT/OFF, since nothing here is even built for it to be unconsumed.

**Scenarios:** [CB-S07](../scenarios/culture-belief-batch-11b.md#cb-s07) (false shared
belief, extended to cover both the institution-backed and institution-free cases).

---

## BEL-02 — Belief that a supernatural entity or effect exists is distinct from that entity or effect objectively existing; ritual practice is distinct from any magical effect it may or may not produce; a religious institution is distinct from any supernatural mechanism; this family owns social belief, ritual practice, doctrine, and shared interpretation only, never metaphysical truth

> This family models social belief, ritual practice, religious doctrine, and shared
> interpretation of the supernatural — never whether the supernatural is objectively real, or
> how it mechanically works. Whether gods exist, whether a ritual produces any magical effect,
> and whether a religious institution wields any real supernatural mechanism are all questions
> this family explicitly defers to Batch 12 (Magic/Supernatural). This Rule exists to state
> that boundary as a target-semantic requirement, not merely a scope note: no content drafted
> under Culture/Belief may assume or imply supernatural truth, one way or the other.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is the explicit boundary
line between this family and a not-yet-drafted future domain, stated so neither family's own
future author accidentally absorbs the other's job — the same pattern Batch 02's AUTH-04
already used to draw the Authority/Reach boundary, and Batch 07's own capability-progression
family used to draw the Combat/Conflict boundary.

**Repository evidence: SUPPORTED, by absence.** No mechanism in this repository currently
grants any religious/ritual/doctrinal content a real supernatural causal effect on world
state — confirmed via the same investigation that found `BeliefInstitution` (a belief-holding
record) and no corresponding "ritual grants a real magical effect" mechanism anywhere. This is
the correct outcome per this Rule's own requirement, not a gap.

**Scenarios:** [CB-S08](../scenarios/culture-belief-batch-11b.md#cb-s08) (sacred place without
magic), [CB-S09](../scenarios/culture-belief-batch-11b.md#cb-s09) (real magic, no cultural
recognition, boundary probe).

---

## Inherited / Applied Foundational Rules

### Where sacredness or comparable social sanctity is modeled, it may arise through collective cultural interpretation alone, without requiring supernatural transformation or an objectively magical property; different attributors may hold different or conflicting attributions toward the same subject at once

> A location, object, or historical event acquiring sacred status is a social/cultural fact —
> a shared interpretation a *specific* culture, group, or institution holds — and never
> requires any actual change to that subject's own physical or supernatural properties,
> exactly as BEL-02 already requires generally for social/religious belief. Because
> significance/sacredness is always attributed by a specific actor (`places.md`'s own revised
> PLACE-02), two distinct cultures or groups may hold different, or directly conflicting,
> attributions toward the identical subject at once — Culture A regarding it as sacred while
> Culture B, aware of the same subject, regards it as ordinary or interprets it differently —
> with no supernatural effect required to explain either, and neither overriding the other.
> Where a domain models sacredness at all, this is a permitted possibility a domain may choose
> to realize, never a required universal feature of every world.

**Disposition: INHERITED (reclassified from a Domain Rule, originally drafted as BEL-03,
during a second 2026-09-22 follow-up review).** The follow-up first asked that this content's
own status be reframed from REQUIRED to PERMITTED — sacredness, where modeled, *may* arise
from cultural interpretation alone; not every world must contain culturally-created
sacredness, and this content's own primary purpose is protecting the boundary "social
sacredness ≠ supernatural truth," not mandating that sacredness exist. Having reframed it that
way, the follow-up then asked whether it still adds genuinely new semantics beyond BEL-02
(social/religious belief ≠ supernatural truth/mechanism) combined with `places.md`'s own
PLACE-02 (significance is always attributed, never intrinsic, with divergent simultaneous
attributions already permitted there). On that reassessment: it does not. "Sacredness" is the
culturally/religiously-flavored instance of the "significance" concept PLACE-02 already
covers in full generality, and "achievable without supernatural transformation" is simply
BEL-02's own belief/truth boundary applied to that specific case — combining two
already-established Rules for one named example, not new content. Per the follow-up's own
explicit instruction not to preserve the Rule count artificially, this is moved to Inherited
rather than kept as a separate Domain Rule.

**Repository evidence: MISSING.** No mechanism was found that marks any Place, object, or
event as sacred/culturally significant, with or without a supernatural component — confirmed
via direct search (no "sacred"/"pilgrimage"/"shrine" terms anywhere in `src/`). This entry's
own target semantics remain independently coherent, connecting three already-real mechanisms
(`PlaceState`, `CultureState`, `BeliefInstitution`) that simply have no bridge between them
yet — a repository-realization fact, not evidence favoring any one of those three as the
eventual bridge (see the significance-grammar note under Cross-domain links below).

**Scenarios:** [CB-S08](../scenarios/culture-belief-batch-11b.md#cb-s08).

### An institution's own declared doctrine does not require every member's private acceptance; membership remains possible alongside private disagreement, exactly as membership already does not require alignment with any other organizational fact

> An institution declaring a doctrine as its own canonical, collective belief does not by
> itself compel or require any specific member's own private acceptance of it — a member may
> privately reject a doctrine while remaining a member in good standing, wherever a domain's
> own declared rules permit that.

**Disposition: INHERITED — direct reuse of Batch 10's ORG-02 (membership ≠ loyalty/
obedience/belief-alignment) combined with this file's own BEL-01 (collective belief ≠
individual belief), applied to the specific institution/doctrine/member case. No new claim
beyond combining two already-established Rules for this specific scenario.**

**Repository evidence: MISSING, for the specific institution/doctrine mechanism — consistent
with BEL-01's own finding that no institution currently holds a declared doctrine at all.**
`ClanState`/`FactionState` (Batch 10 evidence) have no doctrine field distinct from
`BeliefInstitution`'s own belief-around-history content, and `BeliefInstitution` itself has no
live consumer yet (BEL-01's own INERT/OFF finding) — there is no live doctrine mechanism for a
member's own dissent to be checked against.

**Scenarios:** [CB-S10](../scenarios/culture-belief-batch-11b.md#cb-s10) (doctrine vs.
personal belief).

### Recognition of cultural, religious, or place significance requires a real information/perception path, exactly as any other world fact requires

> That a custom, doctrine, or sacred-place status is a real, declared fact does not mean any
> given subject knows it — recognition requires the same declared observation/report/record
> path Perception/Knowledge already requires for any world fact, including reputation
> (Batch 09) and Place significance (`places.md`'s own analogous entry).

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01/KNOW-01, Batch 09's own
reputation-reach entry, and `places.md`'s own analogous recognition entry, applied to
cultural/religious/place significance specifically. No new claim.**

**Repository evidence: MISSING, by the same absence `places.md`'s own analogous entry
reports** — no significance/doctrine/sacred-place fact exists yet for a recognition mechanism
to gate correctly or violate.

**Scenarios:** none newly traced; cross-referenced from `places.md`'s own PLACE-02.

---

## Scope / Deferred Boundaries

### Magic / supernatural mechanism and truth

> This family explicitly does not decide whether any supernatural entity or effect objectively
> exists, or how any such mechanism would work — deferred entirely to Batch 12 (Magic/
> Supernatural), per BEL-02's own explicit boundary and the batch instruction's own repeated
> "do not design Magic here."

**Disposition: SCOPE BOUNDARY.**

### Concrete religious-institution content catalog

> This family states that collective belief and religious institutions are real, distinct
> concepts (BEL-01) but does not design a concrete catalog of specific religions, doctrines,
> or rituals — open-ended, domain-declared content.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **A genuinely positive, well-shaped finding, currently INERT/OFF — but scoped to the
  institution-backed case only (narrowed 2026-09-22 per external follow-up review).**
  `BeliefInstitution` (`src/domains/belief_institution/model.py`) is a real, already-designed
  collective-belief concept grounded in real history (Chronicle-derived fame), explicitly
  documented as a "genuinely third, population-scale concept" distinct from individual belief
  and knowledge — but has "no live caller yet," and is keyed to a specific `clan_id`. It is a
  promising carrier for institution-backed doctrine/belief, not a general-purpose collective-
  belief mechanism. See BEL-01 above.
- **Confirmed MISSING — the institution-*free* half of BEL-01's own permission (a folk myth/
  taboo no institution ever declares) has no candidate mechanism of any kind**, distinct from
  the institution-backed case above. See BEL-01's own re-verified evidence.
- **SUPPORTED, by absence — no content anywhere grants ritual/doctrine a real supernatural
  effect.** See BEL-02 above; the correct outcome, not a gap.
- **Confirmed MISSING — no sacred-place, doctrine-dissent, or cultural/religious-significance
  recognition mechanism exists.** See the reclassified sacredness entry (originally BEL-03)
  and the two other Inherited entries above.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** collective belief may exist and produce real behavior, grounded in
  real history, and — per BEL-01's own explicit permission — may exist with no institution
  ever declaring it at all.
  **Current realization:** `BeliefInstitution` is a real, well-shaped, but currently
  unconsumed ("no live caller yet") mechanism — and it is, by its own design, **institution-
  backed only**: every `BeliefInstitution` record is keyed to a specific `clan_id`. It is a
  promising existing carrier for the institution-backed half of BEL-01, not a general-purpose
  collective-belief mechanism, and it has no bearing on the institution-*free* case at all
  (corrected 2026-09-22 per external follow-up review — the prior draft here overstated its
  scope, see the cross-domain observation below).
  **Gap/mismatch:** the institution-backed mechanism exists but produces no downstream
  behavioral consequence; the institution-free case (a folk myth/taboo no institution ever
  declares) has no candidate mechanism at all, and wiring `BeliefInstitution` would not close
  it.
  **Possible implementation direction:** wire a consumer that reads `belief_strength` to bias
  a clan's own decisions or reactions toward the origin event's own subject or descendants —
  this would exercise only the institution-backed subset of BEL-01, and a separate,
  institution-free mechanism would still be needed for the rest of BEL-01's own permitted
  range.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** a place, object, or event may become sacred/significant through
  cultural interpretation alone, always attributed by a specific culture/group/institution,
  never a universal property (the reclassified sacredness entry, originally BEL-03).
  **Current realization:** no bridge exists between `PlaceState`, `CultureState`, and
  `BeliefInstitution` — and, per the significance-grammar note below, this section names no
  candidate among the three as the intended eventual bridge; that choice remains undecided.
  **Possible implementation direction (constrained 2026-09-22 per external follow-up
  review):** if any "significance"/"sacred"-style field is ever added to `PlaceState` itself,
  it could only be a derived/cached projection with explicit provenance and scope (which
  attributor, as of when) — never the canonical representation of a perspective-dependent
  attribution, since the reclassified sacredness entry and PLACE-02 both require multiple,
  simultaneous, non-reconciled attributions to remain representable. The preferred semantic
  model is relational (`significant-to`, `sacred-to`, `recognized-as` — attributor, subject,
  value), not a universal boolean or scalar on the Place itself.
  **Implementation decision:** DEFERRED. No concrete storage design is committed here.

## Cross-domain links recorded here

- BEL-01 → Perception/Knowledge (KNOW-01/02, Batch 06), Law/Enforcement (LAW-02, Batch 10 —
  the related but narrower institution-scoped analogue), Social Relations (Batch 09's
  correcting-information entry)
- BEL-02 → Authority (AUTH-04, Batch 02 — the same explicit-boundary-drawing pattern), Magic/
  Supernatural (Batch 12, deferred)
- Inherited sacredness entry (originally BEL-03) → Places (`places.md`'s PLACE-02), Culture
  (`culture.md`'s CULT-01), Collective Belief (this file's own BEL-02)
- Inherited doctrine-dissent entry → Organizations (ORG-02, Batch 10)
- Inherited recognition entry → Perception/Knowledge (Batch 06), Social Relations (Batch 09),
  Places (`places.md`)

## Significance-grammar note (added 2026-09-22 per a second external follow-up review)

Batch 11A independently confirmed the same recurring grammar already seen for individuals
(Batch 07), objects (Batch 08), lineage (Batch 09), and organizations (Batch 10): a persistent
subject, plus a consequential event/history, produces provenance, which requires a valid path
to socially available recognition, which then may produce a changed future world reaction.
This is now clearly a cross-domain integration concern, preserved as such. At the semantic
level, this Catalog concludes only: **significance requires some valid path from a subject's
own history/provenance to socially available recognition, and from there to downstream
reaction.** Which mechanism, if any, eventually supplies that path — `BeliefInstitution`,
some other existing structure, or something not yet designed — is an implementation-shape
question this Catalog does not decide. `BeliefInstitution` being a real, well-shaped,
institution-backed carrier (see the Implementation Candidates above) is acceptable to record
there, but it is not, and must not be read as, part of this family's own target semantic
architecture merely because that structure already happens to exist in the repository.

## Open questions carried forward

1. **Can institutional doctrine count as collective belief without individual acceptance?**
   Answered structurally yes by the Inherited doctrine-dissent entry above — but whether this
   Catalog should ever name a small closed set of legitimate doctrine-enforcement patterns
   (as INST-04, Batch 10, left open for legitimacy/authority) is not decided here.
2. Whether `BeliefInstitution`'s own "no live caller yet" status should ever be closed by
   wiring it is a repository-realization and future-mapping question, not decided here — and,
   per the 2026-09-22 follow-up's own item 7, doing so would close only the institution-backed
   subset of BEL-01/the recurring significance gap, never the institution-free case, which
   would need its own, separate mechanism regardless.
3. **Added 2026-09-22 per external follow-up review.** What mechanism, if any, should ever
   realize BEL-01's own institution-free collective-belief permission (a folk myth/taboo no
   institution declares)? Not decided here — no candidate exists in this repository today.
