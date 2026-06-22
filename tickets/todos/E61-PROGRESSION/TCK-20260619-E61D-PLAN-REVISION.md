---
status: open
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E61D-PLAN-REVISION
phase: open
date: 2026-06-22
tags: [progression-planner, plan-revision, blocker-detection, narrative-ledger, social-memory]
---

# TCK-20260619-E61D-PLAN-REVISION

## Title
Epic 6.1D · PlanRevisionService + Initial Plan Generation

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Implement `PlanRevisionService` that:
(a) generates an initial `ProgressionPlan` for HERO entities that lack one at episode start,
(b) detects blocked intermediate goals (mentor died, item unavailable) using
    `SocialMemoryRecord.interaction_history` and `EntityCarryForward.alive`,
(c) re-routes the `goal_queue` by advancing past the blocked goal and promoting the next
    viable goal to head position,
(d) emits a `plan_revision` NarrativeLedgerEntry into `CampaignState.narrative_ledger`.
Wire into `CampaignOrchestrator._prepare_next_episode()` after `ProgressionPlanImporter`.

## Scope
- `src/domains/campaigns/plan_revision.py` (new file):
  - `PlanRevisionService`:
    - `generate_initial_plan(entity_id: int, carry_forward: EntityCarryForward, episode_index: int) -> ProgressionPlan`
      - Produces a 3-goal queue for HERO entities based on current level:
        - Level 1–4: head = BuildGoal(target_route_family="craft_upgrade", status="pending")
        - Level 5–9: head = BuildGoal(target_route_family="quest_opportunity", status="pending")
        - Level 10+: head = BuildGoal(target_route_family="gather_resource", status="pending")
      - Includes one MilestoneCheck per goal (target_level = goal unlock threshold)
      - Includes one RevisionTrigger per goal (kind="mentor_dead", fired=False)
    - `detect_and_revise(entity_id: int, plan: ProgressionPlan, carry_forward: EntityCarryForward, social_memory: Optional[SocialMemoryRecord], episode_index: int) -> Tuple[ProgressionPlan, Optional[NarrativeLedgerEntry]]`
      - For each `RevisionTrigger` in `plan.revision_triggers`:
        - If `trigger.kind == "mentor_dead"` and `trigger.fired == False`:
          check if `trigger.subject` (entity_id str) is in `social_memory.interaction_history`
          and that entity is dead (`EntityCarryForward.alive == False` in persistent_entities)
        - If `trigger.kind == "item_unavailable"`: check if `plan.goal_queue[0].target_item_id`
          is not in `carry_forward.equipment`
        - If trigger fires: mark trigger `fired=True`, mark head goal `status="blocked"`,
          rotate goal_queue by removing the blocked goal and appending it at tail with
          `status="blocked"` — the next goal becomes the new head
      - Returns (revised_plan, NarrativeLedgerEntry) or (original_plan, None) if no revision
      - `NarrativeLedgerEntry`: episode=episode_index, tick=0,
        event_type="plan_revision", subject_id=str(entity_id),
        payload={"blocked_goal": old_head_goal_id, "new_head": new_head_goal_id},
        significance=0.6, entry_id="{episode}:0:plan_revision:{entity_id}"
- `src/domains/campaigns/orchestrator.py`:
  - Import `PlanRevisionService`
  - In `_prepare_next_episode()`: after ProgressionPlanImporter, call `detect_and_revise()`
    for each entity that has a plan; if a NarrativeLedgerEntry is returned, append to
    `campaign_state.narrative_ledger`
  - For HERO entities with no plan: call `generate_initial_plan()` and store in
    `campaign_state.progression_plans`
- `docs/simulation/domains/progression_planner_contract.md` (extend from E61C):
  - Add section: Plan Revision Rules (trigger kinds, rotation algorithm, ledger emission)
  - Add section: Initial Plan Generation (level-bracket → route-family mapping)
- Parity ledger: add PROG-113 to `docs/parity_ledger/progression.yaml`
  - text: "PlanRevisionService detects mentor-dead and item-unavailable blockers, rotates goal_queue, and emits plan_revision NarrativeLedgerEntry"
  - status: verified, priority: P1
- Run `make knowledge-index-update` after docs/ changes

## Out of Scope
- AI-driven plan generation (entity autonomously picks goals based on OCEAN personality)
- Multi-step lookahead (only single-level blocker check)
- Player-readable plan display / REST endpoint

## Acceptance Criteria
1. A HERO entity without a plan at episode 2 start receives an `initial_plan` with a non-empty `goal_queue`
2. When a mentor-type entity is dead (`EntityCarryForward.alive=False`) and is referenced
   in the HERO's `interaction_history`, the `mentor_dead` trigger fires: head goal becomes
   "blocked", the next goal is promoted to head, and a `plan_revision` NarrativeLedgerEntry
   appears in `CampaignState.narrative_ledger`
3. When no trigger fires, `plan` is returned unchanged and no ledger entry is emitted
4. The entry_id dedup format `"{episode}:0:plan_revision:{entity_id}"` matches the
   NarrativeLedgerEntry schema (consistent with existing entry_id pattern in state.py)
5. The full 3-episode acceptance criterion from the epic: HERO pursues coherent upgrade
   chain across 3 episodes, revising the plan when an intermediate goal is blocked

## Related Tickets
- TCK-20260619-E61C-PLAN-SCORER (prerequisite)
- TCK-20260619-E43-SOCIAL-MEMORY (prerequisite — DONE; interaction_history read source)
- TCK-20260619-E61-PROGRESSION (parent epic)

## Related Docs
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/investigation.md`
- `docs/parity_ledger/progression.yaml`
- `docs/simulation/domains/progression_planner_contract.md` (extend in this ticket)

## Related Stored Artifacts
- `stored_artifacts/TCK-20260619-E61-PROGRESSION/`

## Related Code Areas
- `src/domains/campaigns/plan_revision.py` (new)
- `src/domains/campaigns/orchestrator.py` (extend _prepare_next_episode)
- `src/domains/campaigns/social_memory.py` (read: interaction_history, InteractionRecord)
- `src/domains/campaigns/state.py` (read: NarrativeLedgerEntry schema)
- `docs/simulation/domains/progression_planner_contract.md` (extend)
- `docs/parity_ledger/progression.yaml`

## Assumptions / Open Questions
- `InteractionRecord` must expose the referenced entity_id to detect mentor identity;
  verify field name before implementing (read social_memory.py)
- HERO entity detection: use `EntityCarryForward` alone (role not stored there); may need
  to pass entity role from AuthoritativeState — confirm orchestrator has access to entity
  role at `_prepare_next_episode()` time
- "mentor" is defined as any entity with a positive `relationship_score` in
  `SocialMemoryRecord.relationship_scores` — this is the simplest definition that avoids
  adding a dedicated "mentor" role; document in contract

## Implementation Notes
- `PlanRevisionService` methods are static — no state, pure functions
- The level-bracket plan template is deliberately simple (3 goals, fixed families);
  personality-driven plan generation is deferred to a future phase
- `generate_initial_plan` only generates for EntityRole.HERO entities; non-HERO entities
  do not receive plans (guard with role check in orchestrator before calling)
- `goal_queue` rotation: `dataclasses.replace(plan, goal_queue=remaining + (blocked_goal,))`
  where `remaining = plan.goal_queue[1:]` and `blocked_goal = dataclasses.replace(head, status="blocked")`
- Entry dedup: the orchestrator must check for duplicate entry_ids in narrative_ledger before
  appending (consistent with existing E32D dedup logic)

## Test Summary
- `tests/unit/campaigns/test_plan_revision.py`:
  - `test_generate_initial_plan_level_1_hero`: level 1 entity → head goal = craft_upgrade
  - `test_generate_initial_plan_level_5_hero`: level 5 entity → head goal = quest_opportunity
  - `test_generate_initial_plan_level_10_hero`: level 10 entity → head goal = gather_resource
  - `test_detect_mentor_dead_fires_trigger`: mentor dead in carry_forward → trigger fires, goal blocked, queue rotated
  - `test_detect_mentor_alive_no_trigger`: mentor alive → no revision, no ledger entry
  - `test_detect_no_social_memory_no_revision`: social_memory=None → no revision
  - `test_detect_item_unavailable_fires_trigger`: target_item_id not in carry_forward.equipment → trigger fires
  - `test_revision_emits_narrative_ledger_entry`: ledger entry has correct event_type and entry_id
  - `test_revision_entry_id_dedup_format`: entry_id matches "{episode}:0:plan_revision:{entity_id}"
  - `test_no_trigger_fired_returns_original_plan`: unchanged plan returned when no trigger
- `tests/integration/campaigns/test_progression_planner_three_episode.py`:
  - `test_hero_pursues_craft_upgrade_across_three_episodes`: full 3-episode scenario;
    episode 1: plan generated; episode 2: plan carried forward; episode 3: mentor dies →
    plan revised; narrative_ledger contains plan_revision entry

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
