---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 11A (Places / Settlements / Territory)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Split rationale

Batch 11 (Places/Settlements/Territory/Culture/Belief), per its own instruction file's
explicit §1 size/split permission, is split into **Batch 11A** (this file — Places,
Settlements, Territory/Control: persistent spatial/political structure) and **Batch 11B**
(Culture, Collective Belief — see `culture-belief-batch-11b-review.md`). Both remain part of
the same Milestone C completion and the roadmap's own overall batch ordering is unchanged.

## Follow-up revision summary (2026-09-22)

A targeted focused-revision follow-up (`tmp/world-rule-batch-11-followup-ext-ai.md`) was
applied directly to the canonical files, not merely to this export. It did not redesign the
batch and added no Rules merely to increase count — Domain Rule counts for 11A are unchanged
(10). Outcome per item, per the follow-up's own explicit reporting requirement:

1. **Re-opened Settlement identity vs. Place identity — rule refinement + repository-
   classification softening.** SETT-01 revised to explicitly not assume "same Place" implies
   "same Settlement," particularly for total-abandonment-then-unrelated-resettlement; the
   original draft's own stronger "already confirmed sufficient" conclusion is retracted for
   that harder case. PT-S05 extended to evaluate Place-identity continuity and Settlement-
   identity continuity as two independent, both-unresolved questions.
2. **Normalized TERR-01 terminology — wording clarification.** One remaining bare "culture"
   reference (in the Purpose/scope paragraph) corrected to "cultural association," with an
   explicit terminology note distinguishing it from `culture.md`'s own fuller Culture concept.
3. **Re-verified the `owner_faction_id` CONFLICTING classification — repository-classification
   change.** Traced actual consumers directly. Retained CONFLICTING, narrowed to a
   directly-evidenced control-vs-sovereignty conflation (`PlaceState`'s own field comment:
   "Sovereignty override," plus taxation/suppression consumers reading the same field as
   control). Reclassified claim/cultural-association/residence, and TERR-03's own overall
   finding, from CONFLICTING to MISSING/INCOMPLETE — these concepts were never attempted at
   all, so nothing is being actively collapsed. TERR-01/TERR-03's own target-semantic text is
   unchanged; only repository-realization classification changed.
8. **Cross-batch consistency re-confirmed** — see `culture-belief-batch-11b-review.md`'s own
   follow-up summary for the full checklist (items 4–7 below belong to Batch 11B).

Net effect on 11A's own counts: genuine Domain Rules **unchanged at 10**; Inherited entries
**unchanged at 4**; Scope Boundaries **unchanged at 4**; total catalog entries **unchanged at
18**; scenario count **unchanged at 14** (PT-S04/S05/S06/S07/S08/S14 extended in place, no new
IDs).

## Standing direction applied (`tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification records
realization only, never delivery priority. Owner-attention decisions are framed as design
semantics; storage/data-shape questions live only under Implementation Candidates —
Non-Binding.

## Batch scope

The first half of the eighth domain-facing batch — how a location becomes a persistent Place,
how settlements grow/decline/transform, and what it means for land to be claimed, controlled,
governed, occupied, owned, or culturally associated. Three rule families: Places,
Settlements, Territory/Control. Files live under `places-culture/`. No target Rule count was
set.

## Canonical files included

- `places-culture/places.md` (PLACE-01–03)
- `places-culture/settlements.md` (SETT-01–03)
- `places-culture/territory-control.md` (TERR-01, TERR-02, TERR-03, TERR-05)
- `scenarios/places-territory-batch-11a.md` (PT-S01–S14, six extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 18
total catalog entries break down as:

- **10 genuine Domain Rules**: PLACE-01, PLACE-02 (revised), PLACE-03; SETT-01 (revised),
  SETT-02, SETT-03; TERR-01, TERR-02, TERR-03, TERR-05.
- **4 Inherited/Applied Foundational Rules**: in `places.md` — recognition of another
  subject's own attributed significance requires an information path (PERC-01/KNOW-01,
  Batch 06; Batch 09's reputation-reach entry); in `settlements.md` — settlement population
  aggregate ≠ individual (ECOL-01/02, Batch 05); in `territory-control.md` — territorial
  authority/power/legitimacy distinctness (INST-03, Batch 10), jurisdiction's territorial
  basis is one scope among several, resolving Batch 10's own deferred integration (LAW-03,
  Batch 10).
- **4 Scope/Deferred Boundaries**: concrete place-transformation catalog (`places.md`);
  concrete settlement-tier/service/institution catalog (`settlements.md`); border/boundary
  geometry detail, concrete territorial-claim-resolution-mechanism catalog
  (`territory-control.md`).

**Genuine new-Rule count for this sub-batch: 10 (unchanged).** **Inherited/reused foundation
count: 4 entries (unchanged)**, citing PERC-01/KNOW-01 (Batch 06), ECOL-01/02 (Batch 05),
INST-03/LAW-03 (Batch 10), and Batch 09's own reputation-reach entry.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PLACE-01 | Domain Rule | Place ≠ Coordinate/Region/Settlement/Owner/Occupant | First-class identity persisting through declared continuity. | Accepted — REQUIRED |
| PLACE-02 | Domain Rule | Significance Is Always Attributed, Never Intrinsic or Universal | Reworded 2026-09-22: perspective-scoped; multiple divergent attributions coexist. | Accepted (revised) |
| PLACE-03 | Domain Rule | Place Transformation Continuity Is Never Assumed by Default | Domain refinement of ID-03/ID-06/TRANS for Places. | Accepted — REQUIRED |
| SETT-01 | Domain Rule | Settlement = Place + Population, ≠ Five Adjacent Concepts | Softened 2026-09-22: does not assume Settlement identity = Place identity in every case. | Accepted (revised) |
| SETT-02 | Domain Rule | Settlement Growth/Decline Requires a Real Causal Path | No bare incrementing counter. | Accepted — REQUIRED |
| SETT-03 | Domain Rule | Settlement Transformation Is Not One Universal Progression | Each case declares what changes/persists. | Accepted — REQUIRED |
| TERR-01 | Domain Rule | Claim/Control/Jurisdiction/Ownership/Occupation/Cultural-Association/Residence Are Seven Distinct Facts | None collapses into one owner field. | Accepted — REQUIRED |
| TERR-02 | Domain Rule | Territorial Control Requires a Declared Causal Basis | Presence/reach/capability/enforcement/access/connectivity/compliance. | Accepted — REQUIRED |
| TERR-03 | Domain Rule | Claim ≠ Control; Contested Cases Must Remain Representable | No collapsing to one winner. | Accepted — REQUIRED |
| TERR-05 | Domain Rule | Place-Territory Containment/Association ≠ Current Controller | Territory ≠ settlement/region geometry. | Accepted — REQUIRED |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Recognition of another subject's own attributed significance requires an information path | PERC-01, KNOW-01 (Batch 06); reputation-reach entry (Batch 09) | `places.md` |
| Settlement population aggregate ≠ individual | ECOL-01, ECOL-02 (Batch 05) | `settlements.md` |
| Territorial authority/power/legitimacy distinctness | INST-03 (Batch 10) | `territory-control.md` |
| Jurisdiction's territorial basis is one scope among several | LAW-03 (Batch 10) — resolves its own deferred integration | `territory-control.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| PT-S01 | Same Place, New Name | rename after conquest, identity persists | Places | Covered |
| PT-S02 | Same Location, New Place (counter) | temple destroyed, unrelated settlement later | Places | Revealed gap |
| PT-S03 | Village Becomes Town | population/activity change, identity persists | Settlements | Partial |
| PT-S04 | Town Becomes Ruin | war/disaster, place persists | Places, Settlements | Covered (identity half) |
| PT-S05 | Abandoned and Resettled / Place-vs-Settlement Discontinuity | continuity must be determined for Place AND Settlement independently | Places, Settlements | Revealed gap (both questions) |
| PT-S06 | Claim Without Control | claim persists, no presence/reach | Territory | Revealed gap (reclassified) |
| PT-S07 | Control Without Recognized Claim | occupation, no legitimacy | Territory | Revealed gap (reclassified) |
| PT-S08 | Contested Territory | claim/control/recognition diverge three ways | Territory | Revealed gap (reclassified) |
| PT-S09 | Jurisdiction Without Ownership | law applies, doesn't own every property | Territory (inherited) | Revealed gap |
| PT-S10 | Ownership Without Sovereignty | estate owner, no political jurisdiction | Territory | Covered |
| PT-S11 | Migration Changes Settlement | population flow → settlement state | Settlements | Revealed gap |
| PT-S12 | Settlement Growth Without a Level | causal growth, no numeric field required | Settlements | Revealed gap (permission coherent) |
| PT-S13 | Settlement Level With No Consumer (counter) | tier increases, nothing changes | Settlements | Blocked |
| PT-S14 | Ordinary Place Becomes Historically Significant (flagship) | event → attribution → recognition → changed reaction | Places | Revealed gap |

## Coverage Summary

**Places**
- first-class identity, distinct from coordinate/region/owner/occupant — PT-S01, PT-S02
- transformation continuity is never assumed by default — PT-S04, PT-S05
- attribution-relative significance (flagship) — PT-S14

**Settlements**
- settlement = Place + population, distinct from five adjacent concepts; identity is not
  assumed to equal Place identity in every case — PT-S03, PT-S05, PT-S11
- growth/decline requires real causal path, no bare counter — PT-S11, PT-S12, PT-S13
- transformation is not one universal progression — PT-S03, PT-S04

**Territory/Control**
- seven distinct territorial facts, none collapsing to one field — PT-S06, PT-S07, PT-S08, PT-S10
- control requires a declared causal basis — PT-S06, PT-S07
- claim ≠ control, contested cases representable — PT-S06, PT-S07, PT-S08
- jurisdiction is one declared scope among several — PT-S09

## Deferred Semantics

- Concrete place-transformation continuity catalog — `places.md`.
- Concrete settlement-tier/service/institution catalog — `settlements.md`.
- Border/boundary geometry detail; concrete territorial-claim-resolution-mechanism catalog —
  `territory-control.md`.

## Cross-domain findings

- Places ↔ Identity (Foundational): PLACE-01/03 are the Place-specific instance of ID-03/
  ID-06/TRANS's own identity-through-transformation discipline.
- Places ↔ Collective Belief (11B): PLACE-02 directly reconciled with `collective-belief.md`'s
  BEL-03 — both now state significance/sacredness as attribution-relative, never intrinsic.
- Places ↔ Capability/Progression (Batch 07), Lineage/Descent (Batch 09), Organizations
  (Batch 10): PLACE-02/PT-S14 confirm the recurring "ordinary subject → historically
  significant, recognized by specific others" gap now at a fourth scale.
- Settlements ↔ Organizations (Batch 10): SETT-01's persistence-through-turnover and
  multi-way-distinctness pattern directly parallels ORG-01/ORG-02, now with an explicit
  carve-out for the total-abandonment-then-resettlement case.
- Territory ↔ Organizations/Institutions/Politics/Law (Batch 10): TERR-01/TERR-03 directly
  parallel INST-03's non-collapsing multi-fact discipline; the jurisdiction Inherited entry
  directly resolves LAW-03's own deferred territorial-jurisdiction integration.
- Territory ↔ Objects/Ownership (Batch 08): TERR-01 confirms property ownership is already
  structurally separate from territorial `owner_id`.

**Explicit call-out — genuine Domain Rule count:** **10 (unchanged by this follow-up).**

**Explicit call-out — Place vs. Region vs. Settlement semantics:** **Kept distinct as target
concepts.** `PlaceState` and `RegionState` are already structurally separate; Settlement is a
specialized `PlaceKind` (`CITY`) for the ordinary-turnover case — but this follow-up
explicitly withdraws the claim that this collapse is *definitively* the correct shape for the
total-abandonment-then-resettlement case, which remains an open design question (SETT-01's
own carried-forward Open Question).

**Explicit call-out — whether Places have persistent identity/history:** **Identity: yes,
confirmed by construction** (`place_id` stable across `kind` changes) **for the one realized
transformation case; untested for total abandonment/resettlement.** **History/significance as
its own tracked, attributed fact: no — confirmed MISSING** (PLACE-02).

**Explicit call-out — whether settlement growth/decline follows real causal paths:** **No —
confirmed MISSING**, and the migration input this chain depends on is also confirmed
MISSING (SETT-02, PT-S11/S12).

**Explicit call-out — claim vs. control vs. jurisdiction vs. ownership:** **Confirmed
semantically distinct as target concepts (TERR-01); repository realization is mixed, not
uniformly CONFLICTING (re-verified 2026-09-22).** `owner_faction_id` is directly evidenced as
CONFLICTING for a narrow control-vs-sovereignty conflation (its own field comment says
"Sovereignty override," and taxation/suppression consumers both read it as control) — but
claim, cultural association, and residence are MISSING, not CONFLICTING, since nothing
anywhere attempts to represent them at all.

**Explicit call-out — whether territory can be contested:** **Semantically yes (TERR-03);
repository realization is MISSING, not CONFLICTING (reclassified 2026-09-22)** — the claim
concept this Rule's own contested-case requires was never attempted, so nothing is being
actively collapsed; a real structural caveat remains that the single-field shape would need
addressing, not merely supplementing, if a claim concept were ever added.

**Explicit call-out — whether territorial semantics integrate cleanly with Batch 10 authority/
law:** **Yes, cleanly, by direct reuse rather than new content** — INST-03's own authority/
power/legitimacy distinctness and LAW-03's own declared-scope permission both apply to
territorial subject matter unchanged, requiring no refinement.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**CONFLICTING (1 finding, narrowed and re-evidenced 2026-09-22):**
1. `owner_faction_id` is currently, actively read as the authoritative representation of at
   least **control** (`TownResolutionSystem`'s tax pass, `region.suppression_active`'s combat
   penalty) and **sovereignty** (`PlaceState`'s own field comment: "Sovereignty override")
   simultaneously — direct evidence of two distinct target concepts collapsed into one field
   by real, current consumers. This is narrower than the original draft's claim, which
   reasoned from the field's bare existence rather than traced consumers.

**MISSING/INCOMPLETE (7 findings; item 2 reclassified from CONFLICTING this follow-up):**
2. No separate claim, cultural-association, or residence field exists anywhere, and nothing
   reads `owner_faction_id` as any of the three — since none was ever attempted, this is a
   gap, not an active collapse (TERR-01/TERR-03, reclassified 2026-09-22).
3. No significance/historical-meaning field exists on `PlaceState` (PLACE-02).
4. No mechanism exists for retiring a `place_id` and assigning a genuinely new one at the same
   location, and (added this follow-up) no mechanism resolves whether a *settlement* founded
   after total abandonment is the same settlement or a new one (PT-S02, PT-S05).
5. No settlement transformation mechanism beyond the single realized CITY→RUIN case
   (SETT-03).
6. No settlement growth/decline causal mechanism exists (SETT-02).
7. No migration mechanism of any kind exists anywhere in this repository (`settlements.md`).
8. No territorial-claim-vs-control causal-basis mechanism was confirmed (TERR-02).

**UNKNOWN (1 finding):**
9. Whether `PlaceState.scale` is ever mutated during simulation, as opposed to only at
   world-compile time, was not exhaustively traced this batch (SETT-02, PT-S13).

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
10. This repository's own "settlement" concept is already collapsed into a `PlaceKind`
    (`CITY`) rather than a separate durable-state class — confirmed as a working shape for
    ordinary resident turnover, but **not confirmed as the correct shape for the
    total-abandonment-then-resettlement case**, per this follow-up's own re-opened SETT-01.

Key evidence, all confirmed by direct code/doc inspection: `src/core/state.py`
(`PlaceState`, `RegionState`, `PlaceKind`), `docs/plans/rpg_design_roadmap/
rpg_idea66_region_place_rebuild_plan.md`, `src/engine/town_resolution.py` (Batch 10 evidence,
reused), `docs/brainstorm/world-rules/institutions-politics/{roles-institutions,
law-enforcement}.md` (AUTH/INST/LAW families, reused directly).

## Owner-attention decisions (design semantics, per the standing direction)

- **Does settlement continuity, in the total-abandonment-then-unrelated-resettlement case,
  require its own independently representable identity/episode distinct from the underlying
  Place's own identity, or is a settlement genuinely nothing more than "a Place with
  population, whenever population exists"?** (Re-opened 2026-09-22 — see SETT-01.)
- Does Territory need its own authoritative relation model (a typed record set), or can it
  remain a derived projection over existing Region/Place/Faction facts once those facts are
  themselves richer?
- What is canonical vs. derived between Region, Place, and Settlement, once significance and
  growth content is eventually added?
- When does place transformation preserve identity, and when does it not — is there a
  semantic pattern beyond "decide case by case," or is case-by-case genuinely the correct
  target shape?
- What semantic state survives settlement abandonment, distinct from what a future
  resettlement mechanism would need to reconstruct?

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** territorial claim, control, jurisdiction, ownership, occupation, and
  cultural association are seven distinct, independently-representable facts, and contested/
  divergent cases must remain representable.
  **Current realization:** a single field, actively conflating control and sovereignty
  (CONFLICTING); claim, cultural association, and residence simply absent (MISSING).
  **Gap/mismatch:** the single-field shape means a future claim concept could not be added
  alongside control without addressing the same field, though no live conflict exists today.
  **Possible implementation direction:** a `TerritorialRelation`-shaped typed record
  (claimant/controller/kind/since-tick), potentially multiple per region.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** settlement growth/decline requires a real causal path from population/
  resource/safety/hazard conditions.
  **Current realization:** no such mechanism exists; `scale` appears static post-compile.
  **Possible implementation direction:** a scheduled settlement-state-update process
  paralleling `TownResolutionSystem`'s own tax/maintenance pass.
  **Implementation decision:** DEFERRED.
- **Target semantic:** individual and aggregate population movement (migration) connects
  pressure/opportunity to settlement, economic, and cultural consequence.
  **Current realization:** no migration mechanism of any kind exists.
  **Possible implementation direction:** a population-flow process reading regional push/pull
  factors.
  **Implementation decision:** DEFERRED.

## Candidate disposition

Ten Domain Rules were drafted across three families (3 Places, 3 Settlements, 4 Territory/
Control) — **all 10 accepted, 0 rejected, 0 split, 0 merged**, unchanged by this follow-up.
Two were refined in wording/scope (PLACE-02, SETT-01) without changing their own IDs. No
target rule count was set in advance. Four further entries remain Inherited/Applied
Foundational Rules and four remain Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11A (PLACES / SETTLEMENTS / TERRITORY) — PASS, READY TO FREEZE.**
>
> Target semantics are coherent. Repository realization is substantially incomplete for
> settlement growth, migration, and place/settlement significance, and CONFLICTING (narrowly,
> for control-vs-sovereignty) for territorial ownership; claim/cultural-association/residence
> are MISSING rather than actively collapsed. No implementation commitment is implied by this
> freeze.

All required artifacts exist and are current: three rule-family files (10 genuine Domain
Rules; 18 total catalog entries), one scenario file (14 scenarios, six extended in place per
this follow-up's own focused-revision items), this review export with all required sections
including Implementation Candidates — Non-Binding, and a shared local disposition report. No
target-semantic contradiction remains. This follow-up's own applicable items (1, 2, 3, and the
shared item 8 cross-batch check) were each resolved: Settlement identity was re-opened and
SETT-01 softened rather than left over-confident; TERR-01's terminology now consistently says
"cultural association"; the `owner_faction_id` classification was re-verified against actual
consumers and narrowed to a directly-evidenced control-vs-sovereignty conflation, with claim/
cultural-association/residence correctly reclassified MISSING.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review of this focused revision.
