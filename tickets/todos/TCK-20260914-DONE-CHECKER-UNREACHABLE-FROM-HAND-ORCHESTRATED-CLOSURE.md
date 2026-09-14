---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
phase: open
date: 2026-09-14
tags: [claude-md, process-improvement, workflows, data-quality]
---

# TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE

## Title
`done_checker_static.py` has no CLI entry point, so the gate guarding hand-orchestrated closures cannot be run by hand — and CLAUDE.md's own "After Work" bullets instruct a double working-log write that the same gate would have caught

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Two instruction-level defects, found together on 2026-09-14 when `rpg-feature-planning`'s
implementer produced a duplicate `tickets/working_log.csv` row while following CLAUDE.md exactly.
Both were verified against `origin/main` by this session rather than accepted on report.

**Defect A — the instructions prescribe a double write.** CLAUDE.md's "After Work" section says to
append the working-log row via `tools/working_log_writer.py::append_working_log_row()` and never
hand-roll the write. A later bullet in the *same section* says hand-orchestrated closures must
record their own coverage via `tools/agent-monitoring/record_hand_orchestrated_closure.py`. That
wrapper **already performs the working-log append itself** — it imports `append_working_log_row`
(line 58) and calls it unconditionally (line 207), with no existence check and no idempotency
guard. A session that follows both bullets in order writes the row twice while doing exactly what
it was told.

The wrapper's docstring does warn about this, as the final line of a ~45-line docstring:
"do not append that row by hand separately when using this wrapper, or the ticket will get a
duplicate working_log entry." That warning is only visible to someone reading the *callee's*
source. It cannot reach the session that reached for `append_working_log_row` first, which is why
the trap recurred despite being documented — twice on 2026-09-14 alone, and this is the second
occurrence of the specific "both writers legitimate, one calling the other" variant.

Note what does **not** help here: `tests/tools/test_working_log_writer.py`'s sole-writer AST guard
scans `tools/` for *unsanctioned* writers. Every writer in this defect is sanctioned. A writer-level
guard cannot detect a duplicate produced by two correct writers, which is direct evidence for the
"guard the artifact, not the writer" argument recorded in
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS`.

**Defect B — the gate that would have caught it cannot be run by hand.**
`tools/gate_checks/done_checker_static.py::check_working_log_exactly_one_row`
(`tools/gate_checks/done_checker_static.py:824`, wired live into the aggregate at line 968) returns
`FAIL: 2 rows found — duplicate Finalize run` for exactly this defect. It did not fire, and not by
anyone's choice: **the module has no CLI entry point at all.** There is no `__main__`, no
`argparse`, no `sys.argv` anywhere in it. Its own docstring (line 24) states the convention
plainly: "plain functions, plain tuple returns, no argparse/CLI — consumed exclusively via
`python3 -c "..."`."

Running it the obvious way (`python3 tools/gate_checks/done_checker_static.py --ticket-id ...`)
imports the module and exits silently. The *only* output is an unrelated `SyntaxWarning: invalid
escape sequence '\`'` from a non-raw docstring near line 391. No PASS, no FAIL, no usage text, no
error. That is indistinguishable from a gate that ran and found nothing wrong, and it reads as a
broken tool — the implementer who hit it tried twice (once with `--help`), reasonably concluded the
tool had no CLI, and moved on.

This is the same failure-mode-is-silence family as the eight mechanisms catalogued in
`TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS`, but located in the **invocation surface** rather
than in the logic. The gate's logic is entirely correct. It is simply unreachable on the one path
CLAUDE.md explicitly sanctions.

## Scope
- Add a CLI entry point to `tools/gate_checks/done_checker_static.py` (`argparse` + `__main__`)
  exposing the existing aggregate for a given `--ticket-id`, with a non-zero exit on FAIL. This is
  **purely additive**: the formal pipeline consumes the module as plain functions
  (`.claude/workflows/implement-ticket.js`, `.claude/agents/done-checker.md`,
  `.claude/skills/implement-ticket/SKILL.md`), and that path must keep working unchanged.
- Fix the invalid escape sequence near `done_checker_static.py:391` (make the docstring raw or
  escape the backtick). It is cosmetic today — no CI job runs `-W error`, confirmed — but it is the
  sole output a hand-orchestrating session currently sees, so it actively signals "broken tool".
- Make the double write harmless at the artifact level rather than by warning: either make
  `record_hand_orchestrated_closure.py`'s append idempotent for an already-present
  `(ticket_id, title)` row, or give it an explicit opt-out flag. Implementer's call which, with the
  reason recorded in the ticket.
- Correct CLAUDE.md's "After Work" section so the two bullets cross-reference: the
  `append_working_log_row()` bullet must say that `record_hand_orchestrated_closure.py` already
  performs this append, and the closure-tool bullet must say it covers the working-log row. A
  session reading either bullet alone must not be led into the double write.
- Add the cross-gate interaction warning to
  `tickets/todos/TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN.md`
  (see Assumptions below — this is the highest-risk item in the bundle).

## Out of Scope
- Fixing `check_working_log_exactly_one_row`'s false positive on legitimate `BLOCKED`-then-`DONE`
  reopens. That is `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN`'s
  own work and must not be pre-empted here; this ticket only adds a warning to it.
- Re-measuring or changing `DUPLICATE_PAIR_CEILING` (currently 46,
  `tools/gate_checks/working_log_content_duplicate_check.py:57`). It correctly caught the real
  violation on 2026-09-14 and was correctly **not** raised in response. Leave it alone.
- Retroactively auditing existing duplicate rows in `tickets/working_log.csv`. The ratchet freezes
  the historical baseline deliberately; whether that backlog gets cleaned is a separate question.
- Giving the other `python3 -c`-consumed modules the same CLI treatment. They **do** share this
  defect — verified during scoping, see Assumptions — but widening the fix to all of them is a
  scope decision the ticket's author deliberately left to the user rather than taking silently.
  Fix `done_checker_static.py` here, because it is the one with a demonstrated real-world miss.

## Acceptance Criteria
- [ ] `python3 tools/gate_checks/done_checker_static.py --ticket-id <TCK-ID>` prints a readable
      per-condition PASS/FAIL result and exits non-zero when any condition fails.
- [ ] A test asserts the CLI produces output and a non-zero exit for a ticket with a known-failing
      condition — i.e. the test fails if the entry point ever silently returns nothing again. This
      is the real regression guard; the defect was silence, so the test must assert *presence of
      output*, not merely a correct return value.
- [ ] The existing function-level consumers still work unchanged; a test pins that the aggregate is
      still importable and callable as plain functions (the `implement-ticket.js` path).
- [ ] `python3 -W error tools/gate_checks/done_checker_static.py --ticket-id <TCK-ID>` no longer
      raises `SyntaxError` from the docstring escape.
- [ ] Calling `append_working_log_row()` and then `record_hand_orchestrated_closure.py` for the same
      ticket produces **one** row, not two — or the second call fails loudly with a message naming
      the existing row. Silent double-write is not an acceptable end state. Covered by a test that
      performs both calls in that order.
- [ ] CLAUDE.md's two "After Work" bullets cross-reference each other, and neither can be followed
      in isolation to produce the double write.
- [ ] `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN` carries a warning
      naming this ticket and the interaction described under Assumptions.

## Related Tickets
- `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` (done, PR #194) — the eight-mechanism
  catalogue this extends; its item 6 ratchet is what caught the duplicate that surfaced this.
- `TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN` (open) — the adjacent
  work on the same check. See Assumptions.
- `TCK-20260912-WORKING-LOG-APPEND-HELPER` (done) — established `append_working_log_row()` as the
  sole sanctioned writer and added the AST guard that cannot see this defect class.
- `TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION` (done) — CRLF/LF writer variant.
- `TCK-20260906-WORKING-LOG-MERGE-UNION-DUPLICATION-GAP` (done) — `merge=union` variant.
- `TCK-20260903-HAND-ORCHESTRATED-TICKETS-MISSING-MONITORING-COVERAGE` (done) — created the closure
  wrapper whose append is half of Defect A.

## Related Docs
- `CLAUDE.md` — "After Work" section (the defect's actual location).
- `docs/plans/agent_infrastructure/reachability_verification_findings.md` — section 7 addendum;
  this ticket is the ninth instance of the pattern recorded there, and the first where the
  mechanism's logic is correct and only its invocation surface fails.

## Related Stored Artifacts
- `stored_artifacts/TCK-20260912-WORKING-LOG-APPEND-HELPER/` — investigation/plan/test_plan for the
  sole-writer guard whose blind spot this ticket documents.

## Related Code Areas
- `tools/gate_checks/done_checker_static.py` (line 24 docstring convention, line ~391 escape,
  line 824 `check_working_log_exactly_one_row`, line 968 aggregate wiring)
- `tools/agent-monitoring/record_hand_orchestrated_closure.py` (line 58 import, line 207 append)
- `tools/working_log_writer.py` (`append_working_log_row`)
- `tools/gate_checks/working_log_content_duplicate_check.py` (the ratchet that caught it — read
  only, do not modify)
- `CLAUDE.md` ("After Work")

## Assumptions / Open Questions
- **The highest-risk item in this bundle is the interaction with the adjacent ticket.**
  `check_working_log_exactly_one_row` is one of only two gates that catch the duplicate class, and
  after this ticket establishes that it is unreachable by hand, the ratchet is currently the only
  one that fires in practice. `TCK-20260913-...-REJECTS-LEGITIMATE-REOPEN` proposes fixing that same
  check's false positives on legitimate reopens. A fix there that drops the count assertion, rather
  than teaching it to distinguish a reopen from a duplicate, would remove the gate while looking
  like a pure improvement in its own diff. That is the exact "gate maintenance is
  diff-indistinguishable from gate weakening" shape recorded as Finding 8 in the reachability
  findings doc. Hence the warning requirement in Scope.
- **The defect is not confined to `done_checker_static.py` — this was verified while scoping this
  very ticket, not assumed.** `tools/parity_ledger_scan.py`, `tools/registry_query.py`, and
  `tools/ticket_field_values.py` all contain zero occurrences of `__main__` or `argparse`. That is
  four modules, and at least one of them is a validator the project's own CLAUDE.md names as the
  authority for ticket body fields.

  `ticket_field_values.py` deserves its own note, because it caught the author of this ticket in
  the act. Validating this file with
  `python3 tools/ticket_field_values.py <path>` printed **nothing** and exited **0**. That is not a
  pass — it imported the module and did no work. The real result (a genuine PASS, obtained via
  `python3 -c` calling `check_ticket_field_values`) happened to agree, but it could as easily have
  been a FAIL, and the ticket would have been committed as "validated" either way. A validator
  whose silent no-op is byte-identical to its success output is the defect in this ticket,
  reproduced in a second module, inside the same hour.

  Whether to widen the fix to all four modules is a **scope decision for the user**, recorded here
  with evidence rather than decided unilaterally. The argument for widening: the failure mode is
  silent and has now demonstrably misled two different sessions. The argument against: only
  `done_checker_static.py` has a confirmed real-world consequence, and a four-module change is
  harder to review.
- Whether the historical duplicate backlog frozen by the ratchet needs its own cleanup is
  unanswered here, same as in the parent ticket.

## Implementation Notes
- Everything asserted in Request Summary was verified against `origin/main` (not a working tree —
  this session twice produced false claims from a stale checkout during the parent batch, and both
  are recorded in the findings-doc addendum). Re-verify before relying on any line number; the CLI
  addition itself will shift the ones near the end of the module.
- The `SyntaxWarning` and the missing CLI are one user-visible symptom, not two: the warning is the
  only thing printed, so it is what a session actually sees when the gate fails to run. Fixing the
  CLI without fixing the warning leaves a confusing first impression; fixing the warning without the
  CLI leaves silence. Both, or the symptom persists.
- Prefer failing loudly over silently deduplicating in `record_hand_orchestrated_closure.py` if the
  choice is close — a silent dedupe is another mechanism that does not report what it did, which is
  the pattern this whole line of work exists to stop.

## Test Summary
_To be completed by the implementer._

## Files Changed
_To be completed by the implementer._

## Completion Summary
_To be completed by the implementer._
