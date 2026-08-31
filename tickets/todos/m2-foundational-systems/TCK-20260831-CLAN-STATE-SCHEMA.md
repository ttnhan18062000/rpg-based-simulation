---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260831-CLAN-STATE-SCHEMA
phase: open
date: 2026-08-31
tags: [faction, social]
---

# TCK-20260831-CLAN-STATE-SCHEMA

## Title
Define ClanState schema reusing FactionState's shape

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Reuse FactionState's shape almost verbatim for a new ClanState. This ticket is schema/shape wiring only — lifecycle actions (formation, dissolution, succession) belong to idea 40 in M4, which targets the same ClanState class and must not race with this ticket over the same dataclass.

## Scope
- Add a new ClanState frozen dataclass (clan_id, name, member_entity_ids, home_region_ids, tension_level, leader_entity_id, founded_tick, dissolved_tick) with to_canonical_dict/from_dict following FactionState's exact pattern (src/core/state.py:609-645).
- Add a new dedicated parity ledger entry to docs/parity_ledger/social_narrative.yaml (not reusing SOC-166/228/230).
- Record a correction to the epic's own risk framing: the Party Formation & Lifecycle precedent has at least 9 real test files (~73 test functions), not 1 as previously stated.
- Explicitly decide and document whether Clan succession should fire on leader death (Group's SOC-228 does NOT — it dissolves instead per SOC-176/189) — if diverging, add a docs/guidelines/intentional_divergences.md entry.
- Explicitly decide whether ClanState.home_region_ids permits non-contiguous holdings, since FactionState.territory's merge logic (apply.py:348-360) has no adjacency/contiguity check and this ticket would implicitly inherit that if reusing the shape.

## Out of Scope
- Lifecycle actions (formation, dissolution, succession execution) — owned by idea 40/M4, not this ticket.
- idea 66 (Region/Place rebuild) — confirmed not a blocker for this ticket in both source docs, no need to sequence after it.

## Acceptance Criteria
- [ ] A new ClanState frozen dataclass exists with clan_id/name/member_entity_ids/home_region_ids/tension_level/leader_entity_id/founded_tick/dissolved_tick, plus to_canonical_dict/from_dict following FactionState's exact pattern.
- [ ] A new dedicated parity ledger entry (not reusing SOC-166/228/230) is added to docs/parity_ledger/social_narrative.yaml.
- [ ] Ticket scope explicitly excludes lifecycle actions (owned by idea 40/M4) — schema/shape only.

## Related Tickets
- TCK-20260619-E53Aa-FACTION-STATE
- TCK-20260619-E41B-LEADERSHIP
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260826-PARITY-FACTION-CANONICAL-SCAN

## Related Docs
- docs/parity_ledger/social_narrative.yaml
- docs/brainstorm/rpg_expected_schemas.html

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/state.py
- src/systems/social_systems/party_lifecycle.py
- src/systems/social_systems/groups.py
- src/engine/apply.py

## Assumptions / Open Questions
- Leadership-succession-on-death is an open divergence decision (Group dissolves on leader death per SOC-176/189/SOC-228, Clan may want different behavior) — must be decided and documented.
- Territory contiguity for ClanState.home_region_ids is an open decision — FactionState's own territory merge has no adjacency check.
- This ticket must not race with idea 40/M4's ticket over the same ClanState dataclass — scope stays schema-only.
- `layer: core` was chosen because this ticket adds a state dataclass to src/core/state.py following existing entity/state primitive patterns; no dedicated `social` or `faction` layer is registered in registries/layer_registry.jsonl.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
