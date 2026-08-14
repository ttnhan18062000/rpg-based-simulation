---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST
artifact_type: test_plan
tags: [simulation-quality]
---

# Test Plan — TCK-20260711-SIMQ-TRACEABILITY-PATH-INTEGRATION-TEST

## Regression Surface

Existing tests that must keep passing (nothing in this ticket's scope changes production code, so
this is a pure addition — but the new test shares fixture patterns with these and must not
interfere with them, e.g. via leftover `data/runs/` state or env var leakage).

**Unit**
- `tests/simulation_quality/test_combat_scorer.py` — `CombatScorer` behavior for
  `entity_killed` / `combat_hard_law_violation`, whichever event_type the new test injects. Must
  confirm the exact weight/sign assumptions used in the new test still hold.
- `tests/simulation_quality/test_accumulator.py` — in particular
  `test_duplicate_event_id_scored_once` and worst_events sort-order tests
  (`PillarAccumulator.add`), since the new test depends on `worst_events` population and ordering.
- `tests/simulation_quality/test_persistence.py` — `QualityPersistence` write/atomic-rename
  behavior; the new test does not modify this class but shares its on-disk contract.

**Integration**
- `tests/simulation_quality/test_kernel_simq_integration.py` — the direct reference pattern this
  new test extends (minimal Kernel + injected `SimulationEvent`s). All 4 existing tests
  (`test_simq_hub_wired_into_kernel`, `test_no_second_drain_worker`,
  `test_event_recorder_worker_has_quality_fn`, `test_20_tick_run_produces_nonzero_tick_count`)
  must continue to pass unmodified.
- `tests/simulation_quality/test_quality_hub_integration.py` — `QualityHub.on_envelope()` routing,
  accumulation, persistence-write, error isolation, disable-mechanism tests (`INFRA-236`
  parity entry). The new test must not weaken or duplicate these — it composes them at the
  kernel-integration level, not the hub-unit level.

**Observability (adjacent, must not regress)**
- `tests/unit/observability/test_event_recorder_quality_fn.py` — `EventRecorder`→`quality_fn`
  wiring (`INFRA-2xx` entry, `test_event_recorder_quality_fn_called_on_drain`).
- Any test asserting `EventRecorder._write_envelope_to_file` schema
  (`event_id`, `run_id`, `tick`, `entity_id`, `event_type`, ...) — the new test's
  `simulation_events.jsonl` parsing must match that exact schema (field name `event_id`, one JSON
  object per line).

## New Tests Required

Per Acceptance Criteria (all three map to one new test file,
`tests/simulation_quality/test_traceability_path.py`):

1. **`test_worst_event_id_resolves_in_simulation_events_jsonl`**
   - Category: integration
   - What it verifies: builds a minimal `Kernel` (same construction pattern as
     `test_kernel_simq_integration.py::minimal_kernel`), injects at least one `SimulationEvent`
     with `event_type="combat_hard_law_violation"` (unconditional negative-delta trigger, no
     tick-gate dependency — see investigation.md Risk #2) via
     `kernel._event_recorder.record(...)`, waits for the async drain worker, then:
     1. Calls `kernel._quality_hub.get_quality_report()` and asserts at least one pillar's
        `worst_events` is non-empty (explicit precondition assertion — do not silently no-op if
        empty, per investigation.md's Anti-Drift Hazards).
     2. Picks `worst_events[0].event_id` from the COMBAT pillar (`report.pillars["COMBAT"]` —
        string key, not `PillarId.COMBAT`).
     3. Reads back `simulation_events.jsonl` from the run's actual directory
        (`data/runs/{run_id}/simulation_events.jsonl` per investigation.md Risk #1's resolved
        approach — see Scoped Pytest Commands note on cleanup) as JSONL, and asserts the picked
        `event_id` appears as the `event_id` field of at least one line.
   - Where: `tests/simulation_quality/test_traceability_path.py`

2. **`test_worst_event_id_matches_originating_envelope_exactly`** (tightens #1 beyond "appears
   somewhere" to "is the correct originating event, not a coincidental match")
   - Category: integration
   - What it verifies: the specific `simulation_events.jsonl` line matching the picked `event_id`
     has `event_type`, `tick`, and `entity_id` consistent with what was injected (not just that
     *some* line has a matching `event_id` string — guards against a trivial pass from a
     hypothetical future bug that duplicates event_ids or writes them out of order).
   - Where: `tests/simulation_quality/test_traceability_path.py`

3. **`test_run_directory_cleaned_up_after_test`** (anti-drift guard specific to the run_dir
   resolution finding in investigation.md Risk #1)
   - Category: integration / hygiene guard
   - What it verifies: after the fixture's teardown (whether via `kernel.shutdown()` +
     `shutil.rmtree` in a fixture finalizer, or equivalent), the run directory used by the test no
     longer exists — prevents this new test from silently accumulating stray `data/runs/{run_id}/`
     directories across CI runs (see investigation.md's recommended approach (a)).
   - Where: `tests/simulation_quality/test_traceability_path.py` (can be folded into the primary
     fixture's teardown assertion rather than a separate test function, at implementer's
     discretion — the acceptance criterion is that no directory is left behind, not that a
     specific test function name exists for it).

Documentation/ledger updates required alongside the tests (not pytest-verifiable, tracked here for
completeness against the ticket's Acceptance Criteria):
- `docs/simulation_quality/quality_scoring_contract.md` §12 Traceability item 3: `[ ]` → `[x]` with
  citation to `tests/simulation_quality/test_traceability_path.py`.
- `docs/parity_ledger/infrastructure.yaml`: new entry `INFRA-268` (next available ID after
  `INFRA-267`), `status: verified`, `test_path: tests/simulation_quality/test_traceability_path.py`.

## Scoped Pytest Commands

```
pytest tests/simulation_quality/test_traceability_path.py -v
pytest tests/simulation_quality/test_kernel_simq_integration.py tests/simulation_quality/test_quality_hub_integration.py tests/simulation_quality/test_traceability_path.py -v
pytest tests/simulation_quality/ -q
```

Never `pytest tests/`. The last command (full `tests/simulation_quality/` scope, ~456+ tests) is
the appropriate final regression gate for this ticket per the project's domain-scoping rule — do
not run the repo-wide suite.

**Cleanup note**: if the new test uses a real `run_id` under `data/runs/` (recommended approach in
investigation.md), run `find data/runs -maxdepth 1 -type d` before and after the scoped test run to
confirm no directory survives the test's own teardown; if one does, treat it as a test bug, not an
acceptable side effect deferred to ticket-close cleanup.

## Anti-Drift Test Guards

- **Vacuous-pass guard**: `test_worst_event_id_resolves_in_simulation_events_jsonl` must assert
  `worst_events` is non-empty *before* asserting the cross-reference — a test that only checks "if
  worst_events, then event_id resolves" would pass vacuously if the negative-delta trigger silently
  stopped firing (e.g. from an unrelated future scoring-weight change flipping
  `combat_hard_law` to a non-negative value). Assert non-empty explicitly, with a descriptive
  failure message naming the injected event_type, mirroring the existing project convention in
  `test_kernel_simq_integration.py::test_20_tick_run_produces_nonzero_tick_count`.
- **Exact-match guard** (test #2 above): prevents a regression where `event_id` becomes
  non-unique or where `simulation_events.jsonl` write order diverges from scoring order — a naive
  "event_id string appears somewhere in the file" check would not catch either.
- **No-tmp_path-illusion guard**: do not let the new test's fixture set `QUALITY_RUN_DIR` and
  assume it is honored — per investigation.md Risk #1, that env var is inert for the in-process
  kernel path. A future reviewer copying the `test_kernel_simq_integration.py` fixture verbatim
  would silently reintroduce a test that reads from the wrong (empty) `tmp_path` directory and
  either fails opaquely or (worse) is skipped/no-op if wrapped in a try/except. The new test's
  fixture must read from wherever `EventRecorder`/`QualityPersistence` actually resolved
  `run_dir_str` to (`kernel._event_recorder.filepath` is available directly on the recorder object
  post-construction and is the most robust way to avoid hard-coding the path resolution logic a
  second time in the test).
- **Directory-leak guard** (test #3 above): catches silent accumulation of `data/runs/{run_id}/`
  directories if a future edit removes the fixture's cleanup step.
- **No-scope-creep guard**: the new test file must not add coverage for §9 steps 4-6
  (`cognition_graph_snapshots.jsonl`, `world.yaml`/compiled state, root-cause library) — if a
  reviewer sees assertions touching those artifacts in
  `tests/simulation_quality/test_traceability_path.py`, that is out-of-scope creep per the
  ticket's Out of Scope section, not a bonus.
