---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
---

# Review Export: Batch 11B (Culture / Collective Belief)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Split rationale

Batch 11 (Places/Settlements/Territory/Culture/Belief), per its own instruction file's
explicit §1 size/split permission, is split into Batch 11A (Places, Settlements, Territory/
Control — see `places-territory-batch-11a-review.md`) and **Batch 11B** (this file — Culture,
Collective Belief). Both remain part of the same Milestone C completion.

## Follow-up revision summary (2026-09-22)

A targeted focused-revision follow-up (`tmp/world-rule-batch-11-followup-ext-ai.md`) was
applied directly to the canonical files. It did not redesign the batch and added no Rules
merely to increase count — Domain Rule counts for 11B are unchanged (7). Outcome per item, per
the follow-up's own explicit reporting requirement:

4. **Refined CULT-02 wording — wording clarification.** "Culture consists of durable
   collective artifacts" reworded to "Culture may contain durable/shared practices, norms,
   rituals, institutions, records, symbols, or traditions" — a permitted, non-exhaustive
   description rather than an exhaustive definition. The prohibition on reducing culture to an
   average of individual belief, and the open-ended-content principle, are both unchanged.
5. **Fixed the CULT-03 implementation-candidate contradiction — repository classification/
   candidate change.** The withdrawn candidate proposed a single `cultural_affinity` scalar,
   which would itself have violated CULT-03's own distinctness requirement. Replaced with an
   explicit requirement that knowledge/practice/rejection/identification remain independently
   representable (e.g., separate typed fields/relations), no concrete schema committed.
   CB-S03 extended with a four-way-divergence clause designed to fail any single-scalar
   realization.
6. **Made Place significance and sacredness perspective-scoped — rule refinement.** PLACE-02
   (11A) and BEL-03 both reworded so significance/sacredness is always attributed by a
   specific actor/group/culture/institution, never an intrinsic or universal property;
   different attributors may hold different or conflicting attributions toward the same
   subject simultaneously. CB-S08 extended with a two-group divergent-attribution clause. The
   non-binding significance/sacred-tag candidate is now explicitly constrained: if retained at
   all, only as a derived/cached projection with explicit provenance/scope, never the
   canonical representation, with a relational (`significant-to`/`sacred-to`) model preferred
   over a universal boolean.
7. **Narrowed the role of `BeliefInstitution` — wording clarification + repository
   classification split.** The cross-domain observation and the Implementation Candidate
   proposing a `BeliefInstitution` consumer are both reworded to state it as a promising
   carrier for the institution-*backed* subset of BEL-01 only — not a universal significance
   mechanism, and not evidence for BEL-01's own institution-*free* permission. BEL-01's own
   repository evidence is split: PARTIAL (institution-backed, via `BeliefInstitution`) vs.
   MISSING (institution-free — no candidate mechanism exists at all). CB-S07 extended with an
   explicit institution-free folk-belief clause.
8. **Cross-batch consistency re-run** — see the checklist recorded in
   `scenarios/culture-belief-batch-11b.md`'s own Cross-batch note; all ten boundaries the
   follow-up asked to verify were explicitly re-confirmed, with no new universal Significance
   system created.

Net effect on 11B's own counts: genuine Domain Rules **unchanged at 7**; Inherited entries
**unchanged at 2**; Scope Boundaries **unchanged at 3**; total catalog entries **unchanged at
12**; scenario count **unchanged at 10** (CB-S03/S07/S08 extended in place, no new IDs).

## Standing direction applied (`tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification records
realization only, never delivery priority.

## Batch scope

The second half of the eighth domain-facing batch — what culture is (where modeled), how it
relates to individual belief and adjacent concepts, and how collective/socially-organized
belief relates to individual belief and to objective (and eventually supernatural) truth. Two
rule families: Culture, Collective Belief. Files live under `places-culture/`. No target
Rule count was set.

## Canonical files included

- `places-culture/culture.md` (CULT-01–04)
- `places-culture/collective-belief.md` (BEL-01–03)
- `scenarios/culture-belief-batch-11b.md` (CB-S01–S10, three extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 12
total catalog entries break down as:

- **7 genuine Domain Rules**: CULT-01, CULT-02 (reworded), CULT-03, CULT-04; BEL-01 (evidence
  split), BEL-02, BEL-03 (revised).
- **2 Inherited/Applied Foundational Rules**: in `collective-belief.md` — an institution's
  doctrine does not require member acceptance (ORG-02, Batch 10; this file's own BEL-01),
  recognition of another subject's own attributed cultural/religious/place significance
  requires an information path (PERC-01/KNOW-01, Batch 06; Batch 09's reputation-reach entry;
  `places.md`'s own analogous entry).
- **3 Scope/Deferred Boundaries**: concrete cultural-content catalog (`culture.md`); Magic/
  supernatural mechanism and truth, concrete religious-institution content catalog
  (`collective-belief.md`).

**Genuine new-Rule count for this sub-batch: 7 (unchanged).** **Inherited/reused foundation
count: 2 entries (unchanged)**, citing ORG-02 (Batch 10), PERC-01/KNOW-01 (Batch 06), and
cross-references to Batch 09's and `places.md`'s own analogous entries.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| CULT-01 | Domain Rule | Culture ≠ Belief/Law/Religion/Faction/Ethnicity/Settlement | No generic CultureScore; open-ended content. | Accepted — REQUIRED |
| CULT-02 | Domain Rule | Culture May Contain Durable Structures, ≠ Average Individual Belief | Reworded 2026-09-22: permitted, non-exhaustive description, not a definition. | Accepted (revised) |
| CULT-03 | Domain Rule | Cultural Participation/Knowledge/Practice/Rejection/Identification Are Distinct | Residence ≠ automatic cultural identity; real causal paths required. | Accepted — REQUIRED |
| CULT-04 | Domain Rule | Cultural Transmission/Change Requires a Declared Causal Channel | No assumed convergence or decay. | Accepted — REQUIRED |
| BEL-01 | Domain Rule | Collective Belief ≠ Individual Belief ≠ World Truth, No Institution Required | Evidence split 2026-09-22: institution-backed PARTIAL, institution-free MISSING. | Accepted (evidence refined) |
| BEL-02 | Domain Rule | Social/Religious Belief ≠ Supernatural Truth/Mechanism | Explicit Magic boundary, deferred to Batch 12. | Accepted — REQUIRED |
| BEL-03 | Domain Rule | Sacredness Is Always Attributed, Never Intrinsic or Universal | Reworded 2026-09-22: perspective-scoped, reconciled with PLACE-02. | Accepted (revised) |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| An institution's doctrine does not require member acceptance | ORG-02 (Batch 10); this file's own BEL-01 | `collective-belief.md` |
| Recognition of another subject's own attributed significance requires an information path | PERC-01, KNOW-01 (Batch 06); reputation-reach entry (Batch 09); `places.md`'s own entry | `collective-belief.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| CB-S01 | Culture Spans Border | border changes, same culture continues | Culture | Revealed gap |
| CB-S02 | One Territory, Multiple Cultures | polity contains distinct regional cultures | Culture | Covered |
| CB-S03 | Individual Rejects Local Culture / Four-Way Divergence | settlement norm exists, resident dissents; knowledge/practice/rejection/identification diverge independently | Culture | Revealed gap (permission coherent) |
| CB-S04 | Migrant Adopts Some Practices | migration → exposure → selected adoption | Culture | Revealed gap |
| CB-S05 | Cultural Contact Without Adoption (counter) | interaction → learning → no adoption | Culture | Revealed gap (permission coherent) |
| CB-S06 | Cultural Blending | contact → transmission → mixed practice | Culture | Revealed gap |
| CB-S07 | False Shared Belief / Institution-Free Folk Belief | false story → institutional action; folk belief with no institution at all | Collective Belief | Partial (institution-backed) + revealed gap (institution-free) |
| CB-S08 | Sacred Place Without Magic / Divergent Attribution | interpretation → sacred status; two groups attribute differently, both valid | Collective Belief | Revealed gap (permission coherent) |
| CB-S09 | Real Magic, No Cultural Recognition (boundary) | supernatural event unrecognized → no auto culture change | Collective Belief | Blocked |
| CB-S10 | Doctrine vs. Personal Belief | doctrine declared → member dissents → membership possible | Collective Belief (inherited) | Revealed gap |

## Coverage Summary

**Culture**
- culture ≠ five adjacent concepts, no generic score — CB-S01, CB-S02
- collective content may include durable structures, never reducible to average belief —
  CB-S03
- individual participation requires real causal path; knowledge/practice/rejection/
  identification remain independent — CB-S03, CB-S04
- transmission/change requires a declared channel, no assumed convergence/decay — CB-S05,
  CB-S06

**Collective Belief**
- collective belief ≠ individual belief ≠ truth, no institution required, false belief
  causes real behavior — CB-S07
- social belief ≠ supernatural truth — CB-S08, CB-S09
- sacredness is attribution-relative, achievable through cultural interpretation alone,
  divergent attributions coexist — CB-S08
- doctrine tolerates private dissent — CB-S10

## Deferred Semantics

- Concrete cultural-content catalog — `culture.md`.
- Magic/supernatural mechanism and truth (deferred to Batch 12); concrete
  religious-institution content catalog — `collective-belief.md`.

## Cross-domain findings

- Culture ↔ Perception/Knowledge (Batch 06), Organizations (Batch 10), Settlements (11A): the
  distinctness claims in CULT-01 each cite an already-established adjacent-concept boundary.
- Culture ↔ Ecology/Population (Batch 05), Social Relations (Batch 09): CULT-02/03 build on,
  but genuinely extend beyond, the already-established individual/aggregate distinction.
- Collective Belief ↔ Law/Enforcement (Batch 10): BEL-01 is confirmed genuinely broader than
  LAW-02 — the "no institution required" case is the specific new content — though its own
  repository realization is now correctly split: only the institution-backed half has any
  structural match at all.
- Collective Belief ↔ Places (11A): BEL-03 and PLACE-02 are now directly reconciled — both
  state significance/sacredness as attribution-relative, permitting simultaneous divergent
  attributions, per this follow-up's own item 6.
- Collective Belief ↔ Authority (Batch 02): BEL-02 draws its own family/future-domain
  boundary the same way AUTH-04 already drew the Authority/Reach boundary.

**Explicit call-out — genuine Domain Rule count:** **7 (unchanged by this follow-up).**

**Explicit call-out — whether culture is distinct from individual belief and politics:**
**Yes, as target semantics (CULT-01); the repository's own real "culture" system is
CONFLICTING with this target — a real, consumed, four-axis derived-tendency score, not the
richer concept this family means by the word.**

**Explicit call-out — whether cultural transmission has real causal paths:** **No —
confirmed MISSING at the individual/channel level; PARTIAL at the regional-drift level**
(event-driven, not channel-mediated).

**Explicit call-out — whether collective belief can be false without changing world truth:**
**Yes, semantically (BEL-01); repository realization is now split (re-verified 2026-09-22):
PARTIAL for the institution-backed case (`BeliefInstitution`, currently INERT/OFF), MISSING
for the institution-free case (no candidate mechanism at all).**

**Explicit call-out — whether political conquest automatically changes culture:** **No,
correctly — CULT-04's own explicit prohibition holds; re-confirmed 2026-09-22 that no
conquest-driven cultural-rewrite mechanism was found either way, consistent with a MISSING
repository realization rather than a violation.**

**Explicit call-out — whether place significance respects information propagation:**
**Semantically yes (the Inherited recognition entry, reused from `places.md`, now updated to
recognize a specific *attribution* rather than a bare fact); not exercisable, since no
significance/sacredness fact exists yet for it to gate.**

**Explicit call-out — whether the recurring individual/object/place significance pattern now
constitutes a clear cross-domain integration concern:** **Yes — but `BeliefInstitution` is not
presumed to be its universal solution (corrected 2026-09-22).** It is a promising carrier for
the institution-backed subset only; the institution-free case, and the attribution-relative
requirement PLACE-02/BEL-03 both now state, still need their own mechanism regardless of
whether `BeliefInstitution` is ever wired.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**CONFLICTING (1 finding):**
1. This repository's own "culture" system (`CultureState`, four fixed axes) is real, live,
   and consumed, but structurally mismatched to this family's own richer target concept — a
   naming/scope collision, not a simple gap. See CULT-01.

**INERT/OFF (1 finding, a genuinely positive structural match, narrowed 2026-09-22 to the
institution-backed case only):**
2. `BeliefInstitution` is a real, well-shaped, history-grounded, but institution-*backed-only*
   collective-belief mechanism (keyed to `clan_id`), with "no live caller yet." See BEL-01.

**MISSING (6 findings):**
3. The institution-*free* half of BEL-01's own permission (a folk myth/taboo no institution
   ever declares) has no candidate mechanism of any kind, distinct from item 2 above
   (reclassified/split 2026-09-22 — previously discussed only alongside the institution-backed
   case).
4. No individual-level cultural participation/adoption mechanism exists (CULT-03) — and
   (confirmed this follow-up) no realization anywhere reduces this to a single scalar either,
   since nothing exists at all to check against.
5. No channel-mediated cultural transmission/blending mechanism exists, beyond regional
   event-driven drift (CULT-04).
6. No sacred-place, attributed-significance, or multi-attributor-divergence mechanism exists
   at all (BEL-03, revised).
7. No institutional doctrine field distinct from `BeliefInstitution` exists (the doctrine-
   dissent Inherited entry).
8. No migration mechanism exists (cross-referenced from `settlements.md`, 11A) — the
   precondition for several culture scenarios (CB-S04).

Key evidence, all confirmed by direct code/doc inspection: `src/domains/culture/{model,
deriver,applicator,settlement_personality}.py`, `src/domains/belief_institution/{model,
deriver}.py`, `src/systems/strategic_systems/belief.py` (individual `BeliefEntry`, confirmed
distinct), `src/core/self_model.py` (`KnowledgeFact`, confirmed distinct).

## Owner-attention decisions (design semantics, per the standing direction)

- What distinguishes culture from population-wide reputation (Batch 09's own reputation
  representations)? Both are aggregate, region/population-scoped facts.
- Can institutional doctrine count as collective belief without individual acceptance? (Answered
  structurally yes by the Inherited doctrine-dissent entry — is this the right target shape, or
  should some institutions require acceptance?)
- Should `CultureState`'s own four fixed axes ever be reconciled with, renamed relative to, or
  kept fully separate from this family's own richer target concept?
- **What mechanism, if any, should realize BEL-01's own institution-free collective-belief
  case, distinct from and in addition to `BeliefInstitution`'s own institution-backed case?**
  (Sharpened 2026-09-22 — no longer conflated with the question of whether to wire
  `BeliefInstitution`, since that alone would not answer this.)

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** cultural knowledge, practice, rejection, and identification are each
  their own distinct individual-level fact, none collapsible into the others.
  **Current realization:** `CultureState` is read uniformly by every entity in a region; no
  individual-level field of any kind exists.
  **Possible implementation direction (corrected 2026-09-22 — a prior single-scalar
  `cultural_affinity` candidate is withdrawn as itself a violation of CULT-03):** whatever
  shape is chosen must keep knowledge/practice/rejection/identification independently
  representable — e.g., separate typed fields/relations per individual-per-culture, never one
  scalar. No concrete schema is committed here.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** collective belief may exist and produce real behavior, including with
  no institution declaring it (BEL-01).
  **Current realization:** `BeliefInstitution` is real and well-shaped but institution-backed
  only, with no live caller.
  **Possible implementation direction (narrowed 2026-09-22):** wiring a `BeliefInstitution`
  consumer would exercise only the institution-backed subset of BEL-01; the institution-free
  case would need a separate, distinct mechanism regardless.
  **Implementation decision:** DEFERRED.
- **Target semantic:** a place, object, or event may become sacred/significant through
  cultural interpretation alone, always attributed by a specific culture/group/institution,
  never a universal property (BEL-03, revised).
  **Current realization:** no bridge exists between `PlaceState`, `CultureState`, and
  `BeliefInstitution`.
  **Possible implementation direction (constrained 2026-09-22):** if retained at all, only as
  a derived/cached projection with explicit provenance/scope, never canonical — a relational
  model (`significant-to`, `sacred-to`, `recognized-as`) is preferred over a universal
  boolean/scalar.
  **Implementation decision:** DEFERRED.

## Candidate disposition

Seven Domain Rules were drafted across two families (4 Culture, 3 Collective Belief) — **all
7 accepted, 0 rejected, 0 split, 0 merged**, unchanged by this follow-up. Three were refined
in wording/scope (CULT-02, BEL-01's own evidence, BEL-03) without changing their own IDs. No
target rule count was set in advance. Two further entries remain Inherited/Applied
Foundational Rules and three remain Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11B (CULTURE / COLLECTIVE BELIEF) — PASS, READY TO FREEZE.**
>
> Target semantics are coherent. Repository realization ranges from a genuine naming/scope
> collision (culture) to a real but institution-backed-only, unconsumed structural match
> (collective belief) to substantially MISSING (individual cultural participation, sacred/
> attributed-significance mechanisms, migration-driven cultural change). No implementation
> commitment is implied by this freeze.

All required artifacts exist and are current: two rule-family files (7 genuine Domain Rules;
12 total catalog entries), one scenario file (10 scenarios, three extended in place per this
follow-up's own focused-revision items), this review export with all required sections
including Implementation Candidates — Non-Binding, and a shared local disposition report. No
target-semantic contradiction remains. This follow-up's own applicable items (4, 5, 6, 7, and
the shared item 8 cross-batch check) were each resolved: CULT-02 no longer over-equates
culture with artifacts; CULT-03's own implementation candidate no longer contradicts its own
Rule; PLACE-02/BEL-03 are now both attribution-relative and mutually reconciled;
`BeliefInstitution`'s role is correctly narrowed to the institution-backed subset of BEL-01,
with the institution-free case explicitly recorded as its own, separately-unrealized gap.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review of this focused revision.
