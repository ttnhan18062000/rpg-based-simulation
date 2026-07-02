---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20260623-FIX-ENTITY-ID
artifact_type: test_plan
tags: [pipeline, entity_updates, faction_awareness, KeyError]
---

# Test Plan — TCK-20260623-FIX-ENTITY-ID

## Scoped Test Commands

Run the exact failing tests to confirm the fix:

```bash
# Primary failing tests (all 6 must pass after fix)
python3 -m pytest tests/unit/core/test_hardening_e5.py -x --tb=short -q
python3 -m pytest tests/integration/domains/test_fused_loop.py::test_belief_assimilation_persists_facts -x --tb=short -q
python3 -m pytest tests/integration/pipeline/test_recovery_gaps.py::test_building_sabotage -x --tb=short -q
```

## Regression Scope

The fix touches three `run_phase` lambdas in the faction/diplomatic/military pipeline section. Regression risk is narrow — only affects how faction updates are merged into the ongoing StateUpdate.

```bash
# Faction and diplomatic subsystem tests
python3 -m pytest tests/ -k "faction or diplomatic or military" --tb=short -q

# Full pipeline integration tests
python3 -m pytest tests/integration/pipeline/ --tb=short -q

# Full unit/core tests (fast)
python3 -m pytest tests/unit/core/ --tb=short -q

# Full integration/domains tests
python3 -m pytest tests/integration/domains/ --tb=short -q
```

## Expected Behavior After Fix

1. `test_negative_case_depleted_node` — `refined.entity_updates[1]` exists with `intent_results` containing `accepted=False, reason="SOURCE_DEPLETED"`
2. `test_belief_assimilation_persists_facts` — `1 in refined.entity_updates` is True; `self_model_bundle_set` is populated
3. `test_building_sabotage` — `refined.building_updates[1].hp_delta == -50` and `functional_set is True`
4. `test_hardening_e5.py:219, 240, 251` — `refined.entity_updates[1]` lookups succeed

## What NOT to Run

Do not run the full test suite (`pytest tests/`) — too broad and slow. The scope is the pipeline's faction/diplomatic section.
