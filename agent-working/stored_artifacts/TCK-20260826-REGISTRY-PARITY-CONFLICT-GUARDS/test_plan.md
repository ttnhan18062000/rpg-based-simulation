---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS
artifact_type: test_plan
tags: [registry, process-improvement, debugging]
---

# Test Plan — TCK-20260826-REGISTRY-PARITY-CONFLICT-GUARDS

## Normal flow
- `test_concurrent_branch_appends_merge_without_conflict_markers` (parametrized over all 4
  merge=union paths): two branches each append a distinct line to the same tracked file; merge
  must exit 0, produce no conflict markers, and contain both branches' lines.
- `test_build_against_real_docs_parity_ledger_has_no_duplicate_ids`: `parity_index.build()`
  against the real, live `docs/parity_ledger/` corpus must return `status == "ok"`.

## Edge cases
- `test_gitattributes_lines_present_for_all_four_union_merge_paths`: static guard against an
  accidental removal of any of the 4 `.gitattributes` lines the git-level test's logic depends on.

## Failure modes
- If a real cross-shard ID collision is ever introduced (the exact failure mode this session hit
  3 times), `test_build_against_real_docs_parity_ledger_has_no_duplicate_ids` fails loudly in CI
  with the `DuplicateEntryIdError`'s message (which filenames/id collided), not a silent pass.

## Regression paths
- `tests/integrity/test_merge_union_gitattributes.py` — new file, 5 passed.
- `tests/tools/test_parity_index.py` — full file, 45 passed (44 pre-existing + 1 new).
- `tests/integrity tests/architecture tests/docs tests/static tests/refactor` (arch-docs job's
  full scope) — 178 passed, 2 skipped, 1 deselected, 2 xfailed (pre-existing, unrelated to this
  ticket).
