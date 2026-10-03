---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260613-DOC-COGNITION-SUBSYSTEM
phase: done
date: 2026-06-13
tags: [documentation, cognition, self-model, capability-estimate, knowledge-model, need-interpretation, self-assessment]
---

# TCK-20260613-DOC-COGNITION-SUBSYSTEM

## Title
Document the Entity Cognitive Architecture Subsystem: Self-Model, Capability Estimation, Knowledge Model, Need Interpretation

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`src/cognition/` is a standalone subsystem (~800 lines across 6 files) implementing the entity's internal cognitive architecture — how it models itself, estimates its own capabilities, maintains a knowledge representation of the world, and interprets biological needs into actionable drives.

This is distinct from:
- `src/domains/` — domain-level decision pipelines (adventure routing, motivation evaluation, etc.)
- `src/strategy/` — bounded cognition capacity management
- `docs/systems/strategic_cognition.md` — high-level system overview (85 lines)
- `docs/strategy/bounded_cognition_contract.md` — bounded cognition limits and lead management

None of those docs cover what `src/cognition/` actually does. An agent asked "how does an entity know what it's capable of?" or "what is in an entity's knowledge model?" cannot find an answer without reading source.

The plan proposed adding `self_model.md` to `docs/core/` — but `src/cognition/` is its own subsystem, not a core state model. The correct target location is a new `docs/cognition/` directory (paralleling `src/cognition/`), or grouped docs within `docs/simulation/` if a new directory is undesirable.

## Scope

Create a new `docs/cognition/` directory with the following docs:

### 1. `docs/cognition/README.md`
Index and orientation for the cognition subsystem. Explains:
- What `src/cognition/` is (entity self-knowledge subsystem) and what it is NOT (strategy, domain decision logic, or AI personality)
- How it relates to `src/strategy/` (cognition produces the self-model that strategy reads)
- How it relates to `src/domains/motivation/` and `src/domains/perception/` (cognition feeds those domains)
- The tick lifecycle: when cognition phases run relative to domain phases

### 2. `docs/cognition/self_model_contract.md`
The entity self-model and self-assessment. Covers:
- What the self-model is: the entity's internal representation of its own state, capabilities, and limitations
- Self-assessment logic (`self_assessment.py`): what properties the entity evaluates, how scores are computed, what triggers re-assessment
- Self-model phase (`self_model_phase.py`): when and how the self-model is updated in the tick pipeline
- What state the self-model reads (entity attributes, recent combat outcomes, inventory, skill levels)
- What state the self-model writes (self-model fields on entity state — read-only path, intents only)
- How downstream systems use the self-model (strategy reads it, domains consume it)
- Edge cases: first-tick initialization, entity death mid-self-assessment, stale self-model after rapid attribute change
- Source areas: `src/cognition/self_model_phase.py`, `src/cognition/self_assessment.py`
- Regression tests: cite `docs/testing/self_model_coverage.md` and any test files

### 3. `docs/cognition/capability_and_knowledge_contract.md`
How entities estimate capabilities and maintain world knowledge. Covers:
- **Capability estimation** (`capability_estimate.py`): what it estimates (combat power, crafting success rate, resource reach, movement capacity), estimation algorithm, confidence decay over time, how estimates update after new evidence
- **Knowledge model** (`knowledge_model.py`): what entities know about the world (resource node locations, region threat level, entity positions), knowledge freshness model, forgetting rules, capacity limits, how knowledge feeds adventure routing blockers and strategic planning
- The relationship between capability estimates and adventure route scoring (the adventure domain reads capability estimates to evaluate route feasibility)
- Source areas: `src/cognition/capability_estimate.py`, `src/cognition/knowledge_model.py`
- Regression tests: cite relevant unit or integration tests

### 4. `docs/cognition/need_interpretation_contract.md`
How biological drives are converted to actionable needs. Covers:
- What need interpretation is: translating biological pressure signals (hunger, fatigue, injury) into prioritized need signals that motivation and strategy can act on
- The interpretation rules: which biological state triggers which need type, urgency thresholds, how multiple simultaneous needs are ranked
- How interpreted needs flow to `src/domains/motivation/` (motivation domain reads need priorities to update directive scoring)
- How world motivation pressure (`src/world/motivation/pressure_resolver.py`) overlays with internal need interpretation
- Trace events (`trace_events.py`): what cognitive events are emitted for observability, how they appear in history/warehouse
- Source areas: `src/cognition/need_interpretation.py`, `src/cognition/trace_events.py`
- Regression tests: cite relevant tests

All docs follow the standard logic-contract template.

## Out of Scope
- `src/ai/` personality and scoring (separate subsystem, different concern)
- `src/strategy/` bounded cognition capacity management (already has `docs/strategy/bounded_cognition_contract.md`)
- `src/domains/motivation/`, `src/domains/perception/` (covered by TCK-20260613-DOC-DOMAIN-CONTRACTS — these are domain-level, cognition is the backing subsystem)
- Removing the proposed `self_model.md` from TCK-20260613-DOC-CORE-DIRTY-STATE (that ticket should be updated to drop the self_model doc since this ticket covers it properly)

## Acceptance Criteria
- [ ] `docs/cognition/` directory created.
- [ ] `docs/cognition/README.md` created. Clearly states what the cognition subsystem is and is not. Explains relationship to strategy, domains/motivation, and domains/perception.
- [ ] `docs/cognition/self_model_contract.md` created. Covers self-assessment algorithm, phase lifecycle, downstream consumers. Cites `docs/testing/self_model_coverage.md`.
- [ ] `docs/cognition/capability_and_knowledge_contract.md` created. Covers capability estimation algorithm and knowledge model capacity/freshness rules. Links to adventure domain (capability → route feasibility).
- [ ] `docs/cognition/need_interpretation_contract.md` created. Covers drive-to-need translation rules, urgency thresholds, and trace event schema.
- [ ] All docs have frontmatter: `status: active`, `layer: simulation`, `authority: P1`, `audience: agent`, `last_verified: 2026-06-13`.
- [ ] `docs/cognition/` added to `docs/README.md` layer table.
- [ ] TCK-20260613-DOC-CORE-DIRTY-STATE updated to remove the proposed `self_model.md` (it belongs here, not in `docs/core/`).
- [ ] `make knowledge-index-update` and `make docs-registry` run after completion.

## Related Tickets
- TCK-20260613-DOC-HARDENING-EPIC (parent)
- TCK-20260613-DOC-DOMAIN-CONTRACTS (motivation and perception domains consume cognition output — cross-link and correct source references there)
- TCK-20260613-DOC-CORE-DIRTY-STATE (remove self_model.md from scope of that ticket; it belongs here)
- TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION (world motivation pressure and perception gate feed into cognition — cross-link)

## Related Docs
- `docs/systems/strategic_cognition.md` — high-level strategic cognition overview (cross-link but do not duplicate)
- `docs/strategy/bounded_cognition_contract.md` — bounded cognition capacity limits (adjacent but distinct)
- `docs/testing/self_model_coverage.md` — test coverage for self-model (cite in self_model_contract.md)
- `docs/mechanics/04_strategic_cognition.md` — P0 mechanics law for strategic cognition
- `docs/mechanics/01_entity_anatomy.md` — P0 entity anatomy (biological pressures that drive need interpretation)
- `docs/specs/2026-04-10-STRAT-KNOWLEDGE-UNIFICATION-design.md` — historical design spec for knowledge unification

## Related Stored Artifacts
None

## Related Code Areas
- `src/cognition/self_model_phase.py`
- `src/cognition/self_assessment.py`
- `src/cognition/capability_estimate.py`
- `src/cognition/knowledge_model.py`
- `src/cognition/need_interpretation.py`
- `src/cognition/trace_events.py`
- `src/world/motivation/pressure_resolver.py` (world-side motivation pressure)
- `src/world/perception/gate.py` (world-side perception gate)
- `src/domains/motivation/` (reads cognition output)
- `src/domains/perception/` (reads cognition output)
- `src/strategy/` (reads self-model)

## Assumptions / Open Questions
- Verify whether `docs/cognition/` is the right new directory name or whether these docs should go into `docs/simulation/cognition/`. Check whether any existing Docusaurus sidebar config needs updating for a new top-level docs directory.
- The `trace_events.py` file emits observability events — verify where these appear in the warehouse/history API before writing the trace section.
- Before writing capability estimation algorithm details, verify the actual estimation logic in `src/cognition/capability_estimate.py` — do not invent formulas from the mechanics chapter.

## Implementation Notes
1. Read `docs/testing/self_model_coverage.md` first — it describes what the test suite expects from the self-model, which gives a good starting point for what the contract must cover.
2. Read `src/cognition/` files in this order: `self_model_phase.py` (phase entry point) → `self_assessment.py` → `capability_estimate.py` → `knowledge_model.py` → `need_interpretation.py` → `trace_events.py`.
3. After understanding the cognition subsystem, read `src/domains/motivation/service.py` and `src/domains/perception/service.py` to verify how they consume cognition output — cross-link those relationships.
4. Update TCK-20260613-DOC-CORE-DIRTY-STATE to remove `self_model.md` from its Files Changed list.

## Test Summary
Not applicable — documentation ticket.

## Files Changed
- `docs/cognition/README.md` (new directory + new file)
- `docs/cognition/self_model_contract.md` (new)
- `docs/cognition/capability_and_knowledge_contract.md` (new)
- `docs/cognition/need_interpretation_contract.md` (new)
- `docs/README.md` (updated: add cognition/ to layer table)

## Completion Summary
Created docs/cognition/ directory with 4 docs: README.md (subsystem orientation, pipeline, consumer map), self_model_contract.md (8 weakness/strength thresholds, composite stress/confidence formulas, dirty check logic, edge cases), capability_and_knowledge_contract.md (4 estimation formulas: combat/travel/gather/craft; knowledge model assimilation answer_kind mapping, information opacity invariant), need_interpretation_contract.md (9 need types with urgency thresholds, survival-outranks-growth rule, trace event schema). Updated docs/README.md with cognition/ section. docs-registry: 52 files changed, simulation layer now 18 docs.
