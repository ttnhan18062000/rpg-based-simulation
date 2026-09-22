---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Territory / Control

**Purpose/scope.** What it means for land or space to be claimed, controlled, governed,
occupied, owned, or culturally associated, and how these facts relate to Batch 10's own
authority/power/legitimacy triad and to Places. Directly resolves the territorial-jurisdiction
integration Batch 10 explicitly deferred here.

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 11A (Places/Settlements/Territory), first draft, per
`tmp/world-rule-batch-11-ext-ai.md`.

---

## Domain Rules

## TERR-01 — Territorial claim, de facto control, legal/institutional jurisdiction, property ownership, military occupation, cultural association, and residence are distinct relation types where a domain models them; none is required to be materialized for every territory, and the existence of one never silently establishes another

> A territorial **claim** (an assertion of right), **de facto control** (practical governance
> in fact), **jurisdiction** (legal/institutional applicability, see TERR-04), **property
> ownership** (a specific parcel's own owned-resource status, Batch 08/01), **military
> occupation**, **cultural association**, and **residence** are distinct relation types — where
> a domain models more than one of them for the same land or space, none is automatically
> implied or established by any other. A kingdom may claim a region a rival occupies
> militarily, while the local population culturally identifies with a third polity and a
> merchant owns one estate inside it — all simultaneously, none of them canceling any other.
> This Rule does not require every territory to materialize all seven relations; a domain may
> model as few as it needs. What it forbids is a single `owner_id`-shaped field silently
> standing in for several of these relations at once where a domain *does* need more than one
> of them to diverge — the important requirement is representability of divergence where the
> world actually uses those concepts, not universal materialization.

**Disposition: ACCEPT — REQUIRED for the distinctness and the non-collapsing requirement
where modeled; REQUIRED that materialization of any specific relation remain optional
(clarified 2026-09-22 per a second external follow-up review — the original wording risked
being read as requiring every territory to carry all seven relations at once).** Passes the
admission test: no earlier Rule states this specific relation-type distinctness for
territorial facts — Batch 10's own INST-03 established an analogous authority/capability/
power/legitimacy distinctness for institutional subjects, but territory's own claim/control/
jurisdiction/ownership/occupation/cultural-association/residence split is a genuinely
different, spatially-scoped fact pattern. Terminology note (2026-09-22 follow-up): this
family always says "cultural association" for the territorial relation, never bare "culture"
— the latter is reserved for `places-culture/culture.md`'s own, much fuller Culture concept
(CULT-01), and the two must never be read as the same fact.

**Repository evidence: CONFLICTING for control/sovereignty and for the contested-claim/
divergence case; MISSING for cultural association and residence specifically (re-verified
twice, 2026-09-22, tracing actual consumers and, on the second pass, the field's own
structural role rather than treating consumer-tracing alone as dispositive).**
`RegionState.owner_faction_id` and `PlaceState.owner_faction_id` are each exactly one field.
Checked directly: this single field **is currently, actively read as the authoritative
representation of at least two distinct target concepts at once** — `TownResolutionSystem`'s
tax/maintenance pass and `region.suppression_active`'s combat-penalty check both read it as
**de facto control** (who currently governs/taxes/militarily dominates this region), while
`PlaceState.owner_faction_id`'s own field comment explicitly calls it a **"Sovereignty
override"** — a third, higher-order legitimacy-adjacent concept named in the code's own
documentation, applied to the identical field. Three different consumers treating one field
as control, taxation-authority, and sovereignty simultaneously is direct, checked evidence of
an active collapse between at least those concepts — **CONFLICTING**. This same finding also
resolves TERR-03's own contested-territory case, not merely a separate MISSING gap: because
this one field *is* the sole authoritative slot this repository currently uses for
territorial control/sovereignty, it structurally forecloses ever representing a diverging
claim or a contested state without conflating it with, or overwriting, that same
authoritative control value — the conflict is not merely that "claim" was never attempted, but
that the field's own current, active role as the singular authoritative territorial-relation
slot is itself incompatible with the divergence TERR-01/TERR-03 require wherever a domain
needs it. This is retained/restored as **CONFLICTING**, per a second external follow-up
review correcting an intermediate 2026-09-22 revision that had reclassified it to MISSING/
INCOMPLETE on the narrower reasoning that "claim" alone was never attempted — that reasoning
understated the conflict: the issue is not only that claim is absent, but that the field's own
active, authoritative role forecloses ever adding it without restructuring. By contrast,
**cultural association** and **residence** remain **MISSING**, not CONFLICTING: nothing
anywhere reads or writes `owner_faction_id` *as* either of these two, and neither is
functionally served by the same "sole authoritative control slot" role claim and contested-
control are — they are simply absent, with no structural incompatibility to point to beyond
absence itself. No implementation decision follows from this classification during this
phase, per the follow-up's own explicit reminder. Property ownership (Batch 08's own
`OWN-01`/`PROP-01`) remains confirmed structurally separate already — an entity's own
`inventory`/a building's own ownership is never the same field as `owner_faction_id`.

**Scenarios:** [PT-S06](../scenarios/places-territory-batch-11a.md#pt-s06) (claim without
control), [PT-S07](../scenarios/places-territory-batch-11a.md#pt-s07) (control without
recognized claim), [PT-S08](../scenarios/places-territory-batch-11a.md#pt-s08) (contested
territory), [PT-S09](../scenarios/places-territory-batch-11a.md#pt-s09) (jurisdiction without
ownership), [PT-S10](../scenarios/places-territory-batch-11a.md#pt-s10) (ownership without
sovereignty).

---

## TERR-02 — Territorial control is real only through a declared causal requirement — presence, administrative reach, military capability, institutional enforcement, resource access, connectivity, or local compliance — and may be partial, contested, intermittent, or domain-specific; a bare ownership-field assignment never by itself constitutes real control

> Control over territory is never established merely by an assignment (`faction.owner_id =
> region`) — it requires a real, declared causal basis: physical presence, administrative
> reach, military capability, institutional enforcement capacity, resource access, transport/
> connectivity, or local compliance. No domain is required to check every one of these for
> every case; control may legitimately be partial, contested, intermittent, or specific to one
> of these bases without the others (a kingdom might control taxation but not military
> security in the same region).

**Disposition: ACCEPT — REQUIRED for the causal-basis requirement; which specific bases apply
in any given case is PERMITTED, domain-declared content.** Passes the admission test: this is
the territorial-control-specific instance of the already-established causal-requirement
pattern (CAUSE-01, Foundational; Batch 10's own ORG-03/POL family), naming the *specific*
candidate causal bases for territorial control, which no earlier Rule states.

**Repository evidence: PARTIAL.** `region.owner_faction_id` gates real, causally-consequential
effects (tax collection, `suppression_active` combat penalties for non-controlling-faction
entities, `region_trauma`/pricing) — confirmed control is not entirely inert once assigned, it
does drive real downstream mechanics. But the *assignment itself* was not confirmed to trace to
any of this Rule's own named causal bases (presence, reach, capability, enforcement, access,
connectivity, compliance) — whether `owner_faction_id` is set through a real conquest/
presence-tracking mechanism or through a more direct world-compile/event assignment was not
exhaustively traced this batch.

**Scenarios:** [PT-S06](../scenarios/places-territory-batch-11a.md#pt-s06),
[PT-S07](../scenarios/places-territory-batch-11a.md#pt-s07).

---

## TERR-03 — A territorial claim may exist without control, and control may exist without a recognized claim; multiple actors may simultaneously claim, control, or culturally associate with the same territory; canonical territorial facts may be represented as several independent, possibly-conflicting relations rather than one winner field

> Claim and control (TERR-01/TERR-02) are never required to agree. A polity may validly claim
> land it cannot currently control; another actor may exercise real practical control with no
> recognized legitimate claim at all. Where more than one actor claims, controls, or culturally
> associates with the same territory simultaneously, this is not an error state requiring
> resolution to one winner — it is a legitimate, representable world condition, and a domain
> may model it as several separate, coexisting relations rather than collapsing to a single
> "current sovereign" field.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is the direct, necessary
consequence of TERR-01's own seven-way split (claim ≠ control is the specific pairwise
instance the batch instruction's own §11/§14 singles out as essential) — genuinely new content
in that it explicitly forbids collapsing contested cases to one winner, which TERR-01 alone
does not state.

**Repository evidence: CONFLICTING (restored 2026-09-22 by a second external follow-up
review, correcting an intermediate revision made the same day).** An intermediate revision
had reclassified this MISSING/INCOMPLETE, reasoning that since "claim" was never attempted as
its own concept, nothing was being actively collapsed. A second follow-up review corrected
this: the conflict is not contingent on "claim" having been separately attempted — it follows
from `owner_faction_id`'s own current, active role as the *sole* authoritative territorial-
control/sovereignty slot (TERR-01's own re-verified evidence: read as control by
`TownResolutionSystem`/`suppression_active`, and documented as "Sovereignty override").
Because this repository currently treats that one field as the complete authoritative answer
to "who controls this territory," it structurally forecloses ever representing a diverging
claim or a genuinely contested state (two-or-more simultaneous, non-reconciled relations)
without conflating the new relation with, or overwriting, the existing authoritative control
value — this is what CONFLICTING is for: an active, checked repository behavior that
contradicts the target requirement, not merely an absent feature. No implementation decision
follows from this classification during this phase. This item concerns repository-realization
classification only; TERR-01 and TERR-03's own target-semantic text is unchanged by either
revision.

**Scenarios:** [PT-S06](../scenarios/places-territory-batch-11a.md#pt-s06),
[PT-S07](../scenarios/places-territory-batch-11a.md#pt-s07),
[PT-S08](../scenarios/places-territory-batch-11a.md#pt-s08).

---

## TERR-05 — A Place may lie inside, span, or remain historically/culturally associated with a territory other than its current political controller; a territory may contain many Places; territory is never synonymous with settlement or region geometry

> A Place's own spatial containment within a territory, and its own historical/cultural
> association with a polity, are two further facts distinct from its current political
> controller (TERR-01) — a Place may remain culturally associated with a polity that no longer
> controls it, or may span more than one territory's own claimed boundary. A territory is
> never the same concept as a settlement (`settlements.md`'s SETT-01) or as Region geometry
> (`RegionState.bounds`) — a territory may contain many Places and outlive or precede any
> particular Region boundary a domain happens to draw.

**Disposition: ACCEPT — REQUIRED.** Passes the admission test: this is a distinct spatial-
containment/association claim from TERR-01's own fact-type split — TERR-01 is about which
*kinds* of relation exist between an actor and territory; this Rule is about how a *Place*
specifically relates to a *territory* geometrically and historically, a different axis the
batch instruction's own §9 investigates separately.

**Repository evidence: PARTIAL.** `RegionState.places` (a Region containing zero-or-many
Places, Idea 66 evidence) confirms one half — a territory-equivalent (`RegionState`) already
contains many Places structurally. Cultural/historical association surviving a change of
political control was not confirmed to exist as its own tracked fact — no mechanism was found
that lets a Place's own cultural association diverge from its current `owner_faction_id`.

**Scenarios:** none newly traced; reuses `RegionState.places`'s own structural evidence
directly.

---

## Inherited / Applied Foundational Rules

### Territorial authority, practical power, and legitimacy remain distinct facts, exactly as Batch 10 already establishes for institutional subjects generally

> Holding formal authority over a territory, having the practical power to enforce it, and
> being recognized as legitimate are three separate facts — none is substitutable for another
> merely because they correlate.

**Disposition: INHERITED — direct reuse of Batch 10's INST-03 (authority/capability/power/
legitimacy are distinct dimensions, correlated not substitutable), applied to territorial
authority specifically. No new claim beyond confirming the existing distinction extends to
territorial subject matter without alteration.**

**Repository evidence: SUPPORTED, reusing Batch 10's own evidence directly; no
territory-specific counter-evidence was found.** `FactionState.military_strength`
(Batch 10's own real "power" proxy) and `region.owner_faction_id` (a real, if collapsed,
control fact) remain structurally separate fields, confirming the distinction holds here too.

**Scenarios:** none newly traced.

### Jurisdiction's territorial basis is one declared scope among several — territory is never the universal jurisdiction basis; this directly resolves Batch 10's own deferred integration

> Territorial location is a legitimate basis for a law or institution's own declared scope
> (Batch 10's own LAW-03), but membership-based, role-based, contractual, event-specific, and
> temporal scopes remain equally legitimate, non-territorial bases. A law or institution
> applying outside territorial space entirely (a membership-based or contractual rule) is fully
> valid.

**Disposition: INHERITED — direct reuse of Batch 10's own LAW-03, which (after that batch's
own 2026-09-22 follow-up revision) already explicitly lists "territorial" as one declared
scope among several, alongside membership-based, role-based, contractual, event-specific,
temporal, and explicitly-global. This directly resolves the territorial-jurisdiction
integration Batch 10 deferred to this batch — on inspection, LAW-03's own revised text already
states exactly the content this batch's own §12 asked to investigate, so no new claim is
required.**

**Repository evidence: MISSING, reusing LAW-03's own evidence directly** — no in-world law/
jurisdiction mechanism exists at all (Batch 10's own LAW-01 finding), so no territorial
instance of it exists to check either. The one real, adjacent mechanism —
`region.suppression_active` combined with faction affiliation — remains a military-suppression
effect, not a law/jurisdiction mechanism, per Batch 10's own prior finding.

**Scenarios:** [PT-S09](../scenarios/places-territory-batch-11a.md#pt-s09).

---

## Scope / Deferred Boundaries

### Border/boundary geometry detail

> This family investigates border/boundary semantics only at the level needed for causal
> consequences (movement restriction, taxation, trade, law applicability, military response,
> migration, cultural contact) — detailed border geometry is not designed merely because
> boundaries conceptually exist, per the batch instruction's own explicit "a boundary matters
> where some process consumes it."

**Disposition: SCOPE BOUNDARY.**

### Concrete territorial-claim-resolution-mechanism catalog

> This family states that territory may be contested and that control requires a declared
> causal basis (TERR-02/03) but does not design a concrete mechanism for resolving competing
> claims (negotiation, conquest, arbitration, etc.) — deferred, per the batch instruction's own
> explicit "do not create a universal political-resolution mechanism" (reused from Batch 10).

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **CONFLICTING, directly evidenced and re-confirmed by a second 2026-09-22 follow-up
  review.** `owner_faction_id` is currently, actively read as the authoritative
  representation of at least **control** (tax collection, `suppression_active` combat
  penalties) and **sovereignty** (`PlaceState`'s own field comment: "Sovereignty override")
  simultaneously. Because this one field is this repository's *sole* authoritative
  territorial-control slot, it also structurally forecloses representing a diverging claim or
  a contested state (TERR-03) — an intermediate revision this same day had narrowed this to
  MISSING/INCOMPLETE for the contested-claim half specifically, reasoning that "claim" was
  never separately attempted; a second follow-up review corrected that as understating the
  conflict, since the field's own active, singular authoritative role is itself the
  incompatibility, not merely claim's own absence.
- **Confirmed MISSING, distinct from the above — no separate cultural-association or
  residence field exists anywhere, and nothing reads `owner_faction_id` as either.** Unlike
  claim/contested-control, these two concepts are not merely absent because a shared field
  forecloses them — nothing about `owner_faction_id`'s own current role serves, or claims to
  serve, either of them at all, so their absence is a plain gap, not a structural
  incompatibility.
- **Confirmed MISSING — no territorial-claim-vs-control causal-basis mechanism was confirmed**
  (whether `owner_faction_id` traces to presence/capability/enforcement/etc. was not
  exhaustively determined). See TERR-02 above.
- **A real, live, already-real jurisdiction-adjacent pattern, cross-referenced from Batch 10.**
  `region.suppression_active` combined with faction affiliation is a real location-plus-
  affiliation-scoped effect — but a military-suppression mechanic, not a law/jurisdiction
  mechanism, since no law concept exists (Batch 10's own LAW-01 finding, reused here).

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** territorial claim, control, jurisdiction, ownership, occupation, and
  cultural association are seven distinct, independently-representable facts (TERR-01), and
  contested/divergent cases must remain representable, not collapsed to one winner (TERR-03).
  **Current realization:** `owner_faction_id` is a single field, actively conflating control
  and sovereignty, and structurally foreclosing claim/contested-control divergence
  (CONFLICTING, re-confirmed by a second 2026-09-22 follow-up); cultural association and
  residence are simply absent (MISSING) — see the findings above.
  **Gap/mismatch:** the single-field shape means a future claim concept could not be added
  alongside control without restructuring, since the field's own current, active role
  already forecloses the divergence a claim concept would need to represent.
  **Possible implementation direction:** a `TerritorialRelation`-shaped typed record
  (claimant/controller/kind/since-tick), potentially multiple per region, replacing or
  supplementing the single `owner_faction_id` field.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.

## Cross-domain links recorded here

- TERR-01, TERR-03 → Organizations/Institutions/Politics/Law (Batch 10's own INST-03, the
  same non-collapsing multi-fact discipline); Objects/Ownership (Batch 08's OWN-01/PROP-01,
  confirmed already structurally separate from territorial `owner_id`)
- TERR-02 → Causality (CAUSE-01, Foundational), Organizations (Batch 10's ORG-03/POL family)
- TERR-05 → Places (`places.md`'s PLACE-01)
- Inherited authority/power/legitimacy entry → Roles/Institutions (INST-03, Batch 10)
- Inherited jurisdiction entry → Law/Enforcement (LAW-03, Batch 10 — the deferred integration
  this entry resolves)

## Open questions carried forward

1. **Does Territory need its own authoritative relation model (a typed record set), or can it
   remain a derived projection over existing Region/Place/Faction facts once those facts are
   themselves richer?** Not decided here — this is the design-semantic question underneath the
   Implementation Candidate above.
2. Whether `owner_faction_id`'s own assignment ever traces to a real causal basis (presence,
   conquest, etc.) in any world-generation or event-driven path was not exhaustively confirmed
   this batch — flagged for future investigation, not decided here.
