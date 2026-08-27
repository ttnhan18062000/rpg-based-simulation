---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS
artifact_type: investigation
tags: [registry, process-improvement, debugging]
---

# Investigation — TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Three failure classes, three different states of readiness

1. **`agent-monitoring/{tools,runs,events}.jsonl` + `tickets/working_log.csv`**: `.gitattributes`
   already ships `merge=union` for all four paths (confirmed present, unedited by this ticket).
   Gap was purely a missing regression test proving the git-level behavior actually works — not a
   missing implementation.

2. **`docs/REGISTRY.yaml`**: found existing, already-shipped prior art —
   `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE` (2026-07-09, done) added a `--check` mode to
   `tools/generate_registry.py` that regenerates in-memory and diffs against the on-disk file,
   plus a non-`slow`-marked test (`tests/tools/test_generate_registry.py::TestRealDocsTree::
   test_check_flag_detects_no_drift_against_real_registry`) that already runs inside CI's
   `api-tools` job (`pytest tests/tools`, confirmed `tests/tools` is in that job's path list,
   `.github/workflows/test.yml:266,289`). Confirmed still present and passing. **This AC is
   already satisfied by prior work — no new implementation needed here**, only confirmation.

3. **`docs/parity_ledger/*.yaml` cross-shard ID collisions**: `tools/parity_index.py`'s
   `DuplicateEntryIdError` detector (line 238, in `_populate_entries()`) is real and already
   covered by `test_duplicate_cross_shard_id_rejected_at_import` (a tmp_path synthetic fixture
   proving the LOGIC), and `build()`'s CLI wrapper already returns exit 1 on a collision
   (`main()`: `return 0 if report["status"] == "ok" else 1`). But `make parity-index` is
   explicitly marked "(on-demand only — not CI)" in the Makefile, and grepping
   `.github/workflows/test.yml` for any reference to `parity_index`/`parity-index` returns
   nothing — confirmed zero CI wiring. This is the one real implementation gap.

## Fix for gap 3
Mirror the exact zero-new-workflow-edit pattern `TCK-20260709-REGISTRY-DRIFT-CHECK-GATE`
established: add a new, non-`slow` pytest test (`TestRealLedgerCollisionGuard::
test_build_against_real_docs_parity_ledger_has_no_duplicate_ids` in
`tests/tools/test_parity_index.py`) that runs `parity_index.build()` against the REAL, live
`docs/parity_ledger/` directory (not a synthetic fixture) and asserts `status == "ok"`. This runs
inside the same `api-tools` CI job's `pytest tests/tools -m "not slow"` step with zero
`.github/workflows/test.yml` edits. Verified locally against the real corpus first (2076 entries,
9 shards, `status: "ok"`) before adding the test, to avoid landing a broken gate.

`check-staleness` was considered and rejected as the CI hook: it requires an already-built
`parity.db` file to diff against (`parity-index/` is gitignored — no such artifact exists in a
fresh CI checkout), so it answers "is the built index stale" not "does the live ledger have a
collision." `build()` itself is the right hook — it always runs a full rebuild from the live YAML
shards and fails loudly via `DuplicateEntryIdError` regardless of any pre-existing DB state.

## No custom merge driver built
Per the ticket's Out of Scope: `next_available_id()` computes purely against the on-disk shard
file at call time with no lock/reservation, so two concurrent sessions against the same pre-merge
base will legitimately compute the same "next" ID regardless of client-side logic — a structural
property, not a bug a smarter client can prevent. The fix here is post-merge fail-loud detection
(gap 3 above), not prevention. `TCK-20260824-PARITY-NEXT-ID-LOOKUP` (the existing ID-lookup helper)
is cited as related prior art, not reopened.
