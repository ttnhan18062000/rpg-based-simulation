---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260619-E61-PROGRESSION
artifact_type: investigation
tags: [progression-planner, multi-episode, build-goal, campaign-state, scoring]
---

# Investigation — TCK-20260619-E61-PROGRESSION

## Summary

Epic 6.1 scoped at Phase 5 completion (2026-06-22). Prerequisites E32-CAMPAIGN-RUNTIME and
E43-SOCIAL-MEMORY are both DONE. The codebase provides all structural hooks needed; zero
new architectural patterns are required. Effort is M (1–4 weeks across 4 child tickets).

---

## Prerequisite State (both satisfied)

### CampaignState (E32 — DONE)

File: `src/domains/campaigns/state.py` (`CampaignState` at L193)

- Mutable durable container for multi-episode progress.
- Already carries `social_memories: Dict[int, SocialMemoryRecord]` (keyed by entity_id int).
- Pattern for adding `progression_plans: Dict[int, ProgressionPlan]` is identical: same int
  key, same `to_dict()` / `from_dict()` serialization convention, same `str(k)` JSON key
  convention.
- `to_dict()` and `from_dict()` are fully implemented and round-trip cleanly.

### SocialMemoryRecord (E43 — DONE)

File: `src/domains/campaigns/social_memory.py` (`SocialMemoryRecord` at L275)

- Frozen dataclass with `interaction_history: Tuple[InteractionRecord, ...]`.
- `interaction_history` is the read source for plan revision: detecting mentor death requires
  scanning for `InteractionRecord` entries where the referenced entity is dead (alive=False
  in `EntityCarryForward`).
- No changes to `SocialMemoryRecord` itself needed — the progression planner reads it, does
  not write to it.

### CampaignOrchestrator (E32C — DONE)

File: `src/domains/campaigns/orchestrator.py`

- Already wires `SocialMemoryExporter` (episode-end) and `SocialMemoryImporter` (episode-start).
- The same pattern applies for `ProgressionPlanExporter` / `ProgressionPlanImporter`.
- `_SIGNIFICANCE_MAP` shows where `plan_revision` NarrativeLedgerEntry can be added
  (event_type="plan_revision", significance=0.6).

---

## Existing Progression Infrastructure (no changes needed)

### LevelingService (`src/progression/leveling.py`)

- `process_progression()` handles XP accumulation and level-up.
- `get_unlocked_skills()` returns skill unlocks at given level threshold.
- `get_xp_required(level)` formula: `100 * level^1.5` — deterministic.
- These are the read signals for `ProgressionPlan.milestone_checks[]`: a milestone fires
  when `entity.identity.evolution_level >= milestone.target_level`.

### GoalKind / ProjectKind (`src/core/strategic.py`)

- `GoalKind` enum: HARVESTING, FATIGUE, HUNGER, SOCIAL, TOWN_RETURN, COMBAT_ENGAGE,
  COMBAT_RETREAT, RECOVER, RESOLVE_BLOCKER.
- No `PROGRESSION_PLAN` GoalKind exists. The planner does NOT need one — it operates
  as a cross-episode score modifier and plan revision service, not a tick-level goal scorer.
  Goal scorers fire every tick; the planner fires at episode boundaries and at blocker events.
- `BlockerState` (`src/core/strategic.py` L194) already models blockers with `kind`, `subject`,
  `severity`, `resolved`. The plan revision service will reuse this model to represent
  "mentor_dead" or "item_unavailable" blockers.

### AdventureRouteScorer (`src/domains/adventure/scoring.py`)

- `score()` method computes: `urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty`.
- Already has HERO-role quest bonus (+10%) and WARRIOR+MAGE group bonus (+15%).
- Extension point for E61C: add `progression_plan_bonus` (+1.5) when `route.family` matches
  the head of `active_plan.goal_queue[0].target_route_family`.
- Bonus is flat additive (not multiplicative) to keep scoring auditable and consistent with
  existing pattern.
- `RouteFamily.CRAFT_UPGRADE` is the primary target family for swordsmith-type plans.
  Other relevant families: `GATHER_RESOURCE`, `SELL_LOOT_FOR_GOLD`, `QUEST_OPPORTUNITY`.

### Progression Parity Ledger (`docs/parity_ledger/progression.yaml`)

- Currently PROG-001 through PROG-109, all `verified` or `legacy_verified`.
- No entries for multi-episode planning (expected: none existed before this epic).
- New entries PROG-110 through PROG-113 will be added by child tickets.

---

## Gap Analysis

| Gap | Severity | Addressed by |
|---|---|---|
| No `ProgressionPlan` model | Missing | E61A |
| No `CampaignState.progression_plans` field | Missing | E61A |
| No exporter/importer at episode boundary | Missing | E61B |
| No plan-advance scoring bonus in AdventureRouteScorer | Missing | E61C |
| No plan revision on blocker detection | Missing | E61D |
| No contract doc | Missing | E61D (create during finalize) |
| No parity ledger entries for multi-episode planning | Missing | child tickets |

---

## Risk / Concern Register

| Risk | Mitigation |
|---|---|
| Plan-advance scoring bonus stacks with HERO quest bonus on QUEST_OPPORTUNITY routes | Cap total bonus at 3.0 in scorer; document in contract |
| Mentor-death detection requires cross-referencing EntityCarryForward alive=False against interaction_history; entity_id ints must match | Use persistent_entities dict keyed by int; test with dead-mentor fixture |
| Empty goal_queue (all goals completed) must not crash scorer | Guard: scorer only applies bonus if `goal_queue` is non-empty |
| Plan serialization key collision in to_dict() | Use same `str(k)` pattern as social_memories; from_dict uses `int(k)` |
| Phase 6 note: full scope re-evaluation deferred | Scoped at P5 completion per instructions; note preserved in ticket |

---

## Dependency Order

```
E61A (ProgressionPlan model + CampaignState field)
  └── E61B (ProgressionPlanExporter + Importer — reads CampaignState)
        └── E61C (AdventureRouteScorer plan-advance bonus — reads ProgressionPlan)
              └── E61D (PlanRevisionService — detects blockers, re-queues goals)
```

Linear dependency. No parallelism possible — each ticket depends on the prior.
