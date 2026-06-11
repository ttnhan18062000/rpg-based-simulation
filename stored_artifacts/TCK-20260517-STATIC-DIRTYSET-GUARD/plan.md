---
status: historical
layer: core
authority: P2
audience: agent
ticket_id: TCK-20260517-STATIC-DIRTYSET-GUARD
artifact_type: plan
tags: [static, dirtyset, guard]
---

# Implementation Plan: Static Guard Against Direct DirtySet Usage

## Objective

Create a static verification test suite `tests/static/test_no_direct_dirtyset_candidate_selection.py` that enforces architectural compliance by forbidding direct `dirty_set` property accesses in simulation phase and gameplay logic directories.

## Proposed Changes

### Tests

#### [NEW] [test_no_direct_dirtyset_candidate_selection.py](file:///home/vboxuser/Work/rpg-based-simulation/tests/static/test_no_direct_dirtyset_candidate_selection.py)

Implement static verification checking all `.py` files within:
- `src/engine/pipeline_phases`
- `src/systems`
- `src/ai`

The test will iterate through all Python files in these directories and check for forbidden strings/patterns:
- `.dirty_set`
- `dirty_set.movement_entities`
- `dirty_set.combat_entities`
- `dirty_set.inventory_entities`
- `dirty_set.strategic_entities`
- `dirty_set.social_entities`
- `dirty_set.lifecycle_entities`
- `dirty_set.biological_entities`
- `dirty_set.attribute_entities`
- `dirty_set.town_entities`

If any forbidden pattern is found in these restricted directories, the test will raise an explicit assertion error detailing the violating file and line number.

## Verification Plan

### Automated Verification
- Run `pytest tests/static/test_no_direct_dirtyset_candidate_selection.py -v` to ensure full compliance across existing files.
- Run `pytest tests/unit/ -m "not slow" -v` to verify zero regressions.
