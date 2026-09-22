---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
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

**Repository evidence: PARTIAL, and a genuinely positive, real structural match.**
`BeliefInstitution`/`BeliefInstitutionCarryForward` (`src/domains/belief_institution/model.py`,
"idea 63, Belief Grows Around Real History") is a real, per-(clan, origin-event) collective
belief record, explicitly documented as "a genuinely third, population-scale concept" distinct
from the per-entity `BeliefEntry` (tactical belief) and `KnowledgeFact` (settled individual
knowledge) — confirming this Rule's own individual/collective distinctness by direct
construction, at the design-intent level. `belief_strength` is derived from a real Chronicle
event (the legendary subject's own fame), confirming collective belief grounded in real history
rather than fabricated from nothing. The gap: this mechanism is explicitly documented as having
"no live caller yet... built, not yet visible in play" — a real, well-shaped mechanism that
is currently INERT/OFF rather than CONFLICTING or fully SUPPORTED.

**Scenarios:** [CB-S07](../scenarios/culture-belief-batch-11b.md#cb-s07) (false shared
belief).

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

## BEL-03 — A place, object, or event may become sacred, revered, or culturally significant through shared cultural interpretation alone, without any supernatural transformation of the physical world; pilgrimage, ritual, avoidance, or defense may all follow from purely social/cultural meaning

> A location, object, or historical event acquiring sacred or deeply significant status is a
> social/cultural fact — a shared interpretation a population holds — and never requires any
> actual change to that location, object, or event's own physical or mechanical properties.
> Pilgrimage, ritual observance, avoidance, or defense of a sacred place are all legitimate
> consequences of purely cultural meaning, with no supernatural mechanism required to explain
> any of them.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this directly answers the
batch instruction's own §23 "Sacred/Significant Places" investigation and its explicit
"a place can become sacred without supernatural transformation" framing — genuinely new
content connecting Places (`places.md`'s PLACE-02), Culture (`culture.md`'s CULT-01), and this
family's own belief/interpretation content, none of which alone states that sacredness is
achievable through cultural interpretation without magic.

**Repository evidence: MISSING.** No mechanism was found that marks any Place, object, or
event as sacred/culturally significant, with or without a supernatural component — confirmed
via direct search (no "sacred"/"pilgrimage"/"shrine" terms anywhere in `src/`). This Rule's
own target semantics remain independently coherent, connecting three already-real
mechanisms (`PlaceState`, `CultureState`, `BeliefInstitution`) that simply have no bridge
between them yet.

**Scenarios:** [CB-S08](../scenarios/culture-belief-batch-11b.md#cb-s08).

---

## Inherited / Applied Foundational Rules

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

- **A genuinely positive, well-shaped finding, currently INERT/OFF.** `BeliefInstitution`
  (`src/domains/belief_institution/model.py`) is a real, already-designed collective-belief
  concept grounded in real history (Chronicle-derived fame), explicitly documented as a
  "genuinely third, population-scale concept" distinct from individual belief and knowledge —
  but has "no live caller yet." See BEL-01 above.
- **SUPPORTED, by absence — no content anywhere grants ritual/doctrine a real supernatural
  effect.** See BEL-02 above; the correct outcome, not a gap.
- **Confirmed MISSING — no sacred-place, doctrine-dissent, or cultural/religious-significance
  recognition mechanism exists.** See BEL-03 and the two Inherited entries above.

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** collective belief may exist and produce real behavior, grounded in
  real history, without requiring an institution to declare it (BEL-01).
  **Current realization:** `BeliefInstitution` is a real, well-shaped, but currently
  unconsumed ("no live caller yet") mechanism.
  **Gap/mismatch:** the mechanism exists but produces no downstream behavioral consequence.
  **Possible implementation direction:** wire a consumer that reads `belief_strength` to bias
  a clan's own decisions or reactions toward the origin event's own subject or descendants —
  potentially the same bridge that would close the recurring "ordinary individual → named
  recognition" gap this Catalog has now found at four scales (Batches 07/09/10/11A).
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** a place may become sacred through cultural interpretation alone
  (BEL-03).
  **Current realization:** no bridge exists between `PlaceState`, `CultureState`, and
  `BeliefInstitution`.
  **Possible implementation direction:** a declared "significance" or "sacred" tag on
  `PlaceState`, populated by a process reading real events and cultural/belief state, gated by
  the same information-reach discipline this family's own Inherited recognition entry
  requires.
  **Implementation decision:** DEFERRED.

## Cross-domain links recorded here

- BEL-01 → Perception/Knowledge (KNOW-01/02, Batch 06), Law/Enforcement (LAW-02, Batch 10 —
  the related but narrower institution-scoped analogue), Social Relations (Batch 09's
  correcting-information entry)
- BEL-02 → Authority (AUTH-04, Batch 02 — the same explicit-boundary-drawing pattern), Magic/
  Supernatural (Batch 12, deferred)
- BEL-03 → Places (`places.md`'s PLACE-02), Culture (`culture.md`'s CULT-01)
- Inherited doctrine-dissent entry → Organizations (ORG-02, Batch 10)
- Inherited recognition entry → Perception/Knowledge (Batch 06), Social Relations (Batch 09),
  Places (`places.md`)

## Open questions carried forward

1. **Can institutional doctrine count as collective belief without individual acceptance?**
   Answered structurally yes by the Inherited doctrine-dissent entry above — but whether this
   Catalog should ever name a small closed set of legitimate doctrine-enforcement patterns
   (as INST-04, Batch 10, left open for legitimacy/authority) is not decided here.
2. Whether `BeliefInstitution`'s own "no live caller yet" status should ever be closed by
   wiring it toward the recurring individual/organization/place significance gap this Catalog
   has now found at four scales is a repository-realization and future-mapping question, not
   decided here.
