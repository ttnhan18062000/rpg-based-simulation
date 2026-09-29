---
status: active
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS
phase: open
date: 2026-09-29
tags: [performance, bug]
---

# TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS

## Title
tools/perf/profile_api_payload.py imports two dead APIs (SimulationConfig, EngineManager) and has never actually run

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Found while implementing `TCK-20260929-RETIRE-SCRIPTS-DIR`. That ticket required a smoke run of
`tools/perf/turbo_run.py` (moved from `scripts/turbo_run.py`) and discovered it called
`from src.config import SimulationConfig` (that class doesn't exist anywhere in the repo — a
repo-wide `grep -rn "SimulationConfig"` finds it referenced in exactly two files) and
`from src.api.engine_manager import EngineManager` (the real class is `V2EngineManager`; no
`EngineManager` alias exists — confirmed by checking every other live caller of that module, all
of which import `V2EngineManager`). Both were fixed in `turbo_run.py`, which is now smoke-tested
and works. `tools/perf/profile_api_payload.py` (also moved from `scripts/` by that same ticket)
has the identical pair of dead imports (lines 26/45 as of the move) plus the same
`mgr._loop`/`mgr._loop._step()` private-attribute access pattern that doesn't exist on
`V2EngineManager` either (the real attribute is `_kernel`, exposed publicly as `.kernel`).
`make profile-api` references this file (Makefile) and it is one of the two `scripts/`-era files
the original governance-epic investigation cited as "healthy" because it's Makefile-wired — but
Makefile-wired never meant "someone has run it recently"; this appears to have been broken since
whichever refactor removed `SimulationConfig`/renamed `EngineManager`, and nobody has run
`make profile-api` since.

## Scope
- Fix `tools/perf/profile_api_payload.py`'s imports: `SimulationConfig` -> a `RuntimeProfile`
  (e.g. `PROD_LARGE`, matching `tools/perf/profile_engine.py`'s pattern) and construction of
  whatever config object the CLI's `--ticks --seed` args actually need; `EngineManager` ->
  `V2EngineManager`.
- Fix the `mgr._loop` / `mgr._loop._step()` calls to the real API — likely `mgr.kernel.tick_once()`
  in a loop, mirroring the fix already applied to `tools/perf/turbo_run.py`
  (`TCK-20260929-RETIRE-SCRIPTS-DIR`'s Implementation Notes has the exact before/after).
- Smoke-run it for a short tick count (`--ticks 5` or similar) and confirm it actually measures
  and prints payload sizes without crashing.
- Re-run `make profile-api` end-to-end once fixed.

## Out of Scope
- Any other file under `tools/perf/`, `tools/release/`, or `tools/maintenance/` — this ticket is
  scoped to `profile_api_payload.py` alone. (`turbo_run.py` was already fixed by the ticket that
  found this.)
- Regrouping or renaming anything.

## Acceptance Criteria
- [ ] `tools/perf/profile_api_payload.py` contains no reference to `SimulationConfig` or a bare
  `EngineManager` (only `V2EngineManager`).
- [ ] A recorded smoke run (`python3 tools/perf/profile_api_payload.py --ticks 5 --seed 42` or
  equivalent) completes without `ImportError`/`AttributeError` and prints real payload-size
  output.
- [ ] `make profile-api` runs end-to-end without error.
- [ ] Existing test coverage for this file (if any — check `tests/unit/perf/`,
  `tests/perf/`) still passes; if none exists, note that explicitly (not required to add new
  tests by this hotfix, but don't claim coverage that isn't there).

## Related Tickets
- TCK-20260929-RETIRE-SCRIPTS-DIR

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
- tools/perf/profile_api_payload.py
- tools/perf/turbo_run.py (reference fix pattern)
- src/api/engine_manager.py
- src/config/profiles.py
- Makefile

## Assumptions / Open Questions
- Exactly what config fields `profile_api_payload.py`'s CLI args (`--ticks`, `--seed`, etc.) need
  to map onto `RuntimeProfile`/`V2EngineManager`'s constructor is left to whoever implements this
  — `turbo_run.py`'s fix is the closest precedent but not a 1:1 template, since this file's own
  CLI surface is richer (endpoint-specific payload measurement, not just a tick-driving loop).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
