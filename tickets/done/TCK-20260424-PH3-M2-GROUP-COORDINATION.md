# TCK-20260424-PH3-M2-GROUP-COORDINATION

## Title
Phase 3 Milestone 2: Group-Level Coordination and Social Clustering

## Status
DONE

## Request Summary
Implement group formation, cohesion, and shared strategic intent to allow entities to cooperate on projects and engage in coordinated tactical behavior (e.g., party-based exploration or combat).

## Scope
- Define `GroupRecord` and `groups` registry in the authoritative state model.
- Implement `GroupSystem` for clustering-based group formation and distance-based dissolution.
- Add group-aware biases to `TacticalDecisionSystem` (Cohesion, Focus Fire).
- Implement basic group-level intent propagation (shared target).
- Verify coordinated movement and combat behavior in parity tests.

## Out of Scope
- Multi-faction diplomacy.
- Complex hierarchical command structures (Squad Leaders).
- Large-scale army maneuvers.

## Acceptance Criteria
- [x] Allied entities form a group when nearby and pursuing similar goals.
- [x] Group members stay within a configurable cohesion distance of the group anchor.
- [x] Group members prioritize the group's shared target over individual distractions.
- [x] Groups dissolve naturally if members are too far apart or casualties are high.

## Related Tickets
- TCK-20260424-PH3-M1-STRATEGIC-PERSISTENCE (Done)

## Related Docs
- [docs/archive/phase_3_ds_implementation_plan.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/archive/phase_3_ds_implementation_plan.md)
- [docs/combat/tactical_behavior_rulebook_m4.md](file:///home/vboxuser/Work/rpg-based-simulation/docs/combat/tactical_behavior_rulebook_m4.md)

## Related Code Areas
- `src/core/state.py`
- `src/systems/groups.py`
- `src/engine/tactical.py`
- `src/engine/pipeline.py`

## Assumptions / Open Questions
- Representation: Used a central `groups` registry in `AuthoritativeState`.
- Min size: 2.

## Implementation Notes
- Groups are managed authoritatively in `GroupSystem.update_groups`.
- Intent propagation happens by syncing the leader's `target_id` to the `GroupRecord`.
- Cohesion is enforced via a specific `REGROUP` task bias in the tactical system.

## Test Summary
- `tests/parity/test_group_coordination.py`: Verified automated formation, regrouping on distance breach, and focus-fire prioritization.

## Files Changed
- `src/core/state.py`
- `src/core/updates.py`
- `src/engine/apply.py`
- `src/engine/tactical.py`
- `src/engine/pipeline.py`
- `src/systems/groups.py`
- `tests/parity/test_group_coordination.py`

## Completion Summary
Successfully implemented Phase 3 Milestone 2. Entities now cluster into groups based on faction and proximity, maintain spatial cohesion, and coordinate attacks on shared targets. This provides the social foundation for more complex strategic projects in Milestone 3.
