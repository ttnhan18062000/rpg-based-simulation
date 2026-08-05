---
name: cognition-strategy
description: 'Internal self-model, bounded strategic appraisal, goal hierarchy, and interruption resistance across src/cognition/, src/strategy/, src/ai/goals/ — foregrounds the boundary between them.'
---

# Cognition & Strategy (This Repo)

Flagged as the highest-value gap in this repo's skill-catalog domain sweep — precisely because
the boundary below is a real, repo-specific trap a generic "AI decision-making" skill would
actively get wrong, not just fail to help with.

## The Boundary — Read This First

`src/cognition/` is narrow and specific: **the entity's internal model of itself** — health,
weaknesses, strengths, confidence, capability estimates, learned world facts, interpreted
biological needs. It is NOT general AI decision-making. Per `docs/cognition/README.md`:

- **Not strategy** — `src/strategy/` (bounded cognition capacity management) *reads* the
  self-model produced by `src/cognition/` but does not live there.
- **Not domain decision logic** — `src/domains/motivation/` and `src/domains/perception/` consume
  cognition's output but are separate systems.
- **Not AI personality** — `src/ai/` (goal scoring, personality traits) is a separate subsystem.
- **Not social or intelligence** — `src/systems/strategic_systems/intelligence.py` is the
  strategic *decision* engine; `src/cognition/` only produces the self-model that intelligence
  *reads*. (Cross-checked: `docs/engine/authoritative_pipeline.md`'s "Cognitive Refinement"
  section independently confirms `intelligence.py` backs the `strategic_intelligence` phase — the
  two docs agree, this isn't a one-source claim.)

If you're asked to "improve the entity's decision-making" and the change belongs in
`src/cognition/`, that's almost certainly wrong — check whether it actually belongs in
`src/strategy/`, `src/ai/goals/`, or one of the `src/domains/` consumers instead.

## `SelfModelUpdatePhase` — The 4-Step Cognition Pipeline

Source: `docs/cognition/README.md`. Runs every tick for alive/active entities:

1. **Knowledge assimilation** (`KnowledgeModelService.assimilate`, `knowledge_model.py`) — only if
   `InformationResponse` events exist for this entity this tick.
2. **Self-assessment** (`SelfAssessmentService.assess`, `self_assessment.py`) — evaluates health,
   weaknesses, strengths, confidence, stress. Dirty-checked: skips steps 3-4 if nothing changed.
3. **Need interpretation** (`NeedInterpretationService.interpret`, `need_interpretation.py`) —
   only if the dirty check triggered.
4. **Capability estimation** (`CapabilityEstimateService.estimate`, `capability_estimate.py`) —
   only if the caller provides a scoped `CapabilityContext`.

Output: `SelfModelBundle`, written via `EntityUpdate(self_model_bundle_set=...)`.

## Goal Hierarchy (Strategy Layer)

Source: `docs/mechanics/04_strategic_cognition.md` §1. 4 priority tiers, entities select the
highest-scoring **Project**:

| Tier | Concern Type | Drive |
|---|---|---|
| 1: Survival | `danger`, `fleeing` | Avoid death/incapacitation |
| 2: Biological | `hunger`, `sleep`, `exhaustion` | Maintain operational biological stats |
| 3: Social | `social`, `grudge`, `bond` | Protect allies / seek revenge |
| 4: Economic | `harvest`, `trade`, `craft` | Accumulate wealth/equipment |

## Interruption Resistance

Source: §2. Prevents "Goal Flickering" (rapid switching between similar goals):

```python
Switch_Allowed = New_Goal_Score > (Current_Goal_Score + Interruption_Margin)
Interruption_Margin = Profile_Resistance * resistance_multiplier
```

`Profile_Resistance` is 0.0-1.0, defined by the entity's personality/class. `resistance_multiplier`
is a **profile-defined constant, not a hardcoded 30.0** — it varies by entity profile; don't
assume a fixed value when reading or modifying this logic. **Emergency bypass**: Danger concerns
scoring > 80 ignore the interruption margin entirely.

## Leads, Blockers, Project Lifecycle

Source: §3-4. A **Lead** (knowledge) has Subject/Detail/Certainty (High/Medium/Low, decays if
unrefreshed). A **Blocker** (problem) has one of 6 real `BlockerKind` values
(`src/core/strategic.py`): `access` (path blocked, unreachable, oscillating nav, or congestion),
`material` (missing items/resource unavailable/liquidity exhausted), `inventory` (no space),
`capability` (entity capability limit), `social` (relationship constraint), `group` (group
composition/requirement).

**Project Lifecycle** (4 levels): Directive (high-level intent, e.g. "Improve Defense") → Project
(specific actionable goal, e.g. "Craft Iron Breastplate") → Objective (atomic step, e.g. "Travel
to Forge") → Action (raw engine command).

## Perception & Info Decay

Source: §5. Perception radius: **10.0 units**, consistent across `src/engine/domain_logic.py`,
`src/engine/domain/view.py`, `src/systems/strategic_systems/intelligence.py`. A 15.0-unit radius
also exists but is **cooperation candidate search** (`src/domains/cooperation/providers.py`), NOT
a perception radius — don't conflate the two.

Info decay: strategic leads lose certainty after **50 ticks** without refresh (default
`stale_threshold=50`, `BeliefCycleSystem.decay_stale_beliefs`,
`src/systems/strategic_systems/belief.py:47`), demoting APPROXIMATE → VAGUE → EXHAUSTED. PRECISE
leads (direct observation) never decay.

## `BoundedStrategicAppraisalService` — 7-Stage Pipeline

Source: `docs/strategy/bounded_cognition_decision_flow.md`. Derives strategic outcomes from raw
mental records: Candidate Gathering → Candidate Scoring → Pre-bounding/Early Slicing → Final
Sorting/Cognitive Truncation → Project Continuity Resolution → Objective Derivation → Strategic
Update.

**Gathering**: up to 8 sources — Current Project (always prioritized), Concerns, Obligations,
Suspended Projects, Active Blockers, Leads, Contracts, Active Projects.

**Real scoring formulas**, tied to the entity's `CognitionCapacityProfile`:
- Projects: `0.30*p + 0.20*u + 0.15*s + 0.25*a + 0.10*resume_reliability`
- Concerns: `0.25*p + 0.40*u + 0.25*s + 0.10*(1.0 - resistance)`
- Blockers: `0.40*sev + 0.30*cp_score + 0.15*budget + 0.15*patience`

**Slicing**: `active_slice_limit` (range 3-9). Current project always reserves slot 0. Concerns/
Leads capped before final sorting to prevent "lead/concern floods."

**Continuity (hysteresis)**: `switch_margin` (range 0.10-0.45). `SWITCH IF: BEST_RIVAL_SCORE >
CURRENT_SCORE + switch_margin` — prevents thrashing.

## The Authoritative Pipeline Phases

Source: `docs/engine/authoritative_pipeline.md`. This domain's operations execute as 4 specific
named phases in the 32-phase `AuthoritativeApplyPipeline`:

| Phase # | Name | What it does | Flag/Compliance ID |
|---|---|---|---|
| 3 | `self_model` | Updates cognitive self-model | `ENABLE_SELF_MODEL_COGNITION` |
| 4 | `information_belief` | Assimilates new information into entity belief state | `ENABLE_BELIEF_ASSIMILATION` |
| 5 | `information_intent_execution` | Executes self-model query-routing intents via `ActionIntentAdapter.execute()` | `ENABLE_INFORMATION_INTENT_EXECUTION` |
| 25 | `strategic_intelligence` | Updates strategic blockers, leads, and project markers | `STRAT-002` |

Note phases 3-5 run early (cognition/belief), phase 25 runs much later (strategic intelligence) —
this ordering matters: strategic decisions at phase 25 see the tick's already-updated self-model
and belief state from phases 3-5, not a stale pre-tick snapshot.
