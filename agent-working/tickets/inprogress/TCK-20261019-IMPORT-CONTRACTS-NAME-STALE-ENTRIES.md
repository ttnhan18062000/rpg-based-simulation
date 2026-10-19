---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261019-IMPORT-CONTRACTS-NAME-STALE-ENTRIES
phase: open
date: 2026-10-19
tags: [testing]
---

# TCK-20261019-IMPORT-CONTRACTS-NAME-STALE-ENTRIES

## Title
`import_contracts ci` names the stale ignored import and where to delete it

## Status
INPROGRESS

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
Filled at close.

## Test Summary
Filled at close.

## Files Changed
Filled at close.

## Completion Summary
Filled at close.
