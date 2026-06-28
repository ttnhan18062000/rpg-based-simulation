---
status: historical
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260627-P1B-QUEST-ACTIVATION
artifact_type: plan
tags: [quest, activation, strategic-intelligence, blockers]
---

# Plan: TCK-20260627-P1B-QUEST-ACTIVATION

## Ordered Steps

### Step 1 — Fix bug in `QuestGenerationSystem.quest_to_project()`

**File**: `src/systems/world_systems/quests.py`

**What**: The first objective created for a quest project must have `status=ObjectiveStatus.ACTIVE` (not `UNRESOLVED`). The `StrategicIntelligenceSystem.fused_strategic_pass()` requires `active_objective_id` to point to an `ACTIVE` objective for blocker resolution and navigation to work.

**Change**: Replace the single-pass comprehension that applies `UNRESOLVED` to all objectives with logic that uses `ACTIVE` for the first objective and `UNRESOLVED` for the rest.

**Scope guard**: Do NOT change `generate_from_blockers()`, `generate_from_scar()`, or anything in `intelligence.py`.

### Step 2 — Write unit test file

**File**: `tests/unit/systems/test_quest_activation_pathway.py`

**Tests** (5):
1. `test_generate_from_blockers_returns_quest_template_for_material_blocker`
2. `test_generate_from_blockers_skips_resolved_blockers`
3. `test_quest_to_project_produces_valid_project`
4. `test_quest_project_active_objective_status` (primary regression guard for bug fix)
5. `test_quest_activation_pathway_end_to_end`

All tests are isolated, deterministic, no state mutation.

### Step 3 — Update parity ledger

**File**: `docs/parity_ledger/strategic_cognition.yaml`

Add `STRAT-235` entry covering the blocker-triggered quest activation pathway.

### Step 4 — Update ticket

Fill Implementation Notes section with what was done.

## Dependency Map

Step 1 → Step 2 (test validates the fix)
Step 1, 2 → Step 3 (parity after behavior verified)
Steps 1–3 → Step 4

## Acceptance Criteria Mapping

| AC | Step |
|---|---|
| Unit test exists for blocker-triggered quest project creation | Step 2 |
| Test exercises `intelligence.py` and `quests.py` together | Step 2 (test 5 calls `evaluate_project_switch`) |
| Parity ledger updated | Step 3 |

## Scope Guards (what NOT to touch)

- Do NOT wire `QuestGenerationSystem` into `StrategicIntelligenceSystem.evaluate_strategic_intent()` — that is future work, not this ticket
- Do NOT modify `generate_from_blockers()` logic — only fix `quest_to_project()`
- Do NOT modify `intelligence.py` blocker inference or fused_strategic_pass
- Do NOT add integration/simulation-level tests — those are post-P0 (AC3 deferred)

## Deviations

(None at time of writing)
