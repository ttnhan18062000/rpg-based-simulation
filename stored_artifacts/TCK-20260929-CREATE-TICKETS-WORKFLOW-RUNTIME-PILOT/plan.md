---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT
artifact_type: plan
tags: [workflows, create-tickets, agent-monitoring, process-improvement]
---

# Plan — TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT

## Ordered steps (as executed)

1. **Syntax fix.** Escape the two nested backticks in `create-tickets.js` (lines 613, 778) so the
   file parses under acorn with the runtime's exact options. Verify with a real acorn parse
   before touching anything else — the ticket's own blockers were "confirmed by trying," so the
   fix must be too, not assumed correct from reading the diff.
2. **`args.start_ts` in place of `captureTs()`/`bash('date ...')`.** Add `start_ts` to the
   documented `args` and to the top-of-file validation block (mirroring the existing `source`
   check's exact shape, per AC4). Remove `captureTs()` entirely (not left as dead code) and wire
   `startTs` directly from `args.start_ts`.
3. **`runCommand()` helper + reroute the 3 remaining `bash()` call sites through it.**
   `writeSidecar`, `clearSidecar`, and the tag-registry check keep their exact command strings and
   marker-parsing logic — only the executor changes, from `bash()` to a low-effort `agent()` with
   a fixed `{exit_code, stdout}` schema. Preserve every existing fail-open `log()` WARNING exactly.
4. **`execution_mode: "workflow"`** in the one `record_run.py` call site's literal — this script's
   own code only ever runs when the native tool executes it for real, so no runtime branching is
   needed (see investigation.md's "New finding" on this).
5. **`generate_retro.py`'s execution-mode split** gains the `"workflow"` bucket everywhere
   `"pipeline"`/`"hand"`/`"unlabelled"` are enumerated (the grouping dict, the summary loop, the
   rendered table's row list) — checked by grep for all three sites, not just the first one found.
6. **`docs/agent-monitoring/schema.md`**'s `execution_mode` field row gets the third value
   documented.
7. **Tests**, in this order (each run immediately after its own edit, not batched to the end):
   a. Re-run the 5 AC3-named tests + `test_workflow_meta_conformance.py` after step 3 — expected
      to pass unchanged (they pin structural properties the refactor preserves), which is itself a
      useful signal that the refactor didn't accidentally change behavior it wasn't supposed to.
   b. Update `test_run_execution_mode_field_wiring.py` for the per-file expected literal after
      step 4.
   c. Update `test_generate_retro.py`'s execution-mode tests (four-group instead of three) and the
      two golden-report literals after step 5.
   d. Update `test_step0_ts_orchestrator.py`'s two assertions that expected `create-tickets.js` to
      still have `captureTs()` after step 2, and add a new test for the `args.start_ts` replacement.
   e. Add a new `test_workflow_runtime_acorn_parse.py` (AC1) — a real acorn parse, not a text
      pattern, that skips cleanly without node/acorn.
8. **`SKILL.md` rewrite** — native `Workflow({scriptPath, args})` as primary, hand-translation kept
   as a documented fallback (including the `execution_mode` override note from step 4's finding).
9. **`docs/ai/skills.md`** — reverse its "not available" claim; state which one script is actually
   ported so far and why the other three aren't (their own acorn/bash blockers, out of scope here).
10. **Real pilot run.** Pick a genuinely real, small, not-yet-ticketed proposal (checked against
    `tickets/done/` first — see investigation.md), get `start_ts` via `date -u ...`, invoke
    `Workflow({scriptPath, args})` for real, and record the four Scope-6 measurements plus the
    AC7 recommendation in `stored_artifacts/<this ticket>/pilot_measurement.md`.
11. **`TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME`** gets a dated note (AC8) — stays in backlog.
12. Move this ticket to `tickets/done/`, staging artifacts to `stored_artifacts/`, record
    monitoring (hand-orchestrated closure), update `tickets/working_log.csv`.

## Scope guards

- Do **not** touch `implement-ticket.js`, `implement-epic.js`, or `simq-audit.js` beyond reading
  them for the acorn parse-status list (AC7) and the `bash()`/`Date.now()` counts already stated
  in the ticket. No backtick fixes, no `runCommand()` porting, in any of the three.
- Do **not** change the gate-check architecture of any workflow — `create-tickets.js` has no gate
  checks of its own (the tag-registry check is a filter, not a pass/fail gate on the whole run),
  so this ticket's `runCommand()` exposure genuinely is small, as the ticket's Assumptions section
  states. Do not extrapolate that safety to `implement-ticket.js` in the recommendation without
  saying explicitly why it doesn't transfer.
- If the pilot run's real proposal produces real tickets (expected — that's what the tool does),
  do not implement them as part of this ticket. Report them as pilot output in
  `pilot_measurement.md` and leave them for a future batch.

## Acceptance-criteria map

| AC | Where addressed |
|---|---|
| 1 | `tests/tools/test_workflow_runtime_acorn_parse.py` (new) |
| 2 | Same file's `_acorn_parse_all_workflows` implicitly proves no `bash(`/`Date.now(`/etc. remain (acorn would still parse a file containing dead `bash(` identifiers — the real pin is the grep-based manual verification in investigation.md plus the AC3 tests, which read the `writeSidecar`/`clearSidecar` regions directly) |
| 3 | The 5 named AC3 tests, re-run unmodified and passing |
| 4 | `test_step0_ts_orchestrator.py::test_ts_orchestrator_run_start_time_comes_from_args_start_ts` (new) |
| 5 | `test_run_execution_mode_field_wiring.py` (updated) + `test_generate_retro.py`'s four-group tests (updated) |
| 6 | `docs/ai/skills.md` + `.claude/skills/create-tickets/SKILL.md`, both rewritten; `test_workflow_meta_conformance.py` confirms `SKILL.md` still covers every declared phase |
| 7 | `stored_artifacts/TCK-20260929-CREATE-TICKETS-WORKFLOW-RUNTIME-PILOT/pilot_measurement.md` |
| 8 | `tickets/backlogs/TCK-20260710-EXECUTABLE-WORKFLOW-RUNTIME.md` dated note |

## Deviations from the ticket's own framing

None material. One small addition beyond the letter of Scope item 4: the `SKILL.md` fallback path
now explicitly says to use `"execution_mode":"pipeline"` rather than blindly copying the JS
literal — the ticket didn't call this out, but leaving it unstated would have made the fallback
path silently mislabel its own runs as native the first time anyone actually used it.
