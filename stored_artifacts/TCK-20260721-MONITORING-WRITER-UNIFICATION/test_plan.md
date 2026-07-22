---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-MONITORING-WRITER-UNIFICATION
artifact_type: test_plan
tags: [monitoring, writer, unification]
---

# Test Plan — TCK-20260721-MONITORING-WRITER-UNIFICATION

## Regression Surface

Existing tests that must keep passing (all under `tests/tools/`, unit-style but exercising real
subprocess/file-IO, no `tests/integration/` or `tests/arena_combat/` overlap for this ticket):

**Writer call sites**
- `tests/tools/test_post_tool_hook.py` (166 lines, 6 tests) — all must still pass, but 5 of the
  6 need code changes as part of this ticket, not left untouched (see New Tests Required and
  Anti-Drift Test Guards): the 4 exact-field-set assertions (`test_single_writer_produces_one_
  well_formed_line`, `test_phase_and_agent_included_when_sidecar_present`,
  `test_phase_and_agent_default_to_none_on_partial_sidecar`,
  `test_concurrent_writers_produce_no_interleaved_or_truncated_lines`) only if
  `execution_id`/`provider` are added to `tools.jsonl` records (Plan decision, see
  investigation.md Risk #7); and `test_locking_failure_does_not_propagate` must be rewritten
  regardless (its fcntl-specific monkeypatch shim becomes a no-op once `fcntl` is no longer
  imported).
- `tests/tools/test_record_run.py` (168 lines) — CLI exit-code/validation contract, `duration_s`
  computation, single-record write shape. No exact-field-set assertion found — lower regression
  risk than `test_post_tool_hook.py`, but the write step itself changes (unlocked `open(...,
  "a")` → shared writer), so the underlying mechanism these tests exercise indirectly changes.
- `tests/tools/test_record_events.py` (257 lines) — CLI exit-code/validation contract, batch
  write, `tool_call_count`/`cost_proxy_score` computation, vocabulary-drift warnings. Same
  underlying-mechanism-changes-but-contract-doesn't note as above.

**Dashboard ingest**
- `tests/tools/test_agent_ops_dashboard_ingest.py` (642 lines) — must keep passing unmodified in
  its existing assertions (backward-compatible additive change only); new tests appended, not
  substituted.
- `tests/tools/test_agent_ops_dashboard_api.py`, `test_agent_ops_dashboard_api_boundary.py`,
  `test_agent_ops_dashboard_concurrency.py`, `test_agent_ops_dashboard_frontend_api_surface.py`,
  `test_agent_ops_dashboard_stats.py` — indirectly exercise `DashboardCache`/`ingest.py`; must
  keep passing since this ticket's `ingest.py` change is additive (new optional fields default
  `None`/labeled legacy).

**Prior-work regression proof**
- `tests/tools/test_monitoring_writer_lockfile_candidate.py` (3 tests) — the 3 candidate tests
  named in this ticket's own AC to "promote to production coverage." Promotion means new
  production-targeted tests are added (see New Tests Required) exercising the real
  `tools/agent-monitoring/` module — the candidate file's own tests may stay as-is (they are
  self-contained evidence-gathering tests against `tmp_path`, not broken by this ticket) or be
  retired if fully superseded; either is acceptable as long as the production module has its own
  equivalent coverage under `tests/tools/test_<writer_module_name>.py`.

## New Tests Required

Per AC — one entry per required new test:

1. **Production writer module — single-writer correctness**
   - Category: unit
   - Verifies: appending a record via the new shared writer produces exactly one well-formed
     JSON line, lock file is not left behind after success.
   - Location: `tests/tools/test_<writer_module_name>.py` (new file, name TBD by Plan)

2. **Production writer module — concurrency stress test**
   - Category: unit (process/thread-level stress, not a full integration test)
   - Verifies: AC's literal requirement — 0 corrupted/interleaved/lost lines across concurrent
     writers. Must be at least as strong as the existing 2 precedents (candidate: 10 threads × 20
     iterations = 200 writes; `test_post_tool_hook.py`'s real-subprocess version: 10 threads × 15
     iterations = 150 real subprocess invocations). Given this ticket unifies 3 call sites, this
     test should ideally simulate a **mixed** writer population (e.g. some invocations shaped
     like `post_tool_hook.py` writes, some like `record_run.py`/`record_events.py` writes, all
     targeting the writer module's shared append function directly) rather than only one call
     site's shape, since the AC's stress requirement is about the shared module, not any one
     caller.
   - Location: `tests/tools/test_<writer_module_name>.py`

3. **Production writer module — malformed partial line rejected downstream**
   - Category: unit
   - Verifies: a pre-existing malformed/truncated line in the target file does not block or
     corrupt subsequent valid appends, and `validate.load_jsonl` (or the module's own tolerant
     reader) rejects exactly the malformed line and parses every valid line — promoted from the
     candidate's `test_malformed_partial_line_is_rejected_by_downstream_reader`.
   - Location: `tests/tools/test_<writer_module_name>.py`

4. **Simulated stale-lock recovery**
   - Category: unit
   - Verifies: a lock file whose `mtime` is backdated past `stale_after_s` (5.0s per the
     candidate's constant, unless Plan changes it) is detected as stale, removed, and the waiting
     writer successfully acquires the lock and appends — without waiting the full stale threshold
     in wall-clock test time (backdate the file's `mtime` via `os.utime`, don't `time.sleep(5+)`
     in a test). Must also assert the *content* of the stale lock holder's abandoned write (if
     any) is not corrupted — i.e. this test proves recovery, not just eventual lock acquisition.
   - Location: `tests/tools/test_<writer_module_name>.py`

5. **Writer failure is non-blocking to the caller**
   - Category: unit
   - Verifies: forcing an internal failure (mock `os.open`/`os.remove`/the write step to raise)
     does not propagate an exception out of any of the 3 call sites in a way that would abort the
     calling workflow — for `post_tool_hook.py`: process still exits 0; for `record_run.py`/
     `record_events.py`: the *append* failure specifically (not a validation failure, which is
     legitimately still `sys.exit(1)`) does not crash with an uncaught traceback. Rewrite of
     `test_post_tool_hook.py::test_locking_failure_does_not_propagate` (fcntl-shim approach no
     longer applies) belongs here.
   - Location: `tests/tools/test_post_tool_hook.py` (rewritten test) +
     `tests/tools/test_record_run.py`/`test_record_events.py` (new tests) +
     `tests/tools/test_<writer_module_name>.py` (writer-module-level unit test of the same
     contract, independent of any one caller)

6. **Out-of-band diagnostic surface fires on writer failure, without re-entering the writer**
   - Category: unit
   - Verifies: whatever surface Plan chooses (structured stderr / separate health file) actually
     records the failure, and — critically — the diagnostic write itself does not go through the
     same writer's own append path (would recurse or silently lose the diagnostic on the same
     failure condition that triggered it). If a health file is chosen: assert the file exists,
     contains the failure signal, and is written via a plain/independent I/O path (not the
     lock-file protocol).
   - Location: `tests/tools/test_<writer_module_name>.py` or a new
     `tests/tools/test_monitoring_writer_diagnostics.py`, per Plan's module layout decision

7. **Single shared writer used by all 3 call sites (not 3 ad hoc implementations)**
   - Category: architecture guard
   - Verifies AC's literal "verified by code inspection/import graph" requirement — an AST or
     import-graph test asserting `post_tool_hook.py`, `record_run.py`, `record_events.py` each
     import the shared writer module's public append function, and that none of the 3 contains
     its own inline `os.open(..., O_CREAT | O_EXCL ...)` or `fcntl.flock` call (i.e. `fcntl` is no
     longer imported by any of the 3 once migration is complete). Mirrors the existing
     `tests/agent_orchestration/test_validator_no_network_calls.py`-style AST scan precedent
     already used elsewhere in this repo for "no forbidden call/import" guarantees.
   - Location: `tests/tools/test_<writer_module_name>.py` or a dedicated
     `tests/tools/test_monitoring_writer_single_source.py`

8. **Legacy record shapes still load with zero exceptions after additive fields land**
   - Category: unit
   - Verifies AC's "every legacy record shape (all 5+ documented generations) still loads
     successfully via `load_jsonl` with zero exceptions." Build a fixture `runs.jsonl` (or reuse/
     extend an existing fixture if one exists) with one line per each of the 6 shapes documented
     in `docs/agent-monitoring/schema.md`'s Known Limitations (5 allowlisted + the 1
     `TCK-20260623-TYPE-CHECKER` exception shape) plus one new-format line carrying
     `execution_id`/`provider` (and `ticket_id`, if Plan decides it's in scope), assert
     `validate.load_jsonl` returns all 7 records and raises nothing.
   - Location: `tests/tools/test_<writer_module_name>.py` or
     `tests/tools/test_agent_ops_dashboard_ingest.py` (whichever module actually exercises
     `load_jsonl` against the fixture — likely both, since `ingest.py` reuses the same function
     object)

9. **Dashboard ingest groups/filters by provider and execution_id, labels legacy records**
   - Category: integration (exercises `DashboardCache`/`ingest.py` end-to-end against a fixture
     corpus, not a pure unit test of one function)
   - Verifies: `get_runs()` (or wherever Plan lands the filter) accepts a `provider`/
     `execution_id` filter parameter and returns correctly filtered results against a fixture
     corpus mixing legacy (no `provider`/`execution_id`) and new-format records; legacy/unknown
     records are visibly labeled (not silently dropped, not erroring) in the returned model.
   - Location: `tests/tools/test_agent_ops_dashboard_ingest.py`

10. **Entry/exit-criterion manifest diff — zero unexpected changes**
    - Category: integration (exercises the real `agent-monitoring/*.jsonl` files, or a realistic
      copy of them, through the actual migration diff)
    - Verifies: `manifest.capture_lines()` called before any writer-file change, then again after
      full implementation, and `manifest.assert_prefix_preserved(pre, post)` raises nothing —
      i.e. this is closer to a Verify-phase gate check than a conventional pytest unit test, but
      should still have an automatable form (e.g. a script or a test fixture that snapshots a
      *copy* of the real corpus, runs a representative sequence of new-writer appends against the
      copy, and asserts the prefix-preservation property holds). Never run this destructively
      against the real `agent-monitoring/` directory inside a pytest run — always a `tmp_path`
      copy, mirroring `test_monitoring_writer_lockfile_candidate.py`'s own
      `_assert_not_real_corpus` safety precedent (though inverted here: the writer module itself
      must be allowed to target the real directory in production, only tests must not).
    - Location: `tests/tools/test_<writer_module_name>.py` (unit-level prefix-preservation
      property test) — the literal entry/exit manifest run against the real corpus is an
      Implement/Verify-phase *procedure* for this ticket, not itself a new pytest test.

## Scoped Pytest Commands

```
pytest tests/tools/test_post_tool_hook.py tests/tools/test_record_run.py tests/tools/test_record_events.py -v
pytest tests/tools/test_monitoring_writer_lockfile_candidate.py -v
pytest tests/tools/test_agent_ops_dashboard_ingest.py tests/tools/test_agent_ops_dashboard_api.py tests/tools/test_agent_ops_dashboard_api_boundary.py tests/tools/test_agent_ops_dashboard_concurrency.py -v
pytest tests/tools/ -k "monitoring_writer or writer_lockfile" -v
```

Never `pytest tests/`. If a new dedicated test file is created for the production writer module
(e.g. `tests/tools/test_monitoring_writer.py`), add it explicitly to the first command group
rather than relying on `-k` pattern matching alone.

## Anti-Drift Test Guards

- **AST/import-graph guard (New Test #7 above) doubles as the anti-drift guard** for this
  ticket's core claim: it fails loudly if a future edit reintroduces a 4th ad hoc writer
  implementation, or if one of the 3 call sites regresses back to its own inline
  `fcntl`/`os.open` locking instead of importing the shared module.
- **Corpus-path guard carried forward, inverted.** The candidate's `_assert_not_real_corpus`
  guard must NOT appear in the production writer module (it would break the module's actual
  purpose). Instead, a **test-side** guard should assert that no test in
  `tests/tools/test_<writer_module_name>.py` ever points the writer at a path resolving under the
  real `<repo_root>/agent-monitoring/` directory — same safety property, opposite enforcement
  location (test suite, not production code).
- **Exact-field-set assertions in `test_post_tool_hook.py` (4 occurrences) must be updated to the
  new field set, not silently loosened to a subset check** — if Plan decides `tools.jsonl` does
  NOT get `execution_id`/`provider`, these assertions should stay unchanged as-is (still exact,
  proving the schema wasn't touched); if it does, they should still be exact-field-set
  assertions against the *new* fixed set, not converted to `.issubset()`/`.issuperset()` checks
  that would silently tolerate an unbounded/drifting schema.
- **`record_run.py`/`record_events.py`'s validation-failure exit-code/stderr contract must stay
  byte-for-byte unchanged** — a new test should explicitly assert `ERROR:`-prefixed stderr +
  `sys.exit(1)` still fires for a missing-required-field payload *without* the shared writer ever
  being invoked (i.e. validation failure short-circuits before the writer is touched, exactly as
  today) — this guards against an accidental refactor that routes validation-failure paths
  through the new writer's own error handling instead of the existing CLI contract.
- **`query.py`/`validate.py`/`generate_retro.py` untouched guard** — a lightweight test (or reuse
  of the existing single-source `load_jsonl` identity assertion in
  `tests/tools/test_agent_ops_dashboard_ingest.py`, if present) confirming `ingest.py`'s
  `load_jsonl` is still the identical function object from `validate.py` (`ingest.load_jsonl is
  validate.load_jsonl`), not a fork — guards against this ticket accidentally duplicating
  read-side logic instead of reusing it, which would silently violate its own Out of Scope
  boundary.
- **Stale-lock test must prove recovery, not just eventual success by retry exhaustion timing
  out into a false pass** — assert the *specific* mechanism (old lock file removed, new lock
  acquired) via `os.path.exists`/mtime checks on the lock file at each stage, not only the
  end-to-end "did the record get written" outcome, so a regression that silently disables stale
  detection (falling back to always-eventually-succeeds via unrelated retry luck) is caught.
