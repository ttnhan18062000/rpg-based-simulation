---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS
phase: done
date: 2026-10-09
tags: [testing, regression, determinism]
---

# TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS

## Title
A pinned harness runs each (world, seed) of the rpg gate in a fresh process and collects the metric documents

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Child 3 of TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC. The report is only meaningful if every run is reproducible and isolated. Two findings from 2026-10-09: process-global state leaks between tests in one process (the strict xfail, the CONFLICT-04 xdist red), and tests are governor-mode-sensitive. So: a fresh process per (world, seed), with everything pinned.

## Scope
1. A runner that reads rpg's gate config (worlds, seeds, ticks; rpg-owned content) and, for each (world, seed), starts a fresh Python process. Inside it: compile the world, build a Kernel with `PinnedNormalGovernor`, `LocalSequentialExecutor`, `audit_mode=True` and no tick budget; run the ticks; call rpg's metric module on the typed records; write the metric document (the epic's contract).
2. The harness hash: a stable hash of the harness code, the pin settings and the config, recorded in every document (it is what the baseline staleness uses).
3. Parallelism across processes, with a bounded worker count. Failures in one run do not stop the others; a crashed run yields a `no-data` document with the error.
4. Run directories go under `data/runs/` with a gate prefix and are cleaned by run id (CLAUDE.md cleanup rule).
5. Pooling: once every seed of a world has a document, call rpg's `pool(docs_for_one_world)` in a fresh process and write one world-level document of the pooled validity metrics. A world with any `no-data` seed gets `no-data` for its pooled metrics, never a partial pool. The harness never reads `counts`.
6. Measure and record the wall time and peak memory for the full v1 matrix on CI-class hardware. Child 5 sizes the matrix from it.

## Out of Scope
- The metric computation (rpg), evaluation and states (child 4).

## Acceptance Criteria
1. The same (SHA, world, seed) run twice gives byte-identical metric documents (a determinism test on a small world and few ticks).
2. A deliberately leaking stand-in (a module global mutated in run 1) does not affect run 2. This proves the process isolation.
3. A crashing run gives `no-data` with the error, and the others complete.
4. Cost measured and recorded in the ticket.
5. Standard close.

## Related Tickets
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC; depends on rpg's metric computation module (rpg-planner's ticket) for the real run. Until then a stub metric module that satisfies the contract.

## Related Docs
None.

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS/`

## Related Code Areas
- `tests/helpers/kernel_pinning.py`, `src/engine/kernel.py` (read only), `src/engine/executor.py` (read only), the new module under `tools/test_architecture/`

## Assumptions / Open Questions
- If rpg's metric module isn't ready, build and test against a stub that implements the contract; the real wiring is the last step.

## Implementation Notes
- `tools/test_architecture/rpg_gate_harness.py` (orchestrator) and `rpg_gate_run.py` (the child process). Documented in the harness docstring.
- Child: loads the world with `WorldRepository.load_world_with_context` + `WorldCompiler.compile` (the loader the pinned tests on main use, per rpg-planner), builds `Kernel(PROD_SMALL.model_copy(update={"max_tick_budget_ms": 1e9}), ..., governor=PinnedNormalGovernor(), executor=LocalSequentialExecutor(), flags={"audit_mode": True, "no_frame_pacing": True}, run_id=rpg-gate-<world>-s<seed>-<sha8>)`, ticks, shuts the kernel down (flushing the event stream), then calls the metrics module with `RunArtifacts(world, seed, ticks, sha, state, run_dir)`.
- Metrics module contract (rpg-planner, 2026-10-11): `compute(run_artifacts) -> document` and `pool(docs_for_one_world) -> [metric]`, planned at `src.observability.rpg_gate_metrics` (ticket TCK-20261009-RPG-REGRESSION-METRICS-COMPUTED-FROM-TYPED-RECORDS, not on main yet). The name lives in one constant, `DEFAULT_METRICS_MODULE`; the stub `tests/helpers/rpg_gate_stub_metrics.py` follows the contract (scope run|pooled) and is what the tests use. `compute` may return a whole document or a metric list; the harness keeps the metrics and writes the header.
- `run_matrix`: a thread pool starts one child per (world, seed) with a bounded worker count; a crash, non-zero exit, timeout or malformed document becomes a `no-data` document with the error; the others complete. After all seeds of a world, a fresh process pools them; any `no-data` seed gives a `no-data` pooled document with no partial pool. The harness never reads `counts`.
- Documents are written with sorted keys and carry no time or path (byte-identical per SHA, world, seed). Wall time and peak RSS go to `<doc>.cost.json` and `matrix.json`.
- `harness_hash`: sha256 over the three harness sources (including `kernel_pinning.py`), the pin settings, the config bytes and the metrics module's name and source (read from disk, never imported; `src/` is not hashed). Review (testing-planner): a changed metric definition therefore makes older baselines stale; the run id carries a per-invocation token.
- Run directories: removed by exact id after each run unless `--keep-runs`.
- The world, seed and tick lists are read from rpg's config (`load_config`); no world id is hard-coded.

## Test Summary
`pytest tests/unit/tools/test_rpg_gate_harness.py` 15 passed (about 24 s; real kernel runs of `sandbox_world`, 15 ticks): byte-identical documents for two runs of the same SHA/world/seeds (AC1); a module global mutated in one run does not reach the next, with an in-process negative control showing the stand-in does leak without isolation (AC2); a crashing seed gives `no-data` with the error and the other seeds complete (AC3); a world with a no-data seed gets `no-data` pooled metrics, a complete world pools in a fresh process; a missing world and a timeout are `no-data`; run directories are removed by id and cost is recorded outside the document; the harness hash changes with config, pins and code; the pins are the ones named; the metrics module is named in one place and the run hands it the event stream.

AC4 cost (measured 2026-10-11 on a busy 6-core, 8 GB development host with other sessions running, 4 workers, stub metrics, 5000 ticks, seeds 1-2): `sandbox_world` 200 s and 228 s per run, peak RSS 126-134 MB; `frontier_living_world` 603 s and 706 s per run, peak RSS 174-200 MB; the 4-run matrix took 706 s wall (27.7 CPU-min). A v1 matrix of 3 worlds x 5 seeds at 5000 ticks is then roughly 15 runs of 200-700 s each: about 100 CPU-minutes, about 25-30 min wall on 4 workers if the CI runner has 4 cores. This is NOT CI-class hardware: child 5 re-measures on the first dispatched run and sizes the matrix from that.

## Files Changed
- new: `tools/test_architecture/rpg_gate_harness.py`, `tools/test_architecture/rpg_gate_run.py`, `tests/helpers/rpg_gate_stub_metrics.py`, `tests/unit/tools/test_rpg_gate_harness.py`

## Completion Summary
The rpg gate harness runs each (world, seed) in a fresh pinned process, writes deterministic metric documents, turns crashes and timeouts into no-data documents, pools each world in a fresh process without ever making a partial pool, and records a harness hash. Gaps stated: rpg's metric module is not on main, so all of this ran against the contract stub; the cost figures are from a busy development host, not CI-class hardware.
