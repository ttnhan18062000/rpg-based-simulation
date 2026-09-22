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
Settlements, Territory/Control) and **Batch 11B** (Culture, Collective Belief — see
`culture-belief-batch-11b-review.md`). The split is accepted and unchanged by either
follow-up review. Both remain part of the same Milestone C completion.

## Follow-up revision summary

Two successive targeted follow-up reviews were applied directly to the canonical files on
2026-09-22, neither redesigning the batch nor adding Rules merely to increase count. 11A's
own genuine Domain Rule count is **unchanged at 10** across both.

**First follow-up** (`tmp/world-rule-batch-11-followup-ext-ai.md`): re-opened Settlement
identity vs. Place identity (SETT-01 no longer assumed "same Place" implies "same
settlement"); fixed a stray bare "culture" reference in TERR-01's own prose to "cultural
association"; re-verified `owner_faction_id`'s CONFLICTING classification against actual
consumers, narrowing it to control-vs-sovereignty and reclassifying the contested-claim half
(TERR-03) to MISSING/INCOMPLETE.

**Second follow-up** (`tmp/world-rule-batch-11-followup-2-ext-ai.md`) corrected and extended
the first:

1. **Corrected PLACE-03 against foundational Identity — rule refinement.** The first draft's
   "no single universal answer, not assumed continuous or discontinuous by default" directly
   conflicted with the already-established foundational principle that identity continuity is
   itself the *default* outcome of a transformation, displaced only by a declared exception.
   PLACE-03 now states that default explicitly.
2. **Refined SETT-01 — rule refinement.** "Settlement = Place + Population" was too
   reductive; SETT-01 now defines a settlement as a Place carrying a declared settlement-level
   function/state, normally associated with population but not reducible to it, distinguishing
   active/depopulated/abandoned/resettled status values.
3. **Clarified Settlement vs. abandoned Place — rule refinement (new content, not merely
   wording).** SETT-01 now states the *default* relationship: settlement status may end/become
   dormant while the underlying Place's own identity persists by default (reusing corrected
   PLACE-03); whether a later resettlement reactivates or replaces settlement identity remains
   open, not given one universal answer.
4. **PLACE-02 preserved unchanged** — confirmed strong on re-inspection, no change.
5. **Refined TERR-01 wording — wording clarification.** Added explicit "materializing all
   seven relations is never required; existence of one never silently establishes another,"
   correcting an implication that every territory must carry all seven.
6. **Restored the contested-territory finding to CONFLICTING — repository classification
   correction.** The first follow-up's own reclassification of TERR-03 to MISSING/INCOMPLETE
   (reasoning that "claim" was never separately attempted) understated the conflict: the
   correct basis is that `owner_faction_id` is this repository's *sole* authoritative
   territorial-control slot, which structurally forecloses ever representing a diverging claim
   or contested state — this is an active architectural incompatibility, not a bare absence,
   and is properly CONFLICTING. Cultural association and residence remain MISSING (never
   attempted at all, with no comparable structural incompatibility).
7. **Added two probes — new/extended scenarios.** "Transformation With Default Continuity"
   (extended onto PT-S03) and "Depopulated Settlement" (extended onto PT-S05).

Net effect on 11A's own counts: genuine Domain Rules **unchanged at 10**; Inherited entries
**unchanged at 4**; Scope Boundaries **unchanged at 4**; total catalog entries **unchanged at
18**; scenario count **unchanged at 14** (PT-S03, PT-S05, PT-S06, PT-S07, PT-S08 each carry
extensions, no new IDs).

## Standing direction applied (`tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification records
realization only, never delivery priority.

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
- `scenarios/places-territory-batch-11a.md` (PT-S01–S14, five extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 18
total catalog entries break down as:

- **10 genuine Domain Rules**: PLACE-01, PLACE-02, PLACE-03 (corrected); SETT-01 (corrected),
  SETT-02, SETT-03; TERR-01 (clarified), TERR-02, TERR-03, TERR-05.
- **4 Inherited/Applied Foundational Rules**: in `places.md` — recognition of another
  subject's own attributed significance requires an information path (PERC-01/KNOW-01, Batch
  06; Batch 09's reputation-reach entry); in `settlements.md` — settlement population
  aggregate ≠ individual (ECOL-01/02, Batch 05); in `territory-control.md` — territorial
  authority/power/legitimacy distinctness (INST-03, Batch 10), jurisdiction's territorial
  basis is one scope among several, resolving Batch 10's own deferred integration (LAW-03,
  Batch 10).
- **4 Scope/Deferred Boundaries**: concrete place-transformation catalog (`places.md`);
  concrete settlement-tier/service/institution catalog (`settlements.md`); border/boundary
  geometry detail, concrete territorial-claim-resolution-mechanism catalog
  (`territory-control.md`).

**Genuine new-Rule count for this sub-batch: 10 (unchanged across both follow-ups).**
**Inherited/reused foundation count: 4 entries (unchanged)**, citing PERC-01/KNOW-01 (Batch
06), ECOL-01/02 (Batch 05), INST-03/LAW-03 (Batch 10), and Batch 09's own reputation-reach
entry.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PLACE-01 | Domain Rule | Place ≠ Coordinate/Region/Settlement/Owner/Occupant | First-class identity persisting through declared continuity. | Accepted — REQUIRED |
| PLACE-02 | Domain Rule | Significance Is Always Attributed, Never Intrinsic or Universal | Perspective-scoped; multiple divergent attributions coexist. | Accepted — REQUIRED |
| PLACE-03 | Domain Rule | Identity Continuity Is the Default Outcome of Transformation | Corrected 2026-09-22: default is continuity, not case-by-case; exception must be declared. | Accepted (corrected) |
| SETT-01 | Domain Rule | Settlement = Place + Declared Function/State, Not Reducible to Population | Corrected 2026-09-22: settlement status may end/dormant while Place identity persists by default. | Accepted (corrected) |
| SETT-02 | Domain Rule | Settlement Growth/Decline Requires a Real Causal Path | No bare incrementing counter. | Accepted — REQUIRED |
| SETT-03 | Domain Rule | Settlement Transformation Is Not One Universal Progression | Each case declares what changes/persists. | Accepted — REQUIRED |
| TERR-01 | Domain Rule | Claim/Control/Jurisdiction/Ownership/Occupation/Cultural-Association/Residence Are Distinct Relation Types | Clarified 2026-09-22: materialization of all seven is never required. | Accepted (clarified) |
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
| PT-S03 | Village Becomes Town / Transformation With Default Continuity | growth transformation, identity persists by default | Places, Settlements | Partial |
| PT-S04 | Town Becomes Ruin | war/disaster, place persists | Places, Settlements | Covered (identity half) |
| PT-S05 | Abandoned and Resettled / Place-vs-Settlement Discontinuity / Depopulated Settlement | continuity for Place AND Settlement independently; population reaches zero, status ends/dormant | Places, Settlements | Revealed gap (partial for the depopulation default) |
| PT-S06 | Claim Without Control | claim persists, no presence/reach | Territory | Revealed contradiction (restored) |
| PT-S07 | Control Without Recognized Claim | occupation, no legitimacy | Territory | Revealed contradiction (restored) |
| PT-S08 | Contested Territory | claim/control/recognition diverge three ways | Territory | Revealed contradiction (restored) |
| PT-S09 | Jurisdiction Without Ownership | law applies, doesn't own every property | Territory (inherited) | Revealed gap |
| PT-S10 | Ownership Without Sovereignty | estate owner, no political jurisdiction | Territory | Covered |
| PT-S11 | Migration Changes Settlement | population flow → settlement state | Settlements | Revealed gap |
| PT-S12 | Settlement Growth Without a Level | causal growth, no numeric field required | Settlements | Revealed gap (permission coherent) |
| PT-S13 | Settlement Level With No Consumer (counter) | tier increases, nothing changes | Settlements | Blocked |
| PT-S14 | Ordinary Place Becomes Historically Significant (flagship) | event → attribution → recognition → changed reaction | Places | Revealed gap |

## Coverage Summary

**Places**
- first-class identity, distinct from coordinate/region/owner/occupant — PT-S01, PT-S02
- identity continuity is the default outcome of transformation, exception must be declared —
  PT-S03, PT-S04, PT-S05
- attribution-relative significance (flagship) — PT-S14

**Settlements**
- settlement = Place + declared function/state, not reducible to population — PT-S03, PT-S11
- default relationship: settlement status may end/dormant while Place identity persists —
  PT-S05
- growth/decline requires real causal path, no bare counter — PT-S11, PT-S12, PT-S13
- transformation is not one universal progression — PT-S03, PT-S04

**Territory/Control**
- distinct relation types, materialization not required, none collapsing to one field —
  PT-S06, PT-S07, PT-S08, PT-S10
- control requires a declared causal basis — PT-S06, PT-S07
- claim ≠ control, contested cases representable — PT-S06, PT-S07, PT-S08 (all CONFLICTING)
- jurisdiction is one declared scope among several — PT-S09

## Deferred Semantics

- Concrete place-transformation exception catalog — `places.md`.
- Concrete settlement-tier/service/institution catalog — `settlements.md`.
- Border/boundary geometry detail; concrete territorial-claim-resolution-mechanism catalog —
  `territory-control.md`.

## Cross-domain findings

- Places ↔ Identity (Foundational): PLACE-01/03 are the Place-specific instance of ID-03/
  ID-06/TRANS's own identity-continuity-is-the-default discipline, now correctly aligned with
  it rather than contradicting it.
- Places ↔ Collective Belief (11B): PLACE-02 directly reconciled with `collective-belief.md`'s
  own sacredness content (Inherited, originally BEL-03) — both state significance/sacredness
  as attribution-relative, never intrinsic.
- Places ↔ Capability/Progression (Batch 07), Lineage/Descent (Batch 09), Organizations
  (Batch 10): PLACE-02/PT-S14 confirm the recurring "ordinary subject → historically
  significant, recognized by specific others" gap now at a fourth scale.
- Settlements ↔ Organizations (Batch 10): SETT-01's persistence-through-turnover pattern
  directly parallels ORG-01/ORG-02, now further refined with an explicit default relationship
  between settlement status and Place identity.
- Territory ↔ Organizations/Institutions/Politics/Law (Batch 10): TERR-01/TERR-03 directly
  parallel INST-03's non-collapsing multi-fact discipline; the jurisdiction Inherited entry
  directly resolves LAW-03's own deferred territorial-jurisdiction integration.
- Territory ↔ Objects/Ownership (Batch 08): TERR-01 confirms property ownership is already
  structurally separate from territorial `owner_id`.

**Explicit call-out — genuine Domain Rule count:** **10 (unchanged across both follow-ups).**

**Explicit call-out — Place vs. Region vs. Settlement semantics:** **Kept distinct as target
concepts.** `PlaceState` and `RegionState` are already structurally separate; Settlement is a
specialized `PlaceKind` (`CITY`) carrying its own declared function/state — the default
relationship between settlement status and Place identity is now stated explicitly (SETT-01):
status may end/dormant while Place identity persists.

**Explicit call-out — whether Places have persistent identity/history:** **Identity: yes,
confirmed by construction and now aligned with the correct default** (continuity is the
default outcome of transformation) **for the one realized transformation case.** **History/
significance as its own tracked, attributed fact: no — confirmed MISSING** (PLACE-02).

**Explicit call-out — whether settlement growth/decline follows real causal paths:** **No —
confirmed MISSING**, and the migration input this chain depends on is also confirmed
MISSING (SETT-02, PT-S11/S12).

**Explicit call-out — claim vs. control vs. jurisdiction vs. ownership:** **Confirmed
semantically distinct as target concepts (TERR-01, clarified — materialization of all seven
is never required); repository realization is CONFLICTING for control/sovereignty and for
contested-claim divergence (restored 2026-09-22 after an intermediate, incorrect downgrade),
MISSING for cultural association and residence specifically.**

**Explicit call-out — whether territory can be contested:** **Semantically yes (TERR-03);
repository realization is CONFLICTING** — `owner_faction_id`'s own current, active role as
the sole authoritative territorial-control slot structurally forecloses ever representing a
diverging claim or contested state, an active architectural incompatibility, not a bare
absence.

**Explicit call-out — whether territorial semantics integrate cleanly with Batch 10 authority/
law:** **Yes, cleanly, by direct reuse rather than new content** — INST-03's own authority/
power/legitimacy distinctness and LAW-03's own declared-scope permission both apply to
territorial subject matter unchanged, requiring no refinement.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**CONFLICTING (1 finding, spanning both the control/sovereignty conflation and the
contested-claim divergence — restored/confirmed by a second 2026-09-22 follow-up after an
intermediate downgrade):**
1. `owner_faction_id` is currently, actively read as the authoritative representation of both
   **control** (`TownResolutionSystem`'s tax pass, `region.suppression_active`'s combat
   penalty) and **sovereignty** (`PlaceState`'s own field comment: "Sovereignty override"),
   and this same active, singular role structurally forecloses ever representing a diverging
   claim or a genuinely contested territorial state — an active architectural incompatibility
   with TERR-01/TERR-03's own target requirements, not merely an absent feature.

**MISSING (6 findings):**
2. No separate cultural-association or residence field exists anywhere, and nothing reads
   `owner_faction_id` as either — unlike claim/contested-control, these are plain absences
   with no comparable structural incompatibility (TERR-01).
3. No significance/historical-meaning field exists on `PlaceState` (PLACE-02).
4. No mechanism exists for retiring a `place_id` and assigning a genuinely new one at the same
   location, and no mechanism resolves whether a *settlement* founded after total abandonment
   is the same settlement or a new one (PT-S02, PT-S05).
5. No settlement transformation mechanism beyond the single realized CITY→RUIN case
   (SETT-03), and no settlement-status field distinct from raw population presence exists at
   all (SETT-01).
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
    ordinary continuous habitation, but settlement *status* (as opposed to bare population
    presence) is not separately tracked, a narrower realization than SETT-01's own revised
    target.

Key evidence, all confirmed by direct code/doc inspection: `src/core/state.py`
(`PlaceState`, `RegionState`, `PlaceKind`), `docs/plans/rpg_design_roadmap/
rpg_idea66_region_place_rebuild_plan.md`, `src/engine/town_resolution.py` (Batch 10 evidence,
reused), `docs/brainstorm/world-rules/institutions-politics/{roles-institutions,
law-enforcement}.md` (AUTH/INST/LAW families, reused directly).

## Owner-attention decisions (design semantics, per the standing direction)

- Is Settlement's own *status* (active/dormant/abandoned/resettled) authoritative state or a
  derived relation over population/Place facts already tracked elsewhere?
- Does Territory need its own authoritative relation model (a typed record set), or can it
  remain a derived projection over existing Region/Place/Faction facts once those facts are
  themselves richer?
- What is canonical vs. derived between Region, Place, and Settlement, once significance and
  growth content is eventually added?
- When a resettlement follows total abandonment, does it reactivate the same settlement
  identity or establish a new one — is there a semantic pattern beyond "domain-declared," or
  is that genuinely the correct target shape?
- What semantic state survives settlement abandonment, distinct from what a future
  resettlement mechanism would need to reconstruct?

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** territorial claim, control, jurisdiction, ownership, occupation, and
  cultural association are distinct relation types, and contested/divergent cases must remain
  representable where a domain needs them.
  **Current realization:** a single field, actively conflating control and sovereignty and
  structurally foreclosing claim/contested-control divergence (CONFLICTING); cultural
  association and residence simply absent (MISSING).
  **Gap/mismatch:** the single-field shape means a future claim concept could not be added
  alongside control without restructuring, since the field's own current, active role already
  forecloses the divergence a claim concept would need.
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
Control) — **all 10 accepted, 0 rejected, 0 split, 0 merged**, unchanged by either follow-up.
Three were refined in wording/content (PLACE-03, SETT-01, TERR-01) without changing their own
IDs. No target rule count was set in advance. Four further entries remain Inherited/Applied
Foundational Rules and four remain Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11A (PLACES / SETTLEMENTS / TERRITORY) — PASS, READY TO FREEZE.**
>
> Milestone C domain semantics are coherent. Repository realization remains partial/
> conflicting in documented areas — settlement growth, migration, and place significance are
> substantially MISSING; territorial claim/control representation is CONFLICTING. No
> implementation commitment is implied by this freeze.

All required artifacts exist and are current: three rule-family files (10 genuine Domain
Rules; 18 total catalog entries), one scenario file (14 scenarios, five extended in place
across two successive follow-up reviews), this review export with all required sections
including Implementation Candidates — Non-Binding, and a shared local disposition report. No
target-semantic contradiction remains. Both follow-ups' own applicable items were resolved:
PLACE-03 corrected to align with the foundational identity-continuity default; SETT-01
corrected to define settlement by function/state rather than population alone, and to state
the default relationship between settlement status and Place identity; TERR-01 clarified to
not require universal materialization; the contested-territory CONFLICTING finding was
restored after an intermediate follow-up had incorrectly downgraded it; two adversarial probes
were added by extension.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review of this second focused revision.
