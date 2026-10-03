---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY
phase: done
date: 2026-10-03
tags: [performance, determinism, engine]
---

# TCK-20261003-PERF-WALL-CLOCK-READ-INVENTORY

## Title
Inventory every wall-clock and host-resource read in `src/` and whether it can reach authoritative state (PERF-D1 evidence, no measurement)

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
PERF-D1 (owner-approved 2026-10-03) defines a Canonical contract under which no wall-clock or host-resource reading may influence authoritative state. It names three such inputs found by reading the governor and the kernel tick path (`ResourceGovernor._get_indicated_mode()`, the mid-tick cutoff in `Kernel._phase_resolution()`, and the end-of-tick dropped-work check), and records as its main uncertainty that "a complete inventory of wall-clock and host-resource reads that reach authoritative state has not been made". Its revisit condition is "the inventory finds a fourth input". PERF-D1's child packages list this inventory as an evidence-only ticket.

Produce that inventory, with the same conventions as the phase and hash call-site inventories.

## Scope
- Add `tools/perf/wall_clock_inventory.py`: a read-only `ast`-based scan of `src/` (no engine import, no execution) that lists every call to a wall-clock or host-resource source. At minimum: `time.time`, `time.time_ns`, `time.perf_counter(_ns)`, `time.monotonic(_ns)`, `time.process_time(_ns)`, `time.thread_time(_ns)`, `datetime.now`/`utcnow`/`today`, `date.today`, `os.getloadavg`, `os.cpu_count`, `os.sched_getaffinity`, `resource.getrusage`, `tracemalloc.get_traced_memory`, `gc.get_count`/`gc.get_stats`, any `psutil.*` call, and reads of `os.environ` / `os.getenv`. For each: file, line, enclosing function, source kind (wall-clock, CPU time, memory, CPU/host topology, environment), and the guard expression as written. Resolve imports and aliases by name the same way `tools/perf/hash_callsite_inventory.py` does; list unresolved receivers instead of guessing
- Deterministic JSON and markdown output and a `--check` mode against a committed JSON, reusing the conventions settled by `tools/perf/phase_inventory.py` and `tools/perf/hash_callsite_inventory.py` (stable order, no timestamps, `--update-doc` rewrites only the generated block)
- Write `docs/performance/wall_clock_inventory.md`: generated tables plus a hand-written section. For every read that sits in a module reachable from the kernel tick (`src/engine/`, `src/core/`, systems invoked by the authoritative pipeline, the governor and worker manager), record from reading the code:
  - where the value flows: into a log, metric, telemetry, or report only; into a control decision (mode, budget, cutoff, cadence, LOD, scan policy, worker dispatch); or into authoritative state directly (a field of `AuthoritativeState`, an update record, an id, a seed, a sort key)
  - the PERF-D1 classification of each control decision it feeds, using the decision's own table (recorded / derived from a recorded value / not recorded and no effect on authoritative state); mark "not in the PERF-D1 table" where it fits none of the rows
  - whether `audit_mode` or any other flag neutralizes it today
  Reads in modules not reachable from the tick (API, tools-like scripts under `src/`, CLI) are listed in the generated table and grouped as "outside the tick path" with one line of justification per module, not traced individually
- A summary section that answers PERF-D1's revisit condition directly: list every input that can change authoritative state other than the three PERF-D1 names, with evidence, or state that none was found and what the scan could not see
- Tests under `tests/tools/` for the scanner: synthetic source covering direct calls, `from time import perf_counter as pc`, `import datetime as dt`, attribute chains (`datetime.datetime.now`), and guarded calls; deterministic output; `--check` pass and fail; one run against real `src/` asserting only that it parses and that the reads behind the three PERF-D1 inputs are found by function name (not by line number or total count)
- Add the tool and its test to the test-scope map (`tools/gate_checks/test_scope_coverage_static.py`, `_TOOLS_PERF_BASENAME_MAP`), as the sibling tickets did

## Out of Scope
- Any edit under `src/`, including removing or replacing a read the inventory finds
- Running the kernel, profiling, or measuring anything (the RPG-core stability entry gate still forbids measurement as evidence)
- Designing the Canonical deterministic proxies or the Live control trace (PERF-M1 work, blocked on `src/`)
- Editing `docs/architecture/performance_optimization_decisions.md` or any authority-P1 document; the planner updates PERF-D1 from this output
- RNG seeding from time (only if found: list it as a finding, do not fix)
- Wiring `--check` into CI or any gate

## Acceptance Criteria
- [x] `python3 tools/perf/wall_clock_inventory.py --format json` runs without importing `src`, and two consecutive runs are byte-identical
- [x] Every read of the listed sources in `src/` appears with file, line, enclosing function, source kind, and guard expression; a manual `grep` for the source names over `src/` finds no read the script missed, and the comparison is recorded in the test plan
- [x] `docs/performance/wall_clock_inventory.md` traces every tick-path read to its sink (log/metric, control decision, or authoritative state) with file and line, and gives the PERF-D1 classification of each control decision
- [x] The summary section names every authoritative-state input beyond PERF-D1's three, or states that none was found and lists what the scan cannot see
- [x] Tests pass; the real-source test pins no line number and no total count
- [x] `git diff` touches only `tools/perf/`, `tests/tools/`, `tools/gate_checks/test_scope_coverage_static.py`, `docs/performance/`, `docs/REGISTRY.yaml`, `agent-working/tickets/`, `agent-working/stored_artifacts/`, and `agent-working/agent-monitoring/`

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC (parent)
- TCK-20261003-PERF-HASH-CALLSITE-INVENTORY, TCK-20261003-PERF-PHASE-INVENTORY-SCRIPT (siblings; output conventions)
- TCK-20260822-STANDARD-SLOW-REGRESSION-CI-JOB-EXIT-CODE-2 (same seed passing and failing through the mid-tick cutoff)
- TCK-20260908-DEGRADED-POLICY-NONURGENT-MOVEMENT-STARVATION
- TCK-20260911-WORKER-UTILIZATION-ZERO-WORKERS-DEGRADED-MISTRIGGER

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, C-04, C-05)
- `docs/engine/deterministic_execution.md`, `docs/engine/runtime_profiles.md` §4 (read only)
- `docs/engine/contracts/resource_governor_contract.md` (pressure signal semantics; read only)

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261003-PERF-HASH-CALLSITE-INVENTORY/`

## Related Code Areas
- `src/engine/governor.py`, `src/engine/kernel.py`, `src/engine/worker_manager.py`, `src/engine/policy.py`, `src/engine/pipeline.py` (read only)
- `tools/perf/`, `tests/tools/`

## Assumptions / Open Questions
- Evidence-only release on the owner's 2026-10-03 approval of PERF-D1 and of releasing this batch
- `os.environ` reads are included because an environment variable that changes behavior is a host input under DET-PORT tiers (PERF-D2); if the count is large, group environment reads by variable name in the doc rather than tracing each
- A value whose sink cannot be traced with confidence is recorded as "sink not traced" with the last known hand-off point; do not guess
- Implement after or independently of `TCK-20261003-PERF-M2-CLAUSE-INVENTORY`; no shared files besides the test-scope map line
- perf-planner reviews the document before this ticket closes

## Implementation Notes
- Scanner `tools/perf/wall_clock_inventory.py` (stdlib `ast`, deterministic, `--check`, `--update-doc`), reusing the guard and scope helpers of `hash_callsite_inventory.py`; sources beyond the ticket's list: `uuid`, `os.urandom` (host entropy).
- Document `docs/performance/wall_clock_inventory.md` plus committed `docs/performance/wall_clock_inventory.json`.
- perf-planner review: approved with two additions (proof-digest evidence line; completion-summary inputs), both applied.

## Test Summary
- `tests/tools/test_wall_clock_inventory.py`: 16 passed. With `test_test_scope_coverage_static`, `test_hash_callsite_inventory` and `test_perf_threshold_inventory`: 72 passed. `--check` passes against the committed JSON; two runs byte-identical; the script imports no `src` module.
- Text-search comparison recorded in the test plan: every match recorded except an exception-class mention (`observability.py:76`).

## Files Changed
- tools/perf/wall_clock_inventory.py (new)
- tests/tools/test_wall_clock_inventory.py (new)
- docs/performance/wall_clock_inventory.md, docs/performance/wall_clock_inventory.json (new)
- tools/gate_checks/test_scope_coverage_static.py (one map line)

## Completion Summary
Inventory delivered; nothing under `src/` was edited and nothing was measured. Answer to PERF-D1's revisit condition: a fourth input exists. Previous-tick wall-clock `tick_compute_ms` becomes `global_salience` (`kernel.py:661-678`), is stored in `AuthoritativeState.pressure_signals` (`apply.py:335,510`) and sets the shop price (`economy.py:27`, `town/shop.py:36-41`); `audit_mode` zeroes it; `pressure_signals` is not in the proof digest.

Two further inputs that PERF-D1's Canonical proxy set must cover (the planner records them in PERF-D1; the tool is unchanged):
- the replay-buffer backlog as a governor DEGRADED trigger (`governor.py:101-102`), which depends on a background flush thread;
- `PhaseBudgetGovernor` reading per-phase wall-clock costs and `tick_compute_ms` directly, whatever the current mode (`phase_governor.py:108-141`).
