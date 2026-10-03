---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20260709-REGISTRY-DRIFT-CHECK-GATE
phase: done
date: 2026-07-09
tags: []
---

# TCK-20260709-REGISTRY-DRIFT-CHECK-GATE

## Title
Add --check drift-detection gate for docs/REGISTRY.yaml

## Status
DONE

## Tier
standard

## Type
chore

## Priority
P2

## Request Summary
tests/tools/test_generate_registry.py never diffs the checked-in docs/REGISTRY.yaml against a fresh regeneration, so there is no backstop that detects registry drift even if the Finalize-phase trigger is bypassed or fails silently. A `--check` mode plus a CI step is needed to fail loudly on drift, independent of and complementary to the prevention hook.

## Scope
- Add a `--check` flag to tools/generate_registry.py that regenerates the registry in-memory, diffs it against the on-disk docs/REGISTRY.yaml, and exits non-zero with a readable diff/summary on mismatch, writing no file in --check mode
- Make the drift-detected exit path distinguishable from the existing missing-frontmatter exit(1) path (same code with different stderr framing, or a separate documented code)
- Wire a CI job/step (e.g. in .github/workflows/test.yml's arch-docs job, or a dedicated step) that runs `generate_registry.py --check` against the live tree
- Add tests in tests/tools/test_generate_registry.py exercising --check against a deliberately-stale fixture (non-zero exit) and a matching fixture (zero exit)

## Out of Scope
- Wiring the regen call into implement-ticket.js's Finalize phase (see TCK-20260709-REGISTRY-REGEN-ON-CLOSE)
- Fixing existing frontmatterless tickets or stale skip-list entries that would otherwise cause --check to flag drift (see TCK-20260709-DOCSITE-TICKETS-FRONTMATTER-BACKFILL and TCK-20260709-PRUNE-DEAD-SKIP-ENTRIES)

## Acceptance Criteria
- [ ] `python3 tools/generate_registry.py --check` regenerates in-memory and diffs against on-disk docs/REGISTRY.yaml, exits non-zero with a readable diff/summary on mismatch, exits 0 when in sync, and writes no file in --check mode
- [ ] The frontmatter-error exit code (1) and the drift-detected exit code are distinguishable (same code with different stderr framing, or a separate documented code)
- [ ] A CI job/step (e.g. in .github/workflows/test.yml's arch-docs job, or a dedicated step) runs `--check` against the live tree so drift is caught even if the Finalize-phase hook is bypassed
- [ ] A new test in tests/tools/test_generate_registry.py exercises --check against a deliberately-stale fixture (non-zero exit) and a matching fixture (zero exit)

## Related Tickets
- TCK-20260606-DOCSITE-REGISTRY
- TCK-20260706-DOCS-REGISTRY-MISSING-FRONTMATTER
- TCK-20260705-TAG-REGISTRY-QUERY
- TCK-20260706-TICKET-REPORTING-GUIDE
- TCK-20260709-REGISTRY-REGEN-ON-CLOSE

## Related Docs
- `docs/REGISTRY.yaml`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`
- `Makefile`
- `.github/workflows/test.yml`
- `tools/validate_frontmatter.py`
- `tools/tag_registry.py`
- `tools/registry_query.py`

## Assumptions / Open Questions
- No --check/--diff convention exists elsewhere in tools/ (checked validate_frontmatter.py, tag_registry.py) to copy, so the flag's diff-output format is a new convention for this repo
- generate_registry() currently always writes to disk (Path.open('w')) as a side effect — the --check dry-run branch must not regress the ~35 existing tmp_path tests
- CI currently has no job touching docs/REGISTRY.yaml at all, so wiring this in is infra work spanning .github/workflows/test.yml in addition to the Python flag, which pushes this toward standard tier

## Implementation Notes

- `tools/generate_registry.py`:
  - Added `check: bool = False` as a **keyword-only** parameter to `generate_registry(root, output, *, check=False)`. The existing two-positional-arg call sites (`Makefile`'s `docs-registry` target, `check_registry_entry_regenerated()` in `tools/gate_checks/done_checker_static.py`, ~35 existing tests) are unaffected — verified by re-running `test_done_checker_static.py` (all 29 tests pass) and by direct inspection of the call site (line 437: `generate_registry(resolved_root, output_path)`, exactly two positional args, no edit made to that file).
  - Computation of `output_entries` (docs+tickets collection, sort, normalise, strip `None last_verified`) is unconditional and identical in both branches.
  - When `check=True`: if `doc_errors` is non-empty, prints the same frontmatter-error stderr block and returns `1` **before** any disk read/diff is attempted (never writes). Otherwise calls new helper `_check_drift(output, output_entries)`: if `output` doesn't exist, prints a drift message and returns `2`; else `yaml.safe_load()`s the on-disk file and compares the **parsed entry list** (never raw text, so the live `# Generated: <ts>` header line never causes a false positive) against `output_entries` — equal → prints "in sync" and returns `0`; unequal → calls new helper `_print_drift_summary()` (added/removed entries by `path`, changed entries with the differing field names) printed to stderr, returns `2`. Never writes to `output` in this branch.
  - When `check=False` (default): byte-identical to the pre-existing behavior — unconditional write, "Wrote N entries" + `print_summary()`, then `doc_errors` → return 1 else 0. No lines in this branch were altered beyond being moved into the `if check: ... ` / fallthrough structure — the write-then-check-doc_errors ordering (write happens even when doc_errors is non-empty) is preserved exactly, unlike the `check=True` branch which short-circuits on `doc_errors` before any I/O.
  - Module docstring updated to document the `--check` flag and the three exit codes (0/1/2).
- Added `--check` `argparse` flag (`action="store_true"`) in `main()`, wired to `generate_registry(root, output, check=args.check)`.
- `tests/tools/test_generate_registry.py`: added `TestCheckMode` (7 tests: in-sync no-write, stale drift exit 2, header-timestamp-ignored, readable diff summary, missing-output-file-is-drift, frontmatter-error-short-circuits-to-1, backward-compat two-positional-arg default-write regression guard), `TestCLICheckFlag` (1 subprocess end-to-end test covering write→check-in-sync→check-after-drift), and one new test in `TestRealDocsTree` — `test_check_flag_detects_no_drift_against_real_registry` — which runs `check=True` against the real repo root and real `docs/REGISTRY.yaml`. This test carries **no** `@pytest.mark.slow` marker (confirmed via grep), so it runs inside the `api-tools` CI job's existing `pytest tests/tools -m "not slow"` invocation (confirmed `tests/tools` is in that job's path list, `.github/workflows/test.yml:124`) — giving CI drift coverage with zero `.yml` edits, per the plan's Decision #1.
- `docs/parity_ledger/infrastructure.yaml`: appended new entry `INFRA-264` (companion to, not an edit of, `INFRA-183`/`INFRA-263`), `status: verified`, `priority: P2`, `test_path: tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`. Validated YAML parses (`yaml.safe_load`) and the new entry's `id` matches the ledger schema's `^[A-Z]+-[0-9]{3}$` pattern (a pre-existing unrelated entry, `SIMQ-CALIBRATED-001`, already violates that pattern in the file — not touched, not caused by this ticket).
- Cross-check (Step 4): confirmed `check_registry_entry_regenerated()` in `tools/gate_checks/done_checker_static.py` still calls `generate_registry(resolved_root, output_path)` with exactly two positional args — file not edited. Ran `pytest tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py` — 102 passed, 0 failed.
- No deviations from `staging_artifacts/TCK-20260709-REGISTRY-DRIFT-CHECK-GATE/plan.md` — helper function names (`_check_drift`, `_print_drift_summary`) and exact stderr wording were left to implementer discretion per the plan's own phrasing ("Adjust `v2_evidence`/`test_path` to the exact test function names actually used if Step 3's implementation names them differently") and are reflected verbatim in the `INFRA-264` ledger entry's `test_path`.

## Test Summary

`python3 -m pytest tests/tools/test_generate_registry.py tests/tools/test_done_checker_static.py -v --tb=short` — 102 passed, 0 failed (50 in `test_generate_registry.py`: 41 pre-existing + 9 new; 29 pre-existing in `test_done_checker_static.py`, all still green with unchanged call-site behavior confirmed by cross-check).

## Files Changed

- `tools/generate_registry.py`
- `tests/tools/test_generate_registry.py`
- `docs/parity_ledger/infrastructure.yaml`

## Completion Summary

Added a `--check` drift-detection dry-run mode to `tools/generate_registry.py`: it regenerates the registry in-memory, diffs the parsed entry list against the on-disk `docs/REGISTRY.yaml` (ignoring the live-timestamp header), writes nothing, and exits 0 (in sync) / 1 (doc frontmatter errors, unchanged precedence) / 2 (drift or missing output). CI coverage comes for free via a new non-`slow` test in `tests/tools/test_generate_registry.py::TestRealDocsTree` that already runs inside the `api-tools` job's `pytest tests/tools` invocation — no `.github/workflows/test.yml` edit required. New parity ledger entry `INFRA-264` documents this as a third, independent guarantee alongside `INFRA-183` (output shape) and `INFRA-263` (Finalize-time auto-regen).
