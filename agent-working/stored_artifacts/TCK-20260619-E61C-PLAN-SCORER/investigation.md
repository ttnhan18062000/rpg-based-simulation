# Investigation — TCK-20260619-E61C-PLAN-SCORER

## Context Search Results

- `search_docs`: AdventureRouteScorer.score() in scoring.py; formula: urgency + benefit + personality_bias + confidence_bonus - risk_penalty - blocker_penalty.
- `graphify query`: AdventureRouteScorer at src/domains/adventure/scoring.py; AdventureRouteOption at schema.py with slots=True.

## Key Findings

1. `scoring.py` already uses TYPE_CHECKING for deferred imports (FactionDirective, QuestOpportunity, GroupRecord). Same pattern for ProgressionPlan.
2. `AdventureRouteOption` is frozen+slots — new field must be in the class definition body; slots=True means no dynamic attribute assignment.
3. Current audit fields: `benefit_score`, `confidence_bonus`, `risk_penalty`, `blocker_penalty` — all passed in `dataclasses.replace()` at the return site. `plan_advance_bonus` follows the same pattern.
4. No circular import: `progression_plan.py` imports nothing from adventure/. Safe to add TYPE_CHECKING import.
5. Final score computed at line ~222 — plan_advance_bonus added here.
6. Plan-advance bonus must go BEFORE the final score computation; best placed as section 4b after personality biases.

## Circular Import Check

`scoring.py` → `progression_plan.py` → `dataclasses`, `typing` only. No cycle.
