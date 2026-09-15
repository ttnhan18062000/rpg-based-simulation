---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: test_plan
ticket_id: TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
phase: open
date: 2026-09-14
tags: [claude-md, process-improvement, workflows, data-quality]
---

# Test Plan — TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE

## Acceptance-criteria → test mapping

| AC | Test |
|---|---|
| CLI prints readable PASS/FAIL, exits non-zero on FAIL | `test_cli_prints_readable_output_and_exits_nonzero_on_known_failure` |
| Test asserts presence of output, not just exit code | same test — explicitly asserts `result.stdout` non-empty AND `returncode != 0`, both, so the test itself would fail against a silent-but-correctly-coded regression |
| Function-level consumers still work unchanged | `test_cli_still_importable_and_callable_as_plain_functions` |
| `-W error` no longer raises `SyntaxError` | `test_no_syntax_warning_under_dash_w_error` (uses `-B` to force a fresh compile, not relying on a stale `.pyc`) |
| append + closure tool → 1 row or loud failure | `test_calling_append_then_closure_tool_for_same_ticket_refuses_duplicate_and_exits_nonzero` |
| CLAUDE.md bullets cross-reference | manual read-back after edit — no automated test exists for CLAUDE.md prose; verify by reading both bullets independently and confirming each references the other |
| Adjacent ticket carries the warning | manual read-back after edit — same, no automated test for ticket prose |

## Regression coverage (existing suites that must stay green)

- `tests/tools/test_done_checker_static.py` (1950 lines, comprehensive) — run in full; Part 1's
  changes are additive (new `main()`/`argparse`/helper functions + one docstring `r"""` fix) and
  must not perturb any existing `check_*`/`run_*` test.
- `tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer` — the
  AST sole-writer guard. Part 2 adds a read-only `parse_working_log()` call to
  `record_hand_orchestrated_closure.py`, not a new `open(..., "a")`/`open(..., "w")` call, so this
  guard should be unaffected — run it explicitly to confirm rather than assume.
- Any existing test file for `record_hand_orchestrated_closure.py` itself (check
  `tests/tools/`/`tests/agent-monitoring/` for one before writing Part 2's new tests, to follow its
  established fixture pattern for CWD-relative path handling rather than inventing a new one).
- `tests/tools/test_working_log_content_duplicate_check.py` /
  `tests/tools/test_working_log_duplicate_check.py` — Related Code Areas lists
  `working_log_content_duplicate_check.py` as "read only, do not modify," but run these anyway
  since Part 2's guard changes what rows can ever land in `working_log.csv`, and their real-corpus
  ratchet tests read the live file.

## New test files/additions

- `tests/tools/test_done_checker_static.py` — 4 new tests (see plan.md Part 1c) appended, not
  interleaved, to minimize diff noise against the existing 1950-line file.
- `record_hand_orchestrated_closure`'s test coverage — extend its existing test file if one exists,
  else create `tests/tools/test_record_hand_orchestrated_closure.py` following this repo's
  established `tests/tools/test_<module>.py` naming convention.

## Manual verification steps (not test-suite-automatable)

1. `python3 tools/gate_checks/done_checker_static.py --ticket-id
   TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` against this ticket's own
   real in-progress state, confirm readable output.
2. `python3 -W error tools/gate_checks/done_checker_static.py --ticket-id <any-real-ticket-id>` —
   confirm no `SyntaxError`/`SyntaxWarning`.
3. Re-read `CLAUDE.md`'s two edited bullets cold (as if seeing only one, not both) to confirm each
   is self-sufficient to avoid the double write.
4. Re-read the adjacent ticket's new subsection to confirm it doesn't contradict or duplicate
   existing text there.

## Out-of-scope verification (explicitly not tested here, per ticket's own Out of Scope)

- No test added for `check_working_log_exactly_one_row`'s false-positive-on-reopen behavior — that
  stays `TCK-20260913-...-REJECTS-LEGITIMATE-REOPEN`'s own responsibility.
- No test added asserting `DUPLICATE_PAIR_CEILING` changed — it must not, per Out of Scope.
- No CLI added to `parity_ledger_scan.py`/`registry_query.py`/`ticket_field_values.py` — explicitly
  deferred to the user's own scope decision.
