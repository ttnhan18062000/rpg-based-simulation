---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Knowledge / Information / Memory

**Purpose/scope.** What it means for a subject to believe, know, suspect, remember, or
misunderstand something; how information moves between subjects, places, or processes; and what
persists within an individual versus within the world's own historical record. Does not require
one universal epistemology representation — this repository legitimately maintains several
parallel belief/knowledge/memory mechanisms rather than one unified model, and this family
states the boundary between them rather than forcing a merge.

**Status.** Batch 06 (Perception/Knowledge/Information/Agency), drafted 2026-09-22, revised the
same day per follow-up review (`tmp/world-rule-batch-6-followup-ext-ai.md`): KNOW-01 loosened
so exact/categorical knowledge remains permitted, not every claim required to be gradable;
KNOW-02 and KNOW-03 merged into one rule after the refinement removed the semantic distance
between them (both now describe the same "no automatic re-sync, only declared revision"
boundary); INFO-01 loosened so trust's specific shape (gradual, per-source) is one legitimate
example, not a universal requirement. Candidates below originated as external-reviewer
hypotheses (`tmp/world-rule-batch-6-ext-ai.md`); each carries this session's disposition and
repository evidence. Structured per the normalized five-category methodology established in
Batch 05's admission-discipline pass.

---

## Domain Rules

## KNOW-01 — Belief/knowledge semantics must permit uncertainty where causally relevant, distinct from objective truth

> Belief/knowledge semantics must permit uncertainty or confidence to be represented where it
> is causally relevant — a claim's confidence and the world's own objective truth are always
> distinct facts, whatever representation is used. This does not require *every* belief or
> knowledge claim to carry a gradable certainty value: exact or categorical knowledge (a claim
> simply held as true, with no gradation) remains a legitimate representation wherever
> gradation would add no causal value. Where certainty is represented, different claims about
> the same subject may carry different certainty at the same time.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — loosened from a universal
"every claim is gradable" requirement to a permission.** The original wording risked implying
gradability is mandatory everywhere; the fix keeps the same repository evidence as one rich,
real example of the permission being exercised, not as proof the permission is a requirement.
Passes the admission test: no earlier Rule states that belief/knowledge representations must be
*permitted* to carry uncertainty distinct from truth — this is genuinely new domain content.

**Repository evidence: SUPPORTED, richly and redundantly across independent mechanisms, as one
legitimate way of exercising this permission — not the only legitimate shape.**
`LeadCertainty` is a four-step gradient (`PRECISE` → `APPROXIMATE` → `VAGUE` → `EXHAUSTED`);
`BeliefEntry.certainty` is a continuous `0.0–1.0` float (`process_observation()` seeds `1.0`,
`process_rumor()` seeds `0.3` for the same kind of claim from a lower-trust channel);
`KnowledgeFact.certainty` (`src/core/self_model.py`) and `InformationResponse.certainty` carry
the same continuous scale through the information-assimilation pipeline. Three
independently-implemented mechanisms all converge on "certainty may be graded where relevant" —
none of them is evidence that gradation is mandatory for every claim; a `KnowledgeFact` with
`certainty=1.0` and no further gradation is an equally valid, exact/categorical use of the same
type.

**Scenarios:** [KA-S05](../scenarios/knowledge-agency-batch-06.md#ka-s05) (conflicting
reports).

---

## KNOW-02 — Belief/knowledge revises only through a declared process; it never automatically re-syncs with changing world truth or injects hidden ground truth

> A subject's belief or knowledge model changes only through a real, declared process:
> observation, a report from another subject, a paid query response, a deduction from existing
> beliefs, contradiction by a later direct observation, or staleness/decay from age without
> refresh. Two things never happen outside such a declared process: hidden ground-truth world
> state is never injected directly into a subject's own belief/knowledge model (even when that
> state is fully known to the simulation itself), and a belief never automatically re-synchronizes
> with the world once the world changes. A subject may therefore remain confidently, stably
> wrong for as long as no declared revision process actually runs against that specific claim —
> this is expected, not a bug.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — merged with the original
draft's separate KNOW-03.** The follow-up's own refinement of what became KNOW-03 (no automatic
lowering of certainty; a subject may remain confidently wrong; only a declared process revises
certainty/content) converges on the same underlying boundary KNOW-02 already stated (no
automatic truth-injection/re-sync; only a declared arrival/revision path changes belief) — once
stated this way, the two no longer add separate semantics, so they are merged under this one ID
rather than kept as two Rules restating the same boundary from two directions. Passes the
admission test as merged content: the *mechanism* by which belief may change — including staying
unchanged while the world moves on — is domain-specific content no earlier Rule states.

**Repository evidence: SUPPORTED — both the injection-prohibition and the no-auto-resync halves
are confirmed by direct, independent mechanisms.** `docs/cognition/capability_and_knowledge_
contract.md` names the injection half directly: "Hidden world truth is NEVER injected. Only
what the `InformationResponse` returned is assimilated. This preserves information opacity."
`KnowledgeModelService.assimilate()` only ever consumes `InformationResponse` records
(`answer_kind` ∈ `known`/`partial`/`unknown`/`insufficient_gold`); `BeliefCycleSystem.
process_observation()`/`process_rumor()` only ever construct beliefs from an explicit
observation or a named `source_entity_id`'s rumor — no code path in either mechanism reads
`AuthoritativeState` directly and writes it into a subject's own belief/knowledge fields. The
no-auto-resync half is equally direct: `BeliefContradictionService.detect()` only demotes a
lead's certainty by exactly one step (`PRECISE`→`APPROXIMATE`→`VAGUE`→`EXHAUSTED`) when a
*direct observation* actually conflicts with it — absent that event, certainty is stable
indefinitely even after the underlying world fact changes. `BeliefCycleSystem.
decay_stale_leads()` independently demotes only `APPROXIMATE`/`VAGUE` leads after
`stale_threshold=50` ticks without refresh — explicitly **not** `PRECISE` leads ("direct
observations decay slower") — meaning a `PRECISE` belief can remain at full certainty
indefinitely, confidently wrong, until a fresh observation or explicit contradiction actually
runs. Neither mechanism ever restores or corrects certainty without such an event.

**Scenarios:** [KA-S01](../scenarios/knowledge-agency-batch-06.md#ka-s01),
[KA-S06](../scenarios/knowledge-agency-batch-06.md#ka-s06) (stale knowledge),
[KA-S07](../scenarios/knowledge-agency-batch-06.md#ka-s07) (information does not teleport),
[KA-S19](../scenarios/knowledge-agency-batch-06.md#ka-s19) (stale but confident).

---

## INFO-01 — Source trust is a distinct property of an information source, separate from the certainty of any one claim it provides

> A subject may track trust in an information source separately from the certainty of any
> individual claim that source has provided — the two are always distinct properties, whatever
> shape trust takes. This repository's own trust mechanism happens to be gradual and per-source,
> but that specific shape is not a universal requirement: trust may legitimately be
> source-specific, relationship-specific, institution-specific, contextual, or abruptly revised
> by a single decisive event, depending on whatever later domain (Social relations, Politics,
> Groups/organizations) actually needs. What is required is only the distinctness itself: trust
> in a source is never the same fact as the certainty of a claim that source provided.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — loosened from a universal
"gradually-adjusted, per-source" requirement to one legitimate example among several possible
shapes.** The original wording over-specified how trust must behave; the fix keeps the
distinctness claim (INFO-01's own core point) while explicitly permitting later domains to
declare a differently-shaped trust mechanism. Passes the admission test: distinguishing a
*source's* trustworthiness from a *claim's* certainty is a genuinely new domain distinction —
neither KNOW-01 nor any earlier Rule separates these two properties explicitly.

**Repository evidence: SUPPORTED for the distinctness claim; SUPPORTED as one legitimate,
real example of a gradual/per-source shape, not evidence that this is the only valid shape.**
`SourceTrustUpdateService.update()` (`src/domains/information/trust.py`) tracks
`SourceTrustEntry` per `(entity, source_entity_id)` pair, clamped to `[0.0, 1.0]`, adjusted
gradually by outcome (`CONFIRMED` raises, `CONTRADICTED` lowers by a larger delta,
`NOT_VERIFIABLE` has no effect) — never a single-outcome full flip in *this* mechanism.
`InformationSourceKind` (`GUIDE`/`GUILD`/`BLACKSMITH`/`TRAVELER`) seeds a source-kind-dependent
initial trust, and "an entity only assimilates facts from sources whose trust ≥ the entity's
assimilation threshold" (per `docs/simulation/domains/information_contract.md`) — trust gates
assimilation eligibility; it is not itself the certainty value assimilated. Nothing in this
evidence is read as prohibiting a future, differently-shaped trust mechanism (e.g. an
institution-wide trust collapse on a single betrayal) from also being valid.

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
(KNOW-01, KNOW-02, INFO-01) but never the *content* of a claim as it passes through an
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

Classified per the three-way distinction sharpened by the 2026-09-22 follow-up review:
**CONFLICTING** (a live, active behavior that violates a target Rule's own boundary),
**INERT/OFF** (a real mechanism that simply does not run, violating nothing because nothing
runs), or **MISSING** (a permitted mechanism never built at all).

- **INERT/OFF — `entity.cognition.knowledge_model` (`KnowledgeFact`/`UnknownFact`) has no
  consumer outside `src/cognition/` itself.** Checked directly: no decision-making system —
  adventure routing, goal scoring, or any other — reads assimilated knowledge facts. Decisions
  that do depend on belief-like state instead read the separate, lighter-weight
  `entity.strategic.leads`/`entity.strategic.beliefs` (`BeliefEntry`) system (confirmed live via
  `src/ai/goals/scorers.py` and `LeadContradictionSystem`). This answers the batch instruction's
  own required call-out ("whether beliefs materially affect decisions") with a split verdict:
  YES for `leads`/`BeliefEntry`, NO for `knowledge_model` specifically. Classified INERT/OFF, not
  CONFLICTING: `knowledge_model` does not actively violate KNOW-02's own boundary (nothing reads
  hidden truth into it, per KNOW-02's own confirmed evidence) — it is simply never consumed
  downstream, a dormant mechanism rather than an active mismatch.
- **INERT/OFF — `MemoryUpdatePhase` (causal/spatial/temporal memory) is wired into the pipeline
  but gated behind `ENABLE_MEMORY_UPDATE`, which defaults OFF** — wired-but-inactive in
  production, per `docs/simulation/domains/memory_contract.md`'s own disclosure.
  Causal-memory-informed route suppression (`avoid_enemy`→suppress `HUNT_WEAK_ENEMY`) exists in
  `AdventureRouteScorer.score()` but only takes effect when the flag is on.
  `CausalMemoryEntry.confidence` is a hardcoded constant (`0.8`) for every entry regardless of
  cause — the field exists and is typed as gradable (consistent with KNOW-01's own permission,
  not a violation of it — KNOW-01 never requires that gradability be exercised), but this
  repository's own producer never varies it.
- **A minor naming collision, not a semantic gap.** Two distinct `KnowledgeFact` classes exist:
  a minimal `subject`/`fact_type`/`details` version in `src/world/providers/information.py`
  (the provider-layer response shape) and a richer `subject`/`fact_type`/`details`/`certainty`/
  `source_id`/`recorded_tick` version in `src/core/self_model.py` (the assimilated, owned
  record). `normalizer.py` bridges between them. Worth naming so a future author isn't misled by
  the identical class name across two layers; not a Rule-level concern.

**No CONFLICTING finding was identified within this specific family.** The one significant
CONFLICTING finding this batch produced (decision-making bypassing perception/knowledge
entirely) is Perception- and Agency-side — see `perception.md`'s and `agency-decision.md`'s own
Repository Findings for the full evidence; it is not duplicated here since neither
`ResourceOpportunityProvider` nor `HarvestScorer` touches this family's own state
(`knowledge_model`, `strategic.leads`/`beliefs`, the Memory domain) at all — the mismatch is
that they bypass this family's state entirely, not that they corrupt it.

## Cross-domain links recorded here

- KNOW-01, KNOW-02 → Perception (`perception.md`'s PERC-01, what reaches a subject before it
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
