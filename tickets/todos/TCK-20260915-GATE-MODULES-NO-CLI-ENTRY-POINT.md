---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT
phase: open
date: 2026-09-15
tags: [process-improvement, workflows, data-quality]
---

# TCK-20260915-GATE-MODULES-NO-CLI-ENTRY-POINT

## Title
Three more `python3 -c`-only modules exit 0 silently when run directly — `ticket_field_values.py` nearly caused a ticket to be recorded as validated when nothing had been checked

## Status
OPEN

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
- [ ] `python3 tools/parity_ledger_scan.py <args>`, `python3 tools/registry_query.py <args>` and
      `python3 tools/ticket_field_values.py <path>` each produce readable output and a meaningful
      exit code.
- [ ] Each exits **non-zero** when its underlying check fails, and 0 only on a real pass.
- [ ] A test per module asserts **presence of output**, not merely a return value — the failure
      mode here is silence, so a return-value-only test would pass against the broken version.
      (This is the same AC that `TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE`
      used; reuse its test shape.)
- [ ] A test pins that the existing function-level import path still works unchanged for each.
- [ ] `--help` produces usage text rather than silence.

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
  expose — do not assume a single obvious entry point.
- Whether these should additionally be wired into a `make` target is open. The done-checker fix did
  not add one; consistency argues for matching it.

## Implementation Notes
Reproduce the defect first, so the fix is written against observed behaviour: run each module
directly today and confirm it prints nothing and exits 0.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_Open._
