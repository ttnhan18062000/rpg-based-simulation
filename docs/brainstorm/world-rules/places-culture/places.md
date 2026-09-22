---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Places

**Purpose/scope.** What makes a location a persistent Place — a first-class world subject with
its own identity, distinct from a bare coordinate, a Region, a Settlement, an owner, or an
occupant — and how a Place's own historical/cultural/social significance relates to the mere
fact that something happened there. Does not decide Settlement-specific semantics (see
`settlements.md`) or Territory (see `territory-control.md`).

**Standing direction (`tmp/world-rule-direction.md`).** Rule statements describe only target
world semantics; repository classification records realization only, never delivery priority.

**Status.** Batch 11A (Places/Settlements/Territory — split from Batch 11 per that batch's own
explicit size/split permission; Batch 11B, Culture/Collective Belief, is drafted separately),
first draft, per `tmp/world-rule-batch-11-ext-ai.md`.

---

## Domain Rules

## PLACE-01 — A Place is a first-class world subject with its own declared identity, distinct from coordinates, a Region, a Settlement, an owner, and an occupant; it may persist through renaming, ownership change, occupant change, damage, rebuilding, change of use, and political turnover where declared continuity semantics support it

> A location becomes a Place — rather than remaining mere terrain or a bare coordinate — when
> it acquires its own declared identity: something a domain can refer to, track history for,
> and reason about independently of exactly where it sits or who currently controls or occupies
> it. A Place is never identical to the Region containing it, to a Settlement that may occupy
> it, to its current owner/controller, or to its current occupants — each of these may change
> while the Place's own identity persists, where a domain's own declared continuity semantics
> support that persistence. Renaming a Place, by itself, never creates a new identity.

**Disposition: ACCEPT — REQUIRED for the distinctness; continuity through any specific
transformation is PERMITTED, domain-declared content, per §2/§3.** Passes the admission test:
no earlier Rule states this specific multi-way distinctness for a spatial subject — Batch 04's
own Space/Environment family addresses movement and spatial mechanics generally, not a
location's own persistent identity as a first-class subject.

**Repository evidence: SUPPORTED, by construction.** `PlaceState` (`src/core/state.py`,
"Idea 66 — Region/Place foundational rebuild") is a real, first-class subject with its own
`place_id`, structurally distinct from `RegionState` (a Region may contain zero or many
Places via `RegionState.places`) and from any specific settlement population. `PlaceState.kind`
(a `PlaceKind` — `CITY`/`CAMP`/`NEST`/`LAIR`/`RUIN`/`DUNGEON`/`LANDMARK`) can change while
`place_id` itself never does — `PlaceState.prior_kind`/`transformed_tick` explicitly record a
real transformation trail (a CITY destroyed into a RUIN keeps the same `place_id`), confirming
identity survives at least one real transformation case already. `owner_faction_id` on
`PlaceState` is its own field, confirmed structurally distinct from `region.owner_faction_id`
(explicitly documented as "a sovereignty override; defaults to the parent Region's") — a real,
if minimal, instance of ownership/controller changing independently of the Place's own
identity.

**Scenarios:** [PT-S01](../scenarios/places-territory-batch-11a.md#pt-s01) (same place, new
name), [PT-S02](../scenarios/places-territory-batch-11a.md#pt-s02) (same location, new place,
counter).

---

## PLACE-02 — A Place's own historical, social, cultural, or institutional significance is never an intrinsic, universal property of the Place; it is always attributed by some specific actor, group, culture, or institution, and different attributors may attribute different, even conflicting, significance to the same Place simultaneously

> An event occurring at a Place is one fact — distinct from, and never automatically producing,
> significance. Significance itself is a second, further-distinct kind of fact: it is always
> **attributed** by some specific actor, group, culture, or institution — it is never a bare,
> attributor-free property the Place simply *has*. "Is Place P significant?" therefore has no
> single, universal answer; the honest question is always "significant **to whom**?" Two
> distinct groups, cultures, or institutions may attribute different, or directly conflicting,
> significance to the identical Place at the same time — one regarding it as sacred, another as
> ordinary, another as something else entirely — and both attributions remain simultaneously
> real and representable, neither one "the" correct answer the other must yield to. A third,
> further-distinct fact is whether any *other* specific subject knows of, or recognizes, a
> given attribution at all — recognizing that group A attributes significance to P is itself
> distinct from independently attributing the same significance oneself, and from objective
> world truth (which remains its own, separate fact throughout — see also `collective-
> belief.md`'s own sacredness content, Inherited, originally drafted as BEL-03). No mechanism
> may propagate any one attribution globally, or treat it as universal recognition, without a
> real information/recognition path.

**Disposition: ACCEPT — REQUIRED; revised 2026-09-22 per external follow-up review to make
significance explicitly perspective-scoped/relational, reconciled directly with
`collective-belief.md`'s own sacredness content (Inherited, originally drafted as BEL-03).**
The original wording ("a Place subsequently becoming significant... is a second, distinct
fact") risked being read as though significance, once it existed, were a single intrinsic
property of the Place itself — real or not, but at most one value. The follow-up correctly
identified this as incompatible with culturally/religiously attributed significance
(collective-belief.md's own sacredness domain), where two different groups may legitimately
attribute different or conflicting significance to the same Place at once. This revision
replaces "the Place becoming significant" with "significance being attributed by a specific
actor/group/culture/institution," explicitly permitting multiple, simultaneous, non-
reconciled attributions — a relational (`significant-to`) reading rather than a universal-
boolean one. Passes the admission test unchanged: this remains the Place-specific instance of
the flagship "ordinary subject → historically significant subject" trajectory this Catalog has
now traced for individuals (Batch 07/09) and organizations (Batch 10), now correctly stated as
attribution-relative rather than intrinsic.

**Repository evidence: PARTIAL — the "event happened" and "identity persists" halves are real;
attribution, multi-attributor divergence, and recognition-respecting-information-reach are all
confirmed MISSING.** `PlaceState.prior_kind`/`transformed_tick` record that *something*
transformed the Place, but nothing resembling an attributed-significance record, historical
tag, or cultural-meaning field exists on `PlaceState` — no mechanism was found that marks a
Place as "significant-to Group A as the site of the Battle of X." Consequently, neither the
multi-attributor-divergence half (two groups holding different attributions at once) nor the
"does recognition respect information reach" half can be positively tested — there is no
attribution fact yet for either to be checked against.

**Scenarios:** [PT-S14](../scenarios/places-territory-batch-11a.md#pt-s14) (ordinary place
becomes historically significant, flagship).

---

## PLACE-03 — A Place undergoing a declared transformation preserves its identity by default; identity ends, is replaced, splits, or merges only where the transformation explicitly establishes that different identity semantics apply

> Whether a Place transformed by damage, rebuilding, change of use, growth, or long
> abandonment and resettlement remains the *same* Place, or becomes a *new* Place, is not a
> free, undirected case-by-case choice — it follows the same default this Catalog's own
> foundational identity/transformation Rules (ID-03, ID-06, and the TRANS family) already
> establish for any persisting subject: **identity continuity is the default outcome of a
> transformation of an existing subject**, and only an explicit declaration that the
> transformation ends, replaces, splits, or merges that identity displaces that default. A
> village growing into a town, a fort becoming a ruin, a place being renamed, or a structure
> being rebuilt may all preserve Place identity by this same default — changed Place state or
> kind is never automatically a new Place. The default may still be displaced by a real
> declared exception: an ancient temple destroyed, followed centuries later by an entirely
> unrelated settlement built at the same coordinates, may legitimately establish a new Place
> identity rather than continuing the old one. Same coordinates never automatically means the
> same Place either way — the default concerns identity *continuity through a transformation
> of an existing Place*, not bare spatial coincidence with no transformation relationship at
> all.

**Disposition: ACCEPT — REQUIRED for the default-continuity requirement and for the
exception needing explicit declaration; corrected 2026-09-22 per external follow-up
review.** The original wording ("no single universal answer... not assumed continuous or
discontinuous by default") incorrectly presented Place transformation as having no default at
all, decided fresh case by case — this conflicts with the already-established foundational
principle (ID-03/ID-06/TRANS) that identity continuity is itself the default outcome for a
transformation of an *existing* subject, with an identity-ending/replacement case being the
declared exception, not a coin-flip alternative. This correction aligns PLACE-03 with that
default rather than contradicting it. Passes the admission test unchanged: applying the
already-established default explicitly to Places, and stating that "same coordinates" alone
(with no transformation relationship) is a different question from continuity-through-
transformation, is the Place-specific content this Rule adds — per the batch instruction's own
explicit request to use ID-03/ID-06/TRANS-family semantics and add only genuinely
place-specific refinements.

**Repository evidence: PARTIAL, and now confirmed consistent with the corrected default
rather than merely one arbitrary choice among many.** `PlaceState.prior_kind`/
`transformed_tick`'s own CITY→RUIN transformation keeping the same `place_id` is exactly the
default-continuity outcome this Rule's own corrected wording requires, not an arbitrary
implicit choice — the repository's own real behavior matches the target default cleanly. No
mechanism was found for the declared-exception case (an unrelated resettlement establishing a
genuinely new Place identity at an old location) or for village→town/shrine→temple-style
growth transformations specifically, but neither is required to exist for this Rule's own
default to hold.

**Scenarios:** [PT-S03](../scenarios/places-territory-batch-11a.md#pt-s03) (village becomes
town, extended — transformation with default continuity), [PT-S04](../scenarios/places-territory-batch-11a.md#pt-s04)
(town becomes ruin), [PT-S05](../scenarios/places-territory-batch-11a.md#pt-s05) (abandoned
and resettled, extended — depopulated settlement).

---

## Inherited / Applied Foundational Rules

### Recognition of another subject's own attributed significance requires a real information/perception path, exactly as any other world fact requires

> That some actor/group/culture attributes significance to a Place existing as a real fact
> does not mean any other given subject knows of that attribution — a subject's own
> recognition of it requires the same declared observation/report/record path Perception/
> Knowledge already requires for any fact. (Updated 2026-09-22 per external follow-up review
> to match PLACE-02's own revised, attribution-relative framing — recognition is of a
> specific attribution, never of a bare, attributor-free significance fact.)

**Disposition: INHERITED — direct reuse of Batch 06's PERC-01/KNOW-01 and Batch 09's own
reputation-reach Inherited entry (`social-lineage/social-relations.md`), applied to place
significance specifically. No new claim beyond instantiating an already-settled boundary for
this kind of fact.**

**Repository evidence: MISSING, by absence of the underlying fact this entry would gate.**
Since no significance-tracking field exists on `PlaceState` (PLACE-02's own finding), there is
nothing yet for a recognition mechanism to gate correctly or to violate — this entry's own
target requirement remains coherent and stated in advance of any implementation, consistent
with the standing direction's own guidance that a Rule may be valid before any repository
realization exists to check it against.

**Scenarios:** none newly traced; the absence itself, cross-referenced from PLACE-02.

---

## Scope / Deferred Boundaries

### Concrete place-transformation continuity catalog

> This family states that Place transformation identity continuity is the default outcome,
> displaced only by an explicitly declared exception (PLACE-03), but does not design the
> concrete catalog of which specific transformations count as declared exceptions for every
> Place kind — implementation-level content, deferred per this family's own scope.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

- **SUPPORTED — Place is already a real, first-class subject distinct from Region.**
  `PlaceState`/`RegionState`'s own structural separation (Idea 66) confirms PLACE-01's own
  claim by construction.
- **Confirmed MISSING — no significance/historical-meaning field exists on `PlaceState`.** See
  PLACE-02 above. `prior_kind`/`transformed_tick` record *that* a transformation happened, not
  *why it mattered*.
- **A single-field ownership pattern, re-verified 2026-09-22 against actual consumers rather
  than the field's shape alone.** `PlaceState.owner_faction_id`/`RegionState.owner_faction_id`
  are confirmed CONFLICTING specifically for control-vs-sovereignty (both concepts are
  actively read from the same field by real consumers) and MISSING for claim/cultural-
  association/residence (never attempted at all, not collapsed) — the full, re-verified
  trace lives in `territory-control.md`'s own TERR-01/TERR-03, not duplicated here.

## Cross-domain links recorded here

- PLACE-01 → Identity (ID-03/ID-06, Foundational), History/Provenance (Foundational)
- PLACE-02 → History/Provenance (Foundational), Perception/Knowledge (Batch 06), and the same
  flagship pattern as Capability/Progression (Batch 07), Lineage/Descent (Batch 09),
  Organizations (Batch 10); directly reconciled with `collective-belief.md`'s own sacredness
  content (Inherited, originally BEL-03) per the 2026-09-22 follow-up's own item 6
- PLACE-03 → Identity (ID-03/ID-06, TRANS family, Foundational)
- Inherited recognition entry → Perception/Knowledge (PERC-01/KNOW-01, Batch 06), Social
  Relations (Batch 09's reputation-reach entry)

## Open questions carried forward

1. **What semantic facts make a Place's own significance distinct from a Settlement's own
   cultural state (see `settlements.md`, `places-culture/culture.md`)?** Not decided here.
2. Whether the CITY→RUIN transformation trail (`prior_kind`/`transformed_tick`) should ever be
   deepened into a fuller history log, or is intentionally kept as a single-hop trail, is not
   decided here — a repository-realization fact, not a Rule Catalog decision.
3. **Added 2026-09-22 per external follow-up review.** If a `significance`/`sacred`-style
   field is ever added to `PlaceState`, it could only be a derived/cached projection with
   explicit provenance and scope (which attributor, as of when) — never the canonical
   representation of a perspective-dependent attribution. The preferred semantic model is
   relational (`significant-to`, `sacred-to`, `recognized-as`), not a universal boolean. No
   concrete storage design is committed here; see `collective-belief.md`'s own Implementation
   Candidates for the fuller non-binding discussion.
