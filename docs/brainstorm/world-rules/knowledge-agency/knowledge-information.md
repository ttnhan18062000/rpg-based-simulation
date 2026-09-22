---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
---

# World Rule Family: Knowledge / Information / Memory

**Purpose/scope.** What it means for a subject to believe, know, suspect, remember, or
misunderstand something; how information moves between subjects, places, or processes; and what
persists within an individual versus within the world's own historical record. Does not require
one universal epistemology representation — this repository legitimately maintains several
parallel belief/knowledge/memory mechanisms rather than one unified model, and this family
states the boundary between them rather than forcing a merge.

**Status.** Batch 06 (Perception/Knowledge/Information/Agency), first draft. Candidates below
originated as external-reviewer hypotheses (`tmp/world-rule-batch-6-ext-ai.md`); each carries
this session's disposition and repository evidence. Structured per the normalized five-category
methodology established in Batch 05's admission-discipline pass.

---

## Domain Rules

## KNOW-01 — Certainty is a first-class, gradable property of a belief or knowledge claim, never binary

> Whether a subject "knows" something is not a binary known/unknown fact — every belief or
> knowledge claim carries its own gradable certainty/confidence value, and different claims
> about the same subject may carry different certainty at the same time.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states that certainty is
itself a first-class, gradable dimension of a claim — this is genuinely new domain content for
Knowledge/Belief.

**Repository evidence: SUPPORTED, richly and redundantly across independent mechanisms.**
`LeadCertainty` is a four-step gradient (`PRECISE` → `APPROXIMATE` → `VAGUE` → `EXHAUSTED`, not
a binary); `BeliefEntry.certainty` is a continuous `0.0–1.0` float (`process_observation()`
seeds `1.0`, `process_rumor()` seeds `0.3` for the same kind of claim from a lower-trust
channel); `KnowledgeFact.certainty` (`src/core/self_model.py`) and `InformationResponse.
certainty` carry the same continuous scale through the information-assimilation pipeline. Three
independently-implemented mechanisms all converge on "certainty is graded," not accidental
duplication of one idea.

**Scenarios:** [KA-S05](../scenarios/knowledge-agency-batch-06.md#ka-s05) (conflicting
reports).

---

## KNOW-02 — Belief/knowledge state may change only through a declared information-arrival path, never by injecting hidden world truth

> A subject's belief or knowledge model may only be updated through a real, declared arrival
> event — direct observation, a report from another subject, a paid query response, or a
> deduction from existing beliefs. Hidden ground-truth world state is never injected directly
> into a subject's own belief/knowledge model, even when that state is fully known to the
> simulation itself.

**Disposition: ACCEPT.** Passes the admission test: this is a domain-specific integrity
invariant for how a subject's *own* cognitive state may be written — distinct from OWN-04/
OWN-06's claim that belief and truth are different *facts* (Inherited, below); this Rule is
about the *mechanism* by which one becomes the other, which no earlier Rule states.

**Repository evidence: SUPPORTED — this is a named, explicit invariant in the repository's own
documentation, not an inferred pattern.** `docs/cognition/capability_and_knowledge_contract.md`
names it directly: "Hidden world truth is NEVER injected. Only what the `InformationResponse`
returned is assimilated. This preserves information opacity." `KnowledgeModelService.
assimilate()` only ever consumes `InformationResponse` records (`answer_kind` ∈
`known`/`partial`/`unknown`/`insufficient_gold`); `BeliefCycleSystem.process_observation()`/
`process_rumor()` only ever construct beliefs from an explicit observation or a named
`source_entity_id`'s rumor — there is no code path in either mechanism that reads
`AuthoritativeState` directly and writes it into a subject's own belief/knowledge fields.

**Scenarios:** [KA-S01](../scenarios/knowledge-agency-batch-06.md#ka-s01),
[KA-S07](../scenarios/knowledge-agency-batch-06.md#ka-s07) (information does not teleport).

---

## KNOW-03 — Contradiction and staleness degrade certainty through a real, traceable process; belief never self-corrects or vanishes silently

> A belief or knowledge claim's certainty does not spontaneously correct itself toward truth,
> and does not silently disappear. It degrades only through a real, traceable mechanism:
> contradiction by a later direct observation, or staleness from age without refresh. Absent
> either, a claim's certainty is stable, even if the underlying world fact has since changed.

**Disposition: ACCEPT.** Passes the admission test: the mechanics of *how* a claim's certainty
changes over time or under conflict is new domain content — no earlier Rule addresses this.

**Repository evidence: SUPPORTED, by two independent, real mechanisms.**
`BeliefContradictionService.detect()` demotes a lead's certainty by exactly one step
(`PRECISE`→`APPROXIMATE`→`VAGUE`→`EXHAUSTED`) when a direct observation conflicts with it (e.g.
`region_danger_seen` contradicting a `VAGUE`/`APPROXIMATE` "safe" rumor), and degrades the
matching `BeliefEntry.certainty` by `0.3` while incrementing `contradictions`.
`BeliefCycleSystem.decay_stale_leads()` independently demotes `APPROXIMATE`/`VAGUE` leads one
step after `stale_threshold=50` ticks without refresh — but explicitly **not** `PRECISE` leads
("direct observations decay slower") and never `EXHAUSTED` ones. Neither mechanism ever
restores certainty upward without a fresh, real observation.

**Scenarios:** [KA-S06](../scenarios/knowledge-agency-batch-06.md#ka-s06) (stale knowledge),
[KA-S05](../scenarios/knowledge-agency-batch-06.md#ka-s05).

---

## INFO-01 — Source trust is a distinct, gradually-adjusted property of an information source, separate from the certainty of any one claim it provides

> A subject tracks trust per information source (per `(entity, source)` pair), separately from
> the certainty of any individual claim that source has provided. Trust changes gradually —
> confirmation, contradiction, and unverifiable outcomes each move it by a bounded amount, never
> a full flip — and constrains, but does not by itself determine, the certainty assigned to a
> newly-received claim.

**Disposition: ACCEPT.** Passes the admission test: distinguishing a *source's* trustworthiness
from a *claim's* certainty is a genuinely new domain distinction — neither KNOW-01 nor any
earlier Rule separates these two properties explicitly.

**Repository evidence: SUPPORTED.** `SourceTrustUpdateService.update()`
(`src/domains/information/trust.py`) tracks `SourceTrustEntry` per `(entity, source_entity_id)`
pair, clamped to `[0.0, 1.0]`, adjusted gradually by outcome (`CONFIRMED` raises, `CONTRADICTED`
lowers by a larger delta, `NOT_VERIFIABLE` has no effect) — never a single-outcome full flip.
`InformationSourceKind` (`GUIDE`/`GUILD`/`BLACKSMITH`/`TRAVELER`) seeds a source-kind-dependent
initial trust, and "an entity only assimilates facts from sources whose trust ≥ the entity's
assimilation threshold" (per `docs/simulation/domains/information_contract.md`) — trust gates
assimilation eligibility; it is not itself the certainty value assimilated.

**Scenarios:** [KA-S05](../scenarios/knowledge-agency-batch-06.md#ka-s05).

---

## INFO-02 — Information content, not only its certainty, may legitimately change through transmission or storage wherever a declared mechanism does so

> Loss, distortion, compression, reinterpretation, or fabrication of information *content*
> (as distinct from a mere reduction in the certainty attached to unchanged content) is
> permitted wherever a world mechanism explicitly declares it. This is never assumed to happen
> uniformly for every channel, and its absence in this repository's current mechanisms is not a
> violation of the permission — only evidence that no such mechanism has been built yet.

**Disposition: ACCEPT, with a confirmed absence this batch's own investigation found.** The
batch instruction explicitly required investigating whether information transforms through
transmission — the honest finding is that this repository currently varies *certainty/trust*
(KNOW-01, KNOW-03, INFO-01) but never the *content* of a claim as it passes through an
intermediary.

**Repository Finding: MISSING, confirmed directly.** `BeliefCycleSystem.process_rumor()` takes
`rumor_detail` directly from the report and assigns a fixed lower certainty (`0.3`) — it does
not model any intermediary transformation of the detail string itself (no loss, no distortion,
no compression). This reconfirms REACH-05's own already-flagged gap (mediated reach exists, but
"no mechanism currently models a messenger's own failure modes... as a distinct causal event")
from Information's own vantage point: the same absence, seen from the content side rather than
the reach side.

**Scenarios:** [KA-S08](../scenarios/knowledge-agency-batch-06.md#ka-s08) (rumor degrades —
revealed gap, not a rule violation).

---

## MEM-02 — Experiential memory and declarative belief/knowledge are distinct categories, tracked by separate mechanisms

> An entity's experiential memory (lessons learned from past failures, familiarity/danger
> associated with places it has been, urgency derived from active deadlines) is a different
> kind of state from its declarative belief/knowledge claims (structured facts and leads about
> the world it has been told or observed). Both may coexist and be tracked by entirely separate
> mechanisms without collapsing into one representation.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule distinguishes experiential
from declarative cognitive state — this is a genuinely new categorical distinction, and the
repository's own documentation independently arrived at exactly this boundary.

**Repository evidence: SUPPORTED — the repository's own contract explicitly names this
boundary as a disambiguation, not an accident.** `docs/simulation/domains/memory_contract.md`'s
"Disambiguation: Memory Domain vs. Knowledge Model" table states directly: "Confusing them leads
to incorrect attribution of where entity cognition state is managed." The Memory domain
(`src/domains/memory/`) owns three separate experiential subsystems — causal memory
(`CausalMemoryEntry`: cause/advice/confidence extracted from a qualifying failure event, FIFO
capacity-bounded), spatial memory (per-region familiarity `+0.15`/tick capped at `1.0`, and a
danger flag on `combat_loss`/`near_death`), and temporal memory (`TemporalModel.urgency`,
recalculated every tick from deadlines and need-profile urgency) — while the Knowledge model
(`src/cognition/knowledge_model.py`) owns structured `KnowledgeFact`/`UnknownFact` records.
Neither domain writes to the other's fields.

**Scenarios:** [KA-S09](../scenarios/knowledge-agency-batch-06.md#ka-s09) (memory fades but
history remains).

---

## Inherited / Applied Foundational Rules

### Belief/knowledge is a subject-owned representation, never a duplicate of the relevant world domain's own owned ground truth

> Belief, knowledge, and memory state describe (possibly wrong) claims about the world; they
> never become, substitute for, or duplicate the authoritative ground truth the relevant world
> domain itself owns.

**Disposition: INHERITED — direct reuse of OWN-01 ("one authoritative source of durable
truth"), OWN-02 ("participation does not imply ownership"), and OWN-06 ("historical reference
does not imply present ownership... a belief being held does not make it true"). No new claim:
this is exactly OWN-06's own worked principle, restated at Knowledge's point of use.**

**Repository evidence: SUPPORTED, reused directly.** `BeliefEntry`/`LeadState`/`KnowledgeFact`
records are all explicitly modeled as possibly-wrong subject-owned state; nothing in the
belief, lead, or knowledge-model machinery ever writes back into the authoritative fact it
describes. See this file's own Repository Findings, below, for a real risk case adjacent to
this principle (decision systems reading raw world state rather than routing through this
subject-owned layer).

**Scenarios:** none newly traced; reuses Batch 01's own FND-S04/S09/S18/S20 evidence directly.

### Information requires a real transfer path or intermediary link; it does not spontaneously synchronize

> Information moving from one subject to another requires a real reach path — direct or
> mediated through one or more intermediary links, each with its own constraints and possible
> failure modes. It never magically synchronizes across the world the instant one subject learns
> it.

**Disposition: INHERITED — direct reuse of REACH-01 (reach is a precondition for a valid
causal claim), REACH-02 (information is a real, non-spatial reach channel, "carried forward by
a present carrier"), and REACH-05 (mediated reach exists through intermediary links, with
intermediary-failure modeling already confirmed MISSING by Batch 02 and specifically flagged
for this batch). No new reach-level claim: this batch's own contribution is INFO-02's
content-transformation angle (above) and the confirmed reconfirmation that REACH-05's gap still
holds.**

**Repository evidence: SUPPORTED for reach-through-a-channel; reconfirmed MISSING for
intermediary-failure modeling.** `BeliefCycleSystem.process_rumor()` (source_entity_id-sourced,
lower certainty) versus `process_observation()` (direct, full certainty) confirms the reach
channel distinction; no messenger-failure mechanism exists, matching REACH-05's own
already-flagged gap exactly.

**Scenarios:** [KA-S07](../scenarios/knowledge-agency-batch-06.md#ka-s07),
[KA-S08](../scenarios/knowledge-agency-batch-06.md#ka-s08).

### Individual memory fading or reinterpretation does not rewrite the world's own historical fact

> An individual forgetting, misremembering, or reinterpreting a past fact never changes the
> world's own historical record of what actually happened.

**Disposition: INHERITED — direct reuse of HP-01 (historical continuity survives ordinary
change) and OWN-06 (belief ≠ truth). HP-01's own explicit non-goals list names "rumour
propagation" as staying with this family — this batch supplies exactly that content (KNOW-01–03,
INFO-01–02, MEM-02) without needing to restate HP-01's own historical-continuity claim.**

**Repository evidence: SUPPORTED**, reused directly: nothing in `BeliefCycleSystem`,
`KnowledgeModelService`, or the Memory domain ever writes to the Chronicle/`NarrativeLedger`
machinery HP-01's own evidence is built on — individual-level belief/memory decay and
world-level historical record are tracked by entirely non-overlapping mechanisms.

**Scenarios:** [KA-S09](../scenarios/knowledge-agency-batch-06.md#ka-s09).

---

## Scope / Deferred Boundaries

### No universal epistemology representation

> This family does not unify `BeliefEntry`, `KnowledgeFact`/`knowledge_model`, the Memory
> domain's three experiential subsystems, and `BeliefInstitution` (population-scale organized
> belief, `docs/world/belief_institution_contract.md`) into one epistemology model. The batch
> instruction explicitly required this: "do not require one universal epistemology
> representation." `TCK-20260904-KNOWLEDGE-BELIEF-REPRESENTATION-RECONCILIATION` already
> confirmed the `BeliefEntry`/`KnowledgeFact` split is deliberate, not accidental duplication;
> this family extends that same judgment to the Memory domain and `BeliefInstitution` as
> further deliberately-separate representations, each with its own real evidence and role.

**Disposition: SCOPE BOUNDARY.**

### Population-scale organized belief (`BeliefInstitution`)

> `BeliefInstitution` (clan-level organized reverence around a real, Chronicle-recorded legend)
> is real, live-consumed evidence that belief exists at population scale as well as individual
> scale — but designing further population-scale belief/culture content (myth drift, culture
> drift) remains with Social relations/Politics batches, not this one.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

- **Confirmed — `entity.cognition.knowledge_model` (`KnowledgeFact`/`UnknownFact`) has no
  consumer outside `src/cognition/` itself.** Checked directly: no decision-making system —
  adventure routing, goal scoring, or any other — reads assimilated knowledge facts. Decisions
  that do depend on belief-like state instead read the separate, lighter-weight
  `entity.strategic.leads`/`entity.strategic.beliefs` (`BeliefEntry`) system (confirmed live via
  `src/ai/goals/scorers.py` and `LeadContradictionSystem`). This answers the batch instruction's
  own required call-out ("whether beliefs materially affect decisions") with a split verdict:
  YES for `leads`/`BeliefEntry`, NO for `knowledge_model` specifically.
- **Confirmed — `MemoryUpdatePhase` (causal/spatial/temporal memory) is wired into the pipeline
  but gated behind `ENABLE_MEMORY_UPDATE`, which defaults OFF** — wired-but-inactive in
  production, per `docs/simulation/domains/memory_contract.md`'s own disclosure.
  Causal-memory-informed route suppression (`avoid_enemy`→suppress `HUNT_WEAK_ENEMY`) exists in
  `AdventureRouteScorer.score()` but only takes effect when the flag is on.
  `CausalMemoryEntry.confidence` is a hardcoded constant (`0.8`) for every entry regardless of
  cause — the field exists and is typed as gradable, but this repository's own producer never
  varies it.
- **A minor naming collision, not a semantic gap.** Two distinct `KnowledgeFact` classes exist:
  a minimal `subject`/`fact_type`/`details` version in `src/world/providers/information.py`
  (the provider-layer response shape) and a richer `subject`/`fact_type`/`details`/`certainty`/
  `source_id`/`recorded_tick` version in `src/core/self_model.py` (the assimilated, owned
  record). `normalizer.py` bridges between them. Worth naming so a future author isn't misled by
  the identical class name across two layers; not a Rule-level concern.

## Cross-domain links recorded here

- KNOW-01, KNOW-03 → Perception (`perception.md`'s PERC-01, what reaches a subject before it
  can even become a belief)
- KNOW-02 → State Ownership (OWN-04, OWN-06, inherited above), Agency/decision
  (`agency-decision.md`, decisions built on possibly-wrong knowledge)
- INFO-01, INFO-02 → Reach (REACH-01, REACH-02, REACH-05, inherited above)
- MEM-02 → History/Provenance (HP-01, inherited above), Family/lineage & succession (no link
  found; not investigated further here)

## Open questions carried forward

1. Whether `entity.cognition.knowledge_model` should gain a real decision-making consumer, or
   whether `strategic.leads`/`BeliefEntry` should absorb its role entirely (making
   `knowledge_model` redundant rather than merely unconsumed), is a real design question for a
   future batch or ticket — not decided here.
2. Whether `ENABLE_MEMORY_UPDATE` should be turned on is an implementation/rollout decision,
   not a semantic one.
3. INFO-02's content-distortion permission remains unexercised by any current mechanism — left
   open for whichever future batch or ticket first wants a messenger/rumor content-transform
   mechanism (most plausibly Groups/organizations & institutions, for guild/messenger content).
