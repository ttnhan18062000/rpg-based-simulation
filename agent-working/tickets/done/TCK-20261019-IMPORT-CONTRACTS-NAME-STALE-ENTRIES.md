---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-IMPORT-CONTRACTS-NAME-STALE-ENTRIES
phase: done
date: 2026-10-19
tags: [testing]
---

# TCK-20261019-IMPORT-CONTRACTS-NAME-STALE-ENTRIES

## Title
`import_contracts ci` names the stale ignored import and where to delete it

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
On a stale `ignore_imports` entry, `import_contracts ci` prints only "N kept, 0 broken, 1 stale ignored import(s)" and "::error::import contracts: 1 stale ignored import(s): remove the `ignore_imports` entries that no longer match". It never names the entry, so the author has to run `make lint-imports` and read the warning. #673 reproduced this on 309715a72 (the day-of stale pair `src.engine.world_dynamics -> src.world.spawn`).

## Scope
In `codebase/structure/import_contracts.py` and `tests/codebase/test_import_contracts.py`:
1. Parse lint-imports' own "No matches for ignored import A -> B." lines into stale pairs, as `broken_pairs()` does for broken ones. `stale: int` keeps working.
2. Name each stale pair with its location: the line in `codebase/structure/import_layers_baseline.txt` for a baseline pair, otherwise the line in `codebase/structure/importlinter.toml` (a hand-written ignore, for example phase19).
3. `ci` prints one `::error::` per stale pair with the pair, the location and the fix hint "delete the line, then run `python3 -m codebase.structure.import_contracts`"; the summary lists the pairs under the count line (so `advisory` and `report` get them for free).
4. Tests: the parser on #673's real lint-imports text; the location lookup for a baseline pair and a toml-only pair; `run_ci` naming the pair with exit 1; the existing exit-code tests unchanged.

## Out of Scope
Which states fail, exit codes, the `test.yml` step. `ruff check codebase` stays at 0 findings (the self-lint pin).

## Acceptance Criteria
- A stale entry is named, with its file and line, in the `ci` annotation and in the summary.
- The exit codes are unchanged.
- Proof: scratch-copy reproduction before and after is pasted in Implementation Notes.

## Related Tickets
- TCK-20261005-IMPORT-LINTER-FLIP-AND-TEST-RETIREMENT (#671); TCK-20261018-CODEBASE-SELF-LINT (same PR)

## Related Docs
- #673

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
`codebase/structure/import_contracts.py`, `tests/codebase/test_import_contracts.py`.

## Assumptions / Open Questions
None.

## Implementation Notes
New in `codebase/structure/import_contracts.py`: `stale_pairs(output)` (parses "No matches for ignored import A -> B." after joining on whitespace), `locate_stale(root, pair)` (baseline line first, then the config line, else "not found in the baseline or the config"), and `Report.stale_entries` (default `()`, so every existing `Report(...)` construction is unchanged). `stale: int` is unchanged and still counts the warning lines; `ci` prints one `::error::` per entry and keeps the old generic line only when a stale warning could not be parsed into a pair. The summary lists each entry under the count line, so `advisory` and `report` get it too. Exit codes and which states fail are unchanged.

Proof, scratch copy (`git archive origin/main` of src, codebase, visual_assets, pyproject.toml, registries; the line `src.engine.world_dynamics -> src.world.spawn` put back into `import_layers_baseline.txt`, then the plain rewrite regenerated the block; real `lint-imports` 2.15). Real warning text:

```
--------
Warnings
--------

Registry layer order (advisory)
-------------------------------

- No matches for ignored import src.engine.world_dynamics -> src.world.spawn.
```

`ci --annotate` before (exit 1):

```
**Import contracts (blocking):** 17 kept, 0 broken, 1 stale ignored import(s)
::error::import contracts: 1 stale ignored import(s): remove the `ignore_imports` entries that no longer match
```

`ci --annotate` after (exit 1):

```
**Import contracts (blocking):** 17 kept, 0 broken, 1 stale ignored import(s)
- stale: `src.engine.world_dynamics -> src.world.spawn (import_layers_baseline.txt l.119)`
::error::import contracts: stale ignored import `src.engine.world_dynamics -> src.world.spawn (import_layers_baseline.txt l.119)`: delete the line, then run `python3 -m codebase.structure.import_contracts`
```

The scratch copy lived in the session scratchpad and was deleted afterwards; no real worktree's baseline was touched.

## Test Summary
Three new tests in `tests/codebase/test_import_contracts.py`: the parser on the real lint-imports text (and a wrapped warning), the location lookup (baseline pair, config-only pair, not found), and `run_ci` naming the pair with exit 1. The existing stale tests (`test_advisory_counts_stale_ignored_imports_as_a_warning`, `test_ci_exits_1_on_a_stale_ignored_import`) pass unchanged. `ruff check codebase`: 0 findings. Scoped run (`tests/codebase`, `tests/static`, venv on PATH, MemoryMax 3G): 610 passed, 2 skipped.

## Files Changed
- `codebase/structure/import_contracts.py`
- `tests/codebase/test_import_contracts.py`
- Nothing under `src/`.

## Completion Summary
`import_contracts ci` now names each stale ignored import with the file and line to delete (`src.engine.world_dynamics -> src.world.spawn (import_layers_baseline.txt l.119)` in the reproduction), one `::error::` per pair with the fix hint, and the summary lists them; #673 asked for exactly this. Exit codes and the states that fail are unchanged, and `ruff check codebase` stays at 0 findings.
