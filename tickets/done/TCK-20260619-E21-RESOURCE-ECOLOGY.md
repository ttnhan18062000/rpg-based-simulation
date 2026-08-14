---
status: done
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E21-RESOURCE-ECOLOGY
phase: epic_scoped
date: 2026-06-20
tags: [resource-ecology, regeneration, scarcity, economy, world-evolution, epic, phase-2]
---

# TCK-20260619-E21-RESOURCE-ECOLOGY

## Title
Epic 2.1 · Resource Ecology Regeneration

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
`ResourceEcologyService` is wired and tick-live but regeneration cycles are not implemented (D02 Finding 5: Score 19/50). Resource nodes are static or reset on scenario reload. Without scarcity cycles, economy never stresses, quests have no organic demand, world pressure is static, and faction conflict has nothing to fight over.

Score: 9/10 · D01 score 22/25 (highest-leverage missing system) · Effort: M · Source: `docs/audits/D02_foundation_features.md` F5.

## Scope
- **Prerequisite:** TCK-20260619-E13-CONTENT-FOUNDATION (resources to actually deplete)
- Add durable fields to `ResourceNodeState` (`src/core/state.py:L808`): `current_charges`, `max_charges`, `regen_rate_per_tick`, `last_harvested_tick`
- Wire `ResourceEcologyService` to apply depletion on harvest (`ResourceTransferIntent` apply path) and regeneration on world tick (existing world tick cadence)
- Implement three regeneration models: `fixed_rate` (N charges/tick), `seasonal` (rate varies by world-age phase), `ecology_linked` (rate tied to biome health from `RegionalPressureModel`)
- Add `resource_depleted` and `resource_recovered` event kinds to event taxonomy
- Wire depletion state into adventure decision scoring: entities near a depleted node score harvesting routes lower (reduce `expected_benefit` proportionally to depletion fraction)
- Add resource availability to `WorldEmergencePhase` scarcity model: regional pressure increases when depletion exceeds threshold
- Update parity ledger `docs/parity_ledger/town_resource.yaml`
- Child tickets: (a) ResourceNodeState schema extension, (b) depletion/regen service logic, (c) scoring wire-up, (d) scarcity signal to WorldEmergencePhase

## Out of Scope
- Faction territorial claims over nodes (Phase 5)
- Quest generation triggered by depletion (Epic 2.3 — uses this as input)
- Population migration from depletion (Epic 5.2)

## Acceptance Criteria
- In a 1000-tick run, at least one resource node reaches 0 charges and recovers at least once
- Entity harvesting routes to depleted nodes score ≤0.5× routes to full nodes of the same type
- Regional scarcity pressure rises in the window following a node depletion event
- `resource_depleted` and `resource_recovered` events appear in `simulation_events.jsonl`

## Related Tickets
- TCK-20260619-E13-CONTENT-FOUNDATION (prerequisite)
- TCK-20260619-E23-QUEST-GENERATION (unlocked: pressure-driven quests use depletion signals)
- TCK-20260619-E33-MACRO-ECONOMY (unlocked: macro-economy needs scarcity signals)
- TCK-20260619-E53-FACTION-DIPLOMACY (unlocked: faction territorial conflict needs resource pressure)

## Related Docs
- `docs/audits/D02_foundation_features.md` § Finding 5
- `docs/audits/D01_rpg_feature_impact.md` § Resource Ecology Regeneration
- `docs/mechanics/03_economic_laws.md` § 3 (Resource Harvesting — update with depletion/regen mechanics)
- `docs/mechanics/05_world_evolution.md` (seasonal regen model ties into world-age phases; ecology-linked regen uses RegionalPressureModel documented here)
- `docs/world/ecology_and_calamity_contract.md` (update to include ResourceEcologyService depletion/scarcity signals)
- `docs/plans/long_term_development_roadmap.md` § Epic 2.1
- `docs/parity_ledger/town_resource.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260613-DOC-WORLD-RUNTIME-SIMULATION/`

## Related Code Areas
- `src/core/state.py:L808` (ResourceNodeState)
- `src/core/update_models/resources.py:L13` (ResourceTransferIntent)
- `src/systems/world_systems/` (ResourceEcologyService)
- `src/domains/adventure/scoring.py` (depletion→benefit reduction)
- `src/domains/` (WorldEmergencePhase scarcity model)
- `docs/parity_ledger/town_resource.yaml`

## Assumptions / Open Questions
- Does `ResourceEcologyService` already have a tick-dispatch hook, or does it need to be registered with the world tick cadence?
- Is `RegionalPressureModel` the right input for ecology-linked regen, or is it a separate ecological model?

## Implementation Notes
Start with `fixed_rate` model as the simplest implementation. Add `seasonal` and `ecology_linked` as follow-up child tickets once the base depletion/regen loop is proven. The parity ledger entry for resource regeneration is likely `missing` — add it with status `verified` after implementation.

After implementation: update `docs/parity_ledger/town_resource.yaml` — add or update entry for resource regeneration with `status: verified`, `v2_evidence` showing depletion/regen in a reference run, and `test_path` to the new ecology test. Update `docs/mechanics/03_economic_laws.md` § 3 if the regeneration model adds new behavior not yet documented. Run `make knowledge-index-update` after any docs/ changes.

## Test Summary
- New file `tests/unit/world/test_resource_ecology.py`:
  - `test_resource_node_depletes_on_harvest()` — assert `current_charges` decrements after a `ResourceTransferIntent` is applied
  - `test_resource_node_regens_fixed_rate()` — assert charges increment at `regen_rate_per_tick` each world tick
  - `test_resource_node_does_not_exceed_max_charges()` — regen stops at `max_charges`
  - `test_harvesting_score_decreases_with_depletion()` — assert `expected_benefit` for a depleted node ≤ 0.5× full node of same type
- New file `tests/integration/scenarios/test_resource_depletion.py`:
  - `test_depletion_and_recovery_in_1000_tick_run()` — assert `resource_depleted` and `resource_recovered` events both appear
  - `test_regional_scarcity_rises_after_depletion()` — assert regional pressure increases in window following depletion event

## Files Changed
- `tickets/todos/TCK-20260619-E21A-NODE-SCHEMA.md` (new)
- `tickets/todos/TCK-20260619-E21B-REGEN-SERVICE.md` (new)
- `tickets/todos/TCK-20260619-E21C-SCORING-WIRE.md` (new)
- `tickets/todos/TCK-20260619-E21D-SCARCITY-SIGNAL.md` (new)
- `staging_artifacts/TCK-20260619-E21-RESOURCE-ECOLOGY/investigation.md` (new)
- `staging_artifacts/TCK-20260619-E21-RESOURCE-ECOLOGY/plan.md` (new)
- `staging_artifacts/TCK-20260619-E21-RESOURCE-ECOLOGY/test_plan.md` (new)

## Implementation Notes (updated after investigation)
Investigation findings (2026-06-20):
- `ResourceNodeState` already has `remaining_charges`, `max_charges`, `respawn_cooldown`, `cooldown_remaining` — missing only `regen_rate_per_tick` (no last_harvested_tick needed; cooldown_remaining already tracks this indirectly).
- `WorldEventCategory.RESOURCE_DEPLETED` exists in `src/domains/world_emergence/schema.py:L16` — schema wired, consumers ready (`world_emergence/models.py:L100/L164`, `campaigns/behavior_change.py:L97`, `cache_strategy.py:L41`). Missing: the emitter.
- `resource_recovered` event does NOT exist in `WorldEventCategory` — must be added.
- `ResourceEcologyService.process_ecology()` only seeds density (new nodes), does NOT regen charges.
- `HarvestSystem` checks `remaining_charges <= 0` but does not emit `RESOURCE_DEPLETED` event.
- `RegionalPressureModel` at `src/domains/world_emergence/models.py:L14` is already the right input.
- `AdventureRouteScorer` at `src/domains/adventure/scoring.py` needs depletion-aware benefit reduction.

## Completion Summary
EPIC_SCOPED 2026-06-20. Scoped into 4 child tickets (E21A/B/C/D). Investigation confirmed depletion event schema exists but emitter and regen logic are missing. E21A adds regen_rate_per_tick + resource_recovered event kind. E21B wires the emitter and regen loop. E21C wires depletion into scoring. E21D is skip/done (scarcity consumer already exists).
