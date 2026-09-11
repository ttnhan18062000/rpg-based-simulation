---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT
artifact_type: test_plan
tags: [testing, registry]
---

# Test Plan — TCK-20260904-PARITY-TESTPATH-STALE-CITATIONS-AUDIT

## Step 1 — shared parser

- `tests/tools/test_parity_test_path.py` (new): the four legacy shapes the parser already handles —
  clean node-id, single backtick-wrapped, `,`/`+`/`;` multi-citation, unparseable prose returning
  `(None, error)`.
- **Regex-bug regression:** a two-level node-id (`tests/x.py::TestC::test_m`) is accepted. This is the
  case the old index regex wrongly rejected.
- **Equivalence:** `mechanics_auditor_static.parse_test_path_citations` is the same object as the shared
  module's, so the gate check and the index cannot diverge again.
- `tests/tools/test_parity_index.py`: a fixture entry with a multi-citation `test_path` produces one
  `test_refs` row per citation, and a nonexistent file in any one of them flags `absent_file`. Before
  this change that entry produced no rows.
- Existing `absent_file` tests (fixture-based, `tmp_path`) still pass unchanged.
- **Path-level scope preserved:** a citation to an existing file with a nonexistent `::symbol` does
  **not** flag `absent_file`. Guards against quietly turning the index symbol-level, contrary to
  `v1_decisions_phase0.md`.

## Step 2 — `evidence_kind`

- `tests/tools/test_parity_ledger_schema.py`: schema accepts each of the three values and `null`; rejects
  an unknown value; field is not required.
- `tests/tools/test_parity_ledger_writer.py`: `validate_entry()` raises `EntryValidationError` on an
  unknown `evidence_kind`.
- **No enforcement leak:** a `verified` P0 entry with `evidence_kind: existence` is *accepted*. Locks the
  enforcement rule out of this ticket so it is not half-shipped.

## Step 3 — write-time format contract

- `validate_entry()` rejects a non-null unparseable `test_path`; the message names `support_boundary`.
- `validate_entry()` accepts `test_path: null` where the schema permits it.
- `TestValidateEntryAgainstRealMultiSegmentCorpus` passes unmodified.
- **No sweep:** existing on-disk entries are not revalidated; only `write_entry()` calls the contract.
- Re-run the full writer suite; any fixture using a prose `test_path` gets its fixture fixed, not the
  contract relaxed.

## Step 3a — narrowed P0 rule

- P0 + `missing` + `test_path: null` + non-empty `support_boundary` → accepted.
- P0 + `unsupported` + `test_path: null` + non-empty `support_boundary` → accepted.
- P0 + `missing` + `test_path: null` + `support_boundary` null or `""` → **rejected** (the gap must be
  explained).
- P0 + `verified` / `divergent` / `legacy_verified` + `test_path: null` → still **rejected**.
- P1/P2 behavior unchanged.
- Lockstep: validate the same fixtures against `schema.json` with `jsonschema` and assert it agrees with
  `validate_entry()` on every case above — prevents the two copies of the rule drifting apart.
- A real pre-existing entry (`SUB-325`) with a `support_boundary` added passes `validate_entry()`; as-is
  (null `support_boundary`) it is still rejected — documents that the 15 legacy entries need explanation,
  not just permission.

## Step 4 — the 28 entries

- For every repointed entry, run its new `test_path` and record the result:
  `python3 tools/gate_checks/mechanics_auditor_static.py` / `verify_entry_test_path()` against each ID.
- Re-run the enumeration from `investigation.md` §1: **0** entries with a nonexistent cited file.
- Every entry changed to `missing` has `test_path: null` and a non-empty `support_boundary`.
- `TOWN-005`/`TOWN-006` parse under the shared parser and no longer contain the claim that
  `tests_v2/test_occupancy_conflicts.py` never existed.

## Step 5 — measurement

- `absent_file` after Step 1 > before Step 1 (newly-visible entries surface).
- `absent_file` after Step 4 = post-Step-1 count minus the number of stale citations resolved.
- `test_parity_index_baseline.py` passes. `live_missing == 1315` counts entries with no `test_path`; if
  Class B/C nulling changes it, update the literal with the measured value and cite this ticket — the
  documented drift pattern, not a gate to route around.

## Scoped regression command

```
pytest tests/tools/test_parity_test_path.py tests/tools/test_parity_index.py \
       tests/tools/test_parity_index_baseline.py tests/tools/test_parity_ledger_writer.py \
       tests/tools/test_parity_ledger_schema.py tests/tools/test_mechanics_auditor_static.py \
       tests/integrity/test_parity_guards.py -q
```

Plus every test file newly cited by a repointed entry.
