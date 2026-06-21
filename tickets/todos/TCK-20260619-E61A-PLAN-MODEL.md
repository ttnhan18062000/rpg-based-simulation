---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61A-PLAN-MODEL
phase: open
date: 2026-06-22
tags: [progression-planner, campaign-state, data-model, multi-episode]
---

# TCK-20260619-E61A-PLAN-MODEL

## Title
Epic 6.1A · ProgressionPlan Model + CampaignState Field

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Define the `ProgressionPlan` frozen dataclass and its component types (`BuildGoal`,
`MilestoneCheck`, `RevisionTrigger`). Add `progression_plans: Dict[int, ProgressionPlan]`
field to `CampaignState` with full `to_dict()` / `from_dict()` serialization support.

## Scope
- New file: `src/domains/campaigns/progression_plan.py`
  - `BuildGoal(frozen=True)`: `goal_id: str`, `target_route_family: str`,
    `target_item_id: Optional[str]`, `target_level: Optional[int]`, `status: str`
    (values: "pending" | "in_progress" | "completed" | "blocked")
  - `MilestoneCheck(frozen=True)`: `milestone_id: str`, `target_level: int`,
    `episode_index: int`, `achieved: bool`
  - `RevisionTrigger(frozen=True)`: `trigger_id: str`, `kind: str`
    (values: "mentor_dead" | "item_unavailable" | "goal_completed"),
    `subject: str`, `fired: bool`
  - `ProgressionPlan(frozen=True)`: `entity_id: int`,
    `goal_queue: Tuple[BuildGoal, ...]`, `milestone_checks: Tuple[MilestoneCheck, ...]`,
    `revision_triggers: Tuple[RevisionTrigger, ...]`, `created_episode: int`,
    `last_revised_episode: int`
  - Full `to_dict()` / `from_dict()` on all types; dict keys sorted for determinism
- `src/domains/campaigns/state.py`:
  - Import `ProgressionPlan` from `progression_plan.py`
  - Add `progression_plans: Dict[int, ProgressionPlan] = field(default_factory=dict)`
  - Extend `to_dict()`: `"progression_plans": {str(k): v.to_dict() for k, v in sorted(self.progression_plans.items())}`
  - Extend `from_dict()`: reconstruct `{int(k): ProgressionPlan.from_dict(v) for k, v in ...}`
- Parity ledger: add PROG-110 to `docs/parity_ledger/progression.yaml`
  - text: "ProgressionPlan model serializes and deserializes with full round-trip fidelity"
  - status: verified, priority: P1

## Out of Scope
- Exporter/importer logic (E61B)
- Scoring integration (E61C)
- Plan revision service (E61D)

## Acceptance Criteria
1. `ProgressionPlan` round-trips through `to_dict()` / `from_dict()` with identical field values
2. `CampaignState` with a populated `progression_plans` dict round-trips through `to_dict()` / `from_dict()`
3. `CampaignState` with empty `progression_plans` dict (default) round-trips without error
4. All field names and key conventions follow the `social_memories` pattern (str keys in JSON, int keys in Python)

## Related Tickets
- TCK-20260619-E32-CAMPAIGN-RUNTIME (prerequisite — DONE)
- TCK-20260619-E61-PROGRESSION (parent epic)
- TCK-20260619-E61B-PLAN-EXPORTER (next — depends on this)

## Related Docs
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/investigation.md`
- `docs/parity_ledger/progression.yaml`

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/`

## Related Code Areas
- `src/domains/campaigns/state.py` (CampaignState — add field)
- `src/domains/campaigns/progression_plan.py` (new file)
- `docs/parity_ledger/progression.yaml`

## Assumptions / Open Questions
- `target_route_family` is stored as `str` (RouteFamily.value) to avoid circular import
  between `progression_plan.py` and `src/domains/adventure/schema.py`
- `ProgressionPlan` is frozen; mutations are replaced via `dataclasses.replace()`

## Implementation Notes
- Follow the pattern of `SocialMemoryRecord` for frozen dataclass + serialization
- `progression_plans` default is `field(default_factory=dict)` — backward compatible
  with existing `CampaignState.from_dict()` calls that lack the key (use `.get()`)
- Module must NOT import from `src.engine` or `src.core.state` (same constraint as state.py)

## Test Summary
- `tests/unit/campaigns/test_progression_plan.py`:
  - `test_progression_plan_round_trip`: full ProgressionPlan with non-empty queue/milestones/triggers
  - `test_progression_plan_empty_queue_round_trip`: empty tuple fields
  - `test_campaign_state_with_plans_round_trip`: CampaignState.to_dict/from_dict preserves plans
  - `test_campaign_state_missing_plans_key_backward_compat`: from_dict on dict without "progression_plans" key returns empty dict

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
