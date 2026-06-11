---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20260502-STRATEGIC-HARDENING
artifact_type: investigation
tags: [strategic, hardening]
---

# Investigation: Strategic Hardening E5.5

## Reason Code Audit
Currently, many systems use raw strings like `"OUT_OF_RANGE"` or `"INSUFFICIENT_GOLD"`.
`LegalityServiceV2` returns `(bool, str)`.
`Pipeline` uses these strings to populate `rejection_registry`.
Law 83 requires first-class reason codes.

## Strategic Bandwidth
`StrategicIntelligenceSystem` has `infer_leads` and `infer_biological_concerns`.
It currently adds them to the strategic component without checking limits.
The `profile` has `max_leads` and `max_concerns`.
`DetourSuggestionSystem` has a `enforce_bandwidth` method (stubbed or partially implemented).

## Interaction Interruption
`InteractionSystem.enforce` only checks `moved_this_tick`.
Damage is applied in `ApplyPath._apply_entity_update` or the `CombatResolver`.
However, `InteractionSystem` is called in `AuthoritativeApplyPipeline.refine`, which is *before* state application.
Wait, `refined_update` is built in `refine`.
Damage taken is part of the *update* being refined.
So `InteractionSystem` can see `ent_upd.combat_result.damage_taken`.

## Group Priority
In `TacticalDecisionSystem`, we need to check `entity.group_id`.
If present, we check `state.groups[entity.group_id].shared_target_id`.
If the leader is attacking this target, the entity should prioritize it.

## Tick Budget
`Kernel.tick_once` has a tight loop of phases.
We should check the elapsed time after each major phase.
If it exceeds the budget, we should set a `budget_exhausted` flag and skip remaining phases (except cleanup/persistence).
