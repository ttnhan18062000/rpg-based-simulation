---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261013-IMPORT-LAYERS-STALE-KERNEL-IGNORE
phase: done
date: 2026-10-13
tags: [architecture]
---

# TCK-20261013-IMPORT-LAYERS-STALE-KERNEL-IGNORE

## Title

Remove the stale `src.engine.kernel -> src.observability.event_extractor` ignore from the import-layers baseline

## Status

DONE

## Tier

hotfix

## Type

repair

## Priority

P2

## Request Summary

Main's Code health job warns "import contracts: a contract is broken, stale or could not run" (seen on
`71eef3e84` and `b396080cc`). codebase-planner ran the advisory on a clean `origin/main` export: 17 kept,
0 broken, 1 stale ignored import, `src.engine.kernel -> src.observability.event_extractor` in the advisory
"Registry layer order" contract. #536 (`b396080cc`) moved `kernel.py` to
`from src.observability.event_recorder import EventExtractor, extract_events`, so that edge no longer
exists. Removing the ignore tightens the ratchet. Dispatched by codebase-planner (lead-directed).

## Scope

1. Delete line 71 (`src.engine.kernel -> src.observability.event_extractor`) from
   `codebase/structure/import_layers_baseline.txt`; no other line.
2. Regenerate `codebase/structure/importlinter.toml` with `python3 -m codebase.structure.import_contracts`
   (not `seed-baseline`); `--check` exits 0.

## Out of Scope

- `seed-baseline` (re-accepts every current violation), hand edits of `importlinter.toml`, any other
  baseline line, any `src/` change, the 10-19 import-linter flip.

## Acceptance Criteria

1. `importlinter.toml` diff is exactly the one removed ignore line.
2. `python3 -m codebase.structure.import_contracts --check` exits 0.
3. `... advisory` prints "17 kept, 0 broken" with no "stale" suffix.
4. `tests/codebase` passes; on the PR the Code health summary/annotations show no import-contracts warning.

## Related Tickets

- `TCK-20261004-IMPORT-LINTER-ADOPTION` (advisory contract and baseline this ratchets).

## Related Docs

- `docs/plans/codebase_health/import_linter_adoption_ticket_brief.md`

## Related Stored Artifacts

None (hotfix).

## Related Code Areas

- `codebase/structure/import_layers_baseline.txt`
- `codebase/structure/importlinter.toml`
- `codebase/structure/import_contracts.py`

## Assumptions / Open Questions

- The "stale" count comes only from this one ignore (verified: advisory is clean after removal).

## Implementation Notes

Removed the line with `sed` guarded on its exact text, ran the generator, then `--check` (exit 0). Advisory
run with the main checkout's `.venv/bin` on PATH: "17 kept, 0 broken", no stale suffix.

## Test Summary

`tests/codebase`: 258 passed, 1 skipped, plus `test_codebase_health_snapshot.py` 14 passed. The first run
had one failure, `complexipy not found`, because this fresh worktree has no `.venv`; the re-run with the
main checkout's venv on PATH passed. Run under `systemd-run MemoryMax=3G` with own `--basetemp`.

## Files Changed

- `codebase/structure/import_layers_baseline.txt` (-1 line)
- `codebase/structure/importlinter.toml` (-1 line)
- this ticket

## Completion Summary

The stale ignore is removed and the generated config matches. The CI-side check (no import-contracts
warning annotation on the PR's Code health job) is verified after push, from the annotation itself.
