---
status: active
layer: performance
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261003-PERF-PROFILING-TOOLKIT
date: 2026-10-03
tags: [performance]
---

# Investigation: TCK-20261003-PERF-PROFILING-TOOLKIT

- **py-spy works here.** Launching the child under `py-spy record` needs no privilege (ptrace_scope is 1, and
  a child of the profiler is allowed). The profiler prints "No child process (os error 10)" on exit in some
  runs; the sample file is still written, so success is judged by the file, not the exit text.
- **Sampler overhead is large when blocking.** One scenario (combat, 60 entities, PROD_STRESS, flag ON):
  about 235 ms per tick unprofiled, about 1,990 ms with blocking py-spy, about 274 ms with `--nonblocking`.
  The tool defaults to nonblocking. One sandbox, provisional.
- **Two feature-flag mechanisms.** `FeatureFlagManager()` is built fresh with defaults every tick in
  `AuthoritativeApplyPipeline.refine` (`pipeline.py:70`) and cannot be given overrides; `state.feature_flags`
  is a separate dict the kernel merges at construction (`kernel.py:110-112`). Forcing a flag therefore needs both:
  a new state built with `dataclasses.replace` (the frozen state is never written through; perf-planner review) and a process-local wrap of `FeatureFlagManager.get_flag_mode` in the child. This is related
  to `TCK-20260913-FEATURE-FLAG-DEFAULT-DOES-NOT-PROPAGATE-TO-STATE-FEATURE-FLAGS`.
- **The governor leaves NORMAL in these runs.** Under PROD_LARGE a 60-entity combat scenario goes
  DEGRADED -> SURVIVAL within ten ticks in this sandbox; PROD_STRESS (500 ms budget) delays it, and with
  the flag ON a run still reaches CONSTRAINED or DEGRADED. The tools warn instead of hiding it.
- **Phase costs** come from `kernel._phase_costs` (private); events from a listener on `kernel._event_listeners`.
