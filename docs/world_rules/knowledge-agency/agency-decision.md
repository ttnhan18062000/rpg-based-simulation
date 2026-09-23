---
status: authoritative
layer: architecture
authority: P1
audience: agent
tags: [architecture, world, content]
last_verified: "2026-09-23"
---

# World Rule Family: Agency / Decision

**Purpose/scope.** What makes an entity an autonomous decision-maker rather than a passive
state machine, and what makes a decision causally valid. Focuses primarily on individually
simulated living agents, per the locked **Hybrid Agency** principle (organizations/settlements/
institutions may later use coarser goal/pressure models — not designed here). Does not require
every agent to use the same internal decision architecture.

**Status.** Batch 06 (Perception/Knowledge/Information/Agency), drafted 2026-09-22, revised the
same day per follow-up review (`tmp/world-rule-batch-6-followup-ext-ai.md`): AGENCY-02
reworded to remove implementation-specific language ("inside one scoring formula") and to
explicitly allow future reflex/compulsion/mind-control/hard-threshold rules to override
ordinary motivation; AGENCY-03 given a clarified two-tier Opportunity/Actionable-Affordance
terminology. Candidates below originated as external-reviewer hypotheses
(`tmp/world-rule-batch-6-ext-ai.md`); each carries this session's disposition and repository
evidence. Structured per the normalized five-category methodology established in Batch 05's
admission-discipline pass.

---

## Domain Rules

## AGENCY-01 — A decision's stages are causally distinct facts; an earlier stage never guarantees a later one

> Wanting an action, choosing it, being capable of it, being authorized to do it, having reach/
> opportunity to attempt it, committing to it, and the action actually succeeding are seven
> causally distinct facts along one decision's path. Possessing any earlier-stage fact never
> guarantees any later one: a subject may want something it cannot choose (competing priorities
> win), be capable without being authorized, be authorized without reach, commit without
> succeeding, and so on in any combination the world's own rules permit.

**Disposition: ACCEPT.** Passes the admission test: no earlier Rule states that a decision has
this many causally separable stages, or that they must never be conflated — Capability (CAP-*),
Authority (AUTH-*), and Reach (REACH-*) each already establish that *their own* two concepts are
distinct (see Inherited, below), but nothing before this batch states the full decision-stage
chain as its own claim, including the specifically Agency-side stages (wanting, choosing,
committing) that no foundational family addresses.

**Repository evidence: SUPPORTED.** `AdventureRouteScorer.score()`'s blocker handling is the
cleanest single piece of evidence: a blocked route (missing gold/item — a capability-adjacent
fact) is never excluded from the candidate set, only penalized (`blocker_penalty=2.0`) — the
entity can still *choose* (commit to) a route it is not currently capable of executing, and
`ObjectiveIntentResolver.resolve()` then produces an `ActionIntent` whose actual execution
outcome is resolved by a separate downstream system. Wanting/choosing and capability/
authorization/reach and commitment/success are visibly never collapsed into one gate.

**Scenarios:** [KA-S12](../scenarios/knowledge-agency-batch-06.md#ka-s12) (capability without
knowledge), [KA-S13](../scenarios/knowledge-agency-batch-06.md#ka-s13) (knowledge without
capability), [KA-S16](../scenarios/knowledge-agency-batch-06.md#ka-s16) (decision fails).

---

## AGENCY-02 — Ordinary motivations influence decision preference without automatically determining the chosen action

> A subject's ordinary motivations and needs (fear, curiosity, hunger, greed, personality
> traits) add real, competing influence to which action a subject prefers. Multiple motivations
> may compete, and the highest-pressure motivation does not automatically win — it prevails
> only where the world's own declared decision semantics actually favor it over the
> alternatives. This describes *ordinary* motivation only. It does not ban non-voluntary
> behavior in general: a future world rule may explicitly declare a reflex, panic response,
> compulsion, mind-control effect, or hard survival threshold that overrides ordinary
> preference and forces a specific action — such a declared override is a different, legitimate
> category from ordinary motivational influence, not a violation of this Rule.

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — reworded to remove
implementation-specific language ("inside one scoring formula") and to explicitly carve out
room for future non-ordinary override rules.** The original wording's specific mechanism
description (a weighted addend inside one scoring formula) stated this repository's own
current implementation as if it were the Rule itself; the fix states the semantic principle
(influence, not automatic determination) independent of any one scoring mechanism's shape, and
explicitly distinguishes *ordinary* motivational influence (what this Rule governs) from a
*declared override* (reflex/compulsion/mind-control/hard-threshold — a legitimately different
category, carved out as its own Scope/Deferred Boundary, below, rather than smuggled in as an
exception clause). Passes the admission test: Batch 05's SURV-02 already established that
crossing a need threshold produces a real consequence (Inherited, below); the new claim here is
specific to Agency — that ordinary motivation *competes for preference* rather than
*determining the outcome*, and that several independent motivations may compete simultaneously.

**Repository evidence: SUPPORTED, as one legitimate implementation of the principle — not the
principle's own definition.** `AdventureRouteScorer.score()`'s formula (`score = urgency +
benefit + personality_bias + confidence_bonus − risk_penalty − blocker_penalty`) is this
repository's own current mechanism for realizing "influence, not automatic determination": it
sums need urgency, benefit, and up to five independent personality-trait biases (caution,
greed, curiosity, industry, sociability) into one competing scalar per candidate route — a
route with zero matching need urgency can still win on benefit/bias alone (per the routing
contract's own documented edge case: "Entity with no active needs → `urgency=0.0` for all
routes; benefit and personality_bias alone drive scoring"), and a high-urgency need does not
force its own matching route to win if a competing route scores higher overall.
`NeedInterpretationService.interpret()` itself can register multiple simultaneous needs
(healing, food, rest, gold, equipment, information) with independent urgency values — genuine
multi-motivation competition, not a single dominant-need switch. No override mechanism
(reflex/compulsion/mind-control/hard-threshold) currently exists in this repository — this
Rule's own carve-out for one is a standing permission for future content, not a description of
something already built.

**Scenarios:** [KA-S11](../scenarios/knowledge-agency-batch-06.md#ka-s11) (need influences but
doesn't dictate), [KA-S20](../scenarios/knowledge-agency-batch-06.md#ka-s20) (compelled action —
confirms this Rule describes ordinary motivation only, not a ban on all non-voluntary
behavior).

---

## AGENCY-03 — Opportunity and actionable affordance are two distinct tiers, independent of a subject's desire, capability, or authority

> **Opportunity** = a world-relative possibility worth considering: an action possibility that
> exists relative to a particular subject's position/region/context, independent of whether
> that subject currently wants it, can execute it, or may legitimately execute it. **Actionable
> affordance** = an opportunity that is currently exercisable by this specific subject, given
> its actual capability, authority, and reach at this moment. Every actionable affordance is an
> opportunity; not every opportunity is currently an actionable affordance — a subject may face
> a real opportunity it cannot yet act on (missing capability/authority/reach), and the
> opportunity does not stop existing merely because it is not, right now, exercisable. Neither
> tier depends on the subject's desire: wanting is a separate fact from both (AGENCY-01,
> AGENCY-02).

**Disposition: ACCEPT, revised 2026-09-22 per follow-up review — the original draft used
"opportunity" and "affordance" as loose synonyms; this revision establishes the explicit
two-tier distinction the follow-up required, since one tier depends on capability/reach and the
other does not.** Directly answers the batch instruction's own §8 investigation ("whether
Affordance/Opportunity deserves explicit domain semantics") — the answer is yes, and the
repository already implements almost exactly the Opportunity tier under that name; the
Actionable-affordance tier is real but not reified as its own separate type (see evidence,
below). Passes the admission test: no earlier Rule names or states either category.

**Repository evidence: SUPPORTED for the Opportunity tier as a first-class repository type;
SUPPORTED but implicit for the Actionable-affordance tier.** `Opportunity`
(`src/world/providers/resources.py`, `src/domains/adventure/schema.py`) is a frozen dataclass
with `kind`, `target_id`, `subject`, `estimated_reward`, `estimated_risk`, `requirements`, and
`confidence` fields — generated independent of any particular subject's motivation (a resource
node opportunity exists whether or not the entity currently needs that resource), and this is
exactly the Opportunity tier. The Actionable-affordance tier is real but this repository never
reifies it as its own object: a capability shortfall does not remove an `Opportunity` from the
candidate set, it only attaches `blocker_penalty=2.0` at scoring time (AGENCY-01's own
evidence) — meaning "is this currently exercisable" is computed implicitly, per-candidate, at
scoring time, rather than being a persisted second-tier fact a caller could inspect directly.
Opportunity, motivation, and capability remain three separate inputs to one scoring formula,
never collapsed, even though only one of the three (Opportunity) has its own named type.

**Repository Finding, attached: CONFLICTING — opportunities in this repository are currently
generated from raw/omniscient world state, not gated by the subject's own perception or
knowledge.** See `perception.md`'s own Repository Findings for the full evidence
(`ResourceOpportunityProvider.get_opportunities()` reads `state.resource_nodes` directly,
region-scoped only, not perception/knowledge-scoped; `HarvestScorer.score()` similarly).
Classified CONFLICTING, not MISSING, per the follow-up review's own required correction: this
is active, live behavior that contradicts PERC-01's own boundary for these specific decisions,
not an absent or dormant feature. The Opportunity *tier itself* is correctly subject-relative
and desire/capability-independent by design; its current *generation mechanism* is what fails
to respect the subject's own bounded perception — an opportunity the entity has never perceived
or learned of is nonetheless surfaced to it as a candidate, at full `confidence=1.0`.

**Scenarios:** [KA-S12](../scenarios/knowledge-agency-batch-06.md#ka-s12) (capability without
knowledge), [KA-S13](../scenarios/knowledge-agency-batch-06.md#ka-s13) (knowledge without
capability), [KA-S14](../scenarios/knowledge-agency-batch-06.md#ka-s14) (opportunity without
desire), [KA-S15](../scenarios/knowledge-agency-batch-06.md#ka-s15) (desire without
opportunity) — all four revisited in the scenario file using the clarified Opportunity/
Actionable-affordance terminology.

---

## AGENCY-04 — Decision quality/validity and execution outcome are distinct facts

> A decision being well-formed — motivated, capable, authorized, reachable, and validly
> committed — is a separate fact from whether its execution actually succeeds. A failed outcome
> never retroactively makes the originating decision invalid, and decision quality must not be
> evaluated solely by whether the eventual outcome was good.

**Disposition: ACCEPT.** Directly required by §10 and the "Decision Fails" seed scenario.
Passes the admission test: this reuses LIFE-02's defeat≠death framing only loosely (a different
subject matter — decision validity, not lifecycle classification); no earlier Rule states that
decision quality and outcome are separable facts.

**Repository evidence: SUPPORTED.** `AdventureRouteScorer.score()` produces a ranked decision
before any execution attempt; the resulting `ActionIntent` is forwarded to a separate execution
pipeline whose outcome (success, blocked, combat loss, etc.) is resolved independently and later
— nothing in the scoring/decision layer is retroactively revised based on that outcome. A
`combat_loss` outcome does feed back into future decisions (via `CausalAttributionService`,
`MEM-02`'s own evidence, when the memory feature flag is enabled) as a new, separate causal
lesson — it never rewrites the fact that the original decision was validly formed given what
the subject knew and wanted at the time.

**Scenarios:** [KA-S16](../scenarios/knowledge-agency-batch-06.md#ka-s16).

---

## AGENCY-05 — Hidden internal cognitive state is not globally visible to other subjects by default

> A subject's motive, belief content, or need is not automatically knowable to any other
> subject. Another subject may come to know it only through an observable causal trace (a
> repeated action pattern, a visible consequence) and a real, declared inference or observation
> mechanism — never through automatic, omniscient access to another subject's internal
> cognition.

**Disposition: ACCEPT.** Directly required by §14 ("legible does not mean omniscient") and the
"Hidden Motive, Visible Consequence" seed scenario. Passes the admission test: this states a
privacy-by-default boundary specifically for *internal cognitive* state, distinct from
PERC-01's own claim about *world signals* in general (an entity's motive is not a world signal
any sense channel could ever detect directly — it is categorically unlike a resource node or a
sound) and distinct from REACH-03's asymmetry (which is about one-directional perceptual reach
in general, not specifically about the privacy of internal cognition).

**Repository evidence: SUPPORTED for the boundary; MISSING for any live in-simulation
inference mechanism — an important, honestly-recorded gap.** Checked directly: no code path in
`src/ai/`, `src/cognition/`, `src/domains/`, or `src/systems/` allows one entity to read another
entity's `self_model`, `strategic.beliefs`, or need-interpretation fields directly — internal
cognition is never globally exposed. `src/observability/cognition/pattern_miner.py`
(`CognitionPatternMiner.mine_patterns()`) does mine post-hoc run-directory JSON for behavioral
failure patterns (project churn, detour loops, stale blockers) — but this is offline developer/
observability tooling operating on recorded run data outside the simulation, not an in-world
entity-to-entity motive-inference mechanism. No world-semantic mechanism exists by which one
entity infers another's motive from its observed behavior.

**Scenarios:** [KA-S17](../scenarios/knowledge-agency-batch-06.md#ka-s17) (hidden motive,
visible consequence).

---

## Inherited / Applied Foundational Rules

### Capability, authority, and reach are independent preconditions for a valid action, each distinct from the others

> Being mechanically able to attempt an action (capability), being legitimately authorized to
> do it (authority), and being able to reach the target at all (reach) are three independent
> facts — none implies the others.

**Disposition: INHERITED — direct reuse of CAP-01 ("capability is distinct from authority,"
itself already a restatement of AUTH-01 from the Capability side) and REACH-01/REACH-02. This
is the foundation AGENCY-01's own decision-stage chain is built on for its capability/
authority/reach nodes specifically; no new claim about capability/authority/reach themselves is
added here.**

**Repository evidence: SUPPORTED**, reused directly from Batch 03's own CAP-01 evidence.

**Scenarios:** none newly traced; reuses CAP-01's own evidence directly.

### Need pressure accumulates, and crossing a threshold produces a real consequence

> A modeled need's pressure accumulates over time; crossing a declared threshold produces a
> real capability, body, or decision consequence.

**Disposition: INHERITED — direct reuse of Batch 05's SURV-02. AGENCY-02's own new content is
specifically about *how* that consequence manifests inside a competitive decision-scoring
formula (a weighted addend, not an override) — the threshold/pressure/consequence pattern
itself is not restated as new.**

**Repository evidence: SUPPORTED**, reused directly from Batch 05's own SURV-02 evidence.

**Scenarios:** none newly traced; reuses SURV-02's own evidence directly.

### A false belief may still be a real cause of a real action

> A subject acting on a false or incomplete belief produces a real, causally valid consequence
> — the belief's falseness does not retroactively make the resulting action's consequence
> unreal or invalid.

**Disposition: INHERITED — direct reuse of CAUSE-01 (a consequence requires a real causal
path, independent of whether the triggering belief was itself true) and OWN-04. Batch 01's own
FND-S18/S19 already probed exactly this at the foundational level ("a false belief is a real
cause of a real action; a held-but-inert belief is legitimately not a cause of anything") — the
batch instruction's own explicit instruction to "revisit Batch 01's principle" is satisfied by
this reuse, not by restating it as new.**

**Repository evidence: SUPPORTED**, reused directly from Batch 01's own CAUSE-01/FND-S18/S19
evidence.

**Scenarios:** [KA-S04](../scenarios/knowledge-agency-batch-06.md#ka-s04) (false rumor, real
action — reuses/deepens FND-S18/S19 directly).

---

## Scope / Deferred Boundaries

### Hybrid Agency — organizations/institutions use coarser models, not designed here

> Individual characters/creatures receive rich autonomous agency (this family); organizations,
> settlements, and institutions may later use coarser goal/pressure models — that later
> refinement is explicitly out of scope for this batch, per the locked Hybrid Agency principle
> named in the batch instruction itself.

**Disposition: SCOPE BOUNDARY.**

### Non-ordinary override mechanisms (reflex, panic, compulsion, mind control, hard survival thresholds)

> AGENCY-02's own carve-out permits a future world rule to declare a reflex, panic response,
> compulsion, mind-control effect, or hard survival threshold that overrides ordinary
> motivational preference. Designing any such concrete mechanism — its trigger conditions, its
> scope, how it interacts with AGENCY-01's decision-stage chain — is not done here. This batch
> only establishes that AGENCY-02 describes *ordinary* motivation and does not implicitly ban
> such an override from ever existing.

**Disposition: SCOPE BOUNDARY.** Added 2026-09-22 per follow-up review, alongside AGENCY-02's
own reworded carve-out — not a Domain Rule, since it designs no concrete override content.

### Detailed psychological/cognitive-architecture modeling

> This family does not require every agent to use the same internal decision architecture, and
> does not introduce new psychological variables beyond what this repository already evidences
> (personality traits — caution, greed, curiosity, industry, sociability, bravery — feeding
> route-scoring bias). Per §15's own discipline, a candidate internal state earns modeling only
> if it alters decisions, persists meaningfully, can be affected by other systems, has
> observable/inferable consequences, and differentiates entity trajectories — no new dimension
> meeting that bar was found needed this batch.

**Disposition: SCOPE BOUNDARY.**

---

## Repository Findings (significant, cross-referenced)

Classified per the three-way distinction sharpened by the 2026-09-22 follow-up review:
**CONFLICTING** (a live, active behavior that violates a target Rule's own boundary),
**INERT/OFF** (a real mechanism that simply does not run), or **MISSING** (a permitted
mechanism never built at all).

- **CONFLICTING — opportunity generation (AGENCY-03) currently bypasses perception/knowledge
  entirely**, reading raw world state directly. See `perception.md`'s own Repository Findings
  for the full evidence; recorded here as the Agency-side half of the same finding, since it is
  this family's own Opportunity tier that the omniscient read populates. Classified
  CONFLICTING, not MISSING: this is active behavior contradicting a target boundary
  (PERC-01/AGENCY-03's own desire/capability-independence, undermined at the generation-source
  level), not an absent feature. **This is one of the most important findings the Rule Catalog
  has produced to date: individual agents already have real belief/perception infrastructure
  (`PerceptionGate`, `BeliefEntry`/`leads`, `KnowledgeModelService`), but some live decision
  paths bypass it entirely and read omniscient state directly instead.** This finding does not
  invalidate the Rule Catalog — PERC-01 and AGENCY-03's own target semantics remain coherent —
  it means the Catalog successfully exposed a real, documented architecture mismatch.
- **MISSING — no in-simulation motive-inference mechanism.** See AGENCY-05 above.
  `CognitionPatternMiner` is offline developer tooling, not a world-semantic mechanism. This is
  a permitted-but-unbuilt gap, not an active violation — AGENCY-05's privacy-by-default half
  holds cleanly; only the inference half is unbuilt.
- **Not classified under the three-way distinction (a code-cleanliness finding, not a
  Rule-boundary finding) — capability estimation is scorer-local, ad hoc, and architecturally
  split from the entity's own persisted self-model, with no active confidence decay.**
  `CapabilityEstimateService.estimate()` is called directly by `AdventureRouteScorer.score()`
  (for `GATHER_RESOURCE`/`CRAFT_UPGRADE` routes) and `TacticalDecisionSystem.target_score()`
  (combat targeting) — both read-only, ad hoc call sites that bypass `SelfModelUpdatePhase`
  entirely. `entity.self_model.capabilities.estimates` remains empty in production because
  `SelfModelUpdatePhase.apply()` never passes a `capability_context` to `run()` — the
  self-model's own persisted capability-estimate storage is confirmed unpopulated, even though
  the estimation logic itself is real, live, and consumed. The subsystem also has no active
  confidence decay — estimates are static until re-computed (`last_updated_tick` exists for
  freshness-checking but nothing currently checks it). No AGENCY Rule requires this storage to
  be populated, so this is not itself a CONFLICTING finding against any stated Rule — it is
  flagged as an architecture observation worth a future owner's attention.

## Cross-domain links recorded here

- AGENCY-01 → Capability (CAP-01), Authority (AUTH-01), Reach (REACH-01/02, inherited above)
- AGENCY-02 → Survival Needs (SURV-02, inherited above); its own carve-out → the non-ordinary
  override Scope Boundary, above, for whichever future domain first designs a concrete reflex/
  compulsion/mind-control mechanism
- AGENCY-03 → Perception (`perception.md`'s PERC-01 and its own Repository Findings — the
  omniscience-bypass finding, now classified CONFLICTING on both sides)
- AGENCY-04 → Lifecycle (LIFE-02, loosely — decision validity vs. lifecycle outcome are
  analogous but distinct claims, not the same rule)
- AGENCY-05 → Reach (REACH-03, inherited above, for the general asymmetry precedent), Knowledge
  (`knowledge-information.md`'s KNOW-02, the information-opacity invariant this Rule extends to
  cognition specifically)

## Open questions carried forward

1. Whether `CapabilityEstimateService`'s ad hoc, self-model-bypassing call pattern should be
   unified into a real `SelfModelUpdatePhase`-populated path is a real design/implementation
   question, not decided here.
2. Whether a future batch or ticket should build a real in-simulation motive-inference
   mechanism (AGENCY-05's confirmed gap) — most plausibly relevant to Social relations or a
   future observability-facing gameplay feature — is flagged, not decided.
3. Whether opportunity generation (AGENCY-03) should be re-scoped through perception/knowledge
   is the same open design question `perception.md` already carries forward; recorded here from
   Agency's own vantage point rather than duplicated as a second decision.
