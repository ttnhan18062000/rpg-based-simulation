---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL
artifact_type: test_plan
tags: [testing, registry, data-quality]
---

# Test Plan — TCK-20260913-PARITY-LEDGER-CLASS2-CLASS4-RESIDUAL

## Automated

- New: `tests/tools/test_parity_test_path.py::test_pipe_delimiter_with_surrounding_whitespace_splits_correctly`,
  `::test_doubled_pipe_with_no_surrounding_whitespace_is_not_treated_as_a_delimiter` — pin the
  delimiter extension's positive case and its non-match safety case (INFRA-405's `|| true`).
- New: `tests/static/test_typecheck_gate_configured.py` (3 tests) — real citation for
  INFRA-TYPE-001.
- Existing full relevant regression suite: `tests/tools/test_parity_ledger_writer.py`,
  `test_parity_test_path.py`, `test_parity_index_baseline.py`, `tests/static/`, `tests/integrity/`
  — all re-run after every shard's fix batch.

## Manual verification, per entry

- Every citation added to any `test_path` verified to exist via `grep -n "^def <name>"` /
  `^class <name>"` (function/method) or file existence check, before being written — never
  inferred.
- `python3 tools/parity_corpus_check.py` re-run after every fix batch, confirming the exact
  expected count delta (never a surprise number).
- Final state independently confirmed: `class2_malformed_test_path: 4` (all 4 disclosed
  unresolvable, `INFRA-280/302/303/304`), `class4_bad_id_pattern: 0`.

## Scope of testing

Pure ledger-data + tooling change (one parser regex extension, one new small static test file, one
ID rename). No `src/` file touched — Parity is self-referential here (this ticket IS the parity
ledger work) but does not itself require a further parity-ledger update about parity-ledger
tooling, per the same precedent as the parent ticket.
