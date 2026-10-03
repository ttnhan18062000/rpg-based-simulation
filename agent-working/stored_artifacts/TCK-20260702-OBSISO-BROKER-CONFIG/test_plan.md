---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260702-OBSISO-BROKER-CONFIG
artifact_type: test_plan
tags: [observability, simulation-quality, broker-mode, redis, configuration, kernel]
---

# Test Plan — TCK-20260702-OBSISO-BROKER-CONFIG

## Regression Surface

Existing tests that must keep passing, unchanged, after the G1/G3 fix.

### Unit
- `tests/simulation_quality/test_feed.py` — all 12 tests, especially
  `test_build_feed_returns_inprocess_by_default`, `test_build_feed_returns_broker_feed`,
  `test_build_feed_returns_none_when_disabled`, `test_inprocess_feed_start_stores_hub_reference`,
  `test_broker_feed_skips_gracefully_when_redis_unavailable`. G1's fix changes
  `BrokerQualityFeed.__init__`'s and `build_feed_from_env()`'s stream_name *default value* —
  these tests must be checked for any hardcoded assumption of `"sim:events"` and updated in the
  same change if the default changes (see New Tests Required — some of these may need their
  literal expectations rewritten, not just re-run).
- `tests/simulation_quality/test_weights.py` — unaffected, but part of the same package; run to
  confirm no import-order regression from any `feed.py`/`config.py` edits.
- `tests/unit/observability/test_event_recorder_quality_fn.py::test_event_recorder_quality_fn_called_on_drain`
  — covers `INFRA-232`, must not regress (EventRecorder's `quality_fn` wiring is untouched by
  this ticket, but shares the same `kernel.py:227-269` block being edited for G3).

### Integration
- `tests/simulation_quality/test_kernel_simq_integration.py` — all 4 tests, explicitly required
  unchanged by the ticket's own AC #3:
  - `test_simq_hub_wired_into_kernel`
  - `test_no_second_drain_worker`
  - `test_event_recorder_worker_has_quality_fn`
  - `test_20_tick_run_produces_nonzero_tick_count`
  These all run with `QUALITY_FEED_MODE=inprocess` (fixture default,
  `test_kernel_simq_integration.py:19`) — in-process mode must be provably untouched by the G3
  fix (the fix only changes behavior when `_feed` is a `BrokerQualityFeed` instance).
- `tests/simulation_quality/test_broker_feed_integration.py` — both tests
  (`test_broker_feed_graceful_when_redis_unavailable`, `test_broker_feed_dedup_same_event_id`),
  gated by `REDIS_AVAILABLE=1` (module-level `pytestmark`, currently skipped in default CI). Run
  with `REDIS_AVAILABLE=1` if a Redis instance/fakeredis is available in the dev/CI environment
  used for verification; otherwise document the skip explicitly rather than silently passing over
  it. **Pre-existing bug found during investigation, out of this ticket's scope to fix but worth
  flagging to Plan**: `test_broker_feed_graceful_when_redis_unavailable` asserts
  `feed.health == "unavailable"` (line 33) comparing a bound method object to a string — this can
  never be true; the correct assertion is `feed.health()["status"] == "unavailable"`. Because the
  module is skipped by default, this has never actually executed. Do not silently fix this
  pre-existing bug as part of this ticket's diff unless Plan explicitly scopes it in (it's outside
  G1/G3, but blocks trusting this file as "the existing pattern to follow" for the new AC #1 test
  without a fix).

### Arena-Combat
- Not applicable — no combat-domain code is touched by this ticket.

## New Tests Required

1. **Test name**: `test_broker_stream_name_defaults_to_observability_config`
   **Category**: unit
   **Verifies**: with no `QUALITY_STREAM_NAME`/`SIM_STREAM_NAME`/`RPG_STREAM_NAME` env vars set,
   `build_feed_from_env()` (mode=broker) produces a `BrokerQualityFeed` whose `_stream_name`
   equals `ObservabilityConfig.get_stream_name()`'s default (`"simulation:events"`), not the old
   hardcoded `"sim:events"`. Also assert `QUALITY_STREAM_NAME` still overrides when explicitly
   set (explicit-override contract from ticket Scope item 1 must survive).
   **Location**: `tests/simulation_quality/test_feed.py` (extend existing file, follow the
   `monkeypatch.setenv`/`delenv` pattern already used by `test_build_feed_returns_broker_feed`).

2. **Test name**: `test_broker_url_defaults_to_observability_config`
   **Category**: unit
   **Verifies**: same as above but for `QUALITY_BROKER_URL` vs `ObservabilityConfig.get_redis_url()`.
   **Location**: `tests/simulation_quality/test_feed.py`.

3. **Test name**: `test_quality_worker_stream_name_defaults_to_observability_config`
   **Category**: unit
   **Verifies**: `QualityWorker.__init__` (or whatever helper it's refactored to call) resolves
   the same default as `BrokerQualityFeed`/`build_feed_from_env()` — no independent
   `"sim:events"` literal survives in `worker.py`.
   **Location**: new or extended `tests/simulation_quality/test_worker.py` (check whether this
   file exists yet — not read during investigation; if absent, create it, since `worker.py`
   currently has no dedicated test file found under `tests/simulation_quality/`).

4. **Test name**: `test_no_env_vars_set_broker_mode_producer_consumer_share_stream_name`
   **Category**: integration
   **Verifies**: AC #1 exactly — with **no** `QUALITY_*`/`SIM_STREAM_*` env vars set,
   `QUALITY_FEED_MODE=broker` + `SIM_STREAM_BACKEND=redis`, an event published via
   `get_event_stream_adapter().publish(event)` (producer path) is consumed by a `QualityWorker`
   (or its `BrokerQualityFeed`) without manually aligning stream names. Use fakeredis or a
   `REDIS_AVAILABLE`-gated `@pytest.mark.slow` test, following
   `test_broker_feed_integration.py`'s existing skip-gate pattern (fix or avoid its bound-method
   `health` bug noted above rather than copying it forward).
   **Location**: `tests/simulation_quality/test_broker_feed_integration.py` (extend) or a new
   `tests/simulation_quality/test_broker_config_unification.py` if the existing file's
   skip-by-default gating makes it unsuitable for the intended CI-running form of this test —
   Plan should decide which, since AC #1 explicitly says "following the existing pattern."

5. **Test name**: `test_kernel_broker_mode_builds_zero_quality_hub`
   **Category**: integration
   **Verifies**: AC #2, first half — with `QUALITY_FEED_MODE=broker` set on a `Kernel.__init__`
   call, `kernel._quality_hub is None` (or an equivalent "hub absence" contract the fix settles
   on) even though quality scoring is nominally enabled. Mirror
   `test_kernel_simq_integration.py`'s `minimal_kernel` fixture shape but override
   `QUALITY_FEED_MODE=broker` instead of `inprocess`.
   **Location**: `tests/simulation_quality/test_kernel_simq_integration.py` (extend) — keep in
   the same file so the in-process vs broker contrast is visible side by side, or a sibling
   `test_kernel_simq_broker_mode.py` if Plan prefers isolating broker-specific kernel tests
   (broker tests may need Redis-absent handling that in-process tests don't).

6. **Test name**: `test_kernel_broker_mode_starts_zero_consumer_threads`
   **Category**: integration / architecture guard
   **Verifies**: AC #2, second half — after `Kernel.__init__` with `QUALITY_FEED_MODE=broker`, no
   thread named `"broker-quality-feed"` (the exact name `BrokerQualityFeed.start()` uses,
   `feed.py:107`) exists in `threading.enumerate()`. This is the concrete "assert via thread
   names" mechanism the AC names.
   **Location**: same file as test 5.

7. **Test name**: `test_kernel_inprocess_mode_unaffected_by_g3_fix`
   **Category**: architecture guard
   **Verifies**: explicitly re-assert (not just rely on unchanged existing tests) that
   `QUALITY_FEED_MODE=inprocess` still produces a non-None `kernel._quality_hub` with all 10
   scorers present after the fix — guards against an implementation that over-broadly suppresses
   hub construction for *any* non-default feed mode instead of specifically broker mode.
   **Location**: `tests/simulation_quality/test_kernel_simq_integration.py`.

8. **Test name**: `test_quality_scoring_disabled_still_wins_in_both_modes`
   **Category**: unit
   **Verifies**: AC #4 — `QUALITY_SCORING_DISABLED=1` produces `build_feed_from_env() is None`
   (already covered by `INFRA-233`/`test_build_feed_returns_none_when_disabled`) **and**, new for
   this ticket, that the kernel builds zero hub / zero threads in *both*
   `QUALITY_FEED_MODE=inprocess` and `QUALITY_FEED_MODE=broker` when disabled is set — i.e. the
   disabled short-circuit and the new broker-mode short-circuit compose correctly rather than one
   masking a bug in the other.
   **Location**: `tests/simulation_quality/test_kernel_simq_integration.py` or `test_feed.py`.

## Scoped Pytest Commands

```bash
# Core SimQ feed/worker/kernel-wiring surface (primary regression + new tests)
pytest tests/simulation_quality/ -m "not slow" -v

# Redis-gated broker integration tests (only if Redis/fakeredis available in the run environment)
REDIS_AVAILABLE=1 pytest tests/simulation_quality/test_broker_feed_integration.py -v

# Quality-fn wiring guard in the observability queue (adjacent, shares the touched kernel.py block)
pytest tests/unit/observability/test_event_recorder_quality_fn.py -v

# Full observability domain sweep if config.py's get_stream_name/get_redis_url resolution
# order changes in a way that could affect the producer side
pytest tests/unit/observability/ -m "not slow" -v
```

Never run `pytest tests/` — scope to `tests/simulation_quality/` (primary), plus the two
`tests/unit/observability/` targets above since `src/observability/config.py` and
`src/engine/kernel.py`'s SimQ block are shared surfaces.

## Anti-Drift Test Guards

- `test_kernel_simq_integration.py`'s existing 4 tests, run with `QUALITY_FEED_MODE=inprocess`,
  are the primary guard against the G3 fix accidentally changing in-process behavior — treat any
  failure here as a hard stop, not a test to "update."
- New test 7 (`test_kernel_inprocess_mode_unaffected_by_g3_fix`) exists specifically to catch a
  fix that branches on "is broker mode requested at all" instead of "is the resolved feed
  concretely a `BrokerQualityFeed`" — e.g. an implementation that checks
  `os.environ.get("QUALITY_FEED_MODE") != "inprocess"` (wrong: would also suppress the hub for a
  future third mode) instead of `isinstance(feed, BrokerQualityFeed)`.
  `test_quality_feed_mode_enum_values` (`test_feed.py:96-98`) documents the only two valid modes
  today, but the guard should still test the mechanism, not just the current enum's cardinality.
- `INFRA-233`'s short-circuit (`QUALITY_SCORING_DISABLED=1` → `build_feed_from_env()` returns
  `None` unconditionally, checked first) must remain the very first branch — new test 8 exists to
  catch a refactor that accidentally moves the disabled-check below new mode-routing logic.
- G2 guard (do not accidentally fix in this ticket): no new test should assert `QualityWorker`
  builds all 10 scorers — that would silently absorb `TCK-20260702-OBSISO-WORKER-PARITY`'s scope
  into this ticket. If an implementer's diff touches `worker.py`'s `scorers = [AgencyScorer(...),
  CombatScorer(...)]` line for any reason other than the stream-name default, that's scope creep.
- G5 guard (do not add a benchmark): no new test in this plan measures tick latency or CPU
  overhead between modes — that belongs to `TCK-20260702-OBSISO-ISOLATION-PROOF`. A future
  implementer adding a "broker mode is faster" perf assertion here would be scope creep.
