---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260501-SOCIAL-LIFECYCLE
phase: done
date: 2026-05-01
tags: [social, lifecycle]
---

# TCK-20260501-SOCIAL-LIFECYCLE

## Title

Complete Social Contract and Party Lifecycle

## Status

DONE

## Tier
standard

## Type
chore

## Priority
P1

## Request Summary

Implement the full social lifecycle from offer to consequence, ensuring parties are grounded in durable contracts and coordinated through shared strategic objectives.

## Scope

- [ ] Implement explicit Contract Lifecycle: `OFFERED`, `ACCEPTED`, `ACTIVE`, `FULFILLED`, `FAILED`, `BETRAYED`, `EXPIRED`, `CANCELLED`.
- [ ] Implement Offer Appraisal logic: trust, reputation, reward, risk, and greed.
- [ ] Implement Party Membership derived from accepted shared-purpose contracts.
- [ ] Implement Party Coordination: Shared objectives, roles, targets, and regroup commands.
- [ ] Implement Social Consequences: Trust/reputation updates from contract outcomes.
- [ ] Implement Party Dissolution on purpose completion or contract failure.
- [ ] Create regression test suite in `tests/engine/test_social_lifecycle.py`.

## Out of Scope

- Emotional mood systems (kept tactical for now).
- Complex gossip/rumor propagation (Phase 6).

## Acceptance Criteria

- Contract state transitions follow strict rules (no invalid jumps).
- Party formation requires an underlying active contract or quest.
- Party members coordinate movement/combat toward shared goals.
- Trust/Reputation updates correctly after fulfillment or betrayal.
- Parties dissolve correctly when their contract ends.
- Regression tests pass end-to-end.

## Related Tickets

- None

## Related Docs

- `resource_v2_e4_phases.md`

## Related Stored Artifacts

- None

## Related Code Areas

- `src/core/social.py`
- `src/systems/social.py`
- `src/systems/party.py`
- `src/social/appraisal.py`
- `src/social/contracts.py`

## Implementation Notes

- Use `SocialUpdate` for all authoritative social state changes.
- Ensure `EntityState.social` contains the durable contract registry.
- Party coordination should hook into `StrategicIntelligenceSystem` to distribute objectives.

## Test Summary

- [ ] Unit tests for contract state machine.
- [ ] Integration tests for party coordination.
- [ ] Lifecycle tests for appraisal and consequences.
