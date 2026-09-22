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
explicit §1 size/split permission, is split into Batch 11A (Places, Settlements,
Territory/Control — see `places-territory-batch-11a-review.md`) and **Batch 11B** (this file
— Culture, Collective Belief: shared social/cognitive structure). 11B's own subject matter
(shared practice, collective belief, religion) builds primarily on Perception/Knowledge/Agency
(Batch 06) and Organizations (Batch 10), a distinct semantic cluster from 11A's spatial/
political structure. Both remain part of the same Milestone C completion and the roadmap's own
overall batch ordering is unchanged.

## Standing direction applied (`tmp/world-rule-direction.md`)

Rule statements describe only target world semantics; repository classification records
realization only, never delivery priority.

## Batch scope

The second half of the eighth domain-facing batch — what culture is (where modeled), how it
relates to individual belief and adjacent concepts, and how collective/socially-organized
belief relates to individual belief and to objective (and eventually supernatural) truth. Two
rule families: Culture, Collective Belief. Files live under `places-culture/`, alongside
Batch 11A's own families. No target Rule count was set.

## Canonical files included

- `places-culture/culture.md` (CULT-01–04)
- `places-culture/collective-belief.md` (BEL-01–03)
- `scenarios/culture-belief-batch-11b.md` (CB-S01–S10)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 12
total catalog entries break down as:

- **7 genuine Domain Rules**: CULT-01, CULT-02, CULT-03, CULT-04; BEL-01, BEL-02, BEL-03.
- **2 Inherited/Applied Foundational Rules**: in `collective-belief.md` — an institution's
  doctrine does not require member acceptance (ORG-02, Batch 10; this file's own BEL-01),
  recognition of cultural/religious/place significance requires an information path
  (PERC-01/KNOW-01, Batch 06; Batch 09's reputation-reach entry; `places.md`'s own analogous
  entry).
- **3 Scope/Deferred Boundaries**: concrete cultural-content catalog (`culture.md`); Magic/
  supernatural mechanism and truth, concrete religious-institution content catalog
  (`collective-belief.md`).

**Genuine new-Rule count for this sub-batch: 7.** **Inherited/reused foundation count: 2
entries**, citing ORG-02 (Batch 10), PERC-01/KNOW-01 (Batch 06), and cross-references to
Batch 09's and `places.md`'s own analogous entries.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| CULT-01 | Domain Rule | Culture ≠ Belief/Law/Religion/Faction/Ethnicity/Settlement | No generic CultureScore; open-ended content. | Accepted — REQUIRED |
| CULT-02 | Domain Rule | Culture = Durable Artifacts, ≠ Average Individual Belief | Institutions/rituals/records persist beyond current belief distribution. | Accepted — REQUIRED |
| CULT-03 | Domain Rule | Cultural Participation/Knowledge/Practice/Rejection/Identification Are Distinct | Residence ≠ automatic cultural identity; real causal paths required. | Accepted — REQUIRED |
| CULT-04 | Domain Rule | Cultural Transmission/Change Requires a Declared Causal Channel | No assumed convergence or decay. | Accepted — REQUIRED |
| BEL-01 | Domain Rule | Collective Belief ≠ Individual Belief ≠ World Truth, No Institution Required | Broader than Batch 10's LAW-02; may be false and cause real behavior. | Accepted — REQUIRED |
| BEL-02 | Domain Rule | Social/Religious Belief ≠ Supernatural Truth/Mechanism | Explicit Magic boundary, deferred to Batch 12. | Accepted — REQUIRED |
| BEL-03 | Domain Rule | Sacredness Achievable Through Cultural Interpretation Alone | No supernatural transformation required. | Accepted — REQUIRED |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| An institution's doctrine does not require member acceptance | ORG-02 (Batch 10); this file's own BEL-01 | `collective-belief.md` |
| Recognition of cultural/religious/place significance requires an information path | PERC-01, KNOW-01 (Batch 06); reputation-reach entry (Batch 09); `places.md`'s own entry | `collective-belief.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| CB-S01 | Culture Spans Border | border changes, same culture continues | Culture | Revealed gap |
| CB-S02 | One Territory, Multiple Cultures | polity contains distinct regional cultures | Culture | Covered |
| CB-S03 | Individual Rejects Local Culture | settlement norm exists, resident dissents | Culture | Revealed gap |
| CB-S04 | Migrant Adopts Some Practices | migration → exposure → selected adoption | Culture | Revealed gap |
| CB-S05 | Cultural Contact Without Adoption (counter) | interaction → learning → no adoption | Culture | Revealed gap (permission coherent) |
| CB-S06 | Cultural Blending | contact → transmission → mixed practice | Culture | Revealed gap |
| CB-S07 | False Shared Belief | false story → institutional action → real consequence | Collective Belief | Partial |
| CB-S08 | Sacred Place Without Magic | interpretation → sacred status, no supernatural effect | Collective Belief | Revealed gap |
| CB-S09 | Real Magic, No Cultural Recognition (boundary) | supernatural event unrecognized → no auto culture change | Collective Belief | Blocked |
| CB-S10 | Doctrine vs. Personal Belief | doctrine declared → member dissents → membership possible | Collective Belief (inherited) | Revealed gap |

## Coverage Summary

**Culture**
- culture ≠ five adjacent concepts, no generic score — CB-S01, CB-S02
- collective artifact ≠ average individual belief — CB-S03
- individual participation requires real causal path — CB-S03, CB-S04
- transmission/change requires a declared channel, no assumed convergence/decay — CB-S05,
  CB-S06

**Collective Belief**
- collective belief ≠ individual belief ≠ truth, false belief causes real behavior — CB-S07
- social belief ≠ supernatural truth — CB-S08, CB-S09
- sacredness through cultural interpretation alone — CB-S08
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
  LAW-02 — the "no institution required" case is the specific new content, not a restatement.
- Collective Belief ↔ Authority (Batch 02): BEL-02 draws its own family/future-domain
  boundary the same way AUTH-04 already drew the Authority/Reach boundary.
- Collective Belief ↔ Places (11A): BEL-03 directly connects Place significance and Culture/
  Belief content that neither family alone states.

**Explicit call-out — genuine Domain Rule count:** **7.**

**Explicit call-out — whether culture is distinct from individual belief and politics:**
**Yes, as target semantics (CULT-01); the repository's own real "culture" system is
CONFLICTING with this target — a real, consumed, four-axis derived-tendency score, not the
richer concept this family means by the word.**

**Explicit call-out — whether cultural transmission has real causal paths:** **No —
confirmed MISSING at the individual/channel level; PARTIAL at the regional-drift level**
(event-driven, not channel-mediated).

**Explicit call-out — whether collective belief can be false without changing world truth:**
**Yes, semantically (BEL-01); the one real structural match (`BeliefInstitution`) is
currently INERT/OFF, so this cannot yet be positively exercised end-to-end.**

**Explicit call-out — whether political conquest automatically changes culture:** **Not
exercisable — no conquest-driven cultural-change mechanism was found either way; CULT-04's own
explicit prohibition on assumed cultural rewriting from political change remains untested
against real content, consistent with a MISSING repository realization rather than a
violation.**

**Explicit call-out — whether place significance respects information propagation:**
**Semantically yes (the Inherited recognition entry, reused from `places.md`); not
exercisable, since no significance/sacredness fact exists yet for it to gate.**

**Explicit call-out — whether the recurring individual/object/place significance pattern now
constitutes a clear cross-domain integration concern:** **Yes.** `BeliefInstitution`'s own
real, well-shaped, but unconsumed structure is this Catalog's clearest candidate bridge for
closing the gap found at four prior scales (individual, Batch 07; lineage, Batch 09;
organization, Batch 10; place, 11A) — recorded as a significant cross-domain observation, per
the batch instruction's own §37, without designing a `UniversalSignificanceSystem`.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**CONFLICTING (1 finding):**
1. This repository's own "culture" system (`CultureState`, four fixed axes) is real, live,
   and consumed, but structurally mismatched to this family's own richer target concept — a
   naming/scope collision, not a simple gap. See CULT-01.

**INERT/OFF (1 finding, a genuinely positive structural match):**
2. `BeliefInstitution` is a real, well-shaped, history-grounded collective-belief mechanism
   with "no live caller yet." See BEL-01.

**MISSING (5 findings):**
3. No individual-level cultural participation/adoption mechanism exists (CULT-03).
4. No channel-mediated cultural transmission/blending mechanism exists, beyond regional
   event-driven drift (CULT-04).
5. No sacred-place or cultural/religious-significance mechanism exists at all (BEL-03).
6. No institutional doctrine field distinct from `BeliefInstitution` exists (the doctrine-
   dissent Inherited entry).
7. No migration mechanism exists (cross-referenced from `settlements.md`, 11A) — the
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
- Is `BeliefInstitution` the correct structural home for eventually closing the recurring
  individual/object/place significance gap, or should a distinct mechanism be built instead?

## Implementation Candidates — Non-Binding

**This section preserves implementation-relevant discoveries only. Nothing here is approved,
prioritized, or required for implementation during the World Rule Catalog phase.**

- **Target semantic:** cultural participation/identification is an individual-level fact
  requiring its own causal path to change.
  **Current realization:** `CultureState` is read uniformly by every entity in a region.
  **Possible implementation direction:** a per-entity cultural-affinity value, updated through
  declared exposure events, read alongside the existing regional `CultureState`.
  **Implementation decision:** DEFERRED — no commitment in Rule Catalog phase.
- **Target semantic:** collective belief may exist and produce real behavior without
  requiring an institution to declare it.
  **Current realization:** `BeliefInstitution` is real and well-shaped but has no live
  caller.
  **Possible implementation direction:** wire a consumer reading `belief_strength` to bias a
  clan's own decisions — potentially the same bridge closing the recurring significance gap.
  **Implementation decision:** DEFERRED.
- **Target semantic:** a place may become sacred through cultural interpretation alone.
  **Current realization:** no bridge exists between `PlaceState`, `CultureState`, and
  `BeliefInstitution`.
  **Possible implementation direction:** a declared "significance"/"sacred" tag on
  `PlaceState`, populated by a process reading real events and cultural/belief state.
  **Implementation decision:** DEFERRED.

## Candidate disposition

Seven Domain Rules were drafted across two families (4 Culture, 3 Collective Belief) — **all
7 accepted, 0 rejected, 0 split, 0 merged.** No target rule count was set in advance. Two
further entries were identified as Inherited/Applied Foundational Rules and three as
Scope/Deferred Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11B (CULTURE / COLLECTIVE BELIEF) READY FOR HIGH-LEVEL EXTERNAL REVIEW.**
>
> Target semantics are coherent. Repository realization ranges from a genuine
> naming/scope collision (culture) to a real but unconsumed structural match (collective
> belief) to substantially MISSING (individual cultural participation, sacred places,
> migration-driven cultural change). No implementation commitment is implied by this review.

All required artifacts exist: two rule-family files (7 genuine Domain Rules; 12 total catalog
entries), one scenario file (10 scenarios covering every named seed scenario in the batch
instruction's own §32 Culture/Belief subset), this review export with all required sections
including Implementation Candidates — Non-Binding, and a shared local disposition report. No
contradiction was found against any prior batch's own Rules. This sub-batch's own most
significant cross-domain observation: `BeliefInstitution`'s own real, unconsumed structure is
this Catalog's clearest present candidate for eventually closing the recurring "ordinary
subject → historically significant, recognized by name" gap now confirmed at four separate
scales across four separate batches.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review.
