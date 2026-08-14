---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL
artifact_type: test_plan
tags: [ai, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260810-PARITY-LEDGER-WRITE-SAFETY-TOOL

## Regression Surface

Existing tests that must keep passing, unmodified in intent (only touched if `schema.json`'s
restructuring or `parity_ledger_scan.py`'s new try/except genuinely requires it):

- `tests/tools/test_parity_index.py` — full suite (34 tests across 14 classes: atomic lifecycle,
  shard import, reference tables, entry_health, FTS5, atomic failure safety, determinism,
  architecture guards, entry/impact/health query, equivalence fixtures, all-shards coverage,
  check-staleness). In particular `TestArchitectureGuards::
  test_no_mutation_cli_or_write_path_to_docs_parity_ledger` and
  `test_health_subcommand_never_writes_to_docs_parity_ledger` must still pass unchanged —
  `parity_index.py` itself must remain untouched by this ticket except for whatever the writer's
  `build()`/`check_staleness()` reuse requires (none, per this ticket's Decision 1).
- `tests/tools/test_parity_index_baseline.py` — full suite, including
  `test_v1_decision_artifact_covers_all_scope_boundaries` and the malformed/faction fixture tests.
  If `_schema_coverage_as_parsed()` is updated to match the fixed `schema.json` (per
  investigation.md Risk #5), this file's assertions on that function's output shape must be
  updated in the same change, not left silently stale.
- Any existing test exercising `tools/parity_ledger_scan.py::find_p0_intersection` — confirm none
  currently assert the uncaught-crash behavior as *intended* (a test relying on the crash would
  need updating alongside the §6.3 fix; grep found none such directly, confirm at Implement time).
- `tests/tools/test_gate_a_readpath_review.py` — must stay green; it byte-identity-guards
  `tools/parity_index.py`, `tools/parity_ledger_scan.py`, `tools/gate_checks/
  parity_updater_static.py`, every `docs/parity_ledger/*.yaml` shard, `tools/
  context_packet_assembler.py`, and `.claude/workflows/implement-ticket.js` — the §6.3 fix
  **will** change `tools/parity_ledger_scan.py`'s bytes, so this guard's protected-file list and/or
  its own fixtures must be reconciled deliberately at Implement/Verify time, not discovered as a
  surprise failure. `tools/parity_ledger_scan.py` and `docs/parity_ledger/schema.json` are both on
  that protected list — Plan must explicitly account for updating this guard's expectations (it is
  designed to catch exactly this kind of incidental drift, so an update here is legitimate,
  not a guard being routed around).

## New Tests Required

Per Acceptance Criteria, in the new sibling module's own test file
(`tests/tools/test_parity_ledger_writer.py`):

- **`test_writer_rejects_bad_id_pattern`**
  Category: unit. Verifies: a write attempt with an `id` not matching `^[A-Z]+-[0-9]{3}$` is
  rejected with a specific, labeled error (not a generic `ValueError`/`AssertionError`), and the
  target shard file is byte-unchanged after the rejected call.
  Location: `tests/tools/test_parity_ledger_writer.py`.

- **`test_writer_rejects_verified_missing_v2_evidence`**
  Category: unit. Verifies: `status: verified` with `v2_evidence: null` is rejected with a
  specific error naming the missing field; shard unchanged.

- **`test_writer_rejects_verified_missing_test_path`**
  Category: unit. Verifies: `status: verified` with `test_path: null` is rejected with a specific
  error naming the missing field; shard unchanged. (Separate test from the `v2_evidence` case per
  AC's "one test per condition, not one generic invalid test.")

- **`test_writer_rejects_divergent_missing_v2_evidence`** and
  **`test_writer_rejects_divergent_missing_test_path`**
  Category: unit. Same shape as the two `verified` tests above, for `status: divergent` — confirms
  the fixed `schema.json`'s `allOf` restructuring actually enforces both surviving rule branches,
  not just one (this is the exact defect being fixed — a regression here would mean the fix
  didn't take).

- **`test_writer_rejects_divergent_missing_divergence_note`**
  Category: unit. Verifies: `status: divergent` with `divergence_note: null` is rejected with a
  specific error; shard unchanged.

- **`test_writer_rejects_p0_missing_test_path`**
  Category: unit. Verifies: `priority: P0` with `test_path: null` is rejected — this is the
  condition that has **no** existing `schema.json` expression today (prose-only in CLAUDE.md/
  `parity-updater.md`); this test is the primary proof the new conditional was actually added, not
  just documented.

- **`test_writer_accepts_valid_verified_entry_and_writes_shard`**
  Category: integration. Verifies: a fully valid entry is actually appended/updated in the target
  YAML shard, byte-parseable afterward, round-trips via `yaml.safe_load` back to the same entry
  dict. Positive-path counterpart to the six rejection tests above.

- **`test_successful_write_rebuilds_index_in_same_run`** (or equivalent name matching the actual
  Decision 2 outcome — rebuild vs. staleness-flag)
  Category: integration. Verifies the chosen AC #2 behavior actually happens: after a successful
  validated write, `parity_index.check_staleness()` against the same `db_path`/`ledger_dir`
  reports `FRESH` (if rebuild-on-write is chosen) — or, if a staleness-flag design is chosen
  instead, that the writer's own return value/output unambiguously surfaces `STALE`/a rebuild
  instruction such that a caller cannot silently miss it. Must assert the *actual* mechanism, not
  merely that "some staleness-related field exists."

- **`test_failed_write_never_triggers_index_rebuild`**
  Category: unit / anti-drift. Verifies: a rejected (invalid) write does **not** call
  `parity_index.build()`/mark anything fresh — the rebuild-on-write path must be gated strictly on
  write success, never on write attempt.

- **`test_writer_never_bypasses_validation_via_direct_yaml_dump`**
  Category: architecture guard. Static-source check (mirroring
  `test_no_mutation_cli_or_write_path_to_docs_parity_ledger`'s pattern) confirming the new writer
  module has exactly one code path that reaches `docs/parity_ledger/*.yaml` write bytes, and that
  path is always preceded by the schema-validation call in the same function — prevents a future
  edit from adding a second, unvalidated write entry point.

- **`test_find_p0_intersection_malformed_shard_raises_labeled_error_not_crash`** (§6.3 fix)
  Category: unit / regression. Verifies: `find_p0_intersection` against a malformed shard fixture
  raises a specific, labeled exception (not a bare uncaught `yaml.YAMLError`), matching the pattern
  `parity_index.py`'s `ShardParseError` already establishes. Location:
  `tests/tools/test_parity_ledger_scan.py` (new file, or added to wherever
  `parity_ledger_scan.py`'s existing tests currently live — confirm at Implement time whether a
  dedicated test file already exists).

- **`test_parity_updater_agent_md_uses_new_write_path`**
  Category: architecture guard / doc-sync. Confirms `.claude/agents/parity-updater.md`'s "What to
  Do" section no longer instructs raw `Read`/`Edit` of the YAML as the primary mutation path, and
  instead references the new writer tool by name. Static text-content assertion, not a live agent
  run.

## Scoped Pytest Commands

```
pytest tests/tools/test_parity_ledger_writer.py -v
pytest tests/tools/test_parity_index.py -v
pytest tests/tools/test_parity_index_baseline.py -v
pytest tests/tools/test_gate_a_readpath_review.py -v
pytest tests/tools/ -k "parity" -v
```

Never `pytest tests/` — scope stays inside `tests/tools/` (the entire affected domain: parity
tooling, gate checks, and their static-source guards).

## Anti-Drift Test Guards

- `test_writer_never_bypasses_validation_via_direct_yaml_dump` (above) — the single most important
  anti-drift guard: without it, a future edit could reintroduce an unvalidated write path and
  silently defeat this entire ticket's purpose.
- `test_failed_write_never_triggers_index_rebuild` (above) — prevents the rebuild-on-write design
  from masking a rejected/invalid write as if it succeeded.
- Re-run `TestArchitectureGuards` in `tests/tools/test_parity_index.py` unmodified — proves
  `parity_index.py` itself was not turned into a second, competing write path by mistake (Decision
  1's core invariant).
- If `schema.json` is fixed via `allOf`, add an explicit test asserting entries with
  `status: missing`/`unsupported`/`legacy_verified` and no `v2_evidence`/`test_path` are still
  **accepted** — proves the fix didn't accidentally tighten validation beyond the documented Entry
  Schema (a real regression risk given the restructuring touches shared conditional logic).
- `test_gate_a_readpath_review.py`'s byte-identity guard, re-run post-change: confirms the §6.3 fix
  and `schema.json` fix are the *only* changes to the protected-file set, and that the guard's own
  fixtures were deliberately updated (not bypassed) to account for them.
