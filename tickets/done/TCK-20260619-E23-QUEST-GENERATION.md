---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E23-QUEST-GENERATION
phase: open
date: 2026-06-19
tags: [quest-generation, pressure-driven, opportunity-type, adventure, world-emergence, epic, phase-2]
---

# TCK-20260619-E23-QUEST-GENERATION

## Title
Epic 2.3 · Pressure-Driven Quest Generation

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
Quest definitions are the highest-urgency content gap (Gap Risk 15/15 in D07). Only 5 hardcoded `QuestKind`s and 6 static templates exist. The `world_emergence` `OpportunityType` extension pattern is reusable as a trigger source — not starting from zero. Authored templates from Epic 1.3 serve as static fallbacks.

Score: 9/10 · Effort: M · Source: `docs/audits/D07_content_coverage.md` F1, `docs/audits/D01_rpg_feature_impact.md`

Note: `TCK-20260425-PH8-M2` (static level-scaled quest generation) and `TCK-20260427-QUEST-IDENTITY` (quest identity/reward fixes) are done. This epic adds *pressure-driven* dynamic generation on top of the existing static system.

## Scope
- Design `QuestOpportunity` as a new `OpportunityType` in `src/domains/` world emergence layer: `QuestOpportunity(kind, trigger_condition, objective_chain, reward_spec, faction_source, expiry_ticks)`
- Implement `QuestOpportunityGenerator` triggered by: resource depletion events (Epic 2.1), faction tension thresholds (Phase 5 — stub only), calamity aftermath signals, entity needs unsatisfied for N ticks
- Wire generated quests into adventure decision pipeline: HERO entities with matching capabilities score quest opportunities above generic harvesting routes
- Implement 3 quest trigger families: `resource_crisis` (fetch/secure depleted resource), `threat_response` (eliminate/scout threat), `diplomatic_errand` (deliver/negotiate — stub until Phase 5)
- Quest lifecycle state machine: `OFFERED → ACTIVE → PROGRESSED → COMPLETED / FAILED / EXPIRED`; tracked in `AuthoritativeState.quest_registry`
- Quest completion applies rewards (gold, XP, faction reputation delta) through authoritative mutation pipeline
- Authored quest templates (Epic 1.3) serve as static fallbacks when pressure signals are absent
- Child tickets: (a) QuestOpportunity type + generator, (b) lifecycle state machine + quest_registry, (c) reward application, (d) HERO capability matching

## Out of Scope
- Multi-quest chains/branching narratives (Phase 4)
- Faction-commissioned quests (Phase 5 — diplomatic_errand stub only here)
- Quest board/marketplace mechanic
- Player-facing quest UI

## Acceptance Criteria
- In a 400-tick `urban_political` run after a resource depletion event, at least one HERO entity starts a `resource_crisis` quest
- At least one quest reaches COMPLETED state per 1000-tick run
- Quest completion produces a gold and XP reward entry in entity state

## Related Tickets
- TCK-20260619-E21-RESOURCE-ECOLOGY (prerequisite: provides depletion trigger signals)
- TCK-20260619-E13-CONTENT-FOUNDATION (prerequisite: authored templates as fallback)
- TCK-20260619-E31-SCENARIO-RUNTIME (unlocked: scenario has meaningful quest objectives)
- TCK-20260619-E43-SOCIAL-MEMORY (unlocked: quest outcomes to remember)

## Related Docs
- `docs/audits/D07_content_coverage.md`
- `docs/audits/D01_rpg_feature_impact.md` § Pressure-Driven Quest Generation
- `docs/mechanics/03_economic_laws.md` (quest rewards are economic transactions — gold/XP awards must satisfy conservation laws; update if quest reward flow is new)
- `docs/engine/authoritative_pipeline.md` (quest completion applies rewards through the authoritative mutation pipeline — verify phase insertion before implementing reward application)
- `docs/simulation/domains/world_emergence_contract.md` (OpportunityType extension pattern — update with QuestOpportunity entry)
- `docs/quests/quest_contract.md` (update with QuestOpportunity lifecycle, trigger families, and registry contract)
- `docs/plans/long_term_development_roadmap.md` § Epic 2.3
- `docs/parity_ledger/town_resource.yaml` (quest economy entries — update to `verified`)
- `docs/parity_ledger/progression.yaml` (quest XP/reward entries — update to `verified`)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260612-QUESTS-CONTRACT/`
- `stored_artifacts/TCK-20260425-PH8-M2/` (prior static quest generation)

## Related Code Areas
- `src/systems/world_systems/quests.py` (existing LEG-RPG-141 quest gen pattern)
- `tests/unit/quest/test_quest_generation.py` (existing tests)
- `src/core/models/quests.py` (QuestState, RewardState)
- `src/domains/` (WorldEmergencePhase — OpportunityType extension point)
- `src/core/state.py:L981` (AuthoritativeState — add quest_registry field)

## Assumptions / Open Questions
- Is `quest_registry` already a field in `AuthoritativeState`, or does it need to be added? Check `src/core/state.py`
- Does the existing `QuestState` model support lifecycle states OFFERED/ACTIVE/PROGRESSED/EXPIRED, or only OPEN/COMPLETED? Check `src/core/models/quests.py`

## Implementation Notes
Follow the OpportunityType extension pattern from `world_emergence_contract.md` and `adventure_routing_contract.md` — proven twice at small scale. Add `QuestOpportunity` as a new `OpportunityType` enum value, implement a generator, add scorer, add mapper. Keep `diplomatic_errand` as a stub (generate but reward=none) until Phase 5.

After implementation: update `docs/quests/quest_contract.md` with the full lifecycle state machine and QuestOpportunity fields. Update `docs/simulation/domains/world_emergence_contract.md` to list `QUEST_OPPORTUNITY` as a new OpportunityType. Update `docs/parity_ledger/town_resource.yaml` and `progression.yaml` for quest generation/reward entries. Run `make knowledge-index-update` after all docs/ changes.

## Test Summary
- Extend `tests/unit/quest/test_quest_generation.py`:
  - `test_resource_crisis_quest_generated_on_depletion()` — inject a depletion event, assert `QuestOpportunityGenerator` produces a `resource_crisis` QuestOpportunity
  - `test_quest_generation_determinism()` — same depletion signal + same seed → same quest id and parameters (extend existing pattern)
- New file `tests/unit/quest/test_quest_lifecycle.py`:
  - `test_quest_lifecycle_transitions()` — step through OFFERED→ACTIVE→PROGRESSED→COMPLETED; assert each transition valid
  - `test_quest_expires_after_expiry_ticks()` — tick past expiry_ticks; assert EXPIRED state
- New file `tests/integration/scenarios/test_pressure_quest.py`:
  - `test_resource_crisis_quest_starts_after_depletion()` — 400-tick run; deplete a node; assert HERO entity starts `resource_crisis` quest
  - `test_quest_completed_produces_gold_and_xp()` — 1000-tick run; assert ≥1 quest COMPLETED with non-zero reward

## Files Changed
- `tickets/todos/TCK-20260619-E23A-QUEST-OPPORTUNITY.md` (new)
- `tickets/todos/TCK-20260619-E23B-QUEST-LIFECYCLE.md` (new)
- `tickets/todos/TCK-20260619-E23C-QUEST-REWARDS.md` (new)
- `tickets/todos/TCK-20260619-E23D-HERO-MATCHING.md` (new)
- `staging_artifacts/TCK-20260619-E23-QUEST-GENERATION/investigation.md` (new)
- `staging_artifacts/TCK-20260619-E23-QUEST-GENERATION/plan.md` (new)
- `staging_artifacts/TCK-20260619-E23-QUEST-GENERATION/test_plan.md` (new)

## Completion Summary
EPIC_SCOPED 2026-06-20. Scoped into 4 child tickets. Investigation confirmed: WorldOpportunityPressure + DynamicQuestSeedService already exist in services.py (seed generation from opportunity pressures). No QuestOpportunity typed model, no lifecycle state machine (OFFERED/ACTIVE/EXPIRED), no quest_registry in AuthoritativeState, no HERO routing integration. E23 builds typed model + lifecycle on top of existing seed infrastructure.
