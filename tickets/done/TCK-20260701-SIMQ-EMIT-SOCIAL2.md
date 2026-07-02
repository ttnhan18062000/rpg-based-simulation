---
status: done
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY
phase: open
date: 2026-07-01
tags: [simq, event-emission, social, faction, economy, narrative, scoring]
---

# TCK-20260701-SIMQ-EMIT-FACTION-ECONOMY

## Title
SimQ: Emit remaining SOCIAL, FACTION, ECONOMY, and NARRATIVE gap events

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Seven small emission gaps remain across four pillars after all prior emit tickets.
None of these individually moves a grade, but together they close the last scoring
infrastructure stubs in SOCIAL, FACTION, ECONOMY, and NARRATIVE. All 7 are either
one-line emitter additions or require a lightweight new signal in an existing subsystem.

Missing events by pillar:

**SOCIAL (§3.8):**
- `social_memory_created` — no emitter; fires when a new SocialMemoryRecord is created
  (from TCK-20260628-E43G-NEMESIS-RELATION, SocialMemoryRecord exists in campaigns domain)
- `contract_milestone_completed` — no emitter; contract milestone tracking exists but
  completion event not emitted to quality hub

**FACTION (§3.7):**
- `alliance_proposed` — no emitter; `alliance_accepted` fires when ALLIED state is confirmed
  but the proposal stage has no event
- `resource_seized` — no emitter; resource control transfer via faction conflict not emitted

**ECONOMY (§3.4):**
- `paid_info_transaction` — ECONOMY pillar event for information purchases (DISTINCT from
  `paid_information_transaction` which is the INFORMATION pillar event). Engine only emits
  the INFORMATION version. Adding the ECONOMY version requires a second emit in
  `event_extractor.py` when `src_kind == INFORMATION_PURCHASE`
- `conservation_law_verified` — no emitter; conservation law is checked on each transaction
  but a passing verification is not emitted (only violations are caught)

**NARRATIVE (§3.5):**
- `scenario_objective_progressed` — `scenario_runtime.py` only emits `scenario_objective_completed`;
  no intermediate progress event fires when a sub-objective advances

## Scope
1. **SOCIAL — `social_memory_created`**: add emitter in `SocialMemoryExporter` or the
   campaigns orchestrator pathway where `SocialMemoryRecord` is constructed; payload:
   `entity_id`, `target_id`, `memory_type`, `tick`
2. **SOCIAL — `contract_milestone_completed`**: find contract milestone tracking in
   `src/systems/world_systems/` or campaigns domain; emit when a milestone within an active
   contract is marked complete (distinct from `contract_completed`)
3. **FACTION — `alliance_proposed`**: add emitter in diplomatic stance update logic;
   fires when faction A initiates alliance proposal with faction B (before ALLIED state);
   payload: `proposing_faction`, `target_faction`, `tick`
4. **FACTION — `resource_seized`**: add emitter when faction conflict resolution results
   in a resource node changing controlling faction; payload: `faction_id`, `node_id`,
   `region_id`, `tick`
5. **ECONOMY — `paid_info_transaction`**: in `event_extractor.py`, where
   `src_kind == INFORMATION_PURCHASE` emits `paid_information_transaction` (INFORMATION pillar),
   add a second emit of `paid_info_transaction` (ECONOMY pillar); same conditions, different
   contract type
6. **ECONOMY — `conservation_law_verified`**: in `ConservationLawChecker` or equivalent,
   after a passing verification, emit `conservation_law_verified`; payload: `law_id`,
   `entity_id`, `tick`, `checked_value`; emit at low rate (e.g., 1 per N ticks) to avoid
   noise — not on every tick's passing check
7. **NARRATIVE — `scenario_objective_progressed`**: in `ScenarioRuntimeService`, emit when
   a sub-objective within an active scenario objective advances its completion fraction;
   payload: `scenario_id`, `objective_id`, `progress_fraction`, `tick`
8. Update `docs/simulation_quality/event_type_coverage.md §3.4–§3.8`
9. Add unit tests for each emitter

## Out of Scope
- Changing scorer weights for any of the four pillars
- Modifying contract, alliance, or conservation law mechanics
- Creating new campaign or scenario infrastructure

## Acceptance Criteria
- [ ] All 7 event types emitted under correct conditions
- [ ] `paid_info_transaction` and `paid_information_transaction` are distinct events reaching distinct scorers (ECONOMY vs INFORMATION)
- [ ] `conservation_law_verified` emits at throttled rate (not every tick)
- [ ] `event_type_coverage.md §3.4, §3.5, §3.7, §3.8` updated — 7 entries removed
- [ ] No regression in existing economy, faction, social, or narrative tests

## Related Tickets
- TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION — prior social/faction emit pass
- TCK-20260629-SIMQ-EMIT-ECONOMY — prior economy emit pass (paid_info_transaction gap documented there)
- TCK-20260628-E43G-NEMESIS-RELATION — SocialMemoryRecord implementation reference
- TCK-20260629-SIMQ-EMIT-NARRATIVE — prior narrative emit pass (scenario_objective_completed context)

## Related Docs
- `docs/simulation_quality/event_type_coverage.md §3.4–§3.8`
- `docs/simulation_quality/quality_scoring_contract.md §5` — four scorer contracts
- `docs/mechanics/03_economic_laws.md` — conservation law (atomic conservation)

## Related Code Areas
- `src/observability/event_extractor.py` — paid_info_transaction second emit
- `src/engine/scenario_runtime.py` — scenario_objective_progressed
- `src/campaigns/` — SocialMemoryRecord, contract milestone
- Faction diplomacy module — alliance proposal stage
- Economy enforcement / conservation law checker

## Assumptions / Open Questions
- `conservation_law_verified` at full rate (every entity every tick) would generate enormous
  noise. Confirm throttle rate with quality_scoring_contract §5 before implementing.
  Suggested: emit only when `entity_id % 10 == tick % 10` (10% sampling) or once per 50 ticks per entity.
- `resource_seized` requires finding where resource control transfers during faction conflict
  resolution — may not exist yet if faction conflict is still a stub. Investigate first;
  if no transfer logic exists, create a minimal stub that fires during territory ownership changes.
- `alliance_proposed` vs `alliance_accepted` boundary — confirm with faction diplomacy code
  that proposal and acceptance are distinct state transitions, not collapsed into one.

## Test Summary
- Unit: `paid_info_transaction` and `paid_information_transaction` both fire on INFORMATION_PURCHASE, reaching different scorers
- Unit: `conservation_law_verified` fires at throttled rate (not every tick)
- Unit: `social_memory_created` payload includes `memory_type`
- Integration: 500-tick urban_political run produces > 0 conservation_law_verified events

## Files Changed
- `src/observability/event_extractor.py` — paid_info_transaction, conservation_law_verified, alliance_proposed, resource_seized emitters
- `src/engine/scenario_runtime.py` — scenario_objective_progressed emitter
- `tests/unit/observability/test_event_extractor_faction_economy.py` — 12 unit tests
- `docs/parity_ledger/social_narrative.yaml` — updated SOC-235 divergence_note; added SOC-236; fixed pre-existing YAML error
- `docs/simulation_quality/event_type_coverage.md` — §3.4, §3.5, §3.7 gaps marked resolved; §3.8 remains blocked

## Completion Summary
5 emitters implemented: paid_info_transaction, conservation_law_verified, alliance_proposed,
resource_seized (event_extractor.py), scenario_objective_progressed (scenario_runtime.py).
social_memory_created and contract_milestone_completed remain blocked — SocialMemoryExporter
has no event recorder; ContractState has no milestones field. 12 unit tests pass; 1060 total pass.
Fixed pre-existing YAML parse error in social_narrative.yaml line 2790.
