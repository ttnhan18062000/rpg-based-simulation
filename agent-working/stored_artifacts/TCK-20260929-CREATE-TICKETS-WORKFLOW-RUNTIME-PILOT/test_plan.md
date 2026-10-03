---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT
artifact_type: test_plan
tags: [workflows, create-tickets, agent-monitoring, process-improvement]
---

# Test Plan — TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT

No JS test runner exists in this repo for `.claude/workflows/*.js` (established precedent across
every sibling test file for these scripts) — coverage is static source-text parsing (existing
pattern) plus one new real-parser check (acorn), plus a real end-to-end pilot run as the ultimate
integration test (Scope item 6/AC7), which pytest cannot express as an assertion.

## Normal flow
- `create-tickets.js` parses under acorn with the runtime's exact options
  (`test_workflow_runtime_acorn_parse.py::test_create_tickets_js_parses_under_workflow_runtime_acorn_options`).
- `writeSidecar`/`clearSidecar`/tag-check still preserve their marker-parsing and fail-open
  WARNING behavior after rerouting through `runCommand()`
  (`test_create_tickets_sidecar_reset_and_failure_visibility.py`,
  `test_sidecar_clear_reaches_scoped_file.py`,
  `test_epic_create_tickets_sidecar_orchestrator.py`, `test_create_tickets_tag_scope.py` — all
  re-run unmodified and passing, proving the refactor is behavior-preserving at the level these
  tests check).
- `execution_mode: "workflow"` is written and `generate_retro.py` reports it as a fourth group
  (`test_run_execution_mode_field_wiring.py`, `test_generate_retro.py`).
- The real pilot run itself: one real `/create-tickets`-equivalent invocation via
  `Workflow({scriptPath, args})`, producing a real ticket (`TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR`),
  with `execution_mode: "workflow"` confirmed in the resulting run record and tool-call attribution
  confirmed by direct inspection of the resulting shard files — see `pilot_measurement.md`.

## Edge cases
- Missing `args.start_ts` → structured `INVALID_ARGS`, not a throw
  (`test_ts_orchestrator_run_start_time_comes_from_args_start_ts`).
- `runCommand()`'s underlying `agent()` call returning `null` (API failure / user skip) — every
  call site guards with `(result && result.stdout) || ''`, so a null result degrades to "no marker
  found," which each site's existing fail-open logic already treats as a WARNING-worthy failure,
  never a throw. Not independently unit-testable without a JS runtime, but the guard is present at
  all three call sites and verified by direct source read in investigation.md.
- Acorn/node absent (e.g. a worktree that never ran `npm ci` under `frontend/`) → the new test
  file skips cleanly via `pytest.mark.skipif`, not an error (AC1's own explicit requirement).

## Failure modes
- A stray `execution_mode: "workflow"` literal appearing in a file that hasn't actually been
  ported yet would misrepresent hand-narration as native execution —
  `test_only_create_tickets_js_sets_execution_mode_workflow` (new) checks all 4 workflow files.
- A future edit reintroducing `bash(`/`Date.now(`/`Math.random(`/argless `new Date(` into
  `create-tickets.js` — not independently pinned by a dedicated grep-test beyond the acorn parse
  (acorn would still parse a file containing an unused `bash` identifier reference, since it's just
  an undefined-at-runtime free variable, not a syntax error) — this is a known gap, noted rather
  than silently left uncovered: a future ticket touching this file should re-verify by grep, as
  investigation.md's own verification did, not assume the acorn test alone catches regressions here.

## Regression-prone paths
- The two golden/fixture tests in `test_generate_retro.py` that pin exact rendered report text —
  these are the tests most likely to break on any future change to the execution-mode table's
  rendering, and did in fact break during this ticket's own implementation (caught immediately by
  running the full suite, not assumed safe from reading the diff).
- `test_step0_ts_orchestrator.py`'s `create-tickets.js`-specific assertions — this file is shared
  across 3 workflow scripts; a future port of `implement-epic.js` or `implement-ticket.js` to the
  native runtime will need the same kind of targeted per-file assertion flip this ticket made for
  `create-tickets.js`, not a blanket rewrite of the whole file.

## Anti-drift guards
- `test_workflow_runtime_acorn_parse.py::test_acorn_parse_status_matches_pilot_recorded_baseline`
  pins today's known acorn parse status for all 4 named workflow scripts, so a silent future
  regression (or an unremarked fix) in `implement-ticket.js`/`simq-audit.js` is visible here first,
  not just in a stale planning-doc claim (the exact failure mode `TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR`,
  this pilot's own real output ticket, is about).

## Explicitly out of scope for this test plan
- Testing `implement-ticket.js`/`implement-epic.js`/`simq-audit.js` behavior beyond their acorn
  parse status — no code in those files changed.
- Load/performance testing of the native `Workflow` tool itself — out of this repo's control
  surface.

## Coverage run (final, before close)

```
pytest tests/tools/ -k "create_tickets or generate_retro or workflow or sidecar or step0 or tag_scope or execution_mode" -q
```
438 passed (plus the new acorn-parse test file, which skips in this worktree — acorn not
installed locally — and passed when manually verified against the main checkout's
`frontend/node_modules/acorn` via a local symlink, gitignored, not committed).
