---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-PROFILING-TOOLKIT
phase: done
date: 2026-10-03
tags: [performance, observability, engine]
---

# TCK-20261003-PERF-PROFILING-TOOLKIT

## Title
Profiling toolkit: sampling profiles, differential comparison, and feature-flag on/off phase attribution as repeatable tools

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The repository can say whether a performance number got worse, and has almost nothing that says where tick time goes or why it moved. Existing profiling is `cProfile`-based (`tools/perf/profile_engine.py`, `profile_sweep.py`), which distorts hot loops with tracing overhead; nothing stores a profile in a comparable form; and the one phase-attribution study the performance plan relies on (2026-09-14, turning `ENABLE_COMBAT_ENGAGEMENT` on) was assembled by hand from `kernel._phase_costs`.

Add the profiling half of the performance management loop (`performance_optimization_roadmap.md`, "Performance management loop") as tooling: a sampling profiler wrapper, a profile differ, and a flag on/off attribution tool. Tooling only: no `src/` edit, no baseline, no gate.

## Scope
- Add `py-spy` to an optional dependency group (`perf` in `pyproject.toml`, beside the existing `dev` group that already lists `memray`); it must not enter `requirements.txt` or CI's install
- `tools/perf/profile_tick.py`: build a named scenario from `src/perf/scenarios.py::SCENARIO_BUILDERS` at a given entity count and seed, run warmup plus N measured ticks in a child process under `py-spy record`, and write a speedscope JSON and a folded-stack file. It launches the child itself, so no elevated privilege is needed. A `--memory` option runs the same child under `memray` and writes its flame graph. When the profiler binary is absent, exit with a clear message naming the install command
- The same run also writes a per-phase table (mean and p95 ms per tick, share of tick) read the way `tools/perf/profile_engine.py` already reads phase costs, plus the `RuntimeMode` sequence and processed-work count, so a profile is never shown without the tick context
- `tools/perf/profile_diff.py`: compare two folded-stack files and print the functions and phases whose share of samples grew or shrank most, with both shares, as markdown and JSON
- `tools/perf/flag_attribution.py`: for a named feature flag, run the scenario with the flag off and on from the same seed, K repetitions each, and print per-phase ms per tick for each state, the delta, each phase's share of the total delta, the run-to-run spread, and event counts for both states. This reproduces the 2026-09-14 study as one command
- Every output file and table carries a header: commit, scenario, entity count, seed, tick counts, interpreter version, host core count, and the word PROVISIONAL with one line saying it is diagnostic evidence, not a baseline or capacity claim
- Outputs go under `reports/perf/` (already git-ignored); nothing generated is committed
- `docs/guides/performance_profiling.md`: when to use each tool, how to read the outputs, and the rule that a profile explains a cost and never certifies capacity; with valid frontmatter
- Tests under `tests/tools/` for everything that does not need the profiler binary: folded-stack parsing and diffing on synthetic input, attribution arithmetic (delta, share, spread) on synthetic phase costs, header rendering, and the missing-binary message. A test that actually invokes `py-spy` is allowed only if it skips cleanly when the binary is absent
- Add the three tools and their tests to the test-scope map (`tools/gate_checks/test_scope_coverage_static.py`), as the sibling tickets did

## Out of Scope
- Any edit under `src/`, including adding instrumentation, spans, or metrics to the kernel or pipeline — that is M3 and waits for the RPG-core entry gate
- Recording, committing, or comparing against a baseline; wiring any of these tools into CI or a gate
- A continuous-profiling service or dashboard; the roadmap names that as a later step
- Replacing or deleting `profile_engine.py`, `profile_sweep.py`, `profile_memory.py`, or `memory_probe.py`; note overlap in the guide and leave them
- Fixing `build_metropolis_state()` (`TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION`); when that scenario is selected, print a warning that it is known defective and cite the ticket
- Investigating or fixing any hotspot the tools reveal

## Acceptance Criteria
- [x] `py-spy` is installable through the new optional group and is absent from `requirements.txt`
- [x] `python3 tools/perf/profile_tick.py --scenario <name> --entities <n> --ticks <n>` writes a speedscope JSON, a folded-stack file, and a per-phase table under `reports/perf/`, each with the full PROVISIONAL header; one real run is recorded in the test plan with its command and output paths
- [x] `profile_diff.py` on two folded-stack files lists the largest increases and decreases in sample share with both values
- [x] `flag_attribution.py --flag ENABLE_COMBAT_ENGAGEMENT` (or another real flag) produces the off/on per-phase table with deltas, shares of the total delta, spread across K repetitions, and event counts; one real run is recorded in the test plan
- [x] Selecting the metropolis scenario prints the known-defect warning
- [x] The tools run without modifying any tracked file, and `git status` after a run shows nothing new outside ignored paths
- [x] Tests pass with the profiler binary absent
- [x] `docs/guides/performance_profiling.md` exists with valid frontmatter and states the explains-not-certifies rule
- [x] `git diff` touches only `tools/`, `tests/tools/`, `docs/guides/`, `docs/REGISTRY.yaml`, `pyproject.toml`, `tickets/`, `stored_artifacts/`, and `agent-monitoring/`

## Related Tickets
- TCK-20260913-PERF-M0-ARCHITECTURE-GOVERNANCE-EPIC
- TCK-20260914-COOPERATION-FIND-PENDING-OFFER-COST-OBSERVED (carries the hand-made attribution table this automates)
- TCK-20260914-STATE-FINGERPRINT-COST-OBSERVED
- TCK-20260914-DECISION-TRACE-WRITE-COST-OBSERVED
- TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION
- TCK-20260518-PROFILING-HARNESS-MODES
- TCK-20260529-OBS-PHASE20

## Related Docs
- `docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md` ("Performance management loop", "RPG-core stability entry gate")
- `docs/plans/design_enhancement/performance_optimization/performance_stack_survey.md` (section A)
- `docs/plans/design_enhancement/performance_optimization/performance_m4_baseline_gate_a_epic.md` ("Confirmed field evidence")
- `docs/architecture/performance_optimization_decisions.md` (PERF-D1, PERF-D4)

## Related Stored Artifacts
- stored_artifacts/TCK-20261003-PERF-PROFILING-TOOLKIT/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `tools/perf/` (new tools beside `profile_engine.py`, `profile_sweep.py`)
- `src/perf/scenarios.py`, `src/engine/kernel.py` (read and run, not edited)
- `tests/tools/`, `pyproject.toml`

## Assumptions / Open Questions
- Running the kernel to profile it is allowed under the entry gate because the output is diagnostic and labeled provisional; the gate forbids taking measurements **as evidence**, which the header rule enforces
- The owner accepted the stack survey's recommendation of `py-spy` and `memray` on 2026-10-02; this ticket does not evaluate alternatives
- Reading `kernel._phase_costs` uses a private attribute, as `tools/perf/profile_engine.py` already does; if a public accessor exists, use it, and do not add one to `src/`
- If `py-spy` cannot sample in this environment (for example a sandbox that blocks it), stop and report the exact error; do not substitute `cProfile` silently
- Third in `SEQUENCE.md`, after the two inventory tickets, so the shared `tools/perf` output conventions are already settled
- The planner session reviews one real output of each tool before this ticket closes

## Implementation Notes
Hand-orchestrated by perf-implementer. Shared helpers in `tools/perf/_profiling_common.py`; `profile_tick.py` runs the kernel in a child under `py-spy record` (nonblocking by default) and keeps only stacks inside the measured-tick loop; `flag_attribution.py` reuses the child mode with a forced flag. Forcing a flag builds a new state with `dataclasses.replace` (never writes through the freeze) and wraps `FeatureFlagManager.get_flag_mode` in the child process only. py-spy lives only in the opt-in `profiling` dependency group of `pyproject.toml` (beside memray). It was first added as a separate `perf` group; after main replaced the `dev` extra with `[dependency-groups]` (#288) it was folded into the existing `profiling` group on perf-planner's request, so there is one opt-in profiling group.

## Test Summary
`python3 -m pytest tests/tools/test_profiling_toolkit.py tests/tools/test_test_scope_coverage_static.py -q` -> 58 passed, 1 skipped without py-spy (the skipped end-to-end test passes with py-spy on PATH). Real runs of all three tools and a memray smoke run are recorded in the test plan; `git status` after them showed nothing outside ignored paths. perf-planner reviewed one real output of each tool and requested one change (`dataclasses.replace` instead of writing through the freeze), made and re-verified with a fresh `flag_attribution` run.

## Files Changed
- tools/perf/_profiling_common.py, profile_tick.py, profile_diff.py, flag_attribution.py (new)
- tests/tools/test_profiling_toolkit.py (new)
- docs/guides/performance_profiling.md (new)
- pyproject.toml (py-spy added to the existing opt-in `profiling` dependency group)
- tools/gate_checks/test_scope_coverage_static.py (four entries in `_TOOLS_PERF_BASENAME_MAP`)
- tickets/todos/perf-evidence-inventories/ -> tickets/done/ (this file); stored_artifacts/; tickets/working_log.csv, docs/REGISTRY.yaml, agent-monitoring/ (closure bookkeeping)

## Completion Summary
Profiling half of the performance management loop delivered as tooling: `profile_tick.py` (py-spy sampling and a per-phase table with RuntimeMode and work counters, `--memory` via memray), `profile_diff.py` (share-of-samples differences for functions and phases) and `flag_attribution.py` (flag off/on per-phase deltas over K interleaved repetitions), every output stamped PROVISIONAL, plus the guide. No `src/` edit, no baseline, nothing generated is committed.

Findings recorded for follow-up (taken forward by perf-planner):
1. **Two flag mechanisms.** `AuthoritativeApplyPipeline.refine` builds a fresh default `FeatureFlagManager()` every tick (`pipeline.py:70`) that cannot be given overrides, while `state.feature_flags` is a separate dict the kernel merges at construction (`kernel.py:110-112`); forcing a flag needs both (related: TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS).
2. **The governor leaves NORMAL at small entity counts.** In this sandbox a 60-entity `combat` scenario under `PROD_LARGE` goes DEGRADED then SURVIVAL within ten ticks; under `PROD_STRESS` it stays NORMAL with the flag off but reaches CONSTRAINED or DEGRADED with `ENABLE_COMBAT_ENGAGEMENT` on, so a flag delta can include a mode change. The tools warn when this happens.
3. **Sampler overhead.** Per tick, same scenario with the flag on: about 235 ms unprofiled, about 1,990 ms with blocking py-spy, about 274 ms with `--nonblocking` (one scenario, one sandbox, provisional). The tool defaults to nonblocking.

Known follow-up still open: `.claude/agents/test-scoper.md` carries a copy of the test-scope map and was not updated for the `tools/perf` tools added by the three tickets in this batch; agent files are outside this track and perf-planner raises it with the user.
