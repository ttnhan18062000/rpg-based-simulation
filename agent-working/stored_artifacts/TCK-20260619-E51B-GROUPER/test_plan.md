---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260619-E51B-GROUPER
artifact_type: test_plan
tags: [chronicle, grouper, event-hierarchy]
---

# Test Plan — TCK-20260619-E51B-GROUPER

## Test File
`tests/unit/chronicle/test_chronicle_compiler.py`

## Test Cases

| ID | Name | AC |
|----|------|-----|
| TC-7 | `test_event_grouping_produces_incident_clusters` | AC-1: ≥2 incidents from 15-event input |
| TC-8 | `test_chronicle_hierarchy_contains_all_four_levels` | AC-2: events/incidents/episodes/eras all non-empty |
| TC-9 | `test_incident_groups_by_tick_window` | Events >50 ticks apart → separate incidents |
| TC-10 | `test_below_threshold_events_excluded` | Non-worthy events filtered from hierarchy |
| TC-11 | `test_era_boundary_every_n_episodes` | ≥3 episodes per era boundary |
| TC-12 | `test_empty_input_returns_empty_hierarchy` | Edge: empty input produces empty hierarchy |

## Run Command
```bash
pytest tests/unit/chronicle/test_chronicle_compiler.py -x -v
```
