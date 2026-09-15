---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT
phase: done
date: 2026-09-15
tags: [process-improvement, workflows, data-quality]
---

# TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT

## Title
Three more `python3 -c`-only modules exit 0 silently when run directly — `ticket_field_values.py` nearly caused a ticket to be recorded as validated when nothing had been checked

## Status
DONE

## Tier
standard

## Type
repair

## Priority
P2

## Request Summary
`TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` fixed this defect for
`tools/gate_checks/done_checker_static.py`: the module had no `__main__`/`argparse`, so invoking it
the obvious way imported it, did nothing, and exited **0** — indistinguishable from a clean pass.
That ticket's Out of Scope explicitly deferred the sibling modules pending a decision. The decision
is made: fix them.

Confirmed still true on 2026-09-15 (`grep -c "__main__\|argparse"` = **0** for each):

| Module | Matches |
|---|---|
| `tools/parity_ledger_scan.py` | 0 |
| `tools/registry_query.py` | 0 |
| `tools/ticket_field_values.py` | 0 |

**This is not hypothetical — it produced a near-miss during the scoping of this very batch.** While
validating a new ticket, `agent-working-design` ran
`python3 tools/ticket_field_values.py <path>`, received **no output and exit 0**, and came within
one step of recording the ticket as body-field-validated. Nothing had been checked; the module had
imported and exited. The real validation (via `python3 -c` calling `check_ticket_field_values`)
happened to agree, but it could as easily have been a FAIL and the ticket would have been committed
as "validated" either way.

`ticket_field_values.py` is the sharpest case because CLAUDE.md names it as the authority for
`## Tier`/`## Status`/`## Priority` body fields — a validator whose silent no-op is byte-identical
to its success output.

The same class cost another session several hours on 2026-09-14 (see
`TCK-20260914-VENV-NAMING-CI-PARITY-SWAP`'s own history for the adjacent silent-failure pattern).

## Scope
- Add a CLI entry point (`argparse` + `__main__`) to each of the three modules, exposing their
  existing primary function(s) for a path/id argument, printing a readable result and exiting
  non-zero on failure.
- **Purely additive.** Every existing consumer imports these as plain functions (that is the
  documented convention — see `done_checker_static.py`'s own module docstring for the pattern and
  `tools/gate_checks/done_checker_static.py`'s CLI block for the shape to mirror). No existing call
  site may change behaviour.
- Mirror the existing marker/stdout contract used by the `gate_checks` modules where it applies, so
  output is machine-readable as well as human-readable.

## Out of Scope
- Changing what any of the three modules actually validate.
- Auditing the rest of `tools/` for further instances. If one is noticed in passing, record it here
  rather than widening scope — `vocabulary.py` is a known additional candidate (also 0 matches) and
  is deliberately left out until someone establishes whether it has a sensible CLI surface at all.
- Any change to `done_checker_static.py`, already fixed.

## Acceptance Criteria
- [x] `python3 tools/parity_ledger_scan.py <args>`, `python3 tools/registry_query.py <args>` and
      `python3 tools/ticket_field_values.py <path>` each produce readable output and a meaningful
      exit code.
- [x] Each exits **non-zero** when its underlying check fails, and 0 only on a real pass (or a
      successful query, for `registry_query.py`, which has no PASS/FAIL "check" semantics of its
      own — see Implementation Notes).
- [x] A test per module asserts **presence of output**, not merely a return value —
      `result.stdout.strip()` asserted before any return-code check, in every new CLI test across
      all 3 modules. (Same AC `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`
      used; its test shape was reused directly.)
- [x] A test pins that the existing function-level import path still works unchanged for each
      (`test_cli_still_importable_and_callable_as_plain_function[s]` in each of the 3 test files).
- [x] `--help` produces usage text rather than silence, for all 3 modules.

## Related Tickets
- `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE` (done) — the same defect,
  fixed for the fourth module; follow its CLI block and test shape
- `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN` (open) — adjacent
  work in the same gate family
- `TCK-20260915-MONITORING-ANOMALY-DETECTION-EPIC` (done) — the arc this silent-failure class
  belongs to

## Related Docs
- `CLAUDE.md` — names `tools/ticket_field_values.py` as the body-field authority
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — the pattern catalogue

## Related Stored Artifacts
- `stored_artifacts/TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE/`

## Related Code Areas
- `tools/parity_ledger_scan.py`
- `tools/registry_query.py`
- `tools/ticket_field_values.py`
- `tools/gate_checks/done_checker_static.py` (reference implementation, do not modify)

## Assumptions / Open Questions
- Each module's "primary function" needs choosing per module; `ticket_field_values.py`'s is
  `check_ticket_field_values(path)`. The other two need a look before deciding what the CLI should
  expose — do not assume a single obvious entry point. Resolved: `parity_ledger_scan.py` also has
  one clear primary function (`find_p0_intersection`); `registry_query.py` genuinely has two
  (`candidate_tags_from_text`, `filter_registry`), confirmed by reading the file in full rather
  than assuming — exposed as two mutually exclusive CLI modes.
- Whether these should additionally be wired into a `make` target is open. The done-checker fix did
  not add one; consistency argues for matching it. Resolved: followed that precedent, no Makefile
  changes.

## Implementation Notes
See `staging_artifacts/TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT/investigation.md` for the full
per-module primary-function analysis.

Reproduced the defect first: ran all 3 modules directly, confirmed each prints nothing and exits 0
(matching the ticket's own `grep -c "__main__\|argparse"` = 0 finding), before writing any fix.

All 3 mirror `tools/gate_checks/done_checker_static.py`'s own CLI shape exactly: `main(argv=None)
-> int` + argparse + `if __name__ == "__main__": sys.exit(main())`.

- `ticket_field_values.py`: positional `ticket_path`; calls `check_ticket_field_values()`; exits 1
  on any FAIL. Verified the exact near-miss scenario from this ticket's own Request Summary no
  longer happens: `python3 tools/ticket_field_values.py <real ticket>` now prints a real
  `PASS`/`FAIL` line instead of silence.
- `parity_ledger_scan.py`: positional `files_changed` (`nargs="+"`) + `--ledger-dir`; calls
  `find_p0_intersection()`; exit 0 + `PASS` line = no P0 entry depends on any changed file (safe
  to skip Parity); exit 1 + one `FAIL` line per hit otherwise. Verified against the real corpus:
  `src/observability/event_extractor.py` correctly surfaces the real, already-known `FAC-013`
  intersection this file's own existing test (`test_detects_real_fac013_p0_intersection`) already
  covers at the function level — now also reachable via the CLI.
- `registry_query.py`: two mutually exclusive modes, since neither of its two real functions is a
  single obvious entry point (confirmed by reading the whole file, not assumed) — `--text` runs
  `candidate_tags_from_text`; `--layers`/`--tags` runs `filter_registry` against the real
  `docs/REGISTRY.yaml`. Neither function has PASS/FAIL "check" semantics (both are pure queries),
  so this module's own meaningful exit-code contract is narrower than the other two: 0 = a query
  ran (regardless of result count), 1 = no mode selected or the registry file is missing. Recorded
  explicitly rather than force-fitting a PASS/FAIL shape this module's own nature doesn't have.

No Makefile targets added, matching `done_checker_static.py`'s own precedent for the same fix
shape, per this ticket's own Assumptions note.

## Test Summary
- `tests/tools/test_ticket_field_values.py`: 4 new tests — CLI pass/fail via subprocess (presence
  of output asserted before the return code), `--help`, function-level import pin. 12/12 pass.
- `tests/tools/test_parity_ledger_scan.py`: 5 new tests — CLI no-intersection/intersection paths
  (synthetic ledger fixture), `--help`, a real-corpus end-to-end CLI run reproducing the file's own
  existing `FAC-013` function-level test through the actual subprocess, function-level import pin.
  10/10 pass.
- `tests/tools/test_registry_query.py`: 6 new tests — CLI `--text` and `--layers` modes against
  the real registry, no-mode-selected exits non-zero with visible stderr (not silent), `--help`,
  missing-registry-file exits non-zero, function-level import pin for both functions. 12/12 pass.
- Full `tests/tools/` suite: 2738 passed (0 failures) after this ticket's changes.

## Files Changed
- `tools/ticket_field_values.py` — `main()` + CLI entry point added.
- `tools/parity_ledger_scan.py` — `main()` + CLI entry point added.
- `tools/registry_query.py` — `main()` + CLI entry point added (two modes).
- `tests/tools/test_ticket_field_values.py`, `tests/tools/test_parity_ledger_scan.py`,
  `tests/tools/test_registry_query.py` — CLI test coverage above, appended to each existing file.

## Completion Summary
Reproduced the silent no-op for all 3 modules first (confirmed today, matching the ticket's own
`grep` finding), then added a real CLI entry point to each, mirroring
`done_checker_static.py`'s own shape exactly. `ticket_field_values.py` and `parity_ledger_scan.py`
each had one clear primary function to expose; `registry_query.py` genuinely had two (confirmed by
reading the file in full, not assumed), exposed as two mutually exclusive modes rather than forcing
one. `registry_query.py`'s own exit-code contract is narrower than the other two's (0/1 for
query-ran/error, not PASS/FAIL) since it has no check semantics of its own — recorded explicitly.
Every new test asserts presence of output before checking the exit code, and every module keeps a
pin proving its existing function-level import path (the formal pipeline's own `python3 -c` call
sites) still works unchanged. No Makefile targets added, matching the sibling fix's own precedent.
