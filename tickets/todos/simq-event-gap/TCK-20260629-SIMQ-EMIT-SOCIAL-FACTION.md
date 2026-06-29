---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION
phase: open
date: 2026-06-29
tags: [simq, observability, event-gap, social, faction]
---

# TCK-20260629-SIMQ-EMIT-SOCIAL-FACTION

## Title
SimQ: Emit SOCIAL and FACTION Pillar Events from Cooperation, Contract, and Diplomatic Phases

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The SOCIAL pillar scores 11 event types and the FACTION pillar scores 9 event types.
Neither set is currently emitted. SOCIAL events come from PP-05 (cooperation), PP-34 (groups),
PP-35 (active_contracts), PP-36 (expired_offers), PP-18 (interaction_enforcement).
FACTION events come from PP-08 (faction_decision), PP-09 (faction_awareness),
PP-10 (diplomatic_transitions), PP-11 (military_conflict), PP-23 (world_emergence).

Existing engine events (`leadership_changed`, `betrayal_desertion`, `alliance_formed`)
exist in `events.py` — add translation mappings for these in
TCK-20260629-SIMQ-EVENT-TRANSLATE or directly here if that ticket is already done.

## Scope
**SOCIAL events to emit:**

| Event type | Source phase | Trigger |
|---|---|---|
| `cooperation_event` | PP-05 | Joint task formed or help offer accepted |
| `group_joined` | PP-34 | Entity joins a group |
| `group_expelled` | PP-34 | Entity expelled from group |
| `contract_offer_created` | PP-35 | New contract offer generated |
| `contract_offer_accepted` | PP-35 | Contract offer accepted by counterparty |
| `contract_milestone_completed` | PP-35 | Contract milestone achieved |
| `contract_completed` | PP-35 | All milestones completed |
| `contract_lapsed` | PP-35 | Obligor missed milestone; contract lapses |
| `contract_expired_offer` | PP-36 | Offer expired without acceptance |
| `reputation_delta` | PP-18 | Entity reputation changes significantly (> 0.05 threshold) |
| `social_memory_created` | PP-05 or PP-18 | Entity records significant social interaction |

**FACTION events to emit:**

| Event type | Source phase | Trigger |
|---|---|---|
| `diplomatic_transition` | PP-10 | Faction diplomatic state transitions (neutral→hostile etc.) |
| `alliance_proposed` | PP-08 | Alliance proposal generated |
| `alliance_accepted` | PP-08 | Alliance accepted |
| `war_declared` | PP-10 | War declaration event |
| `military_conflict_resolved` | PP-11 | Military battle outcome determined |
| `territory_ownership_changed` | PP-11 or PP-03 | Territory ownership transferred |
| `resource_seized` | PP-11 | Faction acquires contested resource |
| `faction_tension_delta` | PP-09 | Faction tension level changes |
| `faction_extinct` | PP-08 or PP-33 | Faction has no living entities |

**Existing events to map (add to translation table if not already there):**

| Engine event_type | Maps to contract type |
|---|---|
| `leadership_changed` | `diplomatic_transition` (or new type — verify use case) |
| `betrayal_desertion` | `contract_lapsed` (if contract context) or `faction_tension_delta` |
| `alliance_formed` (LegendaryArrivalEvent constant?) | `alliance_accepted` |

## Out of Scope
- NARRATIVE events (quest, chronicle, emergence): TCK-20260629-SIMQ-EMIT-NARRATIVE

## Acceptance Criteria
- [ ] All 11 SOCIAL event types emitted from correct PP phases
- [ ] All 9 FACTION event types emitted from correct PP phases
- [ ] Translation mappings for `leadership_changed`, `betrayal_desertion` added (if not in TRANSLATE ticket)
- [ ] No import of `src/simulation_quality/` from PP-05/08/09/10/11/18/23/34/35/36
- [ ] Faction events carry `faction_id` in payload; social events carry `entity_id`
- [ ] Unit tests per phase emission site
- [ ] SOCIAL and FACTION pillars show non-zero events in calibration run

## Related Tickets
- TCK-20260629-SIMQ-EVENT-TRANSLATE (prerequisite; add `leadership_changed`/`betrayal_desertion` mappings there)
- SIMQ-CALIBRATED-001 parity entry

## Related Docs
- `docs/simulation_quality/quality_scoring_contract.md` §5 SOCIAL, FACTION
- `docs/mechanics/04_strategic_cognition.md` — social memory and cooperation laws

## Related Code Areas
- PP-05 (cooperation), PP-08/09/10/11 (faction phases), PP-18 (interaction_enforcement)
- PP-23 (world_emergence), PP-34/35/36 (groups, contracts, expired offers)
- `src/observability/events.py` — existing LeadershipChangedEvent, BetrayalDesertionEvent

## Assumptions / Open Questions
- PP-34/35/36 are group and contract management phases — verify they are executed each tick
  (may only fire when triggered, not every tick)
- `reputation_delta` fires when delta exceeds a significance threshold (0.05) — verify the
  exact threshold used in PP-18 interaction_enforcement
- `faction_extinct` may be best detected in lifecycle phase (PP-33) rather than PP-08
- `territory_ownership_changed` may overlap with WORLD pillar `region_ownership_changed`
  (faction perspective vs. world perspective of same event) — emit once with both faction_id
  and region_id in payload; both scorers will handle it
