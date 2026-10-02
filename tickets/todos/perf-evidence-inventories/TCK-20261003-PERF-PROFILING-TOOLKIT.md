---
status: active
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261003-PERF-PROFILING-TOOLKIT
phase: open
date: 2026-10-03
tags: [performance, observability, engine]
---

# TCK-20261003-PERF-PROFILING-TOOLKIT

## Title
Profiling toolkit: sampling profiles, differential comparison, and feature-flag on/off phase attribution as repeatable tools

## Status
OPEN

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
- [ ] `py-spy` is installable through the new optional group and is absent from `requirements.txt`
- [ ] `python3 tools/perf/profile_tick.py --scenario <name> --entities <n> --ticks <n>` writes a speedscope JSON, a folded-stack file, and a per-phase table under `reports/perf/`, each with the full PROVISIONAL header; one real run is recorded in the test plan with its command and output paths
- [ ] `profile_diff.py` on two folded-stack files lists the largest increases and decreases in sample share with both values
- [ ] `flag_attribution.py --flag ENABLE_COMBAT_ENGAGEMENT` (or another real flag) produces the off/on per-phase table with deltas, shares of the total delta, spread across K repetitions, and event counts; one real run is recorded in the test plan
- [ ] Selecting the metropolis scenario prints the known-defect warning
- [ ] The tools run without modifying any tracked file, and `git status` after a run shows nothing new outside ignored paths
- [ ] Tests pass with the profiler binary absent
- [ ] `docs/guides/performance_profiling.md` exists with valid frontmatter and states the explains-not-certifies rule
- [ ] `git diff` touches only `tools/`, `tests/tools/`, `docs/guides/`, `docs/REGISTRY.yaml`, `pyproject.toml`, `tickets/`, `stored_artifacts/`, and `agent-monitoring/`

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
None.

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

## Test Summary

## Files Changed

## Completion Summary
