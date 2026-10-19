---
status: active
layer: architecture
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261019-D80B-ENGINE-STOPS-IMPORTING-SIMQ-POST-APPLY-OBSERVER-HOOK
date: 2026-10-19
---

# Investigation: D80 B, the engine stops importing SimQ

Read-only, on origin/main 864f7b281. Nothing implemented.

## 1. Every `src.simulation_quality` import from `src/engine` and `src/core`

`src/core`: none. `src/engine`: only `src/engine/kernel.py`, all function-local, inside `Kernel.__init__`, lines 235-243:

| line | import | use |
|---|---|---|
| 235 | `feed.build_feed_from_env`, `feed.BrokerQualityFeed` | choose the feed from `QUALITY_SCORING_DISABLED` and `QUALITY_FEED_MODE` (`inprocess` default, `broker`) |
| 240 | `weights.ScoringWeights` | `ScoringWeights.load("config/simulation_quality/{scoring_weights,grade_thresholds,detection_params}.yaml", $QUALITY_PROFILE)` |
| 241 | `quality_hub.QualityHub` | the scoring hub |
| 242 | `persistence.QualityPersistence` | writes `quality_scores.jsonl` and the report in the run directory |
| 243 | `scorers.build_all_scorers` | the ten pillar scorers |

Other `src` modules that name `simulation_quality` outside the package: `src/api/dependencies.py` (TYPE_CHECKING only: `QualityHub`, `QualityPersistence`) and `src/api/server.py:168` (the quality routes). Those are API composition, not engine. `src/rendering/*` and `src/domains/optimization/feature_flags.py` mention it only in comments and config paths. Nothing else imports it, so the contract "src.engine must not import src.simulation_quality" has exactly one violator.

## 2. How the kernel wires SimQ today

Construction (`kernel.py:230-272`), gated on `obs_mode != OFF`:
1. `_feed = build_feed_from_env()`; `None` when `QUALITY_SCORING_DISABLED=1`.
2. If the feed is not a `BrokerQualityFeed` (in-process mode), build `ScoringWeights`, `QualityHub(scorers, weights, QualityPersistence(run_dir), run_id)`; a build failure is caught and logged, SimQ is then off for the run. In broker mode no hub is built (the external QualityWorker scores) and `_quality_hub` stays `None`.
3. `quality_fn = hub.on_envelope` goes into `EventRecorder(..., quality_fn=...)`.
4. After the recorder exists: `feed.start(hub)`.

Flow of data: `EventRecorder` hands envelopes to its background drain worker (`observability/queue.py:146`, `quality_fn(env)` on the worker thread) and again in the final synchronous drain (`event_recorder.py:373-381`). So SimQ consumes event envelopes after the tick, off the tick thread. It reads no state and writes none: it cannot feed back into the hash. That is why a hash-identity acceptance criterion is meaningful and cheap.

Teardown (`kernel.py:1148-1170`), order matters (TCK-20260830-KERNEL-SHUTDOWN-PERSISTENCE-DRAIN-ORDERING-HAZARD): (1) `feed.stop()`; (2) `event_recorder.shutdown()`, which joins the drain worker and does its final synchronous drain; (3) only then `hub.get_quality_report()`, `persistence.write_report()`, `persistence.shutdown()`.

Exposure: `Kernel.quality_hub` property (kernel.py:329-333) read by `src/api/server.py:63-65` (`set_quality_hub`, `set_quality_persistence(hub._persistence)`), which fills `src/api/dependencies.py` for the quality routes. Slots `_quality_hub`, `_quality_feed` (kernel.py:56).

## 3. The ticket's phrase "post-apply observer hook" versus the code

SimQ is not a state observer. It consumes already-extracted event envelopes. The hook that fits is therefore an **envelope sink with a run lifecycle**, not a `(prior, current, update)` state observer. Two consequences:
- RunLedger and DeathLedger do **not** move onto this hook. They are state-diff producers (`RunLedger.observe(prior, current, update)`, `DeathLedger.observe`) called from `observability/event_recorder.py:extract_events` (line 419) with StarvationRecorder; their output is events that SimQ (and the lossless file) then read. They import nothing from SimQ or the kernel. The ticket's "move the RunLedger onto the same hook if that fits" does not fit, and moving it would change event production order. Recommend: leave them, say so in the closing record.
- Other things attached to the kernel today: `_event_listeners` (a list of `Callable[[List[events]], None]` set by the API engine manager, `engine_manager.py:140`, and used by `ws/stream.py`) is an existing in-tick event fan-out. It carries events, not envelopes, and runs on the tick thread, so it is not a substitute: SimQ must keep running off the tick thread.

## 4. Composition roots (who builds a Kernel)

`Kernel(` is constructed in: `src/api/engine_manager.py:139` (the live API), `src/cli/entry.py:241`, `src/observability/{sweeper.py:198, readiness/harness.py:105, mining/controller.py:225}`, `src/perf/{long_run_harness, bench_harness, profile_governance}.py`, `src/lab/orchestrator.py`, `src/domains/campaigns/runner.py`, `src/engine/{scenario_runtime,scenario_checkpoint}.py`, `src/certification/harness.py`, and tools `calibrate_simq.py`, `entity_lifecycle_score.py`, `balance_measure.py`, `execution_census.py`, `personality_audit.py`, `test_architecture/rpg_gate_run.py`, `perf/*`, `release/generate_release_proof.py`. The paired tool is `tools/rpg_measure/arm_child.py` (runs a kernel in the arm tree).

Today **every** one of these gets SimQ for free whenever observability is not OFF and the env allows it. The readers of SimQ output are few: the API (`server.py`, via `kernel.quality_hub`), `tools/calibrate_simq.py`, `evaluate_simq.py`, `simq_long_run_observation.py`, `calibrate_rendering.py`, `test_architecture/simq_audit_rows.py`, `observability/mining/{priority,auditor}.py`, `observability/understanding/quality/`, and about nine tests in `tests/simulation_quality/` plus `tests/perf/test_simq_isolation_overhead.py`.

Tests that touch the kernel's SimQ attributes directly (must change): `tests/simulation_quality/test_kernel_simq_integration.py` (`_quality_hub`, `_quality_feed`, lines 43, 50, 90, 155, 198, 221-224, 245), `test_traceability_path.py` (73, 93, 157, 219), `tests/perf/test_simq_isolation_overhead.py:128`.

## 5. Behaviour that must be preserved

- With observability ON and in-process mode: same hub, same scorers, same `quality_scores.jsonl` and report, same shutdown order.
- Observability OFF: no SimQ (today the whole block is skipped).
- Broker mode: no in-engine hub, feed object still started/stopped; `quality_hub` is `None`.
- A hub-construction failure is non-fatal and only disables SimQ for the run.
- `QUALITY_SCORING_DISABLED=1` still disables it.
- Final state hash: unchanged (SimQ never writes state). The report: unchanged on one calibration run.

## 6. Risks and open decisions for the planner

1. **Default behaviour of the ~20 other Kernel callers.** If SimQ becomes opt-in at the composition root, harnesses that registered nothing silently stop producing `quality_scores.jsonl`. Decide per caller group which keep it; the plan defaults to: API, CLI, calibrate/evaluate/long-run tools and the SimQ tests register it; perf, certification, scenario and gate/paired runs do not (they ignore the output). An alternative is a single `default_observer_factories()` helper in `src/simulation_quality/` that roots call; that keeps the choice explicit without a global.
2. **No hidden global registration.** A module-level registry that SimQ fills on import would be implicit durable behaviour (CLAUDE.md); the plan uses an explicit constructor argument instead.
3. **Hook name.** "Post-apply observer" is a misnomer for an envelope sink; the plan names it `RunObserver` and states why.
4. Memo row 82 guards (rpg-designer-after-v1 ff0a4a9df): this ticket adds no typed record and no event, so guard 1 is satisfied trivially; guard 2 (reported, not required) does not apply. Its SimQ criterion is "the report is unchanged".
