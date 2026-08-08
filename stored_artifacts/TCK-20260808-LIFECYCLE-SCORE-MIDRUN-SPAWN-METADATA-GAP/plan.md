---
status: active
layer: simulation
authority: P2
audience: agent
ticket_id: TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP
artifact_type: plan
phase: plan
date: 2026-08-08
tags: [simulation-quality, observability, world]
---

# Plan — TCK-20260808-LIFECYCLE-SCORE-MIDRUN-SPAWN-METADATA-GAP

## Fix

1. **`tools/entity_lifecycle_score.py::_run_for_analysis()`**: capture `kernel.state.entities`
   (the real, final, post-run entity map) into a new return value, before `kernel.shutdown()`.
   Change return shape from `tuple[str, dict]` (`run_dir, health`) to
   `tuple[str, dict, dict]` (`run_dir, health, final_entities`) — `final_entities` is
   `dict[int, EntityState]`, the same shape `world_state.entities` already has, so
   `_entity_metadata()` can be reused unmodified on it.
2. **`_entity_metadata()`**: no signature change — already takes a `world_state`-like object;
   called a second time on a lightweight wrapper around `final_entities` (or refactored to accept
   a raw entities dict directly — decided during Implement based on the cleanest real diff).
3. **`extract_entity_paths()`**: build metadata by merging two sources — the existing
   pre-run `metadata` dict (unchanged for entities present at world-load time, preserving their
   real spawn-time identity) **overlaid with** post-run metadata for any `entity_id` NOT in the
   pre-run set. Only entities in neither snapshot (the disclosed born-and-removed-within-window
   edge case) keep the `None` fallback.
4. **`score_run()`/`main()`**: thread the new `final_entities` value through from
   `_run_for_analysis()`'s new return shape. `--run-dir` mode (scoring an existing run, not
   driving a new one) cannot access post-run state — falls back to pre-run-only metadata,
   documented as a real, disclosed limitation of that mode specifically (unavoidable — the Kernel
   object no longer exists when scoring a historical run_dir).
5. **`tools/simq_long_run_observation.py`**: no change needed — it already calls
   `_run_for_analysis()` and can simply thread the new 3rd return value through the same way.

## Acceptance-criteria map

| Criterion | Satisfied by |
|---|---|
| Real cause of exactly-10 pattern reported | investigation.md — multi-source mechanic, precise arithmetic not chased (disproportionate effort, disclosed) |
| Post-run state resolution confirmed viable | investigation.md, with 1 disclosed residual limitation |
| Real fix lands, re-verified via long-run tier | Steps 1-5 + re-run `make simq-long-run-lifecycle-observation` |
| Docs updated | investigation.md's own Docs Requiring Update |
| Scoped pytest passes | test_plan.md |
