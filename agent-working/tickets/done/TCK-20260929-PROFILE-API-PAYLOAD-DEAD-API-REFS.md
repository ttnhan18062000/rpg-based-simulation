---
status: historical
layer: performance
authority: P1
audience: agent
ticket_id: TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS
phase: done
date: 2026-09-29
tags: [performance, bug]
---

# TCK-20260929-PROFILE-API-PAYLOAD-DEAD-API-REFS

## Title
tools/perf/profile_api_payload.py imports two dead APIs (SimulationConfig, EngineManager) and has never actually run

## Status
DONE

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
- [x] `tools/perf/profile_api_payload.py` contains no reference to `SimulationConfig` or a bare `EngineManager` (only `V2EngineManager`); a unit test asserts it.
- [x] A recorded smoke run (`make profile-api`, i.e. `--ticks 10 --seed 42`) completes without `ImportError`/`AttributeError` and prints real payload sizes (output under Implementation Notes).
- [x] `make profile-api` runs end to end: exit 0, 5.3 s, under `systemd-run --user --scope -p MemoryMax=2G -p MemorySwapMax=0`.
- [x] Test coverage: there was none for this file; `tests/unit/perf/test_profile_api_payload.py` (4 tests) is new. It imports the module, builds the manager through a stub factory, and runs `measure`/`render` on a real synthetic state, so a dead reference fails fast. (Requested by perf-planner beyond the original hotfix.)

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
- **The dead references were not just the two imports.** `V2EngineManager` has no `get_grid`, `get_snapshot`, `event_log` or `config`; `src.api.schemas` no longer has 11 of the 12 schema names the tool imported (`BuildingSchema`, `EntitySlimSchema`, `MapResponse`, ...); `src.api.routes.state` has no `_serialize_full_entity` or `_get_weapon_range`; the V1 `/state`-with-selection payload no longer exists. So the whole measurement body was V1 and the tool is rewritten, not patched: it builds a headless `V2EngineManager` (no thread), advances with `kernel.tick_once()` (as `turbo_run.py` does) and measures the JSON of the `StatePresenter` calls the routes make (`present_map`, `present_static`, `present_minimal`, `present_full`, `present_entity_slim`, `present_entity`). The V1 "before/after pre-optimization" comparison is removed (its V1 shapes are gone). This is a scope growth beyond "fix the imports"; the ticket's own acceptance criteria are met.
- **One world helper (perf-planner, for D69/#542):** `build_manager(seed, world_id, entities, profile, factory)` is the only place a manager is built; `--world` and `--entities` flags select it.
- Smoke run, `make profile-api` (exit 0, 5.27 s): tick 10, 25 entities; `/map` 759 B (144 RLE pairs); `/static` 781 B (2 regions, 2 resource nodes); `/state` 70 B; 25 slim entities x 116 B = 2.8 KB; full snapshot 23.0 KB; entity #1 slim 111 B / full 820 B.
- The two planner commits `c1ef36b6a` (closes `COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED`) and `e233228f9` (files `PERF-TICK-COST-GROWTH-INVESTIGATION` and `PERF-T08-NOISY-AND-OFF-NORMAL-BASELINES`) ride in this batch's PR by perf-planner's direction (cherry-picked; `cb4c09846`, the #542 ticket, is not).

### 2026-09-30 — classified via `TCK-20260929-UNREACHABLE-CLASSIFY-ZERO-CALLER` (epic `TCK-20260929-EPIC-UNREACHABLE-MECHANISM-CLASSIFICATION`, child `T01`): verdict `DEFECT`

**Executed, not read.** At branch tip `3dbdff48a`,
`python3 tools/perf/profile_api_payload.py --ticks 5 --seed 42` fails at import:
`ImportError: cannot import name 'EngineManager' from 'src.api.engine_manager'`
(`profile_api_payload.py:26`). The second dead name is also confirmed: `SimulationConfig` (`:45`) is not
defined by any class in `src/`, and `V2EngineManager` (`src/api/engine_manager.py:20`) is the only manager
class. `make profile-api` (`Makefile:255-256`) invokes exactly this file, so the make target is broken too.
The file has had no change since filing other than the `scripts/` -> `tools/` move (`d431a6edb`), so the
claim is not stale.

Real wiring defect (imports of names that do not exist), fully covered by the ticket's own fix scope; no
content or run-length condition is involved. The ticket's suspicion that the `mgr._loop` access is wrong
is unexecuted (the run dies before reaching it) and stays the fixer's to confirm.

## Test Summary
`tests/unit/perf/test_profile_api_payload.py` (4 passed); `make profile-api` run (exit 0). No test existed for this file before.

## Files Changed
`tools/perf/profile_api_payload.py` (rewritten), `tests/unit/perf/test_profile_api_payload.py` (new), this ticket.

## Completion Summary
`tools/perf/profile_api_payload.py` is rewritten onto the live V2 read path (`V2EngineManager` + `StatePresenter`) and `make profile-api` runs to completion (exit 0, 5.3 s). Its world is chosen in one helper for #542 to re-point, and a unit test fails fast on a dead reference. Known gap: it measures presenter payloads, not HTTP bytes (no FastAPI envelope or compression).

**Verdict as of 2026-09-30: `DEFECT`** — confirmed by executing the tool (ImportError); see Implementation Notes. Still `OPEN`; fix scope unchanged.
