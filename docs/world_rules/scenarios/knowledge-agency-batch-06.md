---
status: authoritative
layer: architecture
authority: P2
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# Scenario Bank: Perception / Knowledge / Information / Agency (Batch 06)

**Purpose/scope.** Twenty scenarios used to pressure-test the Perception, Knowledge/
Information/Memory, and Agency/Decision rule families in `knowledge-agency/perception.md`,
`knowledge-agency/knowledge-information.md`, and `knowledge-agency/agency-decision.md`, per
`tmp/world-rule-batch-6-ext-ai.md` and its 2026-09-22 follow-up
(`tmp/world-rule-batch-6-followup-ext-ai.md`). Covers all sixteen required seed probes from the
original instruction's §11, plus one additional scenario (KA-S10) added directly from this
batch's own repository investigation, plus three further adversarial probes the follow-up
review required (KA-S18–S20).

Scoring uses the same vocabulary as prior batches: **covered** / **partially covered** /
**blocked** / **revealed missing rule** / **revealed contradiction**, against current
repository behavior, not the ideal design.

---

## KA-S01 — See it, know something about it

An entity observes an event; obtains a knowledge/belief claim; a later decision may use it.

- **Rules invoked:** PERC-01, KNOW-02.
- **Result: covered.** `PerceptionGate.can_perceive()` gates whether a signal is even
  available; `BeliefCycleSystem.process_observation()` converts a direct observation into a
  `PRECISE`/`1.0`-certainty `LeadState`/`BeliefEntry` pair; `src/ai/goals/scorers.py` reads
  `strategic.leads` for goal scoring — a real, traceable perceive→believe→decide path exists,
  even though the richer `PerceptionUpdatePhase` salience layer itself does not run in
  production (PERC-01's own finding).

## KA-S02 — Event happens unobserved

A world event occurs; nobody perceives it; world state changes anyway.

- **Rules invoked:** PERC-01 (Inherited: world fact independent of perception).
- **Result: covered.** The typed `Update`/`Patch`/`AuthoritativeState` apply path commits durable
  state changes (a resource node depleting, a calamity striking a region) without any entity's
  perception or cognition as an input — confirmed by construction, not merely by absence of a
  counter-example.

## KA-S03 — Partial observation

An entity observes only part of an event; forms an incomplete belief; missing facts are not
automatically filled from world truth.

- **Rules invoked:** PERC-01, KNOW-02.
- **Result: covered.** `PerceptionFilterService.filter()`'s budget-clamped partitioning
  (`max_perceived=10`, overflow recorded as `IgnoredSignal` up to `max_ignored_to_record=5`,
  the rest silently dropped) produces exactly this: an incomplete, budget-bounded observation,
  never backfilled from anything the entity didn't actually perceive.

## KA-S04 — False rumor, real action

A false report is believed; an action is chosen; a real consequence follows.

- **Rules invoked:** Inherited (CAUSE-01, OWN-04, reusing Batch 01's FND-S18/S19 directly).
- **Result: covered — reconfirms rather than newly discovers.** `BeliefCycleSystem.
  process_rumor()` produces a real, `0.3`-certainty belief from a rumor; nothing in the
  architecture requires that belief to be true before it can feed `strategic.leads` into real
  goal-scoring and a real `ActionIntent`. Exactly the pattern FND-S18/S19 already confirmed at
  the foundational level.

## KA-S05 — Conflicting reports

Source A says X; source B says not-X; the entity must retain uncertainty/conflict or resolve it
through declared semantics.

- **Rules invoked:** KNOW-01, KNOW-02, INFO-01.
- **Result: covered.** `BeliefContradictionService.detect()` provides the declared resolution
  path: a later direct observation demotes a conflicting lead's certainty by exactly one step
  and degrades the matching `BeliefEntry.certainty` by `0.3`, incrementing `contradictions` —
  the entity does not average or silently pick a source; contradiction is a real, traceable
  event. `SourceTrustUpdateService` separately tracks each source's own trust — this
  repository's own current implementation happens to be gradual and per-source, one legitimate
  shape among the several INFO-01 now explicitly permits — as a second, independent axis for
  handling conflicting sources over time.

## KA-S06 — Stale knowledge

An entity learns a location/state; the world changes later; the old belief remains; a decision
is based on outdated information.

- **Rules invoked:** KNOW-02.
- **Result: covered.** `decay_stale_leads()` only demotes `APPROXIMATE`/`VAGUE` leads after
  `stale_threshold=50` ticks without refresh — and explicitly does not touch `PRECISE` leads
  ("direct observations decay slower") — meaning a `PRECISE` belief about a location can remain
  at full certainty indefinitely even after the world has changed, until a new direct
  observation or an explicit contradiction event corrects it. This is the honest, confirmed
  shape of KNOW-02's own "no automatic re-sync" claim in this repository: certainty-based
  demotion for uncertain leads, but no active mechanism at all forces even a `PRECISE` belief to
  re-check itself against current world state — a subject may remain confidently, stably wrong
  indefinitely. See KA-S19 for the adversarial version of this same finding.

## KA-S07 — Information does not teleport

An event occurs in a distant region; an unrelated entity with no valid information path remains
unaware.

- **Rules invoked:** Inherited (REACH-01, REACH-02), KNOW-02.
- **Result: covered.** No code path exists by which an entity's belief/knowledge/leads state is
  populated from an event it has no observation, report, or query-response path to — confirmed
  directly (KNOW-02's own information-opacity invariant). REACH-01/02 already establish the
  reach precondition this depends on.

## KA-S08 — Rumor degrades

Event → witness → messenger → second recipient; content loses or distorts detail through the
chain.

- **Rules invoked:** INFO-02, Inherited (REACH-05).
- **Result: revealed gap — the probe's own instruction anticipated this ("do not require
  distortion; probe that the architecture permits it").** The architecture *permits* content
  distortion (INFO-02's own permissive claim), but no mechanism currently exercises it:
  `process_rumor()` takes `rumor_detail` unchanged from `source_entity_id`, varying only
  certainty (`0.3`), never content. This reconfirms REACH-05's own already-flagged
  intermediary-failure gap from the content side.

## KA-S09 — Memory fades but history remains

A fact occurred; an individual once knew it; memory fades; the historical fact remains true.

- **Rules invoked:** MEM-02, Inherited (HP-01, OWN-06).
- **Result: covered.** `decay_stale_leads()`/staleness demotion operates entirely on
  entity-local `strategic.leads`/`BeliefEntry` state; nothing in that decay path, or in the
  Memory domain's causal/spatial/temporal subsystems, ever writes to the Chronicle/
  `NarrativeLedger` machinery HP-01's own evidence is built on. The two are confirmed
  non-overlapping mechanisms.

## KA-S10 — Decision reads omniscient state (added this batch, not a seed probe)

An entity's goal-scoring or opportunity-generation path selects a target the entity has never
perceived, observed, or been told about.

- **Rules invoked:** PERC-01 (Repository Finding), AGENCY-03 (Repository Finding).
- **Result: revealed contradiction — CONFLICTING, per the 2026-09-22 follow-up review's own
  required correction, not merely MISSING.** `ResourceOpportunityProvider.get_opportunities()`
  surfaces every resource node in the entity's current *region* directly from
  `state.resource_nodes`, at `confidence=1.0`, regardless of whether `PerceptionGate` would ever
  have let that node's signal through to the entity. `HarvestScorer.score()` independently
  confirms the same pattern via `SpatialQueryService.nearest_resource_node(state, ...)` — the
  nearest node in the *entire* world, not the entity's own perceived or known set. Both are
  real, live, and unconditional today — active behavior, not an absent or dormant feature, which
  is exactly why this is classified CONFLICTING rather than MISSING: the target semantics
  (subject-bounded perception/knowledge should gate these decisions) are coherent and already
  partly implemented (`PerceptionGate` itself); these two call sites simply do not route through
  it. This scenario is added specifically because the seed list's own emphasis ("agents reading
  omniscient world state" — §16) is not merely a hypothetical to probe; it is a confirmed,
  active fact about two major decision paths in this repository, and deserves its own scenario
  trace rather than living only as a Repository Finding prose note. This does not invalidate
  the Rule Catalog — it means the Catalog successfully exposed a real architecture mismatch.

## KA-S11 — Need influences but doesn't dictate

A hungry entity finds food a higher priority, but chooses another urgent action instead.

- **Rules invoked:** AGENCY-02.
- **Result: covered.** `AdventureRouteScorer.score()`'s additive formula means a `food`-need
  route's urgency term competes with, but does not override, other routes' benefit/bias/risk
  terms — a sufficiently threatening or beneficial competing route can still win over a
  hunger-matching one. Multiple `InterpretedNeed` entries (healing, food, rest, gold, equipment,
  information) can be simultaneously active, confirming real competition rather than a single
  dominant-need switch.

## KA-S12 — Capability without knowledge

An entity is physically capable of exploiting an opportunity but does not know it exists, so
does not choose it. Revisited using the clarified terminology: capability alone does not turn
an Opportunity into a chosen Actionable Affordance if the subject never learns the Opportunity
exists.

- **Rules invoked:** AGENCY-01, AGENCY-03 (Opportunity/Actionable-affordance distinction).
- **Result: covered, with a caveat tied to KA-S10's CONFLICTING finding.** In the *intended*
  design, an Opportunity the entity's own perception/knowledge never surfaced cannot become a
  chosen Actionable Affordance, because it never enters the candidate set — this is
  capability-without-knowledge working correctly by omission. The caveat: since Opportunity
  generation currently bypasses perception (KA-S10, CONFLICTING), the actual boundary this
  scenario probes is enforced by *region-scoping*, not by knowledge — an entity may still be
  offered an Opportunity in-region it never perceived, which is not the same failure mode the
  probe describes, but is adjacent to it.

## KA-S13 — Knowledge without capability

An entity knows exactly what must be done but lacks the capability/resources to execute it, and
cannot. Revisited: the entity correctly identifies a real Opportunity, but it never becomes an
Actionable Affordance for this entity because the capability precondition is unmet.

- **Rules invoked:** AGENCY-01, AGENCY-03.
- **Result: covered.** The routing contract's own blocked-buy-upgrade example is exactly this:
  the entity's belief/lead may correctly identify a needed item or gold amount (the Opportunity
  is real and known), but `blocker_penalty=2.0` (not exclusion) means the route remains a
  visible, chosen-but-failing candidate rather than a silently-removed one — knowledge does not
  manufacture the missing capability that would make it a genuinely Actionable Affordance.

## KA-S14 — Opportunity without desire

A valid Opportunity exists; the agent has no relevant pre-existing goal/motivation for it. Per
AGENCY-02's own clarified explanation, this does not automatically mean the Opportunity is
ignored.

- **Rules invoked:** AGENCY-02, AGENCY-03.
- **Result: partially covered — cleanly explained per the follow-up review's own required
  clarification, not merely "partially covered and left unresolved."** An Opportunity with zero
  matching need urgency is not automatically dropped from consideration in this repository's
  scoring formula — it can still win on `benefit`/`personality_bias` alone. This is not a
  violation of "opportunity ≠ desire," and it is not evidence that desire was secretly present
  either: **positive expected benefit is itself a motivational/utility input to the decision**,
  distinct from a pre-existing named goal but not distinct from motivation in the broader sense
  AGENCY-02 describes. The clean statement: absence of a *pre-existing goal* does not entail
  absence of *all* decision-relevant motivation, since raw expected benefit is itself one such
  input. The Rule (AGENCY-03: Opportunity's existence is independent of desire) is fully
  confirmed either way — an Opportunity with no matching need is still real and still
  candidate-eligible; whether it is *chosen* is a separate question this scenario now answers
  precisely rather than leaving open.

## KA-S15 — Desire without opportunity

An agent strongly wants an outcome, but no reachable Opportunity/Actionable-Affordance path
exists; it cannot currently pursue it.

- **Rules invoked:** AGENCY-02, AGENCY-03.
- **Result: covered, with a nuance.** If no Opportunity of the matching kind exists in the
  generated candidate set, no Actionable Affordance toward that specific desire can exist
  either — but the entity is not left idle: structural defaults (forced `RECOVER` for
  low-health/healing needs, forced `ASK_INFORMATION` for equipment needs) or the
  `DEFER_WITH_REASON` fallback ensure the entity always ends up with *some* valid decision, just
  not the one matching its strongest unmet desire.

## KA-S16 — Decision fails

An agent chooses a valid action; commits; the outcome fails.

- **Rules invoked:** AGENCY-04.
- **Result: covered.** Route scoring and selection happen entirely before execution; execution
  outcome (success, blocked, combat loss) is resolved by a separate downstream system and never
  retroactively invalidates the original decision's own validity. Reconfirms: decision
  quality/intent ≠ guaranteed success.

## KA-S17 — Hidden motive, visible consequence

An internal motive is not directly observable; repeated actions create an observable pattern;
another entity may later infer the motive.

- **Rules invoked:** AGENCY-05.
- **Result: revealed missing rule — the boundary (motive is not globally visible) is confirmed;
  the inference half is confirmed absent.** No code path exposes one entity's internal
  cognition to another (the privacy-by-default half holds). No in-simulation mechanism exists by
  which another entity infers a motive from an observed behavioral pattern
  (`CognitionPatternMiner` is offline developer tooling, not a world mechanism) — this supports
  observer legibility as a *permitted future capability*, not a currently-realized one.

## KA-S18 — Complete observation where declared (adversarial probe, added 2026-09-22)

A special channel or an explicitly declared condition grants a subject complete, relevant
information about something, rather than the usual bounded/partial access.

- **Rules invoked:** PERC-01.
- **Result: covered — confirms PERC-01 does not prohibit legitimate perfect observation.**
  PERC-01's own revised wording states a *default* ("perception does not imply complete or
  perfect knowledge by default"), not a prohibition — an explicit world rule declaring a
  channel or condition that grants complete observation (a special sense, an unconditional
  reveal) is a legitimate, permitted exception, not a violation. No such mechanism was found to
  currently exist in this repository (every real channel — `PerceptionGate`'s 7 senses,
  `BeliefCycleSystem`'s observation/rumor paths — produces bounded, partial, or graded access),
  so this scenario is scored as covered against the *Rule's own permission*, not against a real
  repository example of it being exercised.

## KA-S19 — Stale but confident (adversarial probe, added 2026-09-22)

A subject learns X with high confidence; the world later changes to not-X; no new information
ever arrives; the subject remains confidently wrong indefinitely.

- **Rules invoked:** KNOW-02.
- **Result: covered — this is exactly KNOW-02's own revised claim, exercised adversarially.**
  A `PRECISE`-certainty lead (`certainty=1.0`-equivalent observation-sourced belief) is
  explicitly *not* touched by `decay_stale_leads()` ("direct observations decay slower") and is
  only ever demoted by `BeliefContradictionService.detect()`, which requires a real, matching
  direct-observation event to fire. If no such event ever occurs — the world changes, but the
  entity never happens to observe the change directly — nothing in this repository ever revises
  that belief. The entity remains confidently, stably wrong indefinitely. This is not a defect;
  it is KNOW-02's own explicit, intended shape ("a subject may therefore remain confidently
  wrong for as long as no declared revision process actually runs").

## KA-S20 — Compelled action (adversarial probe, added 2026-09-22)

An entity's ordinary preference favors action A; an explicit reflex/compulsion rule requires
action B instead; B occurs.

- **Rules invoked:** AGENCY-02, Scope Boundary (non-ordinary override mechanisms).
- **Result: covered by permission, not by an existing mechanism — confirms AGENCY-02 describes
  ordinary motivation only, not a ban on all non-voluntary behavior.** AGENCY-02's own revised
  text explicitly carves out room for a future reflex/panic/compulsion/mind-control/
  hard-threshold rule to override ordinary preference; no such override mechanism currently
  exists in this repository (checked directly: no code path forces an action against the
  competitive scoring formula's own selected outcome). This scenario confirms the Rule's own
  boundary is honest about what it does and does not govern — ordinary motivational competition,
  not every possible category of action-selection — rather than confirming a built mechanism.

---

## Cross-batch note

KA-S10 is this batch's own most load-bearing discovery, on par with Batch 05's ECOL-03 and
BODY-05, and confirmed **CONFLICTING** (not merely MISSING) per the 2026-09-22 follow-up
review's own required correction: two independent, unconditional, live decision paths
(`ResourceOpportunityProvider`, `HarvestScorer`) read raw world state directly rather than
routing through any perception- or knowledge-gated representation. This is not a dormant or
absent feature — it is active behavior that directly contradicts PERC-01's own default and
AGENCY-03's own generation-independence claim for these specific decisions. **Individual agents
already have real belief/perception infrastructure (`PerceptionGate`, `BeliefEntry`/`leads`,
`KnowledgeModelService`), but some live decision paths bypass it entirely and read omniscient
state directly instead** — this remains one of the most important findings the Rule Catalog has
produced. Recorded honestly, per every prior batch's own practice of naming divergence rather
than assuming the intended design is already realized, and explicitly not treated as
invalidating the Catalog: PERC-01 and AGENCY-03's own target semantics remain coherent: the
Catalog successfully exposed a real, documented architecture mismatch.

KA-S08's and KA-S17's findings remain this batch's other significant new material: INFO-02's
confirmed absence of content-level distortion (only certainty/trust vary, never claim content
itself — MISSING), and AGENCY-05's confirmed absence of any in-simulation motive-inference
mechanism (MISSING) — both real, both honestly recorded as permitted-but-unbuilt rather than
assumed to already exist, and both distinct in kind from KA-S10's own CONFLICTING finding.

KA-S18–S20 (added per the 2026-09-22 follow-up review) confirm the batch's revised Rules are
correctly bounded rather than over-broad: PERC-01 permits legitimate perfect observation
(KA-S18), KNOW-02 permits a subject to remain confidently, stably wrong indefinitely absent a
real revision event (KA-S19), and AGENCY-02 permits — without currently implementing — a
declared override of ordinary motivation (KA-S20). None of the three reveals a new gap beyond
what KNOW-02/AGENCY-02's own revised text already discloses.
