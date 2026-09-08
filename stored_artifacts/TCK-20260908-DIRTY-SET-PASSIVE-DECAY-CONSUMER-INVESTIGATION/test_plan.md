---
status: active
layer: engine
authority: P2
audience: agent
ticket_id: TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION
artifact_type: test_plan
tags: [determinism]
---

# Test Plan — TCK-20260908-DIRTY-SET-PASSIVE-DECAY-CONSUMER-INVESTIGATION

New file: `tests/unit/engine/test_dirty_set_passive_decay_consumers.py` (4 tests, all real
pipeline/apply calls, no mocking of `refine()`/`apply_generation()`/`ReadModelCache` internals):

1. `test_passive_decay_only_tick_produces_real_state_change_with_no_entity_update` — sanity
   precondition: real state changes (hunger accrual, `lifecycle.active` flip) with genuinely zero
   `EntityUpdate` staged for the entity that tick.
2. `test_consumer_1_phase_shortcircuit_is_confirmed_benign_not_a_bug` — confirms
   `near_death_hardening`/`evolution` are genuinely skipped (`metric_counters`), and that running
   them directly on the same input (bypassing the skip) produces an identical result — proving the
   skip drops zero real work, not just that none was observed.
3. `test_consumer_2_read_model_cache_serves_a_stale_dto_confirmed_bug` — real `ReadModelCache`
   fed the real, empty `dirty_set` from the same tick; proves `get_entity_dto()` serves the stale
   pre-tick snapshot rather than reflecting the real, committed change.
4. `test_consumer_2_full_scan_or_explicit_dirty_tag_avoids_the_staleness` — control: the same
   scenario with `force_full_scan=True` does NOT go stale, isolating the defect to the
   passive-decay dirty-set omission specifically.

Scoped regression run (touched no production code — new test file only):

```
pytest tests/unit/api/test_read_model_cache.py tests/unit/domains/optimization/test_phase_dependency_graph.py tests/unit/engine/ -m "not slow and not extra_slow"
```

Result: **228 passed, 1 skipped, 3 deselected**, 0 failed (using
`/home/u24desktop/Working/venv/bin/python3`, the venv with `pydantic` installed — the bare
`python3` on this machine lacks it, per this session's own project-environment memory).
