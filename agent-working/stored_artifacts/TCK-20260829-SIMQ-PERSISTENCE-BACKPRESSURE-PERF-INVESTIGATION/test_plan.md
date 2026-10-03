---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION
artifact_type: test_plan
tags: [performance, observability, simulation-quality]
---

# Test Plan — TCK-20260829-SIMQ-PERSISTENCE-BACKPRESSURE-PERF-INVESTIGATION

## Regression Surface

Existing tests that must keep passing once a fix from either Root cause (#1 `ReplayManager
._rotate_chunk`'s redundant synchronous serialization, #2 unconditional per-record `flush()` in
`QualityPersistence.write()` / `EventRecorder._write_envelope_to_file()`) — and/or a
`CanonicalStateHasher` cadence change, if Plan chooses that path — is implemented.

**Unit — replay/chunk rotation (Root cause #1 surface):**
- `tests/unit/kernel/test_replay_chunk_rotation.py`
- `tests/unit/kernel/test_replay_contract.py`
- `tests/unit/kernel/test_replay_overflow.py`
- `tests/unit/kernel/test_replay_pressure.py`
- `tests/unit/kernel/test_replay_shutdown_budget.py`
- `tests/unit/engine/test_replay_backpressure.py`
- `tests/unit/engine/test_resource_budget_gate.py`
- `tests/certification/test_artifact_budget.py`

**Unit — observability queue / EventRecorder (Root cause #2 surface):**
- `tests/unit/observability/test_event_recorder.py`
- `tests/unit/observability/test_event_recorder_quality_fn.py`
- `tests/unit/observability/test_obs_backpressure.py`
- `tests/unit/observability/stream/test_phase21_bounded_observability_queue.py`
- `tests/unit/test_queue_worker_singleton.py`
- `tests/unit/engine/test_lifecycle_supervisor.py`

**Unit — SimQ persistence write path:**
- `tests/simulation_quality/test_persistence.py`
- `tests/simulation_quality/test_evaluate_harness.py`
- `tests/simulation_quality/test_quality_hub_integration.py`
- `tests/simulation_quality/test_calibrate_simq.py`
- `tests/simulation_quality/test_broker_feed_integration.py`
- `tests/simulation_quality/test_performance.py`
- `tests/perf/test_simq_isolation_overhead.py`

**Unit — canonical hash / determinism (only if Plan touches `CanonicalStateHasher` cadence):**
- `tests/unit/core/test_engine_integrity.py`
- `tests/unit/core/test_entity_integrity.py`
- `tests/unit/core/test_operational_flags.py`
- `tests/unit/engine/test_hash_scheduler.py`
- `tests/unit/domains/progression/test_progression_decision_canonical_hash.py`

**Integration — determinism/replay fidelity/checkpoint (broad blast radius if hash cadence changes):**
- `tests/integration/kernel/test_determinism_suite.py` (also `INFRA-223`'s own `test_path`)
- `tests/integration/kernel/test_checkpoint_reproducibility.py`
- `tests/integration/kernel/test_replay_fidelity.py`
- `tests/integration/kernel/test_snapshot_integrity.py`
- `tests/integration/kernel/test_kernel_boundaries.py`
- `tests/integration/pipeline/test_phase_order.py`
- `tests/integration/pipeline/test_governance_isolation.py`
- `tests/integration/pipeline/test_no_hidden_mutation.py`
- `tests/integration/observability/test_event_recorder_live_publish.py`
- `tests/integration/observability/test_decision_trace_determinism.py`
- `tests/integration/observability/test_phase28_observability_degradation.py`
- `tests/unit/core/test_graceful_shutdown.py`
- `tests/unit/core/test_non_blocking_io.py`

**Arena-combat:** none of the affected code paths (`persistence.py`, `observability/queue.py`,
`observability/event_recorder.py`, `engine/replay_manager.py`, `engine/checkpoint.py`) are on the
combat resolution path; `tests/arena/state_diff.py` only reads `CanonicalStateHasher`-shaped diffs
for debugging output and is not expected to be affected, but is listed for completeness since it
imports `checkpoint.py`.

**Soft-monitor world-assembly suite (per `docs/testing/regression_policy.md` §3, alert-only, not a
hard gate):**
- `tests/unit/worldassembly/test_corpus_diversity.py` (the full file, not just the 6 named tests
  below — a fix here should not newly break any of the other 141 currently-passing tests in this
  file)

## New Tests Required

Mapped to the ticket's 4 Acceptance Criteria.

**AC1 — "Real profiling data (not guessed) identifies the specific bottleneck":**
Satisfied by this investigation's own profiling (cProfile + clean-baseline runs, documented in
`investigation.md`). No new automated test is needed to satisfy AC1 itself, but the profiling
methodology (representative-scenario `_run_engine` call under `cProfile`, phase_costs collection)
should be captured as a reusable script if Plan wants a regression-detection harness — see the
"perf regression guard" test below, which operationalizes AC1's evidence into an ongoing check.

- **Test name**: `test_rotate_chunk_does_not_serialize_synchronously_on_main_thread` (or similar)
  - **Category**: unit
  - **Verifies**: `ReplayManager._rotate_chunk()`'s budget pre-check no longer does a full
    `json.dumps([_to_dict(e) for e in events])` walk of the entire chunk buffer synchronously
    before dispatching to the executor — e.g. assert the pre-check either uses a cheap estimate
    (sum of a fixed per-event size, or `sys.getsizeof`-based approximation) or is itself moved into
    the submitted background callable. Mock/spy `json.dumps` or the `_to_dict` closure and assert
    call count / call site.
  - **Location**: `tests/unit/kernel/test_replay_chunk_rotation.py` (existing file — extend) or a
    new `tests/unit/engine/test_replay_manager_rotate_chunk_perf.py`

- **Test name**: `test_quality_persistence_write_does_not_flush_every_record` (or similar, depending
  on the batching/interval strategy Plan selects)
  - **Category**: unit
  - **Verifies**: `QualityPersistence.write()` no longer calls `.flush()` unconditionally on every
    call — e.g. assert flush call count is less than record count for N>1 writes under whatever
    batching/interval strategy is chosen (batch-N, time-interval, or flush-on-shutdown-only with an
    explicit durability trade-off documented).
  - **Location**: `tests/simulation_quality/test_persistence.py` (existing file — extend)

- **Test name**: `test_event_recorder_write_envelope_does_not_flush_every_record` (or similar)
  - **Category**: unit
  - **Verifies**: same pattern as above for `EventRecorder._write_envelope_to_file()` /
    `QueueDrainWorker`'s drain loop.
  - **Location**: `tests/unit/observability/test_event_recorder.py` (existing file — extend)

**AC2 — "A concrete fix ... is implemented and verified to reduce persistence phase cost
meaningfully for a representative 1000-tick run":**

- **Test name**: `test_persistence_phase_cost_regression_guard_1000t` (or similar)
  - **Category**: integration / performance (soft-monitor style, per
    `docs/testing/regression_policy.md` §3's "Performance-threshold assertions" row —
    `tests/tools/perf_assertions.py`'s `PerformanceThresholdWarning` pattern, not a hard fail)
  - **Verifies**: runs `tools/calibrate_simq.py::_run_engine` for ~1000 real ticks (a fixed,
    reasonably fast scenario/seed — reuse `urban_political`/`seed=42` for continuity with this
    investigation's own evidence, or a smaller/cheaper scenario if 1000-tick runtime in CI is a
    concern) and asserts the `persistence`-phase share of total tick cost (sum across the run) stays
    under a documented ceiling (e.g. derived from this investigation's clean-run baseline of 29.3%
    at 500 ticks — Plan should set the actual threshold once the fix's real post-fix number is
    measured, not invented here). Emit a `PerformanceThresholdWarning` rather than hard-failing, to
    stay consistent with the existing perf-threshold soft-monitor pattern and avoid CI-hardware
    variance false failures.
  - **Location**: `tests/perf/test_simq_isolation_overhead.py` (existing file, closest thematic fit)
    or a new `tests/perf/test_persistence_phase_cost.py`

**AC3 — "`--resource-budget` question is explicitly decided":**
This is a documentation/policy decision (see `investigation.md`'s Resource-Budget Question section),
not itself a new test — Plan/Implement should record the chosen option (A/B/C) and, if Option A or
B, add the corresponding marker/directory-override with a comment linking back to this ticket. No
new automated test is strictly required for AC3, but if Option A (per-test marker) is chosen:

- **Test name**: `test_resource_budget_marker_applies_large_to_named_grade_stability_tests` (or
  similar)
  - **Category**: architecture guard
  - **Verifies**: the 6 named tests below (and any future test matching the same
    3-trial/500-1000-tick `_run_engine` shape) are correctly marked/configured to run under
    `--resource-budget large`, not silently falling back to the 60s `medium` default.
  - **Location**: `tests/conftest.py`'s own test coverage, if one exists, or
    `tests/tools/test_conftest_resource_budget.py` (new)

**AC4 — "The 6 tests named in Scope are re-run under the fix and their outcome ... is reported":**
Not a new test to write — this is a re-run-and-report action item for Implement/Verify, using the
existing 6 tests unmodified (unless their own floor/tolerance values turn out to need a genuine
re-baseline once they can complete cleanly, which would be its own follow-up ticket per the parent
ticket's precedent, not a change made under this ticket).

## Scoped Pytest Commands

Regression verification (run relevant existing tests before claiming completion — do not run
`pytest tests/`):

```bash
# Root cause #1 surface (replay/chunk rotation)
.venv/bin/python3 -m pytest tests/unit/kernel/test_replay_chunk_rotation.py \
  tests/unit/kernel/test_replay_contract.py tests/unit/kernel/test_replay_overflow.py \
  tests/unit/kernel/test_replay_pressure.py tests/unit/kernel/test_replay_shutdown_budget.py \
  tests/unit/engine/test_replay_backpressure.py tests/unit/engine/test_resource_budget_gate.py \
  tests/certification/test_artifact_budget.py -q

# Root cause #2 surface (observability queue / EventRecorder / SimQ persistence)
.venv/bin/python3 -m pytest tests/unit/observability/ tests/simulation_quality/ \
  tests/perf/test_simq_isolation_overhead.py -q

# If CanonicalStateHasher cadence is touched: determinism/replay/checkpoint blast radius
.venv/bin/python3 -m pytest tests/integration/kernel/ tests/unit/core/test_engine_integrity.py \
  tests/unit/core/test_entity_integrity.py tests/unit/core/test_operational_flags.py \
  tests/unit/engine/test_hash_scheduler.py \
  tests/unit/domains/progression/test_progression_decision_canonical_hash.py -q

# Soft-monitor world-assembly suite (alert-only per regression_policy.md §3)
.venv/bin/python3 -m pytest tests/unit/worldassembly/test_corpus_diversity.py -q --resource-budget large

# AC4 — the 6 explicitly-deferred, previously-timing-out tests, once a fix lands
.venv/bin/python3 -m pytest \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_simq_routing_test_seed42_1000t_cognition_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_hero_guild_routing_seed42_1000t_cognition_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_unit_selfmodel_pilot_seed42_1000t_cognition_economy_narrative_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed42_1000t_social_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_seed123_1000t_social_economy_grade_stability" \
  "tests/unit/worldassembly/test_corpus_diversity.py::test_urban_political_selfmodel_probe_seed42_200t_social_world_grade_stability" \
  -q --resource-budget large
```

Never: `pytest tests/`.

## Anti-Drift Test Guards

- **`INFRA-223`'s own `test_path`, `tests/integration/kernel/test_determinism_suite.py`, must stay
  green** if the `CanonicalStateHasher` cadence is touched — a passing perf fix that silently breaks
  determinism verification coverage would be exactly the kind of gate-integrity violation
  CLAUDE.md's Hard Rules forbid papering over.
- **A test that asserts `_rotate_chunk`'s persist write is still correctly non-blocking** (i.e. the
  fix for Root cause #1 must not accidentally make the *actual* chunk write synchronous while only
  removing the redundant pre-check — the existing async dispatch via `self._executor.submit(...)`
  must remain intact). `tests/unit/engine/test_replay_backpressure.py` and
  `tests/unit/kernel/test_replay_shutdown_budget.py` are the closest existing coverage for this;
  confirm they actually assert non-blocking behavior (not just final-state correctness) before
  relying on them as a guard.
- **A test confirming `QueueDrainWorker`'s drain loop still processes every queued envelope** even
  with a batched/deferred flush — a batching fix for Root cause #2 must not silently drop or reorder
  envelopes relative to the current at-most-10ms-cadence guarantee.
- **Do not let a perf-focused fix touch `tests/unit/worldassembly/test_corpus_diversity.py`'s
  floor/tolerance values** — this ticket is scoped to root-causing and fixing the backpressure/perf
  problem itself (per its own Out of Scope), not to re-baselining; a diff that edits floor constants
  in that file as part of "making tests pass" would be exactly the kind of scope-creep the parent
  ticket (`TCK-20260828-CORPUS-DIVERSITY-TOWN-CENTER-BASELINE-REFRESH`) explicitly avoided by
  deferring these 6 tests here in the first place.
- **The mid-resolution wall-clock throttle (`kernel.py` ~594-610) must remain untouched** — per
  Out of Scope and the Kernel Wall-Clock Throttle Relationship finding in `investigation.md`, any
  diff touching that specific block belongs to a different, already-deferred ticket, not this one.
