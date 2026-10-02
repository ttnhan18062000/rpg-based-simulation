---
status: active
layer: performance
authority: P2
audience: agent
tags: [performance]
---

# Performance Profiling Toolkit

Three tools under `tools/perf/` that say **where tick time goes and why it moved**. They are the
profiling half of the "Performance management loop" in
`docs/plans/design_enhancement/performance_optimization/performance_optimization_roadmap.md`.
They complement, and do not replace, the regression gate that says whether a number got worse.

## The rule: a profile explains a cost, it never certifies capacity

Every output of these tools is **diagnostic evidence about where time goes**. It is not a baseline, not
a capacity claim and not a pass/fail result, and it carries a `PROVISIONAL` header saying so. Until the
RPG-core stability entry gate in the roadmap is lifted, a measurement is not taken as evidence for any
performance decision; these tools exist so that when the gate lifts there is already a repeatable way
to look. Do not cite a number from here as "the cost of X" without the header, the commit, the scenario,
the entity count and the seed that came with it.

Every table and file carries: commit, scenario, entity count, seed, warmup and measured tick counts,
profile, Python version, host core count, and the PROVISIONAL line. Outputs go under `reports/perf/`,
which is git-ignored; nothing generated is committed.

## Which tool when

| Question | Tool |
|---|---|
| Which functions and phases are hot in this scenario? | `profile_tick.py` |
| What changed between two profiles (a change, a flag, a commit)? | `profile_diff.py` |
| What does turning feature flag X on or off cost, and in which phase? | `flag_attribution.py` |
| Where are allocations coming from? | `profile_tick.py --memory` |

### `profile_tick.py`

```
python3 tools/perf/profile_tick.py --scenario combat --entities 60 --ticks 15 --profile PROD_STRESS
```

Builds the scenario from `src/perf/scenarios.py::SCENARIO_BUILDERS`, runs warmup plus N measured ticks
in a child process under `py-spy record` (the tool launches the child itself, so no elevated privilege is
needed), and writes `profile.folded`, `profile.speedscope.json` (open at speedscope.app), and
`phases.md` / `phases.json`: per-phase mean and p95 ms per tick, share of the tick, the `RuntimeMode`
sequence, the processed-work counters and the event count. A profile is never shown without that
context. Only samples taken inside the measured ticks are kept; import, setup and warmup are dropped.

`--memory` runs the same child under `memray` and writes its flame graph (stamped with the header);
the binary capture gets a `.provisional.txt` sidecar.

Install: `uv sync --group perf` for py-spy (an opt-in dependency group in `pyproject.toml`; it is not in
`dev`, so it is not in the `requirements.txt` export, and CI does not install it) and
`uv sync --group profiling` for memray. When the binary is missing the tool exits with that message; it
never falls back to another profiler.

**Sampler overhead.** py-spy pauses the process at every sample by default, which slowed a tick roughly
eightfold in the one sandbox run recorded for this ticket (about 235 ms unprofiled, 1,990 ms blocking,
274 ms with `--nonblocking`; one scenario, 60 entities, one machine, provisional). The tool therefore
defaults to `--nonblocking`; pass `--blocking` for consistent stacks at the price of distortion. Either
way, read shares, not absolute milliseconds, and use `flag_attribution.py` for unprofiled timings.

**Watch the mode.** The governor changes cadence, LOD and scan policy when the `RuntimeMode` leaves
`NORMAL`, which a slow tick can trigger. The tools print a warning when that happens; the numbers then
describe a degraded run. A profile with a larger tick budget (`--profile PROD_STRESS`) delays it.

### `profile_diff.py`

```
python3 tools/perf/profile_diff.py old/profile.folded new/profile.folded --top 10
```

Lists the frames whose share of samples grew or shrank most, with both shares, as markdown (or
`--format json`): phases (kernel `_phase_*` frames and pipeline phase lambdas), then functions by self
share and by inclusive share. Pipeline lambdas are identified by file and line, so profiles from
different commits are not comparable for them; the tool warns when the recorded commits differ, and
when a file has no provenance header.

### `flag_attribution.py`

```
python3 tools/perf/flag_attribution.py --flag ENABLE_COMBAT_ENGAGEMENT --scenario combat --entities 60 --reps 3
```

Runs the scenario from the same seed with the flag forced OFF and ON, K repetitions each, interleaved,
each in its own process with no profiler attached. It prints per-phase mean ms per tick for each state,
the delta, each phase's share of the total tick delta, the run-to-run range of the per-run means, and
event counts for both states. This is the 2026-09-14 combat-engagement study as one command.

A phase's share of the total delta can be negative or above 100% when other phases move the other way,
and sub-phases overlap their parent, so shares are not a partition. Treat a delta smaller than the
reported range as noise.

**How the flag is forced.** Two mechanisms read flags: `state.feature_flags`, and a `FeatureFlagManager`
that `AuthoritativeApplyPipeline.refine` builds fresh with defaults every tick and cannot be given
overrides. The tool builds a new state with `dataclasses.replace` carrying the forced value (the frozen state is
never written through) and wraps `FeatureFlagManager.get_flag_mode` in the child process only; no tracked
file is modified, and the output records what each mechanism reported inside the run. This is a
measurement aid, not a supported way to configure a run.

## Known limits

- Entity counts are small on purpose: these tools run the kernel. Do not read a small-count profile as a
  statement about 1,000 entities.
- The `metropolis` scenario is known defective (entities are stacked on the same tile by construction,
  `TCK-20260919-PERF-SCENARIO-METROPOLIS-SPAWN-COLLISION`); selecting it prints a warning and the header
  repeats it.
- Phase costs come from `kernel._phase_costs`, a private attribute that
  `tools/perf/profile_engine.py` also reads; if a public accessor appears, switch to it. Some entries are
  sub-phases of another, so shares do not sum to 100%.
- Events are counted with a listener appended to `kernel._event_listeners`.
- Nothing here edits `src/` or adds instrumentation to the kernel; that is a later milestone behind the
  entry gate.

## Overlap with the existing tools

`profile_engine.py` and `profile_sweep.py` use `cProfile`, whose tracing overhead distorts hot loops and
which stores nothing comparable; `profile_memory.py` and `memory_probe.py` cover memory in other ways.
They are left in place. Prefer the sampling tools here for "where does time go", and keep the older ones
for what only they do (for example the `pure` / `runtime` / `audit` harness modes of `profile_engine.py`).
