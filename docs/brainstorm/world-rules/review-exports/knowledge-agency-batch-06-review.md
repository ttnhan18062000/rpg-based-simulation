---
status: active
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
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
file rather than given its own, since its own genuinely new content (MEM-02) and its inherited
content (individual memory ≠ world history) both belong naturally alongside Knowledge's own
category work — no further split or merge was found necessary beyond that one adjustment.
Built directly with the five-category admission discipline Batch 05 established
(`world-rules/roadmap.md`'s standing governance rule) — no separate normalization pass was
needed.

## Canonical files included

- `knowledge-agency/perception.md` (PERC-01)
- `knowledge-agency/knowledge-information.md` (KNOW-01–03, INFO-01–02, MEM-02)
- `knowledge-agency/agency-decision.md` (AGENCY-01–05)
- `scenarios/knowledge-agency-batch-06.md` (KA-S01–S17)

## Rule admission accounting

Per the standing admission discipline: a statement earns a new local Rule ID only if it adds or
refines target world semantics beyond Rules already defined elsewhere. This batch's 26 total
catalog entries break down as:

- **12 genuine Domain Rules**: PERC-01; KNOW-01, KNOW-02, KNOW-03; INFO-01, INFO-02; MEM-02;
  AGENCY-01, AGENCY-02, AGENCY-03, AGENCY-04, AGENCY-05.
- **8 Inherited/Applied Foundational Rules** (direct reuse/reconfirmation, no new claim):
  "world fact ≠ perceived/believed fact" (reuses OWN-04, OWN-06, CAUSE-01), "reach is
  asymmetric" (REACH-03) in `perception.md`; "belief/knowledge is subject-owned, never a
  duplicate of ground truth" (OWN-01, OWN-02, OWN-06), "information requires a real transfer
  path" (REACH-01, REACH-02, REACH-05), "individual memory ≠ world history" (HP-01, OWN-06) in
  `knowledge-information.md`; "capability/authority/reach are independent preconditions"
  (CAP-01, AUTH-01, REACH-01/02), "need pressure/threshold produces real consequence" (SURV-02),
  "a false belief may still be a real cause" (CAUSE-01, Batch 01's FND-S18/S19) in
  `agency-decision.md`.
- **6 Scope/Deferred Boundaries** (no world-semantic claim, only a deferral): formal
  stealth/ambush content, universal perception-formula generalization in `perception.md`; no
  universal epistemology representation, population-scale belief content
  (`BeliefInstitution`) in `knowledge-information.md`; Hybrid Agency's organization-scale
  deferral, detailed psychological modeling in `agency-decision.md`.

**Genuine new-Rule count for this batch: 12.** **Inherited/reused foundation count: 8** (citing
OWN-01/02/04/06, CAUSE-01, REACH-01/02/03/05, HP-01, CAP-01, AUTH-01, SURV-02 — eleven distinct
foundational Rule IDs across the 8 inherited entries).

## Rule Inventory

| ID | Category | Short name | One-line semantic purpose | Status |
|---|---|---|---|---|
| PERC-01 | Domain Rule | Perception Is Bounded and Gated | Capability/channel/distance/attention jointly gate partial access; never automatic or complete. | Accepted |
| KNOW-01 | Domain Rule | Certainty Is Gradable, Never Binary | Every belief/knowledge claim carries its own gradable certainty. | Accepted |
| KNOW-02 | Domain Rule | Belief Changes Only Through a Declared Arrival Path | Hidden world truth is never injected into a subject's belief/knowledge model. | Accepted |
| KNOW-03 | Domain Rule | Contradiction/Staleness Degrade Certainty, Never Self-Correct | Certainty changes only through a real, traceable mechanism. | Accepted |
| INFO-01 | Domain Rule | Source Trust ≠ Claim Certainty | Trust is a distinct, gradually-adjusted per-source property. | Accepted |
| INFO-02 | Domain Rule | Information Content May Change in Transit, Where Declared | Permission for content-level distortion; confirmed unrealized in this repository. | Accepted (mechanism MISSING) |
| MEM-02 | Domain Rule | Experiential Memory ≠ Declarative Knowledge | Causal/spatial/temporal memory is a distinct category from knowledge_model. | Accepted |
| AGENCY-01 | Domain Rule | Decision Stages Are Causally Distinct | Want/choose/capable/authorized/reach/commit/succeed never collapse into one gate. | Accepted |
| AGENCY-02 | Domain Rule | Motivation Weights, Never Forces, Decisions | Need pressure competes inside one scoring formula; multiple motivations may compete. | Accepted |
| AGENCY-03 | Domain Rule | Opportunity ≠ Desire/Capability/Authority | A real, world-relative fact independent of wanting/being-able/being-allowed. | Accepted |
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

| Scenario ID | Short name | Trajectory | Rule families challenged | Deferred domain dependencies | Result |
|---|---|---|---|---|---|
| KA-S01 | See It, Know Something About It | observe → belief → decision | Perception, Knowledge | — | Covered |
| KA-S02 | Event Happens Unobserved | world event → no observer → state changes anyway | Perception | — | Covered |
| KA-S03 | Partial Observation | observe part → incomplete belief, not auto-filled | Perception, Knowledge | — | Covered |
| KA-S04 | False Rumor, Real Action | false report → believed → action → real consequence | Agency (inherited) | — | Covered (reconfirms FND-S18/S19) |
| KA-S05 | Conflicting Reports | source A vs. source B → contradiction/trust handling | Knowledge, Information | — | Covered |
| KA-S06 | Stale Knowledge | learn state → world changes → old belief persists | Knowledge | — | Covered |
| KA-S07 | Information Does Not Teleport | distant event → unrelated entity stays unaware | Knowledge, Reach (inherited) | — | Covered |
| KA-S08 | Rumor Degrades | witness → messenger → recipient → content unchanged | Information, Reach (inherited) | Groups/organizations (future messenger content) | Revealed gap |
| KA-S09 | Memory Fades but History Remains | fact occurs → memory fades → history unchanged | Knowledge/Memory, History/Provenance (inherited) | — | Covered |
| KA-S10 | Decision Reads Omniscient State (added) | goal-scoring selects a never-perceived target | Perception, Agency | — | Revealed missing rule enforcement |
| KA-S11 | Need Influences but Doesn't Dictate | hunger raises priority; another action still chosen | Agency | — | Covered |
| KA-S12 | Capability Without Knowledge | capable but unaware → opportunity not chosen | Agency | — | Covered, with KA-S10 caveat |
| KA-S13 | Knowledge Without Capability | knows what's needed, lacks means → cannot execute | Agency | — | Covered |
| KA-S14 | Opportunity Without Desire | valid opportunity, no motivation → may still be chosen on benefit | Agency | — | Partial |
| KA-S15 | Desire Without Opportunity | strong want, no path → structural fallback instead | Agency | — | Covered, with nuance |
| KA-S16 | Decision Fails | valid decision → committed → outcome fails | Agency | — | Covered |
| KA-S17 | Hidden Motive, Visible Consequence | motive hidden → pattern observable → inferable in principle | Agency | Social relations (future inference content) | Revealed missing rule |

## Coverage Summary

**Perception**
- bounded/gated access, never automatic/complete — KA-S01, KA-S02, KA-S03
- world fact independent of observation — KA-S02
- reach asymmetry — evidenced by reuse, no dedicated new scenario this batch

**Knowledge/Information/Memory**
- certainty as gradable property — KA-S05
- information-opacity invariant (no hidden-truth injection) — KA-S01, KA-S07
- contradiction/staleness degrade certainty — KA-S05, KA-S06
- source trust distinct from claim certainty — KA-S05
- content-level distortion permitted but unrealized — KA-S08
- experiential memory vs. declarative knowledge — KA-S09
- individual memory vs. world history — KA-S09

**Agency/Decision**
- decision-stage distinctness — KA-S12, KA-S13, KA-S16
- motivation weights, doesn't force — KA-S11
- opportunity independent of desire/capability/authority — KA-S12–S15
- decision validity ≠ outcome — KA-S16
- hidden cognition privacy/inference boundary — KA-S17
- omniscient-state reads (cross-cutting Perception ↔ Agency finding) — KA-S10

## Deferred Semantics

An unresolved later-domain question is not the same thing as an incomplete foundational rule —
consistent with every prior batch's own framing:

- Formal stealth/ambush content (concealment, detection rolls) stays deferred, per REACH-03's
  own carried-forward open question — this batch only reconfirms the underlying asymmetry.
- No universal epistemology representation is being built — `BeliefEntry`, `KnowledgeFact`/
  `knowledge_model`, the Memory domain's three subsystems, and `BeliefInstitution` remain
  deliberately separate, per `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION`'s
  own already-confirmed judgment, extended here to the Memory domain and `BeliefInstitution`.
- Population-scale organized belief content (myth drift, culture drift, further
  `BeliefInstitution` design) stays with Social relations/Politics batches.
- Hybrid Agency's organization/settlement/institution-scale coarser models stay deferred, per
  the batch instruction's own locked principle — this batch covers individual agents only.
- Detailed psychological/cognitive-architecture modeling beyond what this repository already
  evidences (personality traits feeding route-scoring bias) is not introduced, per §15's own
  discipline — no new candidate state met the five-part bar (alters decisions, persists
  meaningfully, affected by other systems, observable/inferable, differentiates trajectories).
- INFO-02's content-distortion permission and AGENCY-05's motive-inference mechanism both stay
  unbuilt — deferred to whichever future batch or ticket first needs either (most plausibly
  Groups/organizations & institutions for messenger content, Social relations for
  motive-inference gameplay).

## Cross-domain findings

- Perception ↔ Agency/Decision: KA-S10 is this batch's own most significant cross-cutting
  finding — `ResourceOpportunityProvider.get_opportunities()` and `HarvestScorer.score()` both
  read raw/omniscient world state directly, bypassing `PerceptionGate` and
  `entity.cognition.knowledge_model` entirely. PERC-01 and AGENCY-03 both state the *intended*
  boundary correctly; this repository's actual decision call sites do not yet respect it for at
  least these two paths.
- Knowledge/Information ↔ Reach: INFO-01/INFO-02 and the inherited "information requires a real
  transfer path" entry are, together, the domain-refined completion of REACH-02's and REACH-05's
  own explicitly-flagged forward references — REACH-05's own open question ("flagged for
  whichever future batch, most plausibly Perception/knowledge/information, first needs to model
  mediated reach failure") is reconfirmed still open, not resolved, by this batch's own direct
  investigation.
- Knowledge/Information ↔ History/Provenance: MEM-02's inherited boundary ("individual memory ≠
  world history") directly satisfies HP-01's own explicit non-goal ("rumour propagation...
  stays with Perception/knowledge/information") — this batch is where that deferred content
  was actually built, not merely cross-referenced.
- Agency/Decision ↔ Capability/Authority/Reach (Batch 03/02): AGENCY-01's decision-stage chain
  reuses CAP-01/AUTH-01/REACH-01/02 for its capability/authority/reach nodes without needing to
  re-derive them — the same "foundational Rules predict most of a domain's own shape" pattern
  every prior domain-facing batch has found.
- Agency/Decision ↔ Causality (Batch 01): AGENCY-04's decision-validity/outcome distinction and
  the inherited "false belief may still be a real cause" entry both trace to CAUSE-01 and Batch
  01's own FND-S18/S19 — the batch instruction's own explicit instruction to "revisit Batch 01's
  principle" is satisfied by reuse, per the admission discipline, not by restating it as new.

**Explicit call-out — genuine new Domain Rule count:** 12 (see "Rule admission accounting"
above).

**Explicit call-out — inherited/reused foundation count:** 8 entries, citing 13 distinct
foundational Rule IDs across them (OWN-01, OWN-02, OWN-04, OWN-06, CAUSE-01, REACH-01, REACH-02,
REACH-03, REACH-05, HP-01, CAP-01, AUTH-01, SURV-02).

**Explicit call-out — whether agents currently access omniscient state:** **Yes, confirmed for
at least two major decision paths.** `ResourceOpportunityProvider.get_opportunities()` reads
`state.resource_nodes` directly (region-scoped only, not perception/knowledge-gated, every
opportunity surfaced at `confidence=1.0`); `HarvestScorer.score()` calls
`SpatialQueryService.nearest_resource_node(state, ...)` — the nearest node in the entire world
state. See KA-S10.

**Explicit call-out — whether beliefs materially affect decisions:** **Split verdict.**
`strategic.leads`/`BeliefEntry` (the belief/lead system) materially affects decisions — read by
`src/ai/goals/scorers.py` and routed through `LeadContradictionSystem`/`LeadRoutingSystem`.
`entity.cognition.knowledge_model` (`KnowledgeFact`/`UnknownFact`) does **not** — confirmed no
consumer outside `src/cognition/` itself.

**Explicit call-out — how false/stale information propagates:** False information propagates
exactly like true information at the point of receipt (a rumor is a real belief with lower
certainty, `0.3` vs. `1.0`) — its falseness is never checked at assimilation time, only
discovered later through contradiction (`BeliefContradictionService`) or left to decay through
staleness (`decay_stale_leads()`, and only for non-`PRECISE` leads). Content itself never
degrades or distorts through propagation — only certainty and trust do (KNOW-03, INFO-01,
INFO-02's confirmed gap).

**Explicit call-out — whether information has real reach constraints:** **Yes.** Every
information-arrival path (direct observation, rumor with `source_entity_id`, paid query
response) requires a real, traceable source; nothing teleports knowledge across the world
without one of these paths (KA-S07). Intermediary-link failure modeling remains confirmed
MISSING (REACH-05, reconfirmed).

**Explicit call-out — whether needs/motivations create differentiated choices:** **Yes.**
`AdventureRouteScorer.score()`'s additive formula (urgency + benefit + personality_bias +
confidence_bonus − risk_penalty − blocker_penalty) means different entities with different
needs, traits, and capability estimates score the same opportunity set differently, and the
same entity's own choice shifts as its needs/traits change tick to tick — confirmed
differentiation, not a fixed lookup.

**Explicit call-out — which cognitive state is causally inert:** `entity.cognition.
knowledge_model` (no decision consumer, though internally consistent and tested);
`CausalMemoryEntry.confidence` (typed as gradable, hardcoded to `0.8` for every entry, never
actually varies); the entire Memory domain (causal/spatial/temporal) while
`ENABLE_MEMORY_UPDATE` defaults OFF (wired but inactive); `entity.self_model.capabilities.
estimates` (the persisted storage location, confirmed always empty in production, even though
the estimation logic itself is live and consumed ad hoc elsewhere).

## Repository Findings

No CONFLICTING or UNKNOWN findings. Load-bearing MISSING/gap findings, most significant first:

1. **Decision-making bypasses perception/knowledge entirely for at least two live paths**
   (`ResourceOpportunityProvider`, `HarvestScorer`) — reads raw world state directly. The single
   most load-bearing finding in this batch.
2. **`entity.cognition.knowledge_model` has zero decision-making consumers** outside
   `src/cognition/` itself.
3. **`PerceptionUpdatePhase` (the salience/attention/budget layer) has zero call sites in
   production** — only the upstream binary `PerceptionGate` is confirmed live.
4. **`MemoryUpdatePhase` is wired but inactive** — gated behind `ENABLE_MEMORY_UPDATE`, default
   OFF.
5. **No in-simulation motive-inference mechanism exists** — `CognitionPatternMiner` is offline
   developer tooling, not a world mechanism.
6. **`CapabilityEstimateService` is scorer-local/ad hoc and architecturally split from the
   entity's own persisted self-model** — `entity.self_model.capabilities.estimates` stays empty
   in production; no active confidence decay.
7. **No intermediary-link failure modeling** (messenger delayed/blocked/lying) — reconfirms
   REACH-05's already-flagged gap.
8. **No content-level distortion through information transmission** — only certainty/trust
   vary; content itself never does.
9. **A minor naming collision** (two distinct `KnowledgeFact` classes across
   `src/world/providers/information.py` and `src/core/self_model.py`) — not a semantic gap,
   flagged so a future author isn't misled.

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

- Whether `ResourceOpportunityProvider`/`HarvestScorer` (and any other undiscovered
  omniscience-reading call site) should be re-scoped through perception/knowledge is the single
  highest-priority implementation question this batch surfaces — a real architecture gap
  between intended and actual cognitive-gating behavior, not merely an unbuilt nice-to-have.
- Whether `entity.cognition.knowledge_model` should gain a real consumer, or be considered
  redundant against `strategic.leads`/`BeliefEntry` and deprecated, is a real design fork not
  decided here.
- Whether to prioritize building intermediary-link failure modeling (REACH-05) or
  content-distortion (INFO-02) — both remain confirmed-absent, permitted-but-unbuilt gaps.
- Whether `PerceptionUpdatePhase` and `MemoryUpdatePhase`/`ENABLE_MEMORY_UPDATE` should be
  wired live is a rollout decision, not a semantic one.

## Candidate disposition

Twelve Domain Rules were drafted across three families (1 Perception, 6 Knowledge/Information/
Memory, 5 Agency/Decision) — **all 12 accepted, 0 rejected, 0 split, 0 merged.** Eight further
entries were identified as Inherited/Applied Foundational Rules and six as Scope/Deferred
Boundaries, per the admission discipline — none of these required a new Rule ID, and none
represents lost work: every one carries its own evidence and cross-domain link. The batch
instruction's own suggested file grouping (perception / knowledge-information / agency-decision)
was kept, with Memory folded into the Knowledge/Information file rather than given a fourth —
investigated directly and found to fit naturally rather than requiring its own file.

Full per-rule disposition, evidence, and rationale: see the canonical files above, or
`tmp/knowledge-agency-batch-06-report.md` (local review report, not part of this catalog).

---

> **BATCH 06 (PERCEPTION / KNOWLEDGE / INFORMATION / AGENCY) READY FOR HIGH-LEVEL EXTERNAL
> REVIEW.**

All required artifacts exist: three rule-family files (12 genuine Domain Rules; 26 total
catalog entries including inherited/scope entries), one scenario file (17 scenarios covering all
sixteen required seed probes plus one directly evidence-driven addition), this review export
with all ten required sections plus every explicitly-required call-out, and a local disposition
report. All twelve of the batch instruction's own stop-condition checklist items are satisfied:
world truth and belief are kept semantically distinct (PERC-01, inherited OWN-04/06); perception
does not imply omniscience (PERC-01) — though the batch's own investigation found that *decision-
making*, as distinct from perception itself, currently does read omniscient state, and this is
recorded honestly as a Repository Finding, not smoothed over; information requires valid
propagation paths (INFO-01/02, inherited REACH-01/02/05); false/stale/conflicting information
can and does exist (KA-S04–S06); memory and world history remain distinct (MEM-02); decisions
can depend on subject-local knowledge (AGENCY-01, though two call sites currently bypass this);
motivation influences without dictating (AGENCY-02); capability/authority/opportunity/decision/
success remain distinct (AGENCY-01, AGENCY-03, AGENCY-04); hidden cognition remains compatible
with observer legibility (AGENCY-05, inference mechanism confirmed not yet built);
repository omniscience/inert-state gaps are identified (Repository Findings, above); genuine
Domain Rules are distinguished from inherited foundations/findings (Rule admission accounting,
above); adversarial scenarios have been traced (KA-S01–S17, including two explicit counter/
partial results at KA-S08 and KA-S14).

Do not begin Batch 07 (Capability / Progression / Conflict) until this batch receives
high-level review.
