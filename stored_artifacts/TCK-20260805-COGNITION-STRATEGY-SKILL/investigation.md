---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260805-COGNITION-STRATEGY-SKILL
artifact_type: investigation
tags: [skills, strategy]
---

# Investigation — TCK-20260805-COGNITION-STRATEGY-SKILL

## Real Content Grounded

### `docs/cognition/README.md` — the IS/NOT boundary (the ticket's own highest-priority content)
- **IS**: entity's internal self-model (health/weaknesses/strengths/confidence), capability
  estimates, world knowledge (learned facts), interpreted biological needs.
- **NOT strategy** — `src/strategy/` reads the self-model but does not live in `src/cognition/`.
- **NOT domain decision logic** — `src/domains/motivation/`/`src/domains/perception/` consume
  cognition output but are separate systems.
- **NOT AI personality** — `src/ai/` (goal scoring, personality traits) is separate.
- **NOT social/intelligence** — `src/systems/strategic_systems/intelligence.py` is the strategic
  decision engine; cognition produces the self-model intelligence *reads*. Cross-checked against
  `authoritative_pipeline.md`'s own "Cognitive Refinement" section, which confirms
  `intelligence.py` is the file backing the `strategic_intelligence` phase — consistent across
  both docs, not contradictory.
- **Real 4-step `SelfModelUpdatePhase` pipeline**: Step 1 Knowledge assimilation
  (`KnowledgeModelService.assimilate`, only if `InformationResponse` events exist), Step 2
  Self-assessment (`SelfAssessmentService.assess`, dirty-checked), Step 3 Need interpretation
  (`NeedInterpretationService.interpret`, only if dirty), Step 4 Capability estimation
  (`CapabilityEstimateService.estimate`, only if `CapabilityContext` provided). Output:
  `SelfModelBundle` via `EntityUpdate(self_model_bundle_set=...)`.

### `docs/mechanics/04_strategic_cognition.md`
- **Goal hierarchy**: 4 tiers — Survival (danger/fleeing) > Biological (hunger/sleep/exhaustion) >
  Social (social/grudge/bond) > Economic (harvest/trade/craft).
- **Interruption resistance** (real formula): `Switch_Allowed = New_Goal_Score >
  (Current_Goal_Score + Interruption_Margin)`, `Interruption_Margin = Profile_Resistance *
  resistance_multiplier` (a profile-defined constant, not hardcoded 30.0 — a real, easy
  misconception this skill should preempt). Emergency bypass: Danger concerns score > 80 ignore
  the margin entirely.
- **Leads & Blockers**: Leads have Subject/Detail/Certainty (decays if unrefreshed). 6 real
  `BlockerKind` values (`src/core/strategic.py`): `access`, `material`, `inventory`, `capability`,
  `social`, `group`.
- **Project Lifecycle**: Directive → Project → Objective → Action (4 levels).
- **Perception**: radius **10.0 units** consistently across `domain_logic.py`/`domain/view.py`/
  `intelligence.py` — a real, disclosed caveat: a 15.0-unit radius exists but is cooperation
  candidate search, NOT a perception radius (`src/domains/cooperation/providers.py`), don't
  conflate. Info decay: leads lose certainty after **50 ticks** unrefreshed
  (`BeliefCycleSystem.decay_stale_beliefs`, `src/systems/strategic_systems/belief.py:47`),
  demoting APPROXIMATE → VAGUE → EXHAUSTED; PRECISE (direct observation) never decays.

### `docs/strategy/bounded_cognition_decision_flow.md`
- Real 7-stage Mermaid pipeline for `BoundedStrategicAppraisalService`: Candidate Gathering (up to
  8 sources: Current Project, Concerns, Obligations, Suspended Projects, Active Blockers, Leads,
  Contracts, Active Projects) → Candidate Scoring (real formulas) → Pre-bounding/Early Slicing →
  Final Sorting/Cognitive Truncation → Project Continuity Resolution → Objective Derivation →
  Strategic Update.
- **Real scoring formulas**: Projects `0.30*p + 0.20*u + 0.15*s + 0.25*a + 0.10*resume_reliability`;
  Concerns `0.25*p + 0.40*u + 0.25*s + 0.10*(1.0 - resistance)`; Blockers `0.40*sev + 0.30*cp_score
  + 0.15*budget + 0.15*patience`.
- `active_slice_limit` range 3-9, current project always reserves slot 0. Hysteresis:
  `switch_margin` range 0.10-0.45, `SWITCH IF: BEST_RIVAL_SCORE > CURRENT_SCORE + switch_margin`.

### `docs/engine/authoritative_pipeline.md` — real phase grounding
Phase 3 `self_model` (`ENABLE_SELF_MODEL_COGNITION`), phase 4 `information_belief`
(`ENABLE_BELIEF_ASSIMILATION`), phase 5 `information_intent_execution`
(`ENABLE_INFORMATION_INTENT_EXECUTION`), phase 25 `strategic_intelligence` (`STRAT-002`,
`src/systems/strategic_systems/intelligence.py`).

## Scope Decision
One skill, `cognition-strategy`, with the IS/NOT boundary **foregrounded as the very first
section**, per the ticket's own explicit instruction that this is the specific trap a generic
skill would fall into — a community skill would very plausibly conflate "cognition" (this repo's
narrow internal-self-model meaning) with generic "AI decision-making," which is actually
`src/strategy/`+`src/ai/`+`src/domains/`'s combined job here.

## Unresolved Questions
None — all cited content verified against 4 real docs and real file/phase names.
