---
status: active
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY
artifact_type: plan
tags: [ai, observability, process-improvement]
---

# Plan — TCK-20260808-PARITY-INDEX-STALENESS-VISIBILITY

## Steps

1. `tools/parity_index.py`:
   - Extract `_shard_manifest_hash(shards) -> tuple[str, str]` (returns `(shard_manifest_json,
     source_manifest_hash)`) from the inline logic in `_build_into()`, and call it from both
     `_build_into()` and the new `check_staleness()` — guarantees the two can never compute the
     hash differently.
   - New `check_staleness(db_path=None, ledger_dir="docs/parity_ledger") -> dict`.
   - New `check-staleness` argparse subcommand in `main()`, `--db-path` default `DEFAULT_DB_PATH`,
     `--ledger-dir` default `"docs/parity_ledger"`. Exit code `0`/`1` per investigation.md.
   - Module docstring: add `check-staleness` to the documented operation list.
2. `Makefile`: `parity-index` and `parity-index-check` targets (plain `python3` form, matching
   `docs-registry`), added to the `.PHONY` line.
3. `tests/tools/test_parity_index.py`: the 5 tests from test_plan.md.

## Acceptance-criteria map

| AC | Disposition |
|---|---|
| investigation.md confirms hash separability | Done |
| make target exists | Step 2 |
| staleness check correct for all 3 cases | Step 1, Step 3 |
| scoped pytest passes | Step 3 |
