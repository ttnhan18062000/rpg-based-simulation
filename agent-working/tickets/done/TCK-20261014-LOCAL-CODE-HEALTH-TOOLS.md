---
status: historical
layer: architecture
authority: P1
audience: agent
ticket_id: TCK-20261014-LOCAL-CODE-HEALTH-TOOLS
phase: done
date: 2026-10-14
tags: [architecture, bug]
---

# TCK-20261014-LOCAL-CODE-HEALTH-TOOLS

## Title

Local code-health tools: a missing ruff fails loudly, and `make` finds the project interpreter and lint-imports

## Status

DONE

## Tier

hotfix

## Type

bug

## Priority

P2

## Request Summary

Batch #583 (codebase-planner dispatch, lead-directed). The issue's premise that pins are missing is stale:
`ruff==0.16.10`, `ast-grep-cli==0.45.3` and `import-linter==2.15` are already in pyproject's `lint` group and
`[tool.uv] default-groups = ["dev","lint"]`, so a plain `uv sync` installs them. Three real causes:
1. The Makefile's `lint-py`, `code-health*` and `import-contracts` targets called bare `python3`/`complexipy`,
   not `$(PYTHON3)` (which picks `.venv`, then the main checkout's `.venv`, then `python3`). In a worktree with no `.venv`
   the tools were not found (seen on #546: "complexipy not found").
2. A silent false-clean: `scan._scan_ruff` runs `python -m ruff` and accepted exit codes (0, 1). With ruff not installed
   Python itself exits 1, so the scan wrote an EMPTY `ruff.json` and ruff read as clean.
3. `import_contracts.py` defaulted `--lint-imports` to `shutil.which("lint-imports")` (PATH only), unlike
   `scan.find_tool`, so it "could not run" without `.venv/bin` on PATH.

## Scope

1. `codebase/health/scan.py::_scan_ruff`: raise `ToolUnavailableError` whenever ruff's stdout is empty or whitespace,
   whatever the exit code or stderr (real ruff always prints JSON, `[]` when clean); the trimmed stderr goes in the message.
2. `codebase/structure/import_contracts.py`: `default_lint_imports()` (beside this Python, else PATH, else the bare name)
   for both `--lint-imports` defaults; a new `report` subcommand that runs `lint-imports --config <repo config>` with its own
   output and exit code (2 when it cannot start). Module docstring usage block updated.
3. `Makefile`: `lint-py`, `code-health`, `code-health-size`, `code-health-complexity`, `import-contracts` use `$(PYTHON3)`
   (complexity resolves the binary with `scan.find_tool`, because `python -m complexipy` does not work); new `lint-imports`
   target = `$(PYTHON3) -m codebase.structure.import_contracts report`.
4. Tests in `tests/codebase/test_local_health_tools.py`.

## Out of Scope

- Any pyproject/uv.lock pin change (already pinned); creating a `.importlinter` file (the config is
  `codebase/structure/importlinter.toml`); CI workflow edits (CI calls `python3 -m codebase.health check` directly, not through
  make, so the Makefile edits do not change CI; only the `scan.py` change reaches CI, and it only turns a would-be silent pass into a loud failure).
- `staged_ratchet._ruff_json` (already skips loudly on a missing module) and `sarif_feedback` (empty stdout already raises
  `SarifError` in `parse_sarif`); a test pins the latter.

## Acceptance Criteria

1. `scan._scan_ruff` raises `ToolUnavailableError` and writes no `ruff.json` for empty output, for the missing-module case and for a different stderr with exit 0 or 1; a clean `[]` run still writes `[]`.
2. From a worktree with no `.venv` and a PATH without `.venv/bin`, `make code-health` and `make lint-imports` run, and `/usr/bin/python3 -m codebase.health check` fails loudly on ruff.
3. `make lint-imports` prints lint-imports' full report and returns its exit code.
4. The new tests fail on the old `scan.py` and pass after.

## Related Tickets

- `TCK-20261013-IMPORT-LAYERS-STALE-KERNEL-IGNORE` (#546, where `complexipy not found` was hit).
- `TCK-20261014-ANYIO-CVE-BUMP` (same batch, separate commit).

## Related Docs

- `docs/guidelines/python_code_standard.md`

## Related Stored Artifacts

None (hotfix).

## Related Code Areas

- `codebase/health/scan.py`, `codebase/structure/import_contracts.py`, `Makefile`, `tests/codebase/test_local_health_tools.py`

## Assumptions / Open Questions

- `$(PYTHON3)` needs `pydantic` importable; with no `.venv` it falls to the main checkout's `.venv` via `KNOWLEDGE_MAIN_ROOT`.

## Implementation Notes

Proof, from this worktree with no `.venv` (before `uv sync`) and PATH stripped of `.venv/bin`:

```
$ make lint-imports | tail -3        # rc=0
visual_assets imports nothing from src KEPT
src imports nothing from visual_assets KEPT
Contracts: 17 kept, 0 broken.
$ make import-contracts | tail -1
**Import contracts (advisory):** 17 kept, 0 broken
$ /usr/bin/python3 -m codebase.health check      # rc=2
error: ruff produced no output (exit 1): /usr/bin/python3: No module named ruff
$ make code-health-complexity | tail -2
 topological_sort_modules 17  FAILED   (report-only; binary found beside the main checkout's python)
```

Review fixup (codebase-planner): the two remaining `uvx --from import-linter==2.15 lint-imports ...` hints, the
advisory summary line in `import_contracts.py` and the header comment of `importlinter.toml` (hand-edited, outside the
generated block), now say `make lint-imports`. Added as a fixup commit after the first T1 commit.

## Test Summary

With the worktree's own `.venv` (`uv sync --frozen`), each run alone under `systemd-run MemoryMax=3G`, own `--basetemp`:
`make code-health` rc=0; `tests/codebase` 477 passed, 2 skipped; `tests/static` 95 passed; `tests/unit/tools` 886 passed;
`tests/tools` 4878 passed, 57 skipped, 1 xfailed; `tests/unit/api` 53 passed; all `*guard*` test files 406 passed, 1 skipped, 2 xfailed.
The new `tests/codebase/test_local_health_tools.py` 8 tests: 3 fail on the old `scan.py`, all pass now.

## Files Changed

- `codebase/health/scan.py`, `codebase/structure/import_contracts.py`, `Makefile`, `tests/codebase/test_local_health_tools.py`, this ticket.

## Completion Summary

A ruff that did not run now fails the scan loudly instead of recording a clean result, and the local make targets
find the project tools without `.venv/bin` on PATH. New `make lint-imports` prints the full report.
