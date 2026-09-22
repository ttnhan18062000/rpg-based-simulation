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
(Culture, Collective Belief: shared social/cognitive structure — see
`culture-belief-batch-11b-review.md`). The split follows semantic coherence, not file size:
11A's own subject matter (a location's identity, a settlement's population, land's political
control) forms one coherent cluster building on Identity/Ownership/Authority; 11B's own
subject matter (shared practice, collective belief, religion) forms a distinct cluster
building on Perception/Knowledge/Agency. Both remain part of the same Milestone C completion
and the roadmap's own overall batch ordering is unchanged.

## Standing direction applied (`tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification records
realization only, never delivery priority. Owner-attention decisions are framed as design
semantics; storage/data-shape questions live only under Implementation Candidates —
Non-Binding.

## Batch scope

The first half of the eighth domain-facing batch — how a location becomes a persistent Place,
how settlements grow/decline/transform, and what it means for land to be claimed, controlled,
governed, occupied, owned, or culturally associated. Three rule families: Places,
Settlements, Territory/Control. Files live under `places-culture/`, per the batch
instruction's own directory suggestion. No target Rule count was set.

## Canonical files included

- `places-culture/places.md` (PLACE-01–03)
- `places-culture/settlements.md` (SETT-01–03)
- `places-culture/territory-control.md` (TERR-01, TERR-02, TERR-03, TERR-05)
- `scenarios/places-territory-batch-11a.md` (PT-S01–S14)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 18
total catalog entries break down as:

- **10 genuine Domain Rules**: PLACE-01, PLACE-02, PLACE-03; SETT-01, SETT-02, SETT-03;
  TERR-01, TERR-02, TERR-03, TERR-05.
- **4 Inherited/Applied Foundational Rules**: in `places.md` — recognition requires an
  information path (PERC-01/KNOW-01, Batch 06; Batch 09's reputation-reach entry); in
  `settlements.md` — settlement population aggregate ≠ individual (ECOL-01/02, Batch 05); in
  `territory-control.md` — territorial authority/power/legitimacy distinctness (INST-03,
  Batch 10), jurisdiction's territorial basis is one scope among several, resolving Batch 10's
  own deferred integration (LAW-03, Batch 10).
- **4 Scope/Deferred Boundaries**: concrete place-transformation catalog (`places.md`);
  concrete settlement-tier/service/institution catalog (`settlements.md`); border/boundary
  geometry detail, concrete territorial-claim-resolution-mechanism catalog
  (`territory-control.md`).

**Genuine new-Rule count for this sub-batch: 10.** **Inherited/reused foundation count: 4
entries**, citing PERC-01/KNOW-01 (Batch 06), ECOL-01/02 (Batch 05), INST-03/LAW-03 (Batch 10),
and Batch 09's own reputation-reach entry.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PLACE-01 | Domain Rule | Place ≠ Coordinate/Region/Settlement/Owner/Occupant | First-class identity persisting through declared continuity. | Accepted — REQUIRED |
| PLACE-02 | Domain Rule | Event-at-Place ≠ Place-Significance ≠ Universal Recognition | The Place-scale flagship significance chain. | Accepted — REQUIRED |
| PLACE-03 | Domain Rule | Place Transformation Continuity Is Never Assumed by Default | Domain refinement of ID-03/ID-06/TRANS for Places. | Accepted — REQUIRED |
| SETT-01 | Domain Rule | Settlement = Place + Population, ≠ Five Adjacent Concepts | Persists through resident turnover. | Accepted — REQUIRED |
| SETT-02 | Domain Rule | Settlement Growth/Decline Requires a Real Causal Path | No bare incrementing counter. | Accepted — REQUIRED |
| SETT-03 | Domain Rule | Settlement Transformation Is Not One Universal Progression | Each case declares what changes/persists. | Accepted — REQUIRED |
| TERR-01 | Domain Rule | Claim/Control/Jurisdiction/Ownership/Occupation/Culture/Residence Are Seven Distinct Facts | None collapses into one owner field. | Accepted — REQUIRED |
| TERR-02 | Domain Rule | Territorial Control Requires a Declared Causal Basis | Presence/reach/capability/enforcement/access/connectivity/compliance. | Accepted — REQUIRED |
| TERR-03 | Domain Rule | Claim ≠ Control; Contested Cases Must Remain Representable | No collapsing to one winner. | Accepted — REQUIRED |
| TERR-05 | Domain Rule | Place-Territory Containment/Association ≠ Current Controller | Territory ≠ settlement/region geometry. | Accepted — REQUIRED |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| Recognition of a Place's significance requires an information path | PERC-01, KNOW-01 (Batch 06); reputation-reach entry (Batch 09) | `places.md` |
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
| PT-S05 | Abandoned and Resettled | continuity must be determined | Places | Revealed gap |
| PT-S06 | Claim Without Control | claim persists, no presence/reach | Territory | Revealed contradiction |
| PT-S07 | Control Without Recognized Claim | occupation, no legitimacy | Territory | Revealed contradiction |
| PT-S08 | Contested Territory | claim/control/recognition diverge three ways | Territory | Revealed contradiction |
| PT-S09 | Jurisdiction Without Ownership | law applies, doesn't own every property | Territory (inherited) | Revealed gap |
| PT-S10 | Ownership Without Sovereignty | estate owner, no political jurisdiction | Territory | Covered |
| PT-S11 | Migration Changes Settlement | population flow → settlement state | Settlements | Revealed gap |
| PT-S12 | Settlement Growth Without a Level | causal growth, no numeric field required | Settlements | Revealed gap (permission coherent) |
| PT-S13 | Settlement Level With No Consumer (counter) | tier increases, nothing changes | Settlements | Blocked |
| PT-S14 | Ordinary Place Becomes Historically Significant (flagship) | event → recognition → changed reaction | Places | Revealed gap |

## Coverage Summary

**Places**
- first-class identity, distinct from coordinate/region/owner/occupant — PT-S01, PT-S02
- transformation continuity is never assumed by default — PT-S04, PT-S05
- event/significance/knowledge three-way split (flagship) — PT-S14

**Settlements**
- settlement = Place + population, distinct from five adjacent concepts — PT-S03, PT-S11
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
- Places ↔ Capability/Progression (Batch 07), Lineage/Descent (Batch 09), Organizations
  (Batch 10): PLACE-02/PT-S14 confirm the recurring "ordinary subject → historically
  significant, recognized by specific others" gap now at a fourth scale.
- Settlements ↔ Organizations (Batch 10): SETT-01's persistence-through-turnover and
  multi-way-distinctness pattern directly parallels ORG-01/ORG-02.
- Settlements ↔ Social Relations (Batch 09), Capability/Progression (Batch 07), Organizations
  (Batch 10): SETT-02 reuses the same "no default X, only declared causal paths" family
  (SOC-03, PROG-05, the reclassified open-instability entry).
- Territory ↔ Organizations/Institutions/Politics/Law (Batch 10): TERR-01/TERR-03 directly
  parallel INST-03's non-collapsing multi-fact discipline; the jurisdiction Inherited entry
  directly resolves LAW-03's own deferred territorial-jurisdiction integration.
- Territory ↔ Objects/Ownership (Batch 08): TERR-01 confirms property ownership is already
  structurally separate from territorial `owner_id`.

**Explicit call-out — genuine Domain Rule count:** **10.**

**Explicit call-out — Place vs. Region vs. Settlement semantics:** **Kept distinct as target
concepts.** `PlaceState` and `RegionState` are already structurally separate in the
repository; Settlement is confirmed to be, by design, a specialized `PlaceKind` (`CITY`)
rather than a fourth durable-state class — consistent with SETT-01's own explicit permission
that separate materialization is not required.

**Explicit call-out — whether Places have persistent identity/history:** **Identity: yes,
confirmed by construction** (`place_id` stable across `kind` changes). **History/
significance as its own tracked fact: no — confirmed MISSING** (PLACE-02).

**Explicit call-out — whether settlement growth/decline follows real causal paths:** **No —
confirmed MISSING**, and the migration input this chain depends on is also confirmed
MISSING (SETT-02, PT-S11/S12).

**Explicit call-out — claim vs. control vs. jurisdiction vs. ownership:** **Confirmed
semantically distinct as target concepts (TERR-01); confirmed CONFLICTING as a repository
realization** — `owner_faction_id`'s single-field shape actively forecloses representing
more than one of these diverging simultaneously.

**Explicit call-out — whether territory can be contested:** **Semantically yes (TERR-03);
repository realization is CONFLICTING, not merely MISSING** — the current data shape cannot
represent it at all, a stronger finding than an unrealized feature.

**Explicit call-out — whether territorial semantics integrate cleanly with Batch 10 authority/
law:** **Yes, cleanly, by direct reuse rather than new content** — INST-03's own authority/
power/legitimacy distinctness and LAW-03's own declared-scope permission both apply to
territorial subject matter unchanged, requiring no refinement.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**CONFLICTING (1 finding, this sub-batch's own single most significant):**
1. `region.owner_faction_id`/`PlaceState.owner_faction_id` are single nullable fields that
   actively foreclose representing contested claim/control — not merely unrealized, but a
   data shape incompatible with TERR-01/TERR-03's own target requirement.

**MISSING (6 findings):**
2. No significance/historical-meaning field exists on `PlaceState` (PLACE-02).
3. No mechanism exists for retiring a `place_id` and assigning a genuinely new one at the same
   location (PT-S02).
4. No settlement transformation mechanism beyond the single realized CITY→RUIN case
   (SETT-03).
5. No settlement growth/decline causal mechanism exists (SETT-02).
6. No migration mechanism of any kind exists anywhere in this repository (`settlements.md`).
7. No territorial-claim-vs-control causal-basis mechanism was confirmed; no separate claim/
   cultural-association/residence field exists at all (TERR-01/TERR-02).

**UNKNOWN (1 finding):**
8. Whether `PlaceState.scale` is ever mutated during simulation, as opposed to only at
   world-compile time, was not exhaustively traced this batch (SETT-02, PT-S13).

**A significant, notable finding, not itself CONFLICTING/INERT/MISSING but worth its own
category:**
9. This repository's own "settlement" concept is already collapsed into a `PlaceKind` (`CITY`)
   rather than a separate durable-state class — confirmed as the correct, permitted shape per
   SETT-01, not a gap.

Key evidence, all confirmed by direct code/doc inspection: `src/core/state.py`
(`PlaceState`, `RegionState`, `PlaceKind`), `docs/plans/rpg_design_roadmap/
rpg_idea66_region_place_rebuild_plan.md`, `src/engine/town_resolution.py` (Batch 10 evidence,
reused), `docs/brainstorm/world-rules/institutions-politics/{roles-institutions,
law-enforcement}.md` (AUTH/INST/LAW families, reused directly).

## Owner-attention decisions (design semantics, per the standing direction)

- Is Settlement a first-class persistent subject or a specialized Place? (Already answered
  by direct construction — specialized Place — but worth confirming this remains the intended
  target shape as richer settlement content is added.)
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
  **Current realization:** a single nullable `owner_faction_id` field per Region/Place.
  **Gap/mismatch:** the current shape actively forecloses the target requirement.
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
Control) — **all 10 accepted, 0 rejected, 0 split, 0 merged.** No target rule count was set in
advance. Four further entries were identified as Inherited/Applied Foundational Rules and four
as Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11A (PLACES / SETTLEMENTS / TERRITORY) READY FOR HIGH-LEVEL EXTERNAL REVIEW.**
>
> Target semantics are coherent. Repository realization is substantially incomplete for
> settlement growth, migration, and place significance, and actively CONFLICTING for
> contested territorial claim/control. No implementation commitment is implied by this
> review.

All required artifacts exist: three rule-family files (10 genuine Domain Rules; 18 total
catalog entries), one scenario file (14 scenarios covering every named seed scenario in the
batch instruction's own §32 Places/Settlements/Territory subset), this review export with all
required sections including Implementation Candidates — Non-Binding, and a shared local
disposition report. No contradiction was found against any prior batch's own Rules. This
sub-batch's own dominant finding is the CONFLICTING single-field territorial-ownership
pattern (TERR-01/03) — a stronger finding than the MISSING-dominated pattern most of Batch 10
showed, since here the current data shape actively forecloses the target requirement rather
than merely lacking it. The recurring "ordinary subject → historically significant,
recognized by name" gap (PLACE-02/PT-S14) is now confirmed at a fourth scale.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review.
