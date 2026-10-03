---
ticket_id: TCK-20260619-E23D-HERO-MATCHING
phase: plan
date: 2026-06-20
---

# Plan — TCK-20260619-E23D-HERO-MATCHING
## Epic 2.3D · HERO Capability Matching for Quest Routes

---

## Ordered Steps

### Step 1 — Add `QUEST_OPPORTUNITY` to `RouteFamily` enum
**File:** `src/domains/adventure/schema.py`
- Add `QUEST_OPPORTUNITY = "quest_opportunity"` to `RouteFamily(str, Enum)` after `FORM_PARTY`.
- No other enum changes.

**Verifies AC:** prerequisite for all ACs.

---

### Step 2 — Add `quest_id` field to `AdventureRouteOption`
**File:** `src/domains/adventure/schema.py`
- Add `quest_id: Optional[str] = None` to the frozen dataclass, after `target_node_id`.
- Backward-compatible: defaults to `None` for all existing routes.
- Import: no new imports needed (`Optional` already imported).

**Verifies AC:** prerequisite for scorer to look up quest.

---

### Step 3 — Extend `AdventureRouteScorer.score()` for QUEST_OPPORTUNITY
**File:** `src/domains/adventure/scoring.py`
- Add `quest_registry: Optional[Dict[str, "QuestOpportunity"]] = None` parameter to `score()`.
- Add `RouteFamily.QUEST_OPPORTUNITY` entry to `family_needs` dict (mapping to `["gold"]` so greedy entities feel some urgency).
- Add QUEST_OPPORTUNITY capability-match branch in section 3 (after benefit/risk):

```python
# ── QUEST_OPPORTUNITY capability match ────────────────────────────
if route.family == RouteFamily.QUEST_OPPORTUNITY and quest_registry is not None:
    from src.core.enums import EntityRole
    is_hero = entity.identity.role == EntityRole.HERO
    quest_id = route.quest_id
    opportunity = quest_registry.get(quest_id) if quest_id else None

    if is_hero:
        capability_match = 0.0
        if opportunity is not None:
            entity_traits = {t.split(":")[0].lower() for t in (entity.identity.traits or set())}
            required_verbs = {token.split(":")[0].lower() for token in opportunity.objective_chain}
            if required_verbs:
                matched = entity_traits & required_verbs
                ratio = len(matched) / len(required_verbs)
                if ratio >= 1.0:
                    capability_match = 1.0
                elif ratio > 0.0:
                    capability_match = 0.5
        benefit = benefit * (1.0 + capability_match)
    else:
        benefit = benefit * 0.5
```

- Add `QUEST_OPPORTUNITY` to personality_bias section: same as TAKE_EASY_QUEST (greed × 0.25).
- Import: add `QuestOpportunity` to TYPE_CHECKING block (to avoid circular import; already imported in quests.py).

**Verifies AC1, AC2, AC3, AC4.**

---

### Step 4 — Write new test file
**File:** `tests/unit/domains/adventure/test_hero_quest_scoring.py`
- Implement all 7 tests from test_plan.md.
- Helper `_quest_opportunity(objective_chain, ...)` builds minimal `QuestOpportunity` for test use.
- Helper `_hero_entity(traits)` builds HERO entity with given traits using `V2EntityBuilder`.
- Helper `_non_hero_entity()` builds SHOPKEEPER entity.

**Verifies AC3, AC4 (test names match ticket requirements).**

---

### Step 5 — Update `docs/mechanics/04_strategic_cognition.md` §6.4
**File:** `docs/mechanics/04_strategic_cognition.md`
- Add row to §6.4 Personality Bias table: `QUEST_OPPORTUNITY | greed | 0.25`.
- Add §6.7 with QUEST_OPPORTUNITY capability match formula documentation.

---

### Step 6 — Add STRAT-228 parity ledger entry
**File:** `docs/parity_ledger/strategic_cognition.yaml`
- Append new entry STRAT-228 for quest route scoring.

---

## Scope Guards (What NOT to touch)

- Do not modify `QuestState`, `QuestResolutionSystem`, or `QuestService` — entity-level quest handling.
- Do not modify `WorldEmergencePhase`, `StateUpdate`, or `AuthoritativeState`.
- Do not change existing scoring weights (0.25, 0.15, 0.5, 2.0) for any existing route family.
- Do not add `AuthoritativeState` as a parameter to the scorer — pass `quest_registry` dict only.
- Do not touch `AdventureRouteGenerator` — route generation is out of scope (E23E if needed).

---

## Dependency Map

Step 1 → Step 2 → Step 3 (schema changes must precede scorer changes)
Step 3 → Step 4 (tests depend on implementation)
Step 3 → Step 5 (docs reflect implemented formula)
Step 4 → Step 6 (parity entry cites test_path from step 4)

---

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| HERO with matching capability scores QUEST_OPPORTUNITY above GATHER_RESOURCE | Step 3 |
| Non-HERO scores quest route ≤ GATHER_RESOURCE | Step 3 |
| `test_hero_entity_scores_quest_above_harvesting` passes | Step 4 |
| `test_non_hero_entity_unaffected` passes | Step 4 |
| Existing `test_phase3_route_scoring.py` tests pass (no regression) | Step 3 (backward-compat param) |

---

## Deviations
_(none at plan time)_
