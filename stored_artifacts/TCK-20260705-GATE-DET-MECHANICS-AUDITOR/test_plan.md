---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260705-GATE-DET-MECHANICS-AUDITOR
artifact_type: test_plan
tags: [ai, workflows, determinism, mechanics-auditor, parity]
---

# Test Plan — TCK-20260705-GATE-DET-MECHANICS-AUDITOR

## Regression Surface

Existing tests that must keep passing (nothing in this ticket's scope touches simulation `src/`, so
this is a narrow, tooling-only regression surface):

- **unit (tooling):**
  - `tests/tools/test_parity_updater_static.py` — must still pass unmodified; this ticket may import
    from `parity_updater_static.py` but must not change its public functions/return shapes.
  - `tests/tools/test_done_checker_static.py` — unaffected by this ticket, included only because it
    lives in the same `tests/tools/` directory and shares `gate_checks/__init__.py`.
  - Any existing test of `tools/parity_ledger_scan.py` (e.g. a `tests/tools/test_parity_ledger_scan.py`
    if one exists) covering `CANONICAL_LEDGER_FILES` — must still pass, since the new module imports
    this constant rather than redefining it.
- **architecture:** none — `make lane-architecture` (`pytest tests/ -m "architecture"`) is
  `src/`-scoped per `Makefile:185` and SEQUENCE.md decision 1; this ticket's new tests do not carry
  the `architecture` marker and must not be added to that lane.

## New Tests Required

All new tests live in `tests/tools/test_mechanics_auditor_static.py` (mirroring
`tests/tools/test_parity_updater_static.py`'s and `tests/tools/test_done_checker_static.py`'s
location/shape: plain `pytest` functions, `tmp_path`-based fake ledger files, no real
`docs/parity_ledger/` reads).

1. **`test_test_path_existence_check_passes_for_real_passing_test`**
   - Category: unit (coverage-honesty — positive control)
   - Verifies: given a ledger entry whose `test_path` points to a real, currently-passing test node
     ID (e.g. a trivial fixture test file written into `tmp_path`, or an in-repo always-green test
     like a simple `tests/tools/` assertion), the check function returns PASS with `verified_by`
     containing something like `"static:mechanics_auditor_static"`.
   - File: `tests/tools/test_mechanics_auditor_static.py`

2. **`test_test_path_existence_check_fails_for_genuinely_failing_test`**
   - Category: unit (coverage-honesty — the AC's explicitly-required "not just a missing-file case")
   - Verifies: given a `test_path` pointing to a real test file containing a test that asserts
     `False` (write one into `tmp_path`), the check returns FAIL and the returned evidence contains
     the actual pytest failure output (not a generic "not found" string) — asserts the failure text
     itself appears in the returned message, e.g. `assert 0 == 1` or the test's own custom message.
   - File: `tests/tools/test_mechanics_auditor_static.py`

3. **`test_test_path_existence_check_fails_for_nonexistent_file`**
   - Category: unit
   - Verifies: given a `test_path` pointing to a file that does not exist on disk at all, the check
     returns FAIL with an evidence message naming the missing path — and does not attempt to invoke
     pytest (or invokes it and cleanly captures the collection-error, either way asserting no crash).
   - File: `tests/tools/test_mechanics_auditor_static.py`

4. **`test_null_test_path_fails_not_crashes`**
   - Category: unit
   - Verifies: an entry with `test_path: null` (or key absent) returns FAIL (per AC "non-null"
     requirement), never raises an exception.
   - File: `tests/tools/test_mechanics_auditor_static.py`

5. **`test_backtick_wrapped_test_path_is_parsed`**
   - Category: unit (legacy-format tolerance — see investigation.md's format-survey finding: 49
     ledger entries store the value with literal backticks embedded in the string)
   - Verifies: `test_path: "\`tests/tools/test_mechanics_auditor_static.py\`"` (backticks as literal
     characters in the fixture string, pointing at a real file) is stripped and resolved correctly —
     not treated as a literal path containing backtick characters that fails existence check.
   - File: `tests/tools/test_mechanics_auditor_static.py`

6. **`test_legacy_tests_v2_path_fails_cleanly_as_stale`**
   - Category: unit (legacy-format tolerance — per investigation.md: `tests_v2/` does not exist
     anywhere in this repo)
   - Verifies: a `test_path` citing anything under `tests_v2/` returns FAIL with an evidence message
     identifying it as a stale/legacy path — not a raw "file not found," and without ever invoking a
     subprocess (cheap short-circuit), and critically without raising.
   - File: `tests/tools/test_mechanics_auditor_static.py`

7. **`test_parenthetical_annotation_suffix_is_unparseable_and_fails_gracefully`**
   - Category: unit (legacy-format tolerance)
   - Verifies: a `test_path` like `` "`tests/tools/test_x.py` (indirectly via Y)" `` does not crash the
     check; either the path portion is correctly isolated and checked, or (if the implementation
     chooses not to parse this shape) it returns FAIL with the raw string in the evidence — asserts
     no exception either way. This test documents whatever behavior the implementation actually
     settles on (test written to match, not to prescribe, since the Planner must first decide the
     multi/ambiguous-format policy per investigation.md's open question 1).
   - File: `tests/tools/test_mechanics_auditor_static.py`

8. **`test_multi_citation_test_path_policy`**
   - Category: unit (coverage-honesty for the ~13 comma/`+`-joined entries)
   - Verifies: whatever policy the Plan settles on for multi-citation `test_path` values (e.g.
     "first citation only" or "all must pass") — asserts that exact behavior against a fixture with
     two joined paths, one passing and one failing, so the test locks in the chosen semantics rather
     than leaving it implicit.
   - File: `tests/tools/test_mechanics_auditor_static.py`

9. **`test_check_is_scoped_not_full_suite`**
   - Category: unit / architecture-guard style assertion within the same file
   - Verifies: the pytest invocation the check function builds/executes is scoped to exactly the
     cited `test_path` (e.g. by mocking/inspecting the subprocess command args, or by asserting via a
     monkeypatched `subprocess.run` capture that the argv never equals `["pytest", "tests/"]` or lacks
     a specific path argument) — a regression guard against the check silently widening to a full-suite
     run.
   - File: `tests/tools/test_mechanics_auditor_static.py`

10. **`test_verified_by_field_present_and_shaped_correctly`**
    - Category: unit
    - Verifies: the check's return value includes a `verified_by`-compatible marker (per SEQUENCE.md
      decision 3's shared shape, e.g. `"static:mechanics_auditor_static"`), matching the string
      convention already used by `done_checker_static.py`/`parity_updater_static.py`'s own
      `verified_by` entries (checked against `docs/ai/agents.md`'s existing examples,
      `"static:done_checker_static"` / `"static:parity_updater_static"`).
    - File: `tests/tools/test_mechanics_auditor_static.py`

11. **`test_scoped_by_entry_id_not_whole_ledger`**
    - Category: unit (anti-drift — per investigation.md's Anti-Drift Hazards: do not build a
      ledger-wide validator)
    - Verifies: calling the top-level check function with a single entry ID (or small explicit set)
      does not read/iterate over unrelated entries in the same YAML file — e.g., a fixture YAML with
      3 entries, only 1 named, asserts the other 2 are never touched/reported.
    - File: `tests/tools/test_mechanics_auditor_static.py`

## Scoped Pytest Commands

```
python3 -m pytest tests/tools/test_mechanics_auditor_static.py -v
python3 -m pytest tests/tools/test_parity_updater_static.py tests/tools/test_done_checker_static.py tests/tools/test_mechanics_auditor_static.py -v
```

Never `pytest tests/`. If a `tests/tools/` `conftest.py` or shared fixture module exists, run once
more including it implicitly (the above paths already trigger normal pytest conftest discovery).

## Anti-Drift Test Guards

- Test 11 above directly guards against the single biggest scope-creep risk this investigation
  found: given 82% of currently `verified` ledger entries lack any `test_path`
  (`docs/parity_ledger/*.yaml`, see investigation.md), it would be easy for an implementation to
  "helpfully" iterate the whole subsystem file and report on every entry, producing a wall of
  unrelated FAILs. The guard test locks in the narrow, per-entry-ID contract from the ticket's own
  scope wording.
- Test 9 guards against the check silently escalating to `pytest tests/` (the exact anti-pattern
  `CLAUDE.md`'s Testing Rule and this ticket's own Out-of-Scope section explicitly forbid).
- Tests 5–8 collectively guard against a regression where a future edit to the parsing logic starts
  crashing on one of the four confirmed legacy `test_path` shapes (backtick-wrapped, `tests_v2/`-stale,
  parenthetical-suffixed, multi-citation) instead of degrading to a clean FAIL — mirroring
  `test_parity_updater_static.py::test_derive_mapping_skips_malformed_yaml_file`'s established
  "never crash on legacy data" precedent.
- Regression run of `tests/tools/test_parity_updater_static.py` in the combined command above guards
  against an accidental signature/behavior change to `CANONICAL_LEDGER_FILES` or
  `expected_subsystems_for_files` if this ticket's implementation imports and lightly wraps them.
