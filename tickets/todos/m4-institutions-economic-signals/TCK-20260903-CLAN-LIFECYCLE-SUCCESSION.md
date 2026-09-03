---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20260903-CLAN-LIFECYCLE-SUCCESSION
phase: open
date: 2026-09-03
tags: [social]
---

# TCK-20260903-CLAN-LIFECYCLE-SUCCESSION

## Title
Clan lifecycle — joining, leaving, and succession-on-death

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Idea 40 — build Clan lifecycle mechanics (joining, leaving, succession) on the Party Formation & Lifecycle precedent (party_lifecycle.py). Investigation found party_lifecycle.py's SOC-228 check_leadership does NOT fire on death (pure sociability-margin comparison, no leader-liveness check) — the death/succession path must be built fresh rather than assumed to piggyback on SOC-228. groups.py's dissolve-on-dead-leader (SOC-176/SOC-189) is a separate code path for Groups and stays unmodified. This ticket wires ClanState (schema-only since TCK-20260831-CLAN-STATE-SCHEMA) into the authoritative mutation pipeline for the first time, resolving docs/guidelines/intentional_divergences.md §2.48's deferred succession-on-death divergence. Idea 68 (Inter-Clan Relations) is explicitly out of scope.

## Scope
- Clan joining routes through SocialAppraisalSystem.appraise_contract() (or a new dedicated ContractKind-based method), following the TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT direct ContractKind+appraise_contract() pattern (no shared generic ProposalState base class); adds entity to member_entity_ids via typed StateUpdate/ClanUpdate.
- Clan leaving removes entity from member_entity_ids via typed StateUpdate/ClanUpdate and emits a Clan-specific event.
- Clan succession: on dead/inactive leader, promote highest-sociability surviving member to leader_entity_id, no 0.2-margin election gate.
- Clan dissolution: set dissolved_tick only when member_entity_ids and an asset/institutional-footprint measure are BOTH empty simultaneously.
- Wire ClanState into AuthoritativeState/StateUpdate/apply.py (first-time wiring).
- Update docs/guidelines/intentional_divergences.md §2.48 Verification field, flip Status DEFERRED→RATIFIED.
- Add a dedicated parity ledger entry for the new lifecycle logic (not reuse of SOC-166/228/230/256).
- Update tests/unit/domains/faction/test_clan_state.py's test_clan_state_does_not_touch_authoritative_state, which becomes stale once wired.

## Out of Scope
- Idea 68 (Inter-Clan Relations) — any tension_level interaction beyond what joining/leaving naturally touches.
- Group's (non-Clan) dissolve-on-dead-leader path (groups.py SOC-176/SOC-189) — unmodified.
- Personal inheritance / heir assignment (TCK-20260824-DEFAULT-HEIR-ASSIGNMENT) — distinct scope, not Clan leadership succession.
- Any new asset/institutional-footprint mechanic beyond the minimum needed for the "zero assets" dissolution AC — if out of reach this ticket, defer explicitly as an open question, never silently invent.

## Acceptance Criteria
- [ ] A dead or inactive Clan leader results in promotion of the highest-sociability surviving member to leader_entity_id, with no 0.2 sociability-margin gate (unlike Group's living-leader election, party_lifecycle.py SOC-228).
- [ ] A Clan's dissolved_tick is set only when member_entity_ids is empty AND the Clan's asset/institutional-footprint measure is also empty/zero, simultaneously — either alone does not dissolve the Clan.
- [ ] Joining a Clan routes through SocialAppraisalSystem.appraise_contract() (or an equivalent dedicated typed-contract method), never silent auto-composition; the shared trust hard-cancel prelude (appraisal.py lines 48-54) remains unmodified.
- [ ] Leaving a Clan removes the entity from member_entity_ids via a typed StateUpdate/ClanUpdate (never direct field mutation) and emits a Clan-specific event.
- [ ] docs/guidelines/intentional_divergences.md §2.48's Verification field is updated with the landed test path, and Status flips DEFERRED→RATIFIED.
- [ ] tests/unit/domains/faction/test_clan_state.py's test_clan_state_does_not_touch_authoritative_state is updated/replaced to reflect ClanState is now wired (not left contradicting reality).
- [ ] A new dedicated parity ledger entry (docs/parity_ledger/social_narrative.yaml) is added for Clan lifecycle logic, distinct from SOC-166/228/230/256.

## Related Tickets
- TCK-20260831-CLAN-STATE-SCHEMA
- TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT
- TCK-20260619-E41B-LEADERSHIP
- TCK-20260619-E41D-DEFECTION-ESCORT
- TCK-20260824-DEFAULT-HEIR-ASSIGNMENT
- TCK-20260831-TRUST-GATED-TEACHING

## Related Docs
- docs/guidelines/intentional_divergences.md
- docs/parity_ledger/social_narrative.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- src/systems/social_systems/party_lifecycle.py
- src/systems/world_systems/groups.py
- src/core/state.py
- src/core/strategic.py
- src/systems/social_systems/appraisal.py
- tests/unit/social/test_party_lifecycle.py
- tests/unit/social/test_groups.py
- tests/unit/domains/faction/test_clan_state.py

## Assumptions / Open Questions
- Whether the "zero assets" dissolution rule requires a new ClanState schema field (no assets/institutional-footprint concept exists today) is an open Plan-phase question — may need a schema addition, or the AC may need scoping down to member_entity_ids-only with assets deferred to a follow-up ticket. Do not silently invent a field.
- Wiring ClanState into AuthoritativeState/StateUpdate/apply.py for the first time is architecturally larger than a typical "add a service function" change — size Plan accordingly.
- No registered "social" layer exists (20 layers total); predecessor TCK-20260831-CLAN-STATE-SCHEMA used layer: core — follow the same choice unless a new layer is registered.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
