---
status: active
layer: architecture
authority: P1
audience: agent
tags: [architecture, engine, determinism, observability, testing]
---

# Epic Plan — Determinism Envelope for Wall-Clock-Driven Mode Escalation

**Tracking ticket:** `TCK-20260825-EPIC-DETERMINISM-ENVELOPE` (not yet created — this epic is
scope-only, per `docs/plans/design_enhancement/design_enhancement_roadmap.md` Priority 0.5)
**Source:** `tmp/external_ai_suggest_design.md` (not committed) §1, verified directly against
`src/core/governance.py`, `src/engine/governor.py`, `docs/parity_ledger/infrastructure.yaml`
(`INFRA-363`), `docs/engine/deterministic_execution.md`
**Priority:** P1 — ranks ahead of the Performance epic because Performance's own "Risk to
determinism" ratings implicitly assume a guarantee that, for the live/concurrent server, is now
known to need a stated qualifier.

## Problem

`RuntimeMode` (NORMAL/CONSTRAINED/DEGRADED/SURVIVAL) escalation is driven by real wall-clock and
hardware measurements — `PressureSignals.tick_compute_ms` (nanosecond-derived), `memory_estimate_mb`
(RSS), `worker_utilization`, `queue_utilization` (`src/core/governance.py`) — read directly by
`ResourceGovernor._get_indicated_mode()` (`src/engine/governor.py`). `RuntimeMode` in turn gates
cadence, LOD, `scan_policy`, concurrency, and debt accumulation. So two runs of the same seed and
initial state, under different real-world timing or machine load, can genuinely diverge in *what
gets computed*, not merely in execution trace or wall-clock duration — for the live/concurrent
server specifically (sequential/certification mode is unaffected; it doesn't run under live load).

This is **not** the already-documented "concurrent mode isn't bit-exact" scope note in
`docs/engine/deterministic_execution.md` (which cites OS-level worker-completion-order
nondeterminism, a problem the canonical-sort-before-Resolution design already solves). It's a
separate, additional mechanism producing the same top-level symptom.

**Existing, real mitigation, already verified — this epic is not starting from zero.**
`INFRA-363` (`docs/parity_ledger/infrastructure.yaml`, `status: verified`) already labels any run
whose `RuntimeStatus.max_mode_reached` hits DEGRADED/SURVIVAL as `verification_level = "REDUCED"`
on `ShutdownResult`, `RunManifest`, and `run_report.json/.md`, tested by
`tests/unit/kernel/test_verification_level.py`. That's an honest per-run disclosure, not a
cross-run reproducibility guarantee — the residual gap this epic scopes is specifically "is 'same
seed' still a promise for the live server, or only for sequential/certification runs," which
`verification_level` doesn't answer either way.

## Scope for the eventual `create-tickets` pass

Not created yet — this epic is scope-only. Milestones in dependency order:

### M1 — Formalize the reproducibility manifest and make the scope decision explicit

1. **Define what "same seed + same initial state" is actually promising, per execution mode.**
   Decide explicitly between: a **canonical mode** (certification/sequential runs drive
   `RuntimeMode` off deterministic proxies — fixed work-unit counts, queue depth against a fixed
   ceiling — instead of wall-clock timing, making even a "degraded" certification run
   reproducible), and a **live bounded mode** (the live server keeps real wall-clock signals, but
   every `RuntimeMode` transition is appended to a recorded control trace, so a live run becomes
   reproducible *given that trace* — the trace itself isn't predictable in advance, and that's
   accepted). This is a real design decision needing maintainer sign-off, not something to default
   into silently.
2. **Write the decision into `docs/engine/deterministic_execution.md`.** Its "Scope of the
   guarantee" section currently names only OS-level worker-completion-order as the concurrent-mode
   carve-out reason — add `RuntimeMode`-driven divergence as the second, distinct mechanism, and
   state the M1.1 decision as the resolution.
3. **Add a parity ledger entry** for whichever mechanism M1.1 lands on (canonical-proxy signals, or
   the control-trace format) — `docs/parity_ledger/infrastructure.yaml`, following the
   `INFRA-363`/`INFRA-368` precedent already in that file.

### M2 — Instrument and test the chosen mechanism

4. **If canonical mode:** replace `PressureSignals`' wall-clock-derived fields with deterministic
   proxies for the certification/sequential execution path specifically, without changing the live
   path's real signals. Extend `tests/unit/kernel/test_verification_level.py` and
   `tests/unit/kernel/test_worker_equivalence.py` with a case proving two sequential runs of the
   same scenario under artificially different simulated load produce identical `RuntimeMode`
   sequences.
5. **If live bounded mode:** add the control-trace recording (every mode transition, its trigger
   signal values, and the tick it occurred on) to the replay/persistence path, and a divergence
   tool that replays a live run's control trace against a fresh run to confirm it reproduces given
   that trace.
6. **Either way:** confirm Priority 0's `worker_utilization` fix (tracked separately,
   `docs/plans/design_enhancement/design_enhancement_roadmap.md` Priority 0) lands first or
   alongside — every `PERF_*_LOCAL` scenario is currently mislabeled `verification_level=REDUCED`
   because of that defect, which would otherwise contaminate M2's own test baselines.

## Out of Scope

- Making DEGRADED/SURVIVAL mode itself deterministic in the sense of "always reachable at the same
  tick" — the point is honest reproducibility of *whatever* sequence occurs, not eliminating
  load-dependent behavior from the live server.
- Anything in `docs/plans/design_enhancement/design_enhancement_roadmap.md` Section G — those are
  unverified proposals from the same external note, not in scope here unless independently scoped.

## Acceptance Signal

`docs/engine/deterministic_execution.md`'s "Scope of the guarantee" section states the
`RuntimeMode` mechanism explicitly (not just OS-level ordering), the chosen mode (canonical vs.
live bounded) has a passing test proving its specific reproducibility claim, and `INFRA-363`/a new
parity entry reflect the landed mechanism.
