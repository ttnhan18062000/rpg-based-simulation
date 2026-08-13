---
status: authoritative
layer: simulation
authority: P1
audience: agent
---

# Progression Planner Contract

**Status**: AUTHORITATIVE — E61A–E61D complete.
**Tickets**: E61A (ProgressionPlan model), E61B (Exporter/Importer), E61C (Scorer integration), E61D (PlanRevisionService + initial plan generation).

---

## Purpose

The Progression Planner tracks long-term build goals for HERO entities across episodes.
Each `ProgressionPlan` (one per entity) holds an ordered `goal_queue` of `BuildGoal` records,
milestone checks, and revision triggers. Plans persist in `CampaignState.progression_plans`
and are carried forward between episodes by the Exporter/Importer hooks.

---

## ProgressionPlan Model (E61A)

Defined in `src/domains/campaigns/progression_plan.py`.

```
ProgressionPlan(frozen=True)
  entity_id:             int                     — owning HERO entity ID
  goal_queue:            Tuple[BuildGoal, ...]   — ordered goals; index 0 is active
  milestone_checks:      Tuple[MilestoneCheck, ...]
  revision_triggers:     Tuple[RevisionTrigger, ...]
  created_episode:       int
  last_revised_episode:  int
```

```
BuildGoal(frozen=True)
  goal_id:               str
  target_route_family:   str    — RouteFamily.value (str); avoids circular import
  target_item_id:        Optional[str]
  target_level:          Optional[int]
  status:                str    — "pending" | "in_progress" | "completed" | "blocked"
```

```
MilestoneCheck(frozen=True)
  milestone_id:    str
  target_level:    int
  episode_index:   int    — episode by which target_level should be reached
  achieved:        bool
```

```
RevisionTrigger(frozen=True)
  trigger_id:  str
  kind:        str    — "mentor_dead" | "item_unavailable" | "goal_completed"
  subject:     str    — entity_id/item_id/goal_id depending on kind
  fired:       bool
```

**Serialization**: `to_dict()` / `from_dict()` on all types. Tuple fields serialize as lists;
reconstructed via `tuple(...)` on load. Stored in `CampaignState.progression_plans: Dict[int, ProgressionPlan]`
with `str(k)` keys in JSON, `int(k)` keys in Python (same as `social_memories`).

---

## Episode Boundary Hooks (E61B)

### Export (episode end)

`ProgressionPlanExporter.export(entity_id, current_plan, alive) -> Optional[ProgressionPlan]`

Called from `CampaignOrchestrator._advance_state()` after entity carry-forwards are extracted.

| Condition | Result |
|---|---|
| `current_plan is None` | `None` (no plan to export) |
| `alive is False` | `None` (dead entities do not carry plans) |
| `alive is True` | plan returned unchanged |

Dead entity plans are removed from `CampaignState.progression_plans` by `_advance_state()`.

### Import (episode start)

`ProgressionPlanImporter.import_plan(entity_id, plan, new_episode_index, entity_level) -> ProgressionPlan`

Called from `CampaignOrchestrator._build_initial_state()` for each entity with a plan.

Updates `MilestoneCheck.achieved = True` when `entity_level >= milestone.target_level`.
Returns a new `ProgressionPlan` via `dataclasses.replace()` — the original is unchanged.
Empty `milestone_checks` is a no-op; returns the plan object unchanged (identity).

---

## Plan-Advance Scoring Bonus (E61C)

`AdventureRouteScorer.score()` gains an optional `progression_plan` parameter.

### Formula

```
score = urgency + benefit + personality_bias + plan_advance_bonus + confidence_bonus
        - risk_penalty - blocker_penalty
```

### Plan-Advance Bonus Rule

| Condition | Bonus |
|---|---|
| `progression_plan is None` | 0.0 |
| `goal_queue` is empty | 0.0 |
| `head_goal.status` is `"completed"` or `"blocked"` | 0.0 |
| `route.family.value != head_goal.target_route_family` | 0.0 |
| All guards pass | **+1.5** |

Cap: `plan_advance_bonus = min(plan_advance_bonus, 3.0)` (future-proofing for multi-bonus stacking).
Currently this cap has no effect since the maximum single bonus is 1.5.

### Head Goal Selection

Only `goal_queue[0]` (the head goal) is considered. Multi-goal lookahead is deferred (post-E61).

### Audit Field

`AdventureRouteOption.plan_advance_bonus: float = 0.0` records the applied bonus for traceability.
Set to `1.5` when the bonus fires; `0.0` otherwise.

---

---

## Initial Plan Generation (E61D)

`PlanRevisionService.generate_initial_plan(entity_id, carry_forward, episode_index) -> ProgressionPlan`

Called from `CampaignOrchestrator._build_initial_state()` for every alive entity that does not
yet have a plan in `CampaignState.progression_plans`.

### Level-Bracket → Route-Family Mapping

| Level range | Head goal | Fallback 1 | Fallback 2 |
|---|---|---|---|
| 1–4 | `craft_upgrade` | `quest_opportunity` | `gather_resource` |
| 5–9 | `quest_opportunity` | `craft_upgrade` | `gather_resource` |
| 10+ | `gather_resource` | `quest_opportunity` | `craft_upgrade` |

Each bracket produces 3 BuildGoals (status="pending"), 3 MilestoneChecks (threshold = unlock level),
and 3 RevisionTriggers (kind="mentor_dead", subject="0" placeholder).

**Milestone thresholds**: `craft_upgrade=5`, `quest_opportunity=10`, `gather_resource=15`.

---

## Plan Revision Rules (E61D)

`PlanRevisionService.detect_and_revise(entity_id, plan, carry_forward, social_memory, episode_index, persistent_entities) -> Tuple[ProgressionPlan, Optional[NarrativeLedgerEntry]]`

Called from `CampaignOrchestrator._build_initial_state()` for every alive entity that has a plan,
after `generate_initial_plan()`. Returns `(plan, None)` when no trigger fires.

### Trigger Kinds

| Kind | Fire condition |
|---|---|
| `mentor_dead` | Any entity in `social_memory.relationship_scores` with score > 0 is dead (`persistent_entities[id].alive == False`). Requires `social_memory` to be non-None. |
| `item_unavailable` | `head_goal.target_item_id` is not present in `carry_forward.equipment["slots"].values()`. |

Only the **first** firing trigger is processed per call (one revision per episode per entity).
Already-fired triggers (`fired=True`) are skipped.

### Goal-Queue Rotation Algorithm

```
blocked_head = replace(goal_queue[0], status="blocked")
new_queue = goal_queue[1:] + (blocked_head,)
revised_plan = replace(plan, goal_queue=new_queue, revision_triggers=updated, last_revised_episode=episode_index)
```

The blocked head moves to the tail; the next goal (index 1) becomes the new head unchanged.

### Ledger Entry on Revision

```
NarrativeLedgerEntry(
    episode=episode_index, tick=0,
    event_type="plan_revision",
    subject_id=str(entity_id),
    payload={"blocked_goal": head.goal_id, "new_head": new_queue[0].goal_id},
    significance=0.6,
    entry_id=f"{episode_index}:0:plan_revision:{entity_id}",
)
```

Dedup is applied by `_build_initial_state()` before appending (checks `entry_id` against existing ledger).

### "Mentor" Definition

A mentor is any entity with a **positive** `relationship_score` in `SocialMemoryRecord.relationship_scores`.
No dedicated "mentor" role exists in `EntityCarryForward`; detection is purely score-based.

### Wiring Order in `_build_initial_state()`

1. `ProgressionPlanImporter.import_plan()` — update milestone achieved flags.
2. `PlanRevisionService.generate_initial_plan()` — generate plans for entities without one.
3. `PlanRevisionService.detect_and_revise()` — apply trigger-based revisions.

---

## Relationship to `StrategicComponent.committed_intentions` (Distinct Concept)

As of `TCK-20260812-COMMITTED-INTENTION-SEQUENCE`, a second, structurally unrelated planning
concept exists: `StrategicComponent.committed_intentions` (`src/core/strategic.py`), documented in
`docs/mechanics/04_strategic_cognition.md` §4 ("Committed Intentions (Multi-Step Planning)"). Do
not conflate the two — they have non-overlapping responsibility, per
`docs/architecture/2026-08-12-multi-step-persistent-planning-design.md` Design §3:

| | `ProgressionPlan.goal_queue` (this doc) | `StrategicComponent.committed_intentions` |
|---|---|---|
| Cadence | Episode-cadence — written only from `CampaignOrchestrator._build_initial_state()`/`_advance_state()` | Tick-cadence — consulted every eligible `evaluate_strategic_intent()` tick |
| Horizon | Long (18+ months / multi-episode) | Medium (a handful of ticks to a fraction of an episode) |
| How it's consulted | Advisory only — `goal_queue[0]` contributes a flat `+1.5` scoring nudge (see "Plan-Advance Scoring Bonus" above); never writes `current_project_id` directly | Materializes `committed_intentions[0]` as an ordinary tier-5 `GoalScore` candidate that competes through, and can win, `evaluate_project_switch()` |
| Write path status | Live (E61A–E61D) | Not yet implemented — `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` landed consume-side only; nothing in production constructs a `CommittedIntention` yet |

**Auto-seed relationship (deferred, not implemented):** a future ticket could have
`goal_queue`'s head-goal bias seed the initial `committed_intentions` ordering at plan-creation
time. This is explicitly *not* implemented by `TCK-20260812-COMMITTED-INTENTION-SEQUENCE` — see
that design doc's Open Question 4 and its post-landing resolution note.

---

## Parity Ledger References

| ID | Description |
|---|---|
| PROG-110 | ProgressionPlan model serializes/deserializes with full round-trip fidelity |
| PROG-111 | ProgressionPlan exported at episode end; dead entity plans are dropped |
| PROG-112 | Routes matching head BuildGoal target_route_family receive a +1.5 plan-advance bonus |
| PROG-113 | PlanRevisionService detects mentor-dead and item-unavailable blockers, rotates goal_queue, emits plan_revision NarrativeLedgerEntry |
