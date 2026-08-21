---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260817-RUNTIMEMODE-BENCH-SCOPING
artifact_type: investigation
tags: [performance, engine, testing]
---

# Investigation — TCK-20260817-RUNTIMEMODE-BENCH-SCOPING

## Current Behavior

### `docs/engine/performance_contract.md` §3.1 Scoped Claims (exact current text, lines 35-40)
```
### 3.1 Scoped Claims
Performance claims are ONLY valid when combined with:
- **Runtime Profile**: (e.g. `standard_gaming`)
- **Hardware Class**: (e.g. `Class_B`)
- **Scenario**: (e.g. `MOVEMENT_STRESS_100_ACTORS`)
- **Execution Mode**: (LOCAL vs CONCURRENT)
```
Section `3.2 measurement Protocol` starts at line 42. The insertion point for a 5th
`RuntimeMode` dimension is a new bullet immediately after `**Execution Mode**` (after line 40,
before the blank line/line 42 heading) — e.g. `- **RuntimeMode**: (NORMAL — see §7 Adaptive
Phase Budget Governor for the ladder)`.

**Anti-drift note**: `docs/engine/contracts/extended_certification_contract.md` §5 "Honest
Reporting Law (Scoped Claims)" defines a *different* 4-quadrant "Quadrants of Truth" (RuntimeProfile,
CertificationScenario, HardwareClass, OverrideStatus) for full certification runs. This is a
separate doc/contract from `performance_contract.md` §3.1 and is not in this ticket's Related
Docs or scope — do not conflate the two "Scoped Claims"-named sections or edit the wrong one.

### `BenchHarness.run_benchmark()` — `src/perf/bench_harness.py:40-182`
Tick loop structure:
- Warmup: lines 72-74, a bare `for _ in range(warmup_ticks): kernel.tick_once()` — no sampling.
- Sampling: lines 84-90, `for i in range(sample_ticks): kernel.tick_once()` then samples RSS via
  `self._process.memory_info().rss` only every 10th tick (`if i % 10 == 0`).
- Collation (lines 101-166): pulls `kernel.status.get_recent_history(sample_ticks)` — a
  `List[PressureSignals]` — and aggregates `tick_compute_ms`, `phase_costs_ms`, `metrics` from it
  into the result dict. **`PressureSignals` carries no mode field** (see below), so the result
  dict today has zero RuntimeMode information anywhere, and there is no way to reconstruct
  per-tick mode retroactively from `get_recent_history()` — mode must be sampled live inside the
  loop, same as `tick_compute_ms` sampling is (in fact `tick_compute_ms` per-tick history *is*
  recoverable post-hoc via `get_recent_history()`; mode is not, which is a materially different
  situation from what a naive reading of "mirror the active_mode pattern" might suggest).
- Natural hook point: inside the sampling `for i in range(sample_ticks)` loop (line 85-90), right
  after `kernel.tick_once()`, read `kernel.status.current_mode` (a `RuntimeMode` IntEnum) and
  append `.name` to a new list. Note the existing RSS sampling is throttled to every 10th tick to
  reduce overhead (`i % 10 == 0`); mode sampling should likely happen **every tick**, not
  throttled the same way, since a `RuntimeMode` enum-attribute read is a trivial int compare
  (negligible cost vs. `psutil` RSS collection) and throttling risks missing a transient
  CONSTRAINED/DEGRADED excursion inside the un-sampled gap. This is a Plan-phase decision, not
  yet made in code.
- Result dict currently has no `mode_sequence`-shaped key at all. Insertion point: alongside the
  other flat keys added at lines 158-165 (`avg_tick_compute_ms`, `peak_rss_mb`, etc.), or inside
  the main dict literal at lines 134-156, per acceptance criterion's example key name
  `mode_sequence`.
- `BenchHarness` imports (`src/perf/bench_harness.py:1-15`) currently do **not** import
  `RuntimeMode` from `src.core.governance` — this import will need to be added, or `.name` can be
  read directly off `kernel.status.current_mode` without importing the enum type itself (only
  needed if constructing/comparing `RuntimeMode` values directly rather than comparing `.name`
  strings against `"NORMAL"`).

### `long_run_harness.py:225`'s existing pattern
`src/perf/long_run_harness.py` lines 180-227: per-tick loop samples `active_mode=kernel.status.
current_mode.name` (line 225) but only inside a periodic `if t % sample_interval == 0 or t ==
total_ticks:` block (line 192) that also captures RSS, GC counts, and latency percentiles into a
`LongRunSample` dataclass appended to a `samples` list — i.e. it already reads exactly the same
`kernel.status.current_mode.name` accessor BenchHarness needs, but on a *sparser* cadence than
every tick. This confirms the accessor path (`kernel.status.current_mode`) is the correct,
already-proven pattern to mirror; it does **not** by itself resolve whether BenchHarness's new
sampling should be every-tick or throttled (see above).

### `RuntimeMode` / `PressureSignals` — `src/core/governance.py`
- `PressureSignals` (lines 19-52) **is** genuinely frozen at the language level:
  `@dataclass(frozen=True, slots=True)`, with an explicit docstring line "Status: FROZEN (Resource
  Phase 4 Milestone 1)" (line 23). It has no mode field and cannot gain one without an ADR-level
  schema change — confirms the ticket's Out-of-Scope premise.
- **New finding not stated in the ticket**: `RuntimeStatus` (`src/engine/runtime_status.py:9-33`)
  carries the *identical* docstring line "Status: FROZEN (Resource Phase 4 Milestone 1)" (line
  13), but is declared as a plain `@dataclass` — **not** `frozen=True`/`slots=True` like
  `PressureSignals`. So the "FROZEN" marker on `RuntimeStatus` is a stated-intent/process
  convention, not a language-enforced immutability like `PressureSignals`'s. This is moot for this
  ticket because the implementation route (reading `kernel.status.current_mode`) requires no
  schema change to `RuntimeStatus` at all — it's a pure read of an existing field — but Plan
  should not read "RuntimeStatus is FROZEN too" as blocking something this ticket doesn't
  actually need to touch, nor accidentally treat it as license to add fields to `RuntimeStatus`
  for unrelated reasons.
- **Confirmed accessor**: `Kernel` exposes `.status` (a `RuntimeStatus` instance) with
  `.current_mode: RuntimeMode` already populated every tick inside `Kernel._phase_init()`
  (`src/engine/kernel.py` — `prior_mode = self._status.current_mode` at line 545,
  `self._governor.evaluate(...)` at line 546 mutates `self._status.current_mode` via
  `status.reset_dwell()`/`status.increment_dwell()` inside `ResourceGovernor.evaluate()`). This is
  exactly the accessor `BenchHarness` needs and `long_run_harness.py:225` already uses —
  `kernel.status.current_mode` (no touch to `PressureSignals` or its frozen schema required).
- `RuntimeMode` (lines 8-16) is `IntEnum`: `NORMAL=0, CONSTRAINED=1, DEGRADED=2, SURVIVAL=3`.

### `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline`
Full test read (`tests/perf/test_perf_regression_baseline.py:32-71`). Currently:
- Loads a committed `tests/perf/baselines/{scenario_id}.json`, skips if absent.
- Runs `harness.run_benchmark(..., warmup_ticks=10, sample_ticks=50, flags={"no_replay": True})`.
- Compares `result["avg_tick_compute_ms"]` against `threshold = max(5.0, baseline_avg * 1.25)` via
  `assert_perf_threshold(current_avg, threshold, ..., op="<=")` (from
  `tests/tools/perf_assertions.py`).
- **Critical, ticket-relevant finding**: `assert_perf_threshold`/`perf_check` (the exact function
  this test calls) is currently **soft by default** — `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-
  WARNING` downgraded all `tests/perf/`, `tests/arena/`, and `tests/certification/`
  performance-threshold misses from hard `AssertionError` to a non-blocking
  `PerformanceThresholdWarning`, unless the caller explicitly passes `hard=True`. The module
  docstring (`tests/tools/perf_assertions.py:1-27`) explicitly carves out an exception: "hash/state
  equality, invariant checks, structural correctness... stay hard failures" — `hard=True` is meant
  for exactly this class of check. A `RuntimeMode != NORMAL` excursion is a structural-correctness
  question (was this benchmark run actually measuring what its baseline claims), not a
  hardware-calibration question, so there is direct, applicable precedent in this file for making
  the new assertion `hard=True` rather than routing it through the same soft path as
  `avg_tick_compute_ms`. This is presented as evidence for Plan to decide with, not a decision
  made here (Uncertainty Rule) — see Risks below for the countervailing empirical-gap concern.
- Minimal, precise change: after `result = harness.run_benchmark(...)` (line 49-55), once
  `mode_sequence` exists in `result`, add something like:
  ```python
  excursions = [m for m in result["mode_sequence"] if m != "NORMAL"]
  assert_perf_threshold(len(excursions), 0, f"RuntimeMode excursions during {scenario_id}", op="<=", hard=<Plan decides>)
  ```
  placed independently of (before or after) the existing `avg_tick_compute_ms` check, so a
  RuntimeMode excursion is surfaced even when the compute-time threshold itself still passes
  (this is the literal acceptance criterion: "independent of the avg_tick_compute_ms threshold
  result").

### The idiomatic mechanism for forcing a Governor mode transition in a test
Found in `tests/unit/domains/optimization/test_phase_budget_governor.py::
test_resource_governor_propagates_phase_budgets` (lines 91-99) and
`tests/unit/resource/test_resource_governor_contract.py::test_escalation_path` /
`test_multi_signal_escalation`: construct a `ResourceGovernor()` and a bare `RuntimeStatus()`
directly, then call `governor.evaluate(profile, PressureSignals(tick_compute_ms=<value that
exceeds the profile's thresholds>), status, tick)` and assert `status.current_mode ==
RuntimeMode.<X>`. This is **direct construction**, not mocking/monkeypatching — the idiomatic
pattern in this codebase is to drive the real `ResourceGovernor.evaluate()` with a deliberately
extreme `PressureSignals` value against a `RuntimeProfile` with known thresholds, not to patch
`ResourceGovernor` or `Kernel` internals. `ResourceGovernor._get_indicated_mode()`
(`src/engine/governor.py:73-99`) is the pure function actually driving the escalation ladder off
`profile.max_work_debt` / `profile.max_tick_budget_ms` / `profile.max_ram_mb` /
`worker_utilization` / `queue_utilization` / `replay_backlog_kb` thresholds — reading it confirms
exactly which `PressureSignals` field to set to force each `RuntimeMode` value (e.g.
`tick_compute_ms >= profile.max_tick_budget_ms * 1.5` → immediate `SURVIVAL`).

This ticket's acceptance criterion is about the **gate** (test_perf_regression_baseline.py's new
assertion), not about `ResourceGovernor` itself — so the new unit test needs to either (a) run a
short, real `BenchHarness.run_benchmark()` with a profile whose thresholds are tuned so real load
legitimately trips CONSTRAINED/DEGRADED/SURVIVAL mid-sample (closest to true end-to-end
coverage, but slower/less deterministic), or (b) unit-test the extracted gate-assertion logic in
isolation against a synthetic `mode_sequence` list containing a non-`"NORMAL"` entry (fast,
fully deterministic, but only exercises the assertion logic, not the sampling wiring). Both are
valid; which one (or both) is a Plan-phase decision. Given the precedent above, direct
construction (real `ResourceGovernor`/`RuntimeStatus`/extreme `PressureSignals`, monkeypatched
onto `kernel.status` or driving a real short benchmark with a starved profile) is more idiomatic
here than mocking `Kernel.tick_once()`.

### The "26 scenario builders" claim — does not match the codebase
The ticket's Assumptions section refers to "the 26 scenario builders (10 warmup/50 sample
ticks)". Investigation could not find 26 of anything:
- `src/perf/scenarios.py` defines exactly **7** builder functions: `build_idle_state`,
  `build_resource_state`, `build_movement_state`, `build_combat_arena_state`,
  `build_strategic_state`, `build_mixed_state`, `build_metropolis_state`.
- `tests/perf/test_perf_regression_baseline.py::test_regression_vs_baseline` — the actual live CI
  gate named in the ticket's own Request Summary, and the only place `warmup_ticks=10,
  sample_ticks=50` appears — parametrizes exactly **6** `scenario_id`s: `idle_100_local`,
  `movement_100_local`, `combat_10_local`, plus 3 SimQ-corpus loaders (`simq_corpus_
  frontier_extended`, `simq_corpus_frontier_marches`, `simq_corpus_crowded_frontier`).
- `tests/perf/baselines/` has **16** committed baseline JSON files, of which **10** (the
  `*_concurrent`, `resource_*`, `mixed_*`, `strategic_*` variants) have no corresponding
  parametrize entry in `test_regression_vs_baseline` today — they are orphaned relative to this
  specific gate (may be exercised elsewhere, e.g. `tests/perf/test_perf_*.py`'s own
  `perf_budget`-fixture-based tests, which is a different, `perf_baselines.json`-driven mechanism
  entirely — see `tests/perf/conftest.py`).
- **Conclusion**: the actual scoped surface for this ticket's new gate is the **6** scenarios in
  `test_regression_vs_baseline`'s parametrize table, not 26. Plan should correct this number
  rather than build against it; it does not change the ticket's scope (the gate change applies to
  whatever `test_regression_vs_baseline` parametrizes, however many that is) but does change how
  much empirical verification work "check all scenarios" actually implies.

### Empirical check: does any scenario already dip out of NORMAL?
Cannot be conclusively determined without running the benchmark — no committed artifact records
per-tick `RuntimeMode` today (not in the baseline JSONs, not anywhere else; this is exactly the
gap the ticket exists to close). One material circumstantial signal was found:
`tests/perf/baselines/simq_corpus_crowded_frontier.json` records `peak_rss_mb: 696.3` and
`memory_delta_mb: 627.26` for `"profile": "PERF_512MB_LOCAL"`. `src/perf/profiles.py`'s
`PERF_512MB_LOCAL` sets `max_ram_mb=512`. `ResourceGovernor._get_indicated_mode()`
(`src/engine/governor.py:82`) escalates straight to `SURVIVAL` when `signals.memory_estimate_mb
>= profile.max_ram_mb`, and `memory_estimate_mb` is populated every tick from the same real-
process RSS collector (`self._platform_signals["rss_mb"]`, `src/engine/kernel.py:536,705`) that
`BenchHarness`'s own `psutil` RSS sampling approximates. So this specific committed baseline —
generated with `sample_ticks=1000` (not the live gate's `sample_ticks=50`) — plausibly breached
the RAM ceiling and pushed the governor into `SURVIVAL` at some point during its run. This is
suggestive, not conclusive, for the actual 50-tick gated window (different tick count, and RSS
growth rate within the first 50 ticks vs. over 1000 is not known from the committed data). This
is precisely the empirical gap the ticket's own Assumptions section flags as needing resolution
before the gate can be safely made blocking — flagged here, not resolved, per the Uncertainty
Rule.

### `src/certification/conformance.py`'s `ConformanceEvaluator`
Full file read (145 lines). `ConformanceEvaluator.evaluate()` is a 7-step multi-dimensional
check: (1) reporting completeness / telemetry-gap, (2) RAM/tick-budget envelope, (3) semantic-
equivalence hash comparison (baseline vs. concurrent), (4) reproducibility hash comparison
(concurrent vs. concurrent), (4b) degradation-sequence monotonicity check on a `mode_sequence:
List[str]` param plus `required_governor_modes`, (5) recovery-timing compliance (must return to
NORMAL within `recovery_time_limit_ticks`, must end in NORMAL), (6) lifecycle-outcome compliance,
(7) allowed-failure-kind filtering. It depends on `ScenarioExpectations` (12 fields:
`required_governor_modes`, `requires_recovery`, `requires_semantic_equivalence`,
`recovery_time_limit_ticks`, `sampling_interval_ticks`, `allowed_failure_kinds`,
`reproducibility_required`, `expected_lifecycle_outcome`, `shutdown_timeout_s`,
`required_artifacts`, `allowed_execution_modes`, `allowed_profiles`) and `MeasurementPoint` (11
fields including two separate hash-comparison identities). This confirms the ticket's Out-of-
Scope steer is well-founded: only a small slice of step (4b) — "was every entered mode NORMAL" —
is relevant to this ticket's fast CI gate; the hash-comparison, recovery-timing, telemetry-gap,
and lifecycle machinery are irrelevant overhead for a per-commit perf-regression check and
importing `ConformanceEvaluator` wholesale would pull in dependencies (`ScenarioExpectations`,
dual-hash plumbing) `BenchHarness`/`test_perf_regression_baseline.py` have no other reason to
carry. A standalone `[m != "NORMAL" for m in mode_sequence]` check is sufficient for this
ticket's stated need.

### `docs/plans/kernel_concurrency_design_review_proposal.md` C4 (and adjacent context)
Read in full (lines 78-138, 338-373). This ticket is a near-verbatim extraction of C4. No
materially new information beyond what's already in the ticket body — confirms the same grep
finding (`long_run_harness.py:225` is the only pre-existing hit), the same
`certification_contract.md` §6 citation, and situates this as one of several C-items in the same
epic (`TCK-20260817-KERNEL-CONCURRENCY-DESIGN-EPIC`, already listed as Related Tickets). C5/C6 in
the same doc were separate, already-closed tickets (`TCK-20260817-DOC-CONCURRENCY-LIMIT-
RATIONALE`) — not this ticket's concern.

### `docs/engine/contracts/certification_contract.md` §6
Confirmed exact text (line 51): `- No modification of kernel laws for benchmark vanity.` — under
`## 6. Non-Goals`. This is the "spirit" citation in the ticket's Request Summary; the ticket does
not require editing this doc (not in Related Docs), only honoring the discipline it states.

## Mechanics / Engine Constraints
- `docs/engine/performance_contract.md` §7 "Adaptive Phase Budget Governor" already documents the
  `RuntimeMode`-driven budget ladder (`candidate_budget`, `movement_budget`, `strategic_budget`,
  `scan_policy`, `background_sweep_interval`, `compaction_level`) that makes non-NORMAL ticks
  measurably cheaper — this is the concrete mechanism behind the "masking" risk the ticket
  describes, and is why a blended average can hide a regression.
- `docs/engine/governance_logic.md` §3 "Degradation Laws" — NORMAL/CONSTRAINED/DEGRADED/SURVIVAL
  each get progressively simplified logic; consistent with the above.
- `docs/engine/contracts/signal_truth_contract.md` §7 "Governance Isolation Law": `RuntimeMode`
  and `PressureSignals` are explicitly **NON-AUTHORITATIVE** and must not contaminate
  `AuthoritativeState`/simulation hashes. This constrains implementation: any per-tick mode
  sampling BenchHarness does must stay purely observational (reading `kernel.status.current_mode`
  is a pure read of non-authoritative operational state, already compliant) — never feed
  `mode_sequence` data back into `AuthoritativeState` or use it to alter tick execution.

## Docs Requiring Update
- `docs/engine/performance_contract.md`: §3.1 Scoped Claims must gain RuntimeMode as a required
  5th dimension, per Scope item 1 and Acceptance Criterion 1.
- `docs/parity_ledger/infrastructure.yaml`: no existing entry covers BenchHarness per-tick
  RuntimeMode recording or the perf-baseline gate's excursion check (closest existing entries,
  INFRA-363 and INFRA-365, cover unrelated RuntimeMode-adjacent behavior — verification-level
  labeling and concurrency-limit scaling, respectively, not this). A new entry is needed once the
  behavior is implemented, following the INFRA-363 pattern (RuntimeMode-related, perf/infra
  layer).

Not required by this ticket (flagged, not to be pulled in): `docs/performance/perf_baseline_
policy.md` §3 already carries its own 2026-08-08 correction note stating §3.1-3.3 don't match
what `test_perf_regression_baseline.py` actually runs and defers reconciliation to "a dedicated
doc-accuracy ticket" — do not treat this ticket as that reconciliation ticket; scope creep risk,
see Anti-Drift Hazards.

## Parity Ledger Overlap
- `INFRA-363` (`docs/parity_ledger/infrastructure.yaml:10678`): "A run that ever reaches DEGRADED
  or SURVIVAL RuntimeMode is explicitly labeled reduced-verification in its outputs" —
  `RuntimeStatus.max_mode_reached` / `Kernel.shutdown()`'s `verification_level`. Adjacent
  (RuntimeMode-tracking precedent) but covers a different mechanism (shutdown-time verification
  labeling, not the perf-baseline CI gate). Not touched by this ticket; cite as the nearest prior
  pattern for the new entry's phrasing/`test_path` style.
- `INFRA-365` (`docs/parity_ledger/infrastructure.yaml:10717`): `GovernorPolicy.from_mode()`
  concurrency-limit scaling rationale — unrelated to this ticket (already closed via C6/
  `TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE`).
- No P0 entries found overlapping this ticket's scope.

## Prior Work
- `TCK-20260818-STANDARD-PERF-THRESHOLD-SOFT-WARNING` (stored_artifacts + `tests/tools/
  perf_assertions.py`): directly relevant precedent for the hard-vs-soft assertion decision on the
  new RuntimeMode check (see Current Behavior above).
- `TCK-20260808-SIMQ-CORPUS-PERF-BASELINE-INTEGRATION`: added the 3 SimQ-corpus parametrize
  entries to `test_regression_vs_baseline` and corrected `perf_baseline_policy.md` §3's accuracy
  note — relevant background for why that doc is already flagged stale (see Docs Requiring
  Update).
- `TCK-20260817-DOC-CONCURRENCY-LIMIT-RATIONALE` and `TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT`:
  sibling C-items from the same design-review proposal, both already closed 2026-08-21 — confirms
  this batch is actively working through the same source doc's C-items sequentially.

## Risks and Open Questions
1. **Hard vs. soft assertion** (blocks a clean Plan decision): `assert_perf_threshold`'s
   `hard=False` default (soft-warning stopgap) has documented precedent for `hard=True` on
   structural-correctness checks, which a RuntimeMode excursion arguably is. But the empirical gap
   below means a `hard=True` gate could immediately start blocking `simq_corpus_crowded_frontier`
   (and possibly others) on legitimate load-driven pressure, not a real regression. Plan must
   decide, not assume — this is exactly the tension the ticket's Out-of-Scope item 3 anticipates
   ("don't silently loosen the gate to compensate" vs. not wanting false-positive blocking on
   day one).
2. **Empirical gap on scenario behavior under real load** (see above): cannot be resolved without
   running each of the 6 scenarios (not 26) through the actual 10-warmup/50-sample gate
   configuration with mode sampling wired in. This is exactly the info Plan needs before deciding
   blocking-vs-flagging, and this investigation cannot produce it without doing that work itself
   (out of Investigate's scope; flagged for Plan/Implement to measure once `mode_sequence` exists).
3. **Every-tick vs. throttled sampling cadence** inside `BenchHarness`'s sampling loop — not
   specified by the ticket, no direct precedent (`long_run_harness.py` throttles; the ticket's
   own "any sampled tick" language suggests every tick matters). Needs a Plan decision.
4. Ticket's "26 scenario builders" premise does not match the codebase (7 builders, 6
   parametrized scenario_ids in the actual gate) — flagged above; Plan should use the corrected
   number.

## Anti-Drift Hazards
- Do not confuse `performance_contract.md` §3.1 "Scoped Claims" with
  `extended_certification_contract.md` §5's differently-shaped "Scoped Claims"/"Quadrants of
  Truth" — different docs, different dimension sets, only the former is in scope.
- Do not modify `PressureSignals` (`src/core/governance.py`) to add a mode field — genuinely
  frozen (`frozen=True, slots=True`), and unnecessary: `kernel.status.current_mode` already
  exposes live RuntimeMode without touching it.
- Do not treat `RuntimeStatus`'s "FROZEN" docstring comment as blocking a *read* of its existing
  `current_mode` field — it isn't language-enforced immutable like `PressureSignals`, and this
  ticket needs no write/schema change to it regardless.
- Do not get pulled into reconciling `docs/performance/perf_baseline_policy.md` §3's already-
  flagged staleness — that doc explicitly defers to a separate "dedicated doc-accuracy ticket";
  doing it here is scope creep.
- Do not silently loosen/skip the new gate for any scenario found to dip out of NORMAL under
  real load without a stated rationale — ticket's Out-of-Scope item 3 is explicit that this must
  be flagged as a follow-up, not silently compensated for.
- Do not import/reuse `ConformanceEvaluator` wholesale for this fast CI gate — confirmed
  unnecessary weight (hash comparisons, recovery timing, lifecycle checks the fast gate has no
  use for); a standalone `mode != "NORMAL"` scan is sufficient per this investigation.
