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
Collective Belief). The split is accepted and unchanged by either follow-up review.

## Follow-up revision summary

Two successive targeted follow-up reviews were applied directly to the canonical files on
2026-09-22, neither redesigning the batch nor adding Rules merely to increase count. 11B's
own genuine Domain Rule count **decreased from 7 to 6** across the two follow-ups (BEL-03
reclassified — the only Rule-count change either follow-up produced).

**First follow-up** (`tmp/world-rule-batch-11-followup-ext-ai.md`): reworded CULT-02 away
from equating culture with "durable artifacts"; corrected the CULT-03 Implementation
Candidate away from a single scalar; made PLACE-02/BEL-03 attribution-relative; narrowed the
cross-domain observation about `BeliefInstitution`.

**Second follow-up** (`tmp/world-rule-batch-11-followup-2-ext-ai.md`) corrected and extended
the first:

8. **Rewrote CULT-02 — rule refinement.** Even the first follow-up's "may contain durable/
   shared structures" wording still implicitly centered culture on artifacts/durability as
   the primary carrier. CULT-02 now states explicitly that culture may equally be carried
   through purely non-durable means — oral tradition, repeated practice, shared convention —
   with no institution, record, or object storing it at all, as an equally legitimate carrier,
   not an implied lesser case.
9. **Refined CULT-01 — wording clarification.** Removed the implementation-oriented "no
   generic `CultureScore`" language from the Rule's own normative text; the semantic principle
   ("culture cannot be reduced to a single adjacent concept or an assumed-universal scalar")
   now states the Rule itself, with the data-shape question moved to Repository Findings/
   Implementation Candidates.
10. **Reassessed `CultureState`'s classification — repository classification correction.**
    Naming collision with the word "culture," and narrower scope, are not by themselves
    grounds for CONFLICTING. Checked directly: no code treats `CultureState`'s four axes as
    the complete or exhaustive definition of culture in a way that forecloses a richer model
    coexisting alongside it — `CulturalBiasApplicator`'s own consumption is transient and
    never durable. Reclassified from CONFLICTING to **PARTIAL** (a real, valid, narrower
    derived-tendency projection).
11. **Kept CULT-03/CULT-04 — no change after evidence review.** Both Rules' own content was
    confirmed to already state the required distinctions correctly.
12. **Reclassified BEL-03's own status from REQUIRED to PERMITTED — rule refinement.**
    Sacredness, where modeled, *may* arise through cultural interpretation alone — not every
    world must contain culturally-created sacredness.
13. **Reassessed BEL-03 after that reframing — Domain Rule → Inherited/Applied
    reclassification.** Once stated as a mere permission, BEL-03 adds no genuinely new
    semantics beyond combining BEL-02 (social/religious belief ≠ supernatural truth) with
    `places.md`'s own PLACE-02 (significance is always attributed, divergent attributions
    permitted) for the specific case of sacredness. Moved to Inherited (originally BEL-03),
    per the follow-up's own explicit instruction not to preserve the Rule count artificially.
14. **Added two Culture probes — new/extended scenarios.** "Culture Without Durable
    Artifact" (extended onto CB-S06) and "Shared Practice, Different Beliefs" (extended onto
    CB-S03).
15. **Preserved the recurring significance grammar as a cross-domain concern without
    presuming `BeliefInstitution` is its semantic/implementation home — wording
    clarification + citation/provenance correction.** The conclusion is now stated purely at
    the semantic level (significance requires some valid path from provenance to socially
    available recognition to downstream reaction); `BeliefInstitution` being a "promising
    carrier" is confined strictly to Implementation Candidates, never target semantic
    architecture.
16. **Owner-Attention cleaned — wording clarification.** Storage-shaped questions ("should
    `CultureState` be renamed," "is `BeliefInstitution` the correct structural home," "does
    Territory need a typed record set") moved to Implementation Candidates; replaced with
    genuinely semantic questions.

Net effect on 11B's own counts: genuine Domain Rules **7 → 6** (BEL-03 reclassified);
Inherited entries **2 → 3** (BEL-03 reclassified in); Scope Boundaries **unchanged at 3**;
total catalog entries **unchanged at 12**; scenario count **unchanged at 10** (CB-S03, CB-S06,
CB-S07, CB-S08 each carry extensions, no new IDs).

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
- `places-culture/collective-belief.md` (BEL-01, BEL-02; BEL-03 now Inherited)
- `scenarios/culture-belief-batch-11b.md` (CB-S01–S10, four extended in place)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds
or refines target world semantics beyond Rules already defined elsewhere. This sub-batch's 12
total catalog entries break down as:

- **6 genuine Domain Rules**: CULT-01 (wording corrected), CULT-02 (reworded twice), CULT-03,
  CULT-04; BEL-01 (evidence split), BEL-02.
- **3 Inherited/Applied Foundational Rules**: in `collective-belief.md` — an institution's
  doctrine does not require member acceptance (ORG-02, Batch 10; this file's own BEL-01),
  recognition of another subject's own attributed cultural/religious/place significance
  requires an information path (PERC-01/KNOW-01, Batch 06; Batch 09's reputation-reach entry;
  `places.md`'s own analogous entry), and sacredness may arise through cultural
  interpretation alone without supernatural transformation, with divergent attributions
  permitted (reclassified from BEL-03, reusing BEL-02 and `places.md`'s own PLACE-02).
- **3 Scope/Deferred Boundaries**: concrete cultural-content catalog (`culture.md`); Magic/
  supernatural mechanism and truth, concrete religious-institution content catalog
  (`collective-belief.md`).

**Genuine new-Rule count for this sub-batch: 6 (was 7 before the second follow-up
reclassified BEL-03).** **Inherited/reused foundation count: 3 entries (was 2)**, citing
ORG-02 (Batch 10), PERC-01/KNOW-01 (Batch 06), BEL-02 (this file), and cross-references to
Batch 09's and `places.md`'s own analogous entries.

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| CULT-01 | Domain Rule | Culture ≠ Belief/Law/Religion/Faction/Ethnicity/Settlement | Wording corrected 2026-09-22: implementation-shaped "no CultureScore" language removed from the Rule text. | Accepted (revised) |
| CULT-02 | Domain Rule | Culture May Be Carried By Durable Artifacts OR Purely Non-Durable Practice, ≠ Average Belief | Reworded twice 2026-09-22: oral/repeated-practice carriers made explicit, not implied. | Accepted (revised) |
| CULT-03 | Domain Rule | Cultural Participation/Knowledge/Practice/Rejection/Identification Are Distinct | Preserved unchanged after re-evidence review. | Accepted — REQUIRED |
| CULT-04 | Domain Rule | Cultural Transmission/Change Requires a Declared Causal Channel | Preserved unchanged after re-evidence review. | Accepted — REQUIRED |
| BEL-01 | Domain Rule | Collective Belief ≠ Individual Belief ≠ World Truth, No Institution Required | Evidence split 2026-09-22 (first follow-up): institution-backed PARTIAL, institution-free MISSING. | Accepted (evidence refined) |
| BEL-02 | Domain Rule | Social/Religious Belief ≠ Supernatural Truth/Mechanism | Explicit Magic boundary, deferred to Batch 12. | Accepted — REQUIRED |
| ~~BEL-03~~ | *(reclassified)* | *(was: Sacredness Achievable Through Cultural Interpretation Alone)* | Moved to Inherited 2026-09-22 (second follow-up) — fully covered by BEL-02 + PLACE-02 once reframed as PERMITTED. | Reclassified (see Inherited) |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| An institution's doctrine does not require member acceptance | ORG-02 (Batch 10); this file's own BEL-01 | `collective-belief.md` |
| Recognition of another subject's own attributed significance requires an information path | PERC-01, KNOW-01 (Batch 06); reputation-reach entry (Batch 09); `places.md`'s own entry | `collective-belief.md` |
| Sacredness may arise through cultural interpretation alone, no supernatural transformation required, divergent attributions permitted *(new, second follow-up, originally BEL-03)* | BEL-02 (this file); PLACE-02 (Batch 11A) | `collective-belief.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| CB-S01 | Culture Spans Border | border changes, same culture continues | Culture | Revealed gap |
| CB-S02 | One Territory, Multiple Cultures | polity contains distinct regional cultures | Culture | Covered |
| CB-S03 | Individual Rejects Local Culture / Four-Way Divergence / Shared Practice, Different Beliefs | resident dissents; four facts diverge; shared practice, per-participant divergent meaning | Culture | Revealed gap (permission coherent) |
| CB-S04 | Migrant Adopts Some Practices | migration → exposure → selected adoption | Culture | Revealed gap |
| CB-S05 | Cultural Contact Without Adoption (counter) | interaction → learning → no adoption | Culture | Revealed gap (permission coherent) |
| CB-S06 | Cultural Blending / Culture Without Durable Artifact | contact → transmission → mixed practice; oral tradition with no durable backing persists | Culture | Revealed gap (permission coherent) |
| CB-S07 | False Shared Belief / Institution-Free Folk Belief | false story → institutional action; folk belief with no institution at all | Collective Belief | Partial (institution-backed) + revealed gap (institution-free) |
| CB-S08 | Sacred Place Without Magic / Divergent Attribution | interpretation → sacred status; two groups attribute differently, both valid | Collective Belief (inherited) | Revealed gap (permission coherent) |
| CB-S09 | Real Magic, No Cultural Recognition (boundary) | supernatural event unrecognized → no auto culture change | Collective Belief | Blocked |
| CB-S10 | Doctrine vs. Personal Belief | doctrine declared → member dissents → membership possible | Collective Belief (inherited) | Revealed gap |

## Coverage Summary

**Culture**
- culture ≠ five adjacent concepts, cannot be reduced to a single adjacent concept or a
  universal scalar — CB-S01, CB-S02
- culture may be carried by durable artifacts or purely non-durable practice, never reduced
  to average belief — CB-S03, CB-S06
- individual participation requires real causal path; knowledge/practice/rejection/
  identification remain independent — CB-S03, CB-S04
- transmission/change requires a declared channel, no assumed convergence/decay — CB-S05,
  CB-S06

**Collective Belief**
- collective belief ≠ individual belief ≠ truth, no institution required, false belief
  causes real behavior — CB-S07
- social belief ≠ supernatural truth — CB-S08, CB-S09
- sacredness through cultural interpretation alone, permitted not required, divergent
  attributions coexist — CB-S08
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
  repository realization is correctly split: only the institution-backed half has any
  structural match at all.
- Collective Belief ↔ Places (11A): the reclassified sacredness entry and PLACE-02 are
  directly reconciled — both state significance/sacredness as attribution-relative,
  permitting simultaneous divergent attributions, without either requiring it to exist.
- Collective Belief ↔ Authority (Batch 02): BEL-02 draws its own family/future-domain
  boundary the same way AUTH-04 already drew the Authority/Reach boundary.
- **Significance-grammar cross-domain concern, corrected 2026-09-22 (second follow-up).**
  Batch 11A independently confirms the same recurring grammar already seen for individuals,
  objects, lineage, and organizations. At the semantic level, this Catalog concludes only that
  significance requires some valid path from provenance to socially available recognition to
  downstream reaction — no specific mechanism (`BeliefInstitution` or otherwise) is named as
  the intended bridge outside Implementation Candidates.

**Explicit call-out — genuine Domain Rule count:** **6 (was 7 before the second follow-up
reclassified BEL-03).**

**Explicit call-out — whether culture is distinct from individual belief and politics:**
**Yes, as target semantics (CULT-01); the repository's own real "culture" system is a
narrower, valid PARTIAL projection, not CONFLICTING (reassessed 2026-09-22) — nothing treats
its four axes as culture's complete or exhaustive definition.**

**Explicit call-out — whether cultural transmission has real causal paths:** **No —
confirmed MISSING at the individual/channel level, including for the purely-non-durable
oral-tradition carrier CULT-02 now names explicitly; PARTIAL at the regional-drift level**
(event-driven, not channel-mediated).

**Explicit call-out — whether collective belief can be false without changing world truth:**
**Yes, semantically (BEL-01); repository realization is split: PARTIAL for the
institution-backed case (`BeliefInstitution`, currently INERT/OFF, keyed to `clan_id` only),
MISSING for the institution-free case (no candidate mechanism at all).**

**Explicit call-out — whether political conquest automatically changes culture:** **No,
correctly — CULT-04's own explicit prohibition holds; no conquest-driven cultural-rewrite
mechanism was found either way, consistent with a MISSING repository realization rather than
a violation.**

**Explicit call-out — whether place significance respects information propagation:**
**Semantically yes (the Inherited recognition entry, reused from `places.md`, recognizing a
specific *attribution* rather than a bare fact); not exercisable, since no significance/
sacredness fact exists yet for it to gate.**

**Explicit call-out — whether the recurring individual/object/place significance pattern now
constitutes a clear cross-domain integration concern:** **Yes — but `BeliefInstitution` is
explicitly not presumed to be its semantic or implementation home (corrected 2026-09-22 by
the second follow-up).** The semantic-level conclusion (a valid path from provenance to
recognition to reaction is required) is preserved; which mechanism, if any, supplies that
path remains an undecided implementation question, confined to Implementation Candidates.

## Repository Findings

Classified per the CONFLICTING/INERT-OFF/MISSING distinction established in prior batches.
**These are repository/implementation facts, not World Rule decisions, and imply no delivery
priority.**

**No CONFLICTING finding remains in this sub-batch (reassessed 2026-09-22 — was 1 before the
second follow-up).** `CultureState`'s own four-axis derived-tendency score was reclassified
from CONFLICTING to PARTIAL: naming collision with "culture," and narrower scope, are not by
themselves grounds for CONFLICTING, and no code treats those four axes as culture's complete
or exhaustive definition in a way that forecloses a richer model.

**PARTIAL (1 finding, reclassified from CONFLICTING):**
1. `CultureState` (four fixed axes) is real, live, and consumed
   (`CulturalBiasApplicator`), and is a real, valid, narrower derived-tendency projection —
   not this family's own full target concept, but not an active collapse of it either. See
   CULT-01.

**INERT/OFF (1 finding, a genuinely positive structural match, scoped to the
institution-backed case only):**
2. `BeliefInstitution` is a real, well-shaped, history-grounded, but institution-*backed-only*
   collective-belief mechanism (keyed to `clan_id`), with "no live caller yet." See BEL-01.

**MISSING (6 findings):**
3. The institution-*free* half of BEL-01's own permission (a folk myth/taboo no institution
   ever declares) has no candidate mechanism of any kind, distinct from item 2 above.
4. No individual-level cultural participation/adoption mechanism exists (CULT-03) — no
   realization anywhere reduces this to a single scalar either, since nothing exists at all
   to check against.
5. No channel-mediated cultural transmission/blending mechanism exists, beyond regional
   event-driven drift, including no purely-non-durable oral-tradition carrier of any kind
   (CULT-02, CULT-04).
6. No sacred-place, attributed-significance, or multi-attributor-divergence mechanism exists
   at all (the reclassified sacredness entry, originally BEL-03).
7. No institutional doctrine field distinct from `BeliefInstitution` exists (the doctrine-
   dissent Inherited entry).
8. No migration mechanism exists (cross-referenced from `settlements.md`, 11A) — the
   precondition for several culture scenarios (CB-S04).

Key evidence, all confirmed by direct code/doc inspection: `src/domains/culture/{model,
deriver,applicator,settlement_personality}.py`, `src/domains/belief_institution/{model,
deriver}.py`, `src/systems/strategic_systems/belief.py` (individual `BeliefEntry`, confirmed
distinct), `src/core/self_model.py` (`KnowledgeFact`, confirmed distinct).

## Owner-attention decisions (design semantics, per the standing direction)

Cleaned 2026-09-22 per the second follow-up's own item 16 — storage-shaped questions moved to
Implementation Candidates below; only design-semantic questions remain here:

- **What makes cultural state persistent beyond current individuals** — through durable
  artifacts/institutions, through purely repeated social behavior, or both, and does the
  answer differ by specific culture?
- **What counts as socially shared belief rather than merely coincidentally similar
  individual belief** — is there a semantic threshold, or is "shared" itself always a
  domain-declared fact?
- **What semantic conditions turn historical association into socially meaningful
  significance** — is attribution alone sufficient, or does it require some further
  threshold of recognition?
- Can institutional doctrine count as collective belief without individual acceptance?
  (Answered structurally yes by the Inherited doctrine-dissent entry — is this the right
  target shape, or should some institutions require acceptance?)
- **What mechanism, if any, should realize BEL-01's own institution-free collective-belief
  case, distinct from `BeliefInstitution`'s own institution-backed case?**

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
  **Current realization:** `BeliefInstitution` is real and well-shaped but institution-backed
  only, with no live caller.
  **Possible implementation direction:** wire a consumer reading `belief_strength` to bias a
  clan's own decisions — this would exercise only the institution-backed subset of BEL-01,
  never the institution-free case, which needs its own separate mechanism regardless.
  **Implementation decision:** DEFERRED.
- **Target semantic:** a place may become sacred through cultural interpretation alone,
  always attributed by a specific culture/group/institution.
  **Current realization:** no bridge exists between `PlaceState`, `CultureState`, and
  `BeliefInstitution` — no candidate among the three is named as the intended bridge; that
  choice remains undecided (per the significance-grammar note above).
  **Possible implementation direction:** a declared "significance"/"sacred" tag on
  `PlaceState`, populated by a process reading real events and cultural/belief state, only as
  a derived/cached projection with explicit provenance/scope, never canonical, relational
  model preferred.
  **Implementation decision:** DEFERRED.
- **Target semantic (added 2026-09-22, second follow-up):** should `CultureState`'s own four
  fixed axes ever be reconciled with, renamed relative to, or kept fully separate from this
  family's own richer target concept.
  **Current realization:** `CultureState` is a real, valid, narrower PARTIAL projection.
  **Implementation decision:** DEFERRED. Moved here from Owner-Attention, per the second
  follow-up's own explicit instruction.

## Candidate disposition

Seven Domain Rules were originally drafted across two families; the second follow-up
reclassified one (BEL-03) to Inherited after re-testing it against the admission discipline
once reframed as a permission, leaving **6 accepted Domain Rules, 1 reclassified, 0 rejected,
0 split, 0 merged.** Two others were refined in wording (CULT-01, CULT-02) without changing
their own IDs. No target rule count was set in advance. Three entries are now Inherited/
Applied Foundational Rules (2 original + 1 reclassified) and three remain Scope/Deferred
Boundaries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/places-culture-batch-11-report.md` (local review report, not part of this catalog,
covering both 11A and 11B).

---

> **BATCH 11B (CULTURE / COLLECTIVE BELIEF) — PASS, READY TO FREEZE.**
>
> Milestone C domain semantics are coherent. Repository realization ranges from a real but
> narrower, valid PARTIAL projection (culture) to a real but institution-backed-only,
> unconsumed structural match (collective belief) to substantially MISSING (individual
> cultural participation, sacred/attributed-significance mechanisms, migration-driven
> cultural change). No implementation commitment is implied by this freeze.

All required artifacts exist and are current: two rule-family files (6 genuine Domain Rules;
12 total catalog entries), one scenario file (10 scenarios, four extended in place across two
successive follow-up reviews), this review export with all required sections including
Implementation Candidates — Non-Binding, and a shared local disposition report. No
target-semantic contradiction remains. Both follow-ups' own applicable items were resolved:
CULT-01/CULT-02 corrected; `CultureState` correctly reassessed from CONFLICTING to PARTIAL;
BEL-03 reclassified to Inherited after being reframed as a permission; the significance-
grammar conclusion was corrected to name no mechanism as its intended semantic home; and
Owner-Attention was cleaned of storage-shaped questions.

Do not begin Batch 12 (Magic / Supernatural) until Batch 11A and Batch 11B both receive
high-level review of this second focused revision.
