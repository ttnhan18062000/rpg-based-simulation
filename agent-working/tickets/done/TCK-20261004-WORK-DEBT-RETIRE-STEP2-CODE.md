---
status: historical
layer: performance
authority: P2
audience: agent
ticket_id: TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE
phase: done
date: 2026-10-04
tags: [performance, engine]
---

# TCK-20261004-WORK-DEBT-RETIRE-STEP2-CODE

## Title
Work-debt retirement step 2: remove `work_debt` and the branches that can never fire

## Status
DONE

## Tier
standard

## Type
refactor

## Priority
P2

## Request Summary
On 2026-10-04 the owner chose to retire work debt, in two steps
(`TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`). No producer is to be built: "overflowed
work" has no deterministic definition, and feeding wall-clock-driven shedding into it would break
PERF-D1 A1. This is step 2. It removes the field and every branch that can only ever see 0. It
touches gated files, so it is BLOCKED until the RPG-core entry gate lifts.

## Scope
The reader list is in the investigation ticket, AC2. Remove:
- `AuthoritativeState.work_debt` (`state.py`), with its canonical-hash entry (`checkpoint.py`
  `data["work_debt"]`). This changes the proof digest's input, so it needs a scheme-version
  decision under PERF-D5 (for example `flat-sha256-v2`) and a baseline note
- `StateUpdate.work_debt_updates` and the `apply.py` clamp
- the kernel's `work_debt_updates` merge and `debt_ratio`
- the debt half of `global_salience`. Coordinate with `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`:
  if that fix lands first, it removes the salience term entirely
- the governor and phase_governor debt thresholds and recovery limit, and the `work_debt_total`
  signal
- the `DRAIN_DEBT` scheduler, executor and validator path, including the per-subsystem rule from
  #319. Update the T04 analysis in `deterministic_execution.md`
- `max_work_debt` in the profiles, `PressureInjector.inject_work_debt`, and the
  `WORK_DEBT_BUILDUP` certification scenario
- reporting surfaces: API, snapshot, Prometheus `sim_work_debt_total`, certification model, the
  root-cause rule
- Replace the guard test `test_work_debt_stays_empty_in_production.py` with a test that the field
  is gone
- **Added 2026-10-06 (owner decision, option (c) of `TCK-20261006-PERF-SCHEDULER-SHEDS-NOTHING-IN-SHIPPED-RUNS`):**
  the same PERF-D5 scheme bump also removes the never-wired periodic/opportunistic shedding path. That
  means: `state.periodic_due_ticks` (hashed, `checkpoint.py` about 116) and `StateUpdate.periodic_updates`
  (no producer), `PeriodicDefinition` and the periodic branch of `DeterministicScheduler.select_work`
  (unless a real task has been registered by then), the empty `allow_opportunistic` branch, and the
  unread `diagnostic_verbosity` / `metrics_detail` policy fields. It also fixes two misleading comments,
  `src/engine/observability.py:32` and `src/core/governance.py:45`: the counter counts only scheduler
  drops. Update the mechanism tests that register test-only periodic definitions (`test_degradation_order`,
  `test_scheduler_contract`, `test_work_classes`, `test_signal_truth`, `test_deferred_work_debt`, the
  work-debt guard) to match. The evidence is in that ticket's stored investigation.

## Out of Scope
- Any producer, or any new deferred-work design (PERF-D3: needs its own feature contract)

## Acceptance Criteria
1. `git grep -n work_debt -- src` is empty, or each remaining reference is listed with a reason
2. Proof digest scheme versioned, with a baseline / replay compatibility note
3. Governor mode behaviour is unchanged on non-combat runs (it never read a non-zero value)
4. Docs, parity ledger and the Prometheus metric list are updated

## Related Tickets
- `TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION`, `TCK-20261004-WORK-DEBT-RETIRE-STEP1-DOCS`
- `TCK-20261003-SALIENCE-WALL-CLOCK-PRICE-COUPLING`, `TCK-20261004-PERF-M1-VALIDATOR-ONE-SYSTEM-RESULT-PER-SUBSYSTEM`

## Related Docs
- `docs/architecture/performance_optimization_decisions.md` (PERF-D3, PERF-D5)
- `docs/engine/deterministic_execution.md`

## Related Stored Artifacts
- `agent-working/stored_artifacts/TCK-20261004-WORK-DEBT-NEVER-ACCUMULATES-IN-PRODUCTION/`

## Related Code Areas
- `src/core/state.py`, `src/engine/apply.py`, `src/engine/kernel.py`, `src/engine/governor.py` (all gated)
- `src/engine/phase_governor.py`, `src/engine/scheduler.py`, `src/engine/executor.py`,
  `src/core/protocol_validator.py`, `src/engine/checkpoint.py`, `src/certification/`, `src/config/profiles.py`

## Assumptions / Open Questions
- BLOCKED by the RPG-core entry gate (it edits gated core files). Code-health gates are blocking
  from 2026-10-18, so run `make code-health` and `make typecheck-py` before the PR

## Implementation Notes
- **2026-10-08, design only (perf-planner dispatch):** `investigation.md` (reader and writer inventory against `origin/main` `5e0994837`), `plan.md` (files by gate class, the PERF-D5 owner question, commit order, estimate, risks, docs) and `test_plan.md` (every pinned hash and test that moves) are written in `agent-working/staging_artifacts/`. No `src/` or `tests/` edit. The ticket stays INPROGRESS until the RPG side opens the Phase B slot (rpg-planner posts that the free-meal / decision-27 PR merged, est. week of 2026-10-12, at most 5 working days).
- **2026-10-09, Phase B built (gate item 7, owner decisions 2026-10-08: Q1 `flat-sha256-v2`, Q2 extended file list, C0 approved).** One batch on `perf-retire-step2-design`, each commit green and reviewed by perf-planner before it was made: C0 tests-only prep (`475bebedb`, 34 files), C1 stop producing deferred and periodic work (`5a4b16ea4`), C2 remove the state fields and bump the scheme (`15c61f378`), C3 remove the signal, thresholds and reporting (`1ea7c6676`), C4 docs, parity and DEV-019 (`452f3be64`).
- **Design verification:** after merging `origin/main` `3ffa6b95b` the inventory was re-checked (61 `work_debt` hits in `src/` with the same per-file split; #457 only moved line numbers in `apply.py` and `scheduler.py`).
- **What the design had not found, found in the build:** (1) `src/domains/cooperation/phase.py` read `periodic_due_ticks` for a test-only OFF sentinel (the phase stays correct through its `hasattr` guard; the two tests that used the sentinel now use the real `ENABLE_SOCIAL_COOPERATION` switch); (2) a second literal of the scheme name, `tests/unit/engine/test_hash_scheduler.py:117`; (3) `test_milestone_a_closure.py` pinned exactly one `pass` in `scheduler.py` (the empty opportunistic branch), tightened to 0; (4) with the ID-zero system results gone the result sort key is unique, so the arrival-order test now asserts that no two results tie and keeps the instrument with non-vacuity checks.
- **Migration proof:** rebuilding the v1 form of the pinned fixture (`{**v2_data, "periodic_due_ticks": {}, "work_debt": {"A": 1, "B": 2}}`) reproduces the old v1 digest `ec75b106...` exactly, so `flat-sha256-v2` is v1 minus the two keys and nothing else changed.
- **AC1:** `git grep -n work_debt -- src` finds two comments only (`checkpoint.py:15`, which records what v2 removed, and the Prometheus numbering marker). **AC3:** the Live golden fixture (NORMAL, SURVIVAL, DEGRADED) passes with only the `work_debt_total` keys removed; `test_milestone_b_closure` pins modes.
- **Left as follow-ups (listed in DEV-019 and INFRA-429):** the unused `WorkClass` members and `ConcurrencyLaw` priorities; the dead `hasattr` guard in `cooperation/phase.py` (RPG side); the certification recovery rows' CERTIFIED status was not re-certified.

## Test Summary
- Per commit, each lane run as its own foreground step and read before the commit. Final tree (`452f3be64`): `tests/tools` in full 4735 passed, 0 failed (12.5 min); `tests/observability` in its own invocation, as CI runs it, 8 passed; docs, parity, static, architecture and `tests/unit/tools` 953 passed; at C3 the unit and integration lanes 2907 and 2293 passed. `uv run make code-health`: 0 new, 0 worse (91 improved at C3); `uv run make typecheck-py`: filter empty; the three perf inventories pass `--check`.
- New or rewritten proofs: `test_work_debt_is_gone.py`; `test_proof_digest_contract.py` (v2 pin, v1 migration proof, no removed fields); `test_tied_worker_result_order.py` (no ties, permutations really reorder, instrument fails when a level differs, entity 0 rejected); `test_protocol_validator_system_results.py`; the cooperation OFF pair through the pipeline switch; the governor-escalation event test through a Canonical profile.
- **Failures seen and proven pre-existing (reproduced on a worktree without these changes):** (1) `tests/api/test_observability_websocket.py` and `tests/api/test_ws_protocol.py` fail with connection refused to a local port; they need a live server (reproduced on the C2 commit). (2) `tests/observability/test_metrics_export.py::test_metrics_endpoint_integration` fails when run after `tests/unit/resource` and `tests/unit/observability` in one pytest invocation (a fixed port 8011 and a fixed 3 s sleep, per codebase-planner); it fails identically on plain `origin/main` `8754f94f2`, passes alone and in its own invocation, and CI runs those directories as separate steps; routed to testing. (3) `tests/tools/test_entity_lifecycle_score.py::...test_sandbox_world_800t_end_to_end_produces_sane_output` hit the 60 s per-test limit in one earlier run on this VM and times out identically without these changes; it passed in the final `tests/tools` run. (4) A one-off flake in `tests/integration/observability/test_event_recorder_live_publish.py::test_event_recorder_integration`, which passed alone, in its directory and in a rerun of the same lane.

## Files Changed
- `src/`: `core/state.py`, `core/updates.py`, `core/governance.py`, `core/worker_protocol.py`, `core/protocol_validator.py`, `engine/apply.py`, `engine/checkpoint.py`, `engine/kernel.py`, `engine/scheduler.py`, `engine/executor.py`, `engine/domain_logic.py`, `engine/policy.py`, `engine/governor.py`, `engine/phase_governor.py`, `engine/runtime_status.py`, `engine/signal_source.py`, `engine/observability.py`, `engine/worker_manager.py` (comment), `config/profiles.py`, `perf/profiles.py`, `perf/long_run_harness.py`, `certification/{models,harness,scenarios}.py`, `api/engine_manager.py`, `observability/prometheus_collector.py`, `observability/live/snapshot_provider.py`, `observability/understanding/rootcause/rules.py` (text only); `tools/perf/hash_callsite_inventory.py`.
- `tests/`: 34 files in C0, and about 50 more across C1 to C3 (deleted: six tests; replaced: the work-debt guard; rewritten: scheduler contract, validator, tie-order, proof digest, cooperation OFF pair; fixtures: the Live golden and the certification key list).
- `docs/`: `guidelines/intentional_divergences.md` (DEV-019), `parity_ledger/infrastructure.yaml` (INFRA-420, INFRA-223, INFRA-429), about twenty engine, observability, performance and architecture docs, the regenerated `hash_callsite_inventory.{md,json}`, `REGISTRY.yaml`.

## Completion Summary
Work debt and the never-wired periodic, deferred and opportunistic scheduling path are removed. The state, update, signal, thresholds, profile field, policy fields, worker-result fields, `DRAIN_DEBT` handling and reporting surfaces are gone; the scheduler produces only CRITICAL entity work with a constant-0 dropped count. The proof digest is `flat-sha256-v2` (v1 minus the two keys, proven by rebuilding the v1 form), the certification result schema is `certification_result.v2`, and the API payload and the Prometheus metric lose their debt field. Live governor behaviour is unchanged (golden fixture). Every pinned value that moved is listed in the PR body: `FIXTURE_DIGEST_V2`, the scheme literal in `test_hash_scheduler.py`, the hash-callsite inventory string and docs, the Live golden's `work_debt_total` keys and the certification key list.
