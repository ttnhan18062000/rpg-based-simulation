---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261003-PERF-PROFILING-TOOLKIT
date: 2026-10-03
tags: [performance]
---

# Test Plan: TCK-20261003-PERF-PROFILING-TOOLKIT

`python3 -m pytest tests/tools/test_profiling_toolkit.py tests/tools/test_test_scope_coverage_static.py -q`
(58 passed, 1 skipped with py-spy absent; the skipped test passes with py-spy on PATH).

Covers header fields and the PROVISIONAL line on every format, p95 and spread arithmetic, phase tables,
folded-stack parsing and filtering, speedscope validity, frame normalization, diff of two synthetic profiles,
attribution delta/share/spread arithmetic including a zero total delta, missing-binary message and exit code 2,
the metropolis warning, the CLIs of `profile_diff`, the flag override (builds a new state with `dataclasses.replace`, original untouched, both mechanisms set), and report rendering.

## Real runs (provisional; sandbox; commit 2d4d739d at the time)
All with `--py-spy <scratch install>` (py-spy 0.4.2 installed with `pip install --target` outside the repo),
`--profile PROD_STRESS`, scenario `combat`, 60 entities, seed 42. Outputs under the git-ignored `reports/perf/`.
1. `profile_tick.py --scenario combat --entities 60 --ticks 15 --warmup 2 --profile PROD_STRESS --flag ENABLE_COMBAT_ENGAGEMENT --flag-mode ON --out-dir reports/perf/profile_combat_60_ON`
   (and `--flag-mode OFF` to `profile_combat_60_OFF`): each wrote `profile.folded`, `profile.speedscope.json`,
   `phases.md`, `phases.json`, every one with the PROVISIONAL header.
2. `profile_diff.py reports/perf/profile_combat_60_OFF/profile.folded reports/perf/profile_combat_60_ON/profile.folded --top 6 > reports/perf/profile_diff_combat_60_OFF_vs_ON.md`:
   the pipeline lambda at `pipeline.py:320` (combat_engagement) goes from 0.00% to 42.89% of samples.
3. (re-run after the replace() change, same command: both mechanisms still reported the forced value; tick wall 100.5 ms off, 200.9 ms on)
   `flag_attribution.py --flag ENABLE_COMBAT_ENGAGEMENT --scenario combat --entities 60 --ticks 10 --reps 3 --profile PROD_STRESS`
   -> `reports/perf/flag_attribution/ENABLE_COMBAT_ENGAGEMENT_combat_60_s42.md`: tick wall time 100.4 ms off,
   206.6 ms on (+106.2 ms); combat_engagement +97.1 ms (91.4% of the delta); combat events 902 -> 1,097 per run;
   a GovernorModeChanged event appears with the flag on; the run warns that on-runs left NORMAL.
4. `profile_tick.py --memory --memray <scratch install>` on a tiny `mixed` run wrote the stamped flame graph.
`git status` after the runs shows nothing new outside ignored paths.

## Proof Plan
- level: unit plus real-kernel runs of each tool at small entity counts
- proof kind: behavioral tests and recorded real outputs
- oracle source: the ticket's acceptance criteria and a hand check that the flag-off run has no combat_engagement samples
- expected effect: tooling only; no engine behavior change
- selected commands: the pytest command above and the three real commands listed
