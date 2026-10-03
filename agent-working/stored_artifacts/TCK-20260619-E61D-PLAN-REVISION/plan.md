# Plan — TCK-20260619-E61D-PLAN-REVISION

## New file: src/domains/campaigns/plan_revision.py

`PlanRevisionService` with two static methods:

### generate_initial_plan(entity_id, carry_forward, episode_index) -> ProgressionPlan
Level brackets: 1-4 → craft_upgrade head; 5-9 → quest_opportunity head; 10+ → gather_resource head.
3-goal queue (head + 2 fallbacks in order). 3 MilestoneChecks with level thresholds. 3 RevisionTriggers (kind="mentor_dead", subject="0" placeholder).

### detect_and_revise(entity_id, plan, carry_forward, social_memory, episode_index, persistent_entities)
- mentor_dead: scan relationship_scores for positive-score entities → check dead in persistent_entities → fire
- item_unavailable: check target_item_id not in carry_forward.equipment slots → fire
- On fire: mark trigger fired, rotate goal_queue (blocked head to tail), return (revised_plan, NarrativeLedgerEntry)
- No fire: return (original_plan, None)

## Orchestrator wiring in _build_initial_state()

After ProgressionPlanImporter block:
1. For each alive entity without a plan: generate_initial_plan() → store in progression_plans
2. For each alive entity with a plan: detect_and_revise() → update plan; if entry returned, append to narrative_ledger (dedup by entry_id)

## Files

1. `src/domains/campaigns/plan_revision.py` (new)
2. `src/domains/campaigns/orchestrator.py` (extend _build_initial_state)
3. `tests/unit/campaigns/test_plan_revision.py` (new — 10 tests)
4. `tests/integration/campaigns/test_progression_planner_three_episode.py` (new — 1 test)
5. `docs/simulation/domains/progression_planner_contract.md` (extend)
6. `docs/parity_ledger/progression.yaml` (PROG-113)
