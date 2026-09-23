---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Review Export: Batch 06 (Perception / Knowledge / Information / Agency)

**This file is a generated, non-authoritative review view.** It exists so an external reviewer
can assess the batch without opening every canonical file. It is never edited directly as the
fix for a review finding — feedback goes back into the canonical files below, and this export is
regenerated from them. See `world-rules/README.md`'s review index for the current status of
every batch.

## Batch scope

The third domain-facing (Milestone B) batch, and a high-priority one — perception, knowledge,
information transfer, memory, and autonomous agency are the mechanisms by which individual
entities form an imperfect view of the world and act from it. Three rule families: Perception,
Knowledge/Information/Memory, Agency/Decision. Files live under `knowledge-agency/`, per the
batch instruction's own directory suggestion; Memory was folded into the Knowledge/Information
file rather than given its own. Drafted 2026-09-22 with the five-category admission discipline
Batch 05 established, then revised the same day per a targeted semantic-cleanup follow-up
review (`tmp/world-rule-batch-6-followup-ext-ai.md`) — see "Follow-up revision summary" below.

## Follow-up revision summary (2026-09-22)

A targeted semantic cleanup was applied without redesigning the batch, preserving the
normalized Rule-admission structure:

1. **PERC-01 generalized.** No longer requires every perception mechanism to jointly gate on
   capability + channel + distance + attention — those are possible constraints, not a
   universal mandatory formula. Explicit-rule-permitted complete/perfect perception is no
   longer implicitly prohibited. Core principle narrowed to: perception does not imply complete
   or perfect knowledge *by default*.
2. **KNOW-01 loosened.** No longer requires every belief/knowledge claim to carry gradable
   certainty — exact/categorical knowledge remains a legitimate representation. Certainty and
   objective truth remain distinct facts wherever certainty *is* represented.
3. **KNOW-02 and KNOW-03 merged.** KNOW-03 was refined to "beliefs do not automatically
   synchronize with changing world truth; only a declared process (contradiction, new evidence,
   decay) revises certainty/content — a subject may remain confidently wrong." Once stated this
   way, it no longer added semantics separate from KNOW-02's own "no automatic truth-injection"
   claim, so the two were merged under KNOW-02.
4. **INFO-01 loosened.** Kept "source trust ≠ claim certainty" as the core claim; removed the
   universal requirement that trust be gradually-adjusted and per-source — trust may legitimately
   be source-specific, relationship-specific, institution-specific, contextual, or abruptly
   revised, depending on later domain semantics.
5. **AGENCY-02 reworded.** Removed implementation language ("inside one scoring formula");
   softened to "ordinary motivations influence decision preference without automatically
   determining the chosen action"; explicitly allows future reflex/panic/compulsion/
   mind-control/hard-threshold rules to override ordinary choice (new Scope/Deferred Boundary).
6. **AGENCY-03 terminology clarified.** Introduced an explicit two-tier distinction: Opportunity
   (a world-relative possibility worth considering) vs. Actionable Affordance (an Opportunity
   currently exercisable under this subject's actual capability/reach). KA-S12–S15 revisited
   using this terminology; KA-S14 given a clean explanation (positive expected benefit is itself
   a motivational/utility input, distinct from a pre-existing named goal but not from motivation
   in the broader sense AGENCY-02 describes).
7. **Repository classification corrected.** `ResourceOpportunityProvider`/`HarvestScorer`
   reclassified from MISSING to **CONFLICTING** — active behavior that violates the target
   semantic boundary, not merely an unbuilt feature. A three-way distinction (CONFLICTING /
   INERT-OFF / MISSING) now applies across all three canonical files' Repository Findings.
   This does not invalidate the Rule Catalog — the target semantics remain coherent; the Catalog
   successfully exposed a real, documented architecture mismatch.
8. **Three adversarial probes added:** KA-S18 (complete observation where declared), KA-S19
   (stale but confident), KA-S20 (compelled action) — confirming the revised Rules are correctly
   bounded rather than over-broad.

**The major architectural finding is preserved, not weakened:** individual agents already have
real belief/perception infrastructure, but some live decision paths bypass it and read
omniscient state directly instead.

## Canonical files included

- `knowledge-agency/perception.md` (PERC-01)
- `knowledge-agency/knowledge-information.md` (KNOW-01–02, INFO-01–02, MEM-02)
- `knowledge-agency/agency-decision.md` (AGENCY-01–05)
- `scenarios/knowledge-agency-batch-06.md` (KA-S01–S20)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. Post-follow-up, this
batch's 26 total catalog entries break down as:

- **11 genuine Domain Rules**: PERC-01; KNOW-01, KNOW-02 (merged); INFO-01, INFO-02; MEM-02;
  AGENCY-01, AGENCY-02, AGENCY-03, AGENCY-04, AGENCY-05.
- **8 Inherited/Applied Foundational Rules** (unchanged by the follow-up — direct reuse/
  reconfirmation, no new claim): "world fact ≠ perceived/believed fact" (OWN-04, OWN-06,
  CAUSE-01), "reach is asymmetric" (REACH-03) in `perception.md`; "belief/knowledge is
  subject-owned, never a duplicate of ground truth" (OWN-01, OWN-02, OWN-06), "information
  requires a real transfer path" (REACH-01, REACH-02, REACH-05), "individual memory ≠ world
  history" (HP-01, OWN-06) in `knowledge-information.md`; "capability/authority/reach are
  independent preconditions" (CAP-01, AUTH-01, REACH-01/02), "need pressure/threshold produces
  real consequence" (SURV-02), "a false belief may still be a real cause" (CAUSE-01, Batch 01's
  FND-S18/S19) in `agency-decision.md`.
- **7 Scope/Deferred Boundaries** (6 original + 1 added by the follow-up): formal
  stealth/ambush content, universal perception-formula generalization in `perception.md`; no
  universal epistemology representation, population-scale belief content
  (`BeliefInstitution`) in `knowledge-information.md`; Hybrid Agency's organization-scale
  deferral, detailed psychological modeling, and (new) non-ordinary override mechanisms
  (reflex/panic/compulsion/mind control/hard survival thresholds) in `agency-decision.md`.

**Genuine new-Rule count for this batch: 11** (was 12 before the follow-up's KNOW-02/03 merge).
**Inherited/reused foundation count: 8 entries, citing 13 distinct foundational Rule IDs**
(OWN-01, OWN-02, OWN-04, OWN-06, CAUSE-01, REACH-01, REACH-02, REACH-03, REACH-05, HP-01,
CAP-01, AUTH-01, SURV-02).

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PERC-01 | Domain Rule | Perception Is Bounded by Declared Constraints | A default of partiality; possible (not mandatory joint) dimensions; explicit-rule perfect perception permitted. | Accepted, revised |
| KNOW-01 | Domain Rule | Certainty May Be Represented Where Relevant, ≠ Truth | Belief/knowledge semantics permit uncertainty; exact/categorical knowledge remains legitimate. | Accepted, revised |
| KNOW-02 | Domain Rule | Belief Revises Only Through a Declared Process | No hidden-truth injection; no automatic re-sync; a subject may remain confidently wrong. (Merged with former KNOW-03.) | Accepted, revised/merged |
| INFO-01 | Domain Rule | Source Trust ≠ Claim Certainty | Distinct properties; trust's specific shape (gradual/per-source) is one example, not a universal requirement. | Accepted, revised |
| INFO-02 | Domain Rule | Information Content May Change in Transit, Where Declared | Permission for content-level distortion; confirmed unrealized in this repository. | Accepted (mechanism MISSING) |
| MEM-02 | Domain Rule | Experiential Memory ≠ Declarative Knowledge | Causal/spatial/temporal memory is a distinct category from knowledge_model. | Accepted |
| AGENCY-01 | Domain Rule | Decision Stages Are Causally Distinct | Want/choose/capable/authorized/reach/commit/succeed never collapse into one gate. | Accepted |
| AGENCY-02 | Domain Rule | Ordinary Motivation Influences, Never Automatically Determines | Competing influence on preference; future declared overrides (reflex/compulsion) are a distinct, permitted category. | Accepted, revised |
| AGENCY-03 | Domain Rule | Opportunity ≠ Actionable Affordance ≠ Desire | Two explicit tiers: a world-relative possibility, and one currently exercisable by this subject; neither depends on desire. | Accepted, revised |
| AGENCY-04 | Domain Rule | Decision Validity ≠ Execution Outcome | A well-formed decision may still fail; failure never invalidates it retroactively. | Accepted |
| AGENCY-05 | Domain Rule | Hidden Cognition Is Not Globally Visible | Motive/belief/need are private by default; only inferable via a real mechanism. | Accepted (inference mechanism MISSING) |

## Inherited Foundations Summary

| Entry (as stated in its own file) | Foundational Rule(s) reused | File |
|---|---|---|
| World fact existence/truth independent of perception or belief | OWN-04, OWN-06, CAUSE-01 | `perception.md` |
| Reach is asymmetric — perceiving ≠ being perceived | REACH-03 | `perception.md` |
| Belief/knowledge is subject-owned, never a duplicate of ground truth | OWN-01, OWN-02, OWN-06 | `knowledge-information.md` |
| Information requires a real transfer path or intermediary link | REACH-01, REACH-02, REACH-05 | `knowledge-information.md` |
| Individual memory fading ≠ world historical fact changing | HP-01, OWN-06 | `knowledge-information.md` |
| Capability/authority/reach are independent preconditions | CAP-01, AUTH-01, REACH-01, REACH-02 | `agency-decision.md` |
| Need pressure accumulates; crossing a threshold produces a real consequence | SURV-02 | `agency-decision.md` |
| A false belief may still be a real cause of a real action | CAUSE-01, Batch 01 FND-S18/S19 | `agency-decision.md` |

## Scenario Inventory

| Scenario ID | Short name | Trajectory | Rule families challenged | Result |
|---|---|---|---|---|
| KA-S01 | See It, Know Something About It | observe → belief → decision | Perception, Knowledge | Covered |
| KA-S02 | Event Happens Unobserved | world event → no observer → state changes anyway | Perception | Covered |
| KA-S03 | Partial Observation | observe part → incomplete belief, not auto-filled | Perception, Knowledge | Covered |
| KA-S04 | False Rumor, Real Action | false report → believed → action → real consequence | Agency (inherited) | Covered |
| KA-S05 | Conflicting Reports | source A vs. source B → contradiction/trust handling | Knowledge, Information | Covered |
| KA-S06 | Stale Knowledge | learn state → world changes → old belief persists | Knowledge | Covered |
| KA-S07 | Information Does Not Teleport | distant event → unrelated entity stays unaware | Knowledge, Reach (inherited) | Covered |
| KA-S08 | Rumor Degrades | witness → messenger → recipient → content unchanged | Information, Reach (inherited) | Revealed gap (MISSING) |
| KA-S09 | Memory Fades but History Remains | fact occurs → memory fades → history unchanged | Knowledge/Memory, History/Provenance (inherited) | Covered |
| KA-S10 | Decision Reads Omniscient State (added) | goal-scoring selects a never-perceived target | Perception, Agency | Revealed contradiction (CONFLICTING) |
| KA-S11 | Need Influences but Doesn't Dictate | hunger raises priority; another action still chosen | Agency | Covered |
| KA-S12 | Capability Without Knowledge | capable but unaware → not chosen as Actionable Affordance | Agency | Covered, KA-S10 caveat |
| KA-S13 | Knowledge Without Capability | knows what's needed, lacks means → not Actionable | Agency | Covered |
| KA-S14 | Opportunity Without Desire | valid Opportunity, no pre-existing goal → benefit itself is motivational | Agency | Partial, cleanly explained |
| KA-S15 | Desire Without Opportunity | strong want, no path → structural fallback instead | Agency | Covered, with nuance |
| KA-S16 | Decision Fails | valid decision → committed → outcome fails | Agency | Covered |
| KA-S17 | Hidden Motive, Visible Consequence | motive hidden → pattern observable → inferable in principle | Agency | Revealed gap (MISSING) |
| KA-S18 | Complete Observation Where Declared (added) | special channel → complete relevant information | Perception | Covered (permission, not built example) |
| KA-S19 | Stale but Confident (added) | high-confidence belief → world changes → no new info → confidently wrong forever | Knowledge | Covered |
| KA-S20 | Compelled Action (added) | ordinary preference A → declared reflex/compulsion → B occurs | Agency, Scope Boundary | Covered (permission, not built example) |

## Coverage Summary

**Perception**
- bounded-by-declared-constraints, defaults to partial, permits explicit complete observation —
  KA-S01, KA-S02, KA-S03, KA-S18
- world fact independent of observation — KA-S02

**Knowledge/Information/Memory**
- certainty permitted where relevant, ≠ truth, exact knowledge remains legitimate — KA-S05
- no hidden-truth injection, no automatic re-sync, confidently-wrong-forever permitted — KA-S01,
  KA-S06, KA-S07, KA-S19
- source trust ≠ claim certainty, shape not mandated — KA-S05
- content-level distortion permitted but unrealized — KA-S08
- experiential memory vs. declarative knowledge, individual memory vs. world history — KA-S09

**Agency/Decision**
- decision-stage distinctness — KA-S12, KA-S13, KA-S16
- ordinary motivation influences, doesn't determine; declared overrides are a distinct category
  — KA-S11, KA-S20
- Opportunity ≠ Actionable Affordance ≠ desire — KA-S12–S15
- decision validity ≠ outcome — KA-S16
- hidden cognition privacy/inference boundary — KA-S17
- omniscient-state reads (cross-cutting Perception ↔ Agency CONFLICTING finding) — KA-S10

## Deferred Semantics

- Formal stealth/ambush content stays deferred, per REACH-03's own carried-forward open
  question — this batch only reconfirms the underlying asymmetry.
- No universal epistemology representation is being built — `BeliefEntry`, `KnowledgeFact`/
  `knowledge_model`, the Memory domain's three subsystems, and `BeliefInstitution` remain
  deliberately separate.
- Population-scale organized belief content (myth drift, culture drift) stays with Social
  relations/Politics batches.
- Hybrid Agency's organization/settlement/institution-scale coarser models stay deferred.
- Detailed psychological/cognitive-architecture modeling beyond what this repository already
  evidences is not introduced.
- **Added by the follow-up.** Non-ordinary override mechanisms (reflex, panic, compulsion, mind
  control, hard survival thresholds) are permitted by AGENCY-02's own carve-out but not
  designed here — deferred to whichever future batch first needs a concrete override mechanism.
- INFO-02's content-distortion permission and AGENCY-05's motive-inference mechanism both stay
  unbuilt — deferred to future batches or tickets.

## Cross-domain findings

- Perception ↔ Agency/Decision: KA-S10 is this batch's own most significant cross-cutting
  finding, and — per the follow-up review's own required correction — is classified
  **CONFLICTING**, not MISSING: `ResourceOpportunityProvider.get_opportunities()` and
  `HarvestScorer.score()` both actively read raw/omniscient world state, directly contradicting
  PERC-01's own default and AGENCY-03's own generation-independence claim, rather than merely
  lacking an unbuilt feature.
- Knowledge/Information ↔ Reach: INFO-01/INFO-02 and the inherited "information requires a real
  transfer path" entry complete REACH-02's and REACH-05's own explicitly-flagged forward
  references — REACH-05's own open question is reconfirmed still open (MISSING), not resolved.
- Knowledge/Information ↔ History/Provenance: MEM-02's inherited boundary satisfies HP-01's own
  explicit non-goal ("rumour propagation... stays with Perception/knowledge/information").
- Agency/Decision ↔ Capability/Authority/Reach (Batch 03/02): AGENCY-01's decision-stage chain
  reuses CAP-01/AUTH-01/REACH-01/02 without needing to re-derive them.
- Agency/Decision ↔ Causality (Batch 01): AGENCY-04's decision-validity/outcome distinction and
  the inherited "false belief may still be a real cause" entry both trace to CAUSE-01 and
  FND-S18/S19.

**Explicit call-out — genuine new Domain Rule count:** **11** (was 12 before the follow-up
merged KNOW-02/KNOW-03).

**Explicit call-out — inherited/reused foundation count:** 8 entries, citing 13 distinct
foundational Rule IDs across them (OWN-01, OWN-02, OWN-04, OWN-06, CAUSE-01, REACH-01, REACH-02,
REACH-03, REACH-05, HP-01, CAP-01, AUTH-01, SURV-02).

**Explicit call-out — whether agents currently access omniscient state:** **Yes, confirmed and
now explicitly classified CONFLICTING (an active violation), not merely MISSING (an absent
feature), for at least two major decision paths.** `ResourceOpportunityProvider.
get_opportunities()` reads `state.resource_nodes` directly; `HarvestScorer.score()` calls
`SpatialQueryService.nearest_resource_node(state, ...)` against the entire world state. See
KA-S10.

**Explicit call-out — whether beliefs materially affect decisions:** **Split verdict.**
`strategic.leads`/`BeliefEntry` materially affects decisions (read by `src/ai/goals/scorers.py`
and `LeadContradictionSystem`). `entity.cognition.knowledge_model` does **not** — confirmed
INERT/OFF (no consumer outside `src/cognition/` itself; not CONFLICTING, since nothing actively
violates KNOW-02's own boundary there — it is simply never consumed).

**Explicit call-out — how false/stale information propagates:** False information propagates
exactly like true information at the point of receipt — its falseness is discovered only
through contradiction or left to decay through staleness (and only for non-`PRECISE` leads).
Per KNOW-02's own revised text, a subject may remain confidently, stably wrong indefinitely
absent a real revision event (KA-S19). Content itself never degrades or distorts through
propagation — only certainty and trust do (KNOW-02, INFO-01, INFO-02's confirmed MISSING gap).

**Explicit call-out — whether information has real reach constraints:** **Yes.** Every
information-arrival path requires a real, traceable source (KA-S07). Intermediary-link failure
modeling remains confirmed MISSING (REACH-05, reconfirmed).

**Explicit call-out — whether needs/motivations create differentiated choices:** **Yes.**
Different entities with different needs, traits, and capability estimates score the same
Opportunity set differently, per AGENCY-02's own revised "influence, not determination" claim —
confirmed differentiation, not a fixed lookup, and not (per KA-S20) a claim that no future
override category could ever force a specific outcome.

**Explicit call-out — which cognitive state is causally inert (INERT/OFF specifically, as
distinguished from CONFLICTING or MISSING):** `entity.cognition.knowledge_model` (no decision
consumer, though internally consistent and tested); `CausalMemoryEntry.confidence` (hardcoded
to `0.8` for every entry, never actually varies); the entire Memory domain while
`ENABLE_MEMORY_UPDATE` defaults OFF; `entity.self_model.capabilities.estimates` (confirmed
always empty in production, though the estimation logic itself is live and consumed ad hoc
elsewhere — not classified under the three-way distinction, since no Rule requires this storage
populated).

## Repository Findings

Classified per the three-way distinction the follow-up review required: **CONFLICTING** (a
live, active behavior that violates a target Rule's own boundary — a real architecture
mismatch, not something invalidating the Catalog), **INERT/OFF** (a real mechanism that simply
does not run, violating nothing), and **MISSING** (a permitted mechanism never built at all).

**CONFLICTING (1 finding — the most significant in this batch):**
1. `ResourceOpportunityProvider.get_opportunities()` and `HarvestScorer.score()` actively read
   raw/omniscient world state directly, bypassing `PerceptionGate` and `entity.cognition.
   knowledge_model` entirely, for at least two live decision paths. This directly contradicts
   PERC-01's own default and AGENCY-03's own generation-independence claim. **This does not
   invalidate the Rule Catalog — it means the Catalog successfully exposed a real, documented
   architecture mismatch**, and remains one of the most important findings produced so far:
   individual agents already have real belief/perception infrastructure, but some live decision
   paths bypass it entirely.

**INERT/OFF (3 findings):**
2. `entity.cognition.knowledge_model` has zero decision-making consumers outside
   `src/cognition/` itself.
3. `PerceptionUpdatePhase` (the salience/attention/budget layer) has zero call sites in
   production — only the upstream binary `PerceptionGate` is confirmed live.
4. `MemoryUpdatePhase` is wired but inactive — gated behind `ENABLE_MEMORY_UPDATE`, default OFF.

**MISSING (3 findings):**
5. No in-simulation motive-inference mechanism exists — `CognitionPatternMiner` is offline
   developer tooling, not a world mechanism.
6. No intermediary-link failure modeling (messenger delayed/blocked/lying) — reconfirms
   REACH-05's already-flagged gap.
7. No content-level distortion through information transmission — only certainty/trust vary.

**Not classified under the three-way distinction (an architecture observation, not a
Rule-boundary finding):**
8. `CapabilityEstimateService` is scorer-local/ad hoc and architecturally split from the
   entity's own persisted self-model — `entity.self_model.capabilities.estimates` stays empty
   in production; no active confidence decay. No AGENCY Rule requires this storage populated.
9. A minor naming collision (two distinct `KnowledgeFact` classes across
   `src/world/providers/information.py` and `src/core/self_model.py`) — not a semantic gap.

Key evidence, all confirmed by direct code/doc inspection: `src/world/perception/gate.py`,
`src/domains/perception/{phase,filter,salience,service}.py`,
`docs/simulation/domains/perception_contract.md`; `src/systems/strategic_systems/belief.py`,
`src/domains/information/{resolver,contradiction,trust}.py`,
`docs/simulation/domains/information_contract.md`,
`docs/cognition/capability_and_knowledge_contract.md`; `src/domains/memory/{attribution,
spatial_update}.py`, `docs/simulation/domains/memory_contract.md`; `src/world/providers/
resources.py`, `src/ai/goals/scorers.py`, `src/domains/adventure/{scoring,generator,schema}.py`,
`docs/mechanics/adventure_routing_contract.md`; `src/observability/cognition/pattern_miner.py`;
`docs/world/belief_institution_contract.md`.

## Owner-attention decisions

- **Highest priority.** Whether `ResourceOpportunityProvider`/`HarvestScorer` (and any other
  undiscovered CONFLICTING call site) should be re-scoped through perception/knowledge — a
  confirmed, active architecture mismatch, not merely an unbuilt nice-to-have.
- Whether `entity.cognition.knowledge_model` should gain a real consumer, or be considered
  redundant against `strategic.leads`/`BeliefEntry` and deprecated.
- Whether to prioritize building intermediary-link failure modeling (REACH-05) or
  content-distortion (INFO-02) — both remain confirmed-absent, permitted-but-unbuilt gaps.
- Whether `PerceptionUpdatePhase` and `MemoryUpdatePhase`/`ENABLE_MEMORY_UPDATE` should be
  wired live — a rollout decision, not a semantic one.
- Whether a future domain should design a concrete reflex/compulsion/mind-control override
  mechanism, now that AGENCY-02 explicitly permits one.

## Candidate disposition

Eleven Domain Rules (post-merge) were drafted across three families (1 Perception: PERC-01; 5
Knowledge/Information/Memory: KNOW-01, KNOW-02, INFO-01, INFO-02, MEM-02; 5 Agency/Decision:
AGENCY-01–05) — **all accepted, 0 rejected, 0 split.** One merge occurred during the follow-up
review (KNOW-02 + KNOW-03 → KNOW-02), reducing the Domain Rule count from 12 to 11 without
losing any evidence, scenario coverage, or cross-domain link — the merged Rule's own text
carries both original claims. Eight Inherited/Applied Foundational Rules and seven
Scope/Deferred Boundaries (six original, one added by the follow-up for non-ordinary override
mechanisms) round out the 26 total catalog entries.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/knowledge-agency-batch-06-report.md` (local review report, not part of this catalog).

---

> **BATCH 06 PASS — READY TO FREEZE.**
>
> Target semantics are coherent. The repository contains a documented **CONFLICTING**
> implementation gap where some decision paths (`ResourceOpportunityProvider`, `HarvestScorer`)
> bypass subject-local perception/knowledge and read omniscient world state directly — this is
> a real, honestly-recorded architecture mismatch, not a defect in the Rule Catalog itself.

All required artifacts exist: three rule-family files (11 genuine Domain Rules; 26 total
catalog entries), one scenario file (20 scenarios covering all sixteen required seed probes,
one evidence-driven addition, and three follow-up-required adversarial probes), this review
export with all ten required sections plus every explicitly-required call-out, and a local
disposition report. No new contradiction was introduced by the follow-up cleanup within the
target Rules themselves — every revision either generalized an over-specific claim (PERC-01,
KNOW-01, INFO-01, AGENCY-02), merged two Rules that had converged on one boundary (KNOW-02/03),
clarified ambiguous terminology (AGENCY-03), or corrected a Repository Finding's own
classification (CONFLICTING vs. MISSING) — none of which changes what any Rule requires of the
world, only how precisely and honestly that requirement and the repository's relationship to it
are now stated. All twelve of the batch instruction's own stop-condition checklist items remain
satisfied, now more precisely: world truth and belief are kept semantically distinct; perception
does not imply omniscience by default, and explicit exceptions are permitted; information
requires valid propagation paths; false/stale/conflicting information can and does exist, and a
subject may remain confidently wrong indefinitely; memory and world history remain distinct;
decisions can depend on subject-local knowledge, though two call sites currently do not (a
documented CONFLICTING gap, not smoothed over); motivation influences without dictating, and
declared overrides are an explicitly permitted distinct category; capability/authority/
opportunity/decision/success remain distinct, with opportunity now split into two clearly
named tiers; hidden cognition remains compatible with observer legibility; repository
omniscience/inert-state gaps are identified and correctly classified (CONFLICTING vs. INERT/OFF
vs. MISSING); genuine Domain Rules are distinguished from inherited foundations/findings;
adversarial scenarios have been traced, now including three added specifically to confirm the
revised Rules are correctly bounded rather than over-broad.

Do not begin Batch 07 (Capability / Progression / Conflict) until this batch receives
high-level review.
