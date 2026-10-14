---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20261013-PERF-TOOLS-LIVE-WORLD-AFTER-D69
phase: open
date: 2026-10-13
tags: [performance, benchmarking]
---

# TCK-20261013-PERF-TOOLS-LIVE-WORLD-AFTER-D69

## Title
Point `tools/perf/live_map_ws_payload_measure.py` and `tools/perf/turbo_run.py` at a named world, since `--entities` stops scaling the live world after D69

## Status
OPEN (blocked: dispatch after the RPG PR that carries owner decision D69 merges)

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
Issue #542 (finding from rpg-planner, relayed by lead-planner-u24, 2026-10-13). Owner decision D69 says the live server runs the authored compiled world. The next RPG PR therefore removes the `entities_count` / `serve --entities` demo spawn. That PR drops the removed kwarg from both perf tools, so they do not crash, but their `--entities N` knob silently stops controlling world size. Any number they report after that PR is labelled with an entity count it did not measure. This ticket makes the world under measurement explicit and reports its real size.

## Scope
1. **Read the merged D69 change first.** Record in Implementation Notes how the live server and `V2EngineManager` select a world after D69 (flag, kwarg, profile field), quoting the merged code at its commit sha. Steps 2 and 3 use that path only. Add no new world-selection mechanism under `src/` outside `src/perf/`. If none exists, stop and report BLOCKED to perf-planner.
2. **`live_map_ws_payload_measure.py`:**
   - Replace `--entities N` with `--world <world_id>`. The default is a named corpus world under `data/worlds/`, chosen and justified in the notes. The candidate for the old 500-entity point is the largest corpus world that fits the 512 MB local profile; the notes give its measured entity count.
   - The result file records `world_id`, the **measured** entity count read from the loaded state, and the seed.
   - The output name uses the world id: `ws_payload_<world_id>.json`, not `ws_payload_<N>.json`.
   - The `--preflight-entities-threshold` memory gate keys off the measured count after load, or off a pre-load count from the world index if one exists. It must never key off a CLI number.
   - The synthetic full-scan path (`_compute_synthetic_full_scan`) loads the same world.
3a. **`tools/perf/profile_api_payload.py`** (rewritten by TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS): its single `build_manager(seed, world_id, entities, profile, factory)` still passes `entities_count`. Re-point that one helper to the D69 world selection, drop `--entities`, and record the measured entity count in its output.
3. **`turbo_run.py`:** replace the hard-coded `entities_count=25, world_id="dungeon_crawl"` with `--world` (default `dungeon_crawl`) and print the measured entity count.
4. **Ad-hoc scaling, if still needed:** a run that wants an N-entity point names a corpus world of that size. It does not get a synthetic spawn on the live path. A table in the tool docstring lists the worlds and their measured counts. Synthetic sized states stay in `src/perf/scenarios.py` for the bench harness only.
5. **Docs:** update every doc that cites `--entities` for these two tools (search `docs/performance/` and the tool docstrings). Add a row to `docs/performance/baseline_invalidation_ledger.md`: every earlier `ws_payload_<N>` / turbo_run number is **incomparable** with post-D69 numbers, because the world differs.
6. **Tests:** a fast unit test per tool:
   - argument parsing: `--entities` is rejected with a message that points at `--world`;
   - the result dict carries `world_id` plus the measured count, using a stubbed manager.
   No live server in the unit tests.

## Out of Scope
- Any change to `src/` outside `src/perf/`, `src/cli/`, or the server spawn path. Those belong to rpg-planner and arrive with the D69 PR.
- The platform load test's flame graph (#542 item 2). It is an fyi: platform-planner asks perf-planner before reusing `tools/perf/_profiling_common.py` / `profile_api_payload.py`, and the toolkit stays perf-owned. No change here.
- Re-recording any committed perf baseline (PERF-M2-T08 owns the canonical reruns).

## Acceptance Criteria
- AC1: Neither tool accepts `--entities`. Both accept `--world`, and each result names the world and its measured entity count.
- AC2: One real local run of each tool on its default world, under the systemd-run memory cap. The output path and measured count are pasted into Test Summary.
- AC3: The ledger row is added, and the docs no longer cite `--entities` for these tools.
- AC4: The unit tests pass. The paths guard and `tests/tools/test_tools_orphan_check.py` pass.
- AC5: Implementation Notes quote the D69 world-selection path with its commit sha.

## Related Tickets
- TCK-20260825-LIVE-MAP-TPS-BUDGET-RECHECK (earlier `--entities 500` runs, now incomparable)
- TCK-20261010-PERF-M2-T08-CANONICAL-RERUNS (baselines; not touched here)

## Related Docs
- docs/performance/baseline_invalidation_ledger.md
- docs/performance/ (tool usage references)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/live_map_ws_payload_measure.py
- tools/perf/turbo_run.py
- tools/perf/profile_api_payload.py (`build_manager`)
- tools/calibrate_simq.py::_load_world_state (existing corpus-world loader that tools/bench_corpus_world.py reuses; candidate for the load path if D69 does not expose one)

## Assumptions / Open Questions
- Q1 (rpg-planner, asked 2026-10-13): after D69, which API selects the live world: a `serve --world` flag, a `V2EngineManager(world_id=...)` kwarg, or something else? Do both tools' `world_id` values keep working? The answer fixes step 1.
- A1: corpus worlds are deterministic for a given seed, so a named world plus seed is a reproducible measurement point.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled)

## Files Changed
(to be filled)

## Completion Summary
(to be filled)
