---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS
artifact_type: test_plan
phase: inprogress
date: 2026-09-13
tags: [testing, registry, data-quality]
---

# Test Plan: TCK-20260913-PARITY-LEDGER-WRITER-INVALID-CORPUS

## New tests

- `tests/tools/test_parity_test_path.py`: 3 new tests for the directory-citation shape
  (`test_bare_directory_citation_is_accepted`, `test_directory_citation_without_trailing_slash_is_
  still_unparseable`, `test_directory_citation_participates_in_multi_citation_lists`).
- `tests/tools/test_parity_ledger_writer.py::TestStep3aRealLegacyEntryNeedsExplanation`: replaced
  the pre-fix-state test with `test_sub_325_now_has_a_real_support_boundary` (asserts the real,
  now-fixed entry validates) and `test_sub_325_synthetic_entry_without_support_boundary_is_still_
  rejected` (proves Step 3a's rule independently of SUB-325's own current state, via a synthetic
  copy).

## Existing tests to verify pass, not just assumed

- `tests/tools/test_parity_index_baseline.py` — the ratchet conversion; verified the assertion
  actually fails on a synthetic value above the ceiling (not just always-passing), separately from
  the pytest run.
- `tests/tools/test_parity_ledger_writer.py` — full suite, since Class 3 fixes and the SUB-325 test
  class rewrite both touch this file's territory.
- `tests/tools/test_parity_index.py` — `write_entry()`'s in-process index rebuild runs on every one
  of the 56 Class 2/3 fixes; this is the module that owns that rebuild path.
- `tests/tools/test_mechanics_auditor_static.py` — `check_test_path()` consumes
  `parse_test_path_citations()` directly; the directory-citation extension must not regress its
  existing file/function-level verification behavior.

## Manual verification (beyond pytest)

- Every one of the 56 applied Class 2/3 fixes was individually verified against real files/
  functions on disk (not just "the parser accepts it") before being written — this caught 5 real
  problems (documented in investigation.md) that a pytest-only check would have missed, since
  pytest doesn't run against ledger content at all.
- `python3 tools/parity_corpus_check.py` re-run after every batch of fixes to confirm the exact
  expected count delta, not just "some number went down".
- `check_test_path()` run end-to-end (with the real venv python, not bare `python3` which lacks
  `pydantic`) against a real directory citation before committing the parser extension, to prove
  the claimed "already handles it correctly" wasn't just theoretical.
