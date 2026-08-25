---
status: active
layer: economy
authority: P1
audience: agent
ticket_id: TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK
phase: open
date: 2026-08-24
tags: [economy, cognition]
---

# TCK-20260824-PERSONAL-ECONOMY-SCOPE-BLOCK

## Title
Scope Personal Economy & Material Ambition, Blocked on MotivationModel.values Foundation

## Status
BLOCKED

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The author wants Personal Economy & Material Ambition attached to MotivationModel.values (ValuePreferenceProfile), which is independently confirmed dead-on-arrival -- never populated above 0.5 defaults. This ticket scopes the target design but explicitly does not start implementation until a separate foundation ticket for MotivationModel.values exists.

## Scope
- Create the ticket in a scoping-only/BLOCKED state -- document target design for a Personal Economy & Material Ambition motivation axis attached to MotivationModel.values (ValuePreferenceProfile), with no implementation.
- State the verified dead-on-arrival fact with file:line evidence: ValuePreferenceProfile's 7 fields all default to 0.5, zero production call sites construct MotivationModel/ValuePreferenceProfile with non-default values, so MotivationBiasService.compute_bias_multiplier's (values.X-0.5) deltas are mathematically always 0.0 in every real run.
- Name the not-yet-existing MotivationModel.values foundation ticket as a hard blocking dependency in Related Tickets/Assumptions (no such ticket exists yet anywhere in docs/tickets/stored_artifacts).
- State eventual (unblocked) implementation acceptance criteria as conditional/deferred.
- Set ticket body Status to BLOCKED, not OPEN.

## Out of Scope
- Any src/ code changes while blocked.
- Designing the content-schema/emergent-derivation mechanism for populating MotivationModel.values -- that belongs to the separate, not-yet-scoped foundation ticket.

## Acceptance Criteria
- [ ] Ticket is created and moved to a scoping-only/BLOCKED state -- documents target design, contains no implementation.
- [ ] Ticket names the not-yet-existing MotivationModel.values foundation ticket as a hard blocking dependency in Related Tickets/Assumptions.
- [ ] Ticket body states the verified dead-on-arrival fact with file:line evidence so future readers don't re-derive it.
- [ ] Eventual (unblocked) implementation ACs are stated as conditional/deferred.
- [ ] No src/ changes are made under this ticket while blocked.

### Conditional / Deferred Implementation Acceptance Criteria (only apply once unblocked)
- [ ] (Deferred) A Personal Economy & Material Ambition motivation axis is added to MotivationModel.values with a defined weight/derivation contract, once the MotivationModel.values foundation ticket has landed and values are populated above static defaults in production call sites.
- [ ] (Deferred) MotivationBiasService.compute_bias_multiplier produces non-zero, entity-differentiated deltas for the new axis in real runs, verified by a passing test with concrete non-default entity data.
- [ ] (Deferred) Behavior change is reflected in the relevant Mechanics Bible chapter (docs/mechanics/04_strategic_cognition.md) and the corresponding parity ledger entry (docs/parity_ledger/strategic_cognition.yaml).

## Related Tickets
None. No foundation ticket for MotivationModel.values exists yet anywhere in docs/tickets/stored_artifacts. A separate ticket must be filed and completed first to populate MotivationModel.values (ValuePreferenceProfile) above static 0.5 defaults in production call sites; this ticket is hard-blocked on that not-yet-existing ticket.

## Related Docs
- docs/architecture/cognition_domain_ownership.md
- docs/mechanics/04_strategic_cognition.md
- docs/plans/rpg_design_roadmap/rpg_m1_quick_wins_epic.md

## Related Stored Artifacts
None.

## Related Code Areas
- src/core/cognition.py
- src/domains/motivation/service.py

## Assumptions / Open Questions
- No foundation ticket for MotivationModel.values exists yet anywhere in docs/tickets/stored_artifacts -- cannot cite a concrete ticket ID; this must be stated explicitly as "no foundation ticket filed yet" rather than guessed at.
- This concern independently restates an identical blocker already documented in the M1 epic doc's own Idea 24, supporting scope-only/blocked treatment rather than full implementation now.
- `layer: economy` was chosen over `cognition`-adjacent layers (`strategy`, `core`) because the ticket's subject matter (Personal Economy & Material Ambition) is an economy-domain motivation axis; the blocking dependency lives in cognition/motivation code, reflected via the `cognition` tag instead.

## Implementation Notes


## Test Summary


## Files Changed


## Completion Summary

