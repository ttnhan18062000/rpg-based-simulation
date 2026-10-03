---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
phase: open
date: 2026-09-14
tags: [claude-md, process-improvement, workflows, data-quality]
---

# Investigation — TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE

All claims below re-verified directly against the checked-out branch (`done-checker-unreachable-by-hand`,
based on `origin/main` post-#194), not accepted from the ticket's own Request Summary on report.

## Defect A — double working_log write

`tools/agent-monitoring/record_hand_orchestrated_closure.py:58` imports `append_working_log_row`
from `tools/working_log_writer.py`, and `record_hand_orchestrated_closure.py:207` calls it
unconditionally inside a `try/except OSError` block (lines 206-213). There is no existence check
against `tickets/working_log.csv` before the call — only a catch for the write itself failing
(disk error), never for "this ticket/title pair already has a row."

Confirmed CLAUDE.md's "After Work" section (this repo's global project instructions) contains two
separate bullets:
1. "Append to the bottom of `tickets/working_log.csv` ... via `append_working_log_row()` — never
   hand-roll this write."
2. "If this ticket was closed by hand-orchestration ... record its own run + event coverage
   yourself ... Use `tools/agent-monitoring/record_hand_orchestrated_closure.py`."

Neither bullet references the other. A session following bullet 1 first (to close the ticket) and
then bullet 2 (to record monitoring coverage, as instructed) produces two `working_log.csv` rows
for the same `(ticket_id, title)`. The wrapper's own docstring (final line, ~45 lines in) does warn
— "do not append that row by hand separately when using this wrapper, or the ticket will get a
duplicate working_log entry" — but that text is only visible to someone who reads the *callee's*
source, not to a session following the *caller-side* instructions in CLAUDE.md.

**What does not help**: `tests/tools/test_working_log_writer.py::test_working_log_csv_has_exactly_one_writer`
walks `tools/` for write-mode `open()` calls against `tickets/working_log.csv` and asserts there is
exactly one (`working_log_writer.py` itself). Both call sites in this defect route through that one
sanctioned writer — the AST guard is correctly satisfied and structurally cannot see a duplicate
produced by two *legitimate* calls to the one writer, only an unsanctioned second writer. This
matches `TCK-20260914-MONITORING-SURFACE-DEAD-MECHANISMS` item 6's own finding: "a content check on
the artifact itself... can [catch this]; a writer-scan guard structurally cannot."

## Defect B — done_checker_static.py has no CLI entry point

`grep -n '__main__\|argparse\|sys.argv' tools/gate_checks/done_checker_static.py` returns zero
matches. The module's own docstring (line 24) states the convention explicitly: "plain functions,
plain tuple returns, no argparse/CLI — consumed exclusively via `python3 -c "..."`."

`check_working_log_exactly_one_row` (line 824) is wired live into `run_finalize_selfcheck`'s
aggregate (line 968), which is itself called from `.claude/workflows/implement-ticket.js`'s
Finalize phase via a `python3 -c` one-liner (`implement-ticket.js:1728-1729`) — this is the formal
pipeline's own invocation and is untouched by this ticket.

Reproduced the exact symptom directly:
```
$ find tools/gate_checks -name __pycache__ -exec rm -rf {} +
$ python3 -B -c "import sys; sys.path.insert(0,'tools/gate_checks'); sys.path.insert(0,'tools'); import done_checker_static"
tools/gate_checks/done_checker_static.py:385: SyntaxWarning: invalid escape sequence '\`'
  """True if section_text should be treated as "no docs/ paths flagged."
```
(exit code 0, no other output). Confirmed the docstring at `_is_none_section` (line 384) is a plain
`"""` string, not raw (`r"""`), and its line 391 contains `- \`docs/...\`` — a backslash-backtick
sequence Python does not recognize as an escape. The warning only fires on a fresh bytecode compile
(a `.pyc` cache absorbs it on subsequent imports), which matches the ticket's account of a session
seeing it once and concluding the tool is broken, then moving on.

Running the module the "obvious" way (`python3 tools/gate_checks/done_checker_static.py
--ticket-id ...`) currently just imports the module (no `__main__` block executes anything) and
exits 0 with no output beyond the warning above — indistinguishable from a clean pass.

## Existing consumers that must keep working unchanged (Scope constraint)

- `.claude/workflows/implement-ticket.js:1630` — `python3 -c "... from
  tools.gate_checks.done_checker_static import run_static_precheck ..."` (Verify phase).
- `.claude/workflows/implement-ticket.js:1728-1729` — `python3 -c "... from
  gate_checks.done_checker_static import run_finalize_selfcheck ..."` (Finalize phase).
- `.claude/workflows/implement-ticket.js:1262` — `from gate_checks.done_checker_static import
  clean_data_runs_early` (post-Test cleanup checkpoint).
- `.claude/workflows/implement-ticket.js:1807/1834` — `check_monitoring_write_recorded`,
  `check_tag_drift` (Finalize-tail advisory checks).
- `.claude/workflows/implement-ticket.js:355` — `from done_checker_static import
  _frontmatter_has_unregistered_tags`.
- `tests/tools/test_done_checker_static.py` (1950 lines) — imports every `check_*` function
  directly and calls them as plain functions.

None of these use a CLI; all import the module and call functions directly. Adding an
`if __name__ == "__main__":` block with `argparse` is additive and does not change any of these
call sites' behavior, confirmed by reading each one above.

## Related check function signatures (needed for the CLI's argument surface)

- `run_static_precheck(ticket_id: str, tier: str, start_ts: str | None) -> list[dict]` (line 686)
  — Part A, 8 conditions, list-of-dict shape `{"condition", "status", "evidence"}`.
- `run_finalize_selfcheck(ticket_id: str, tier: str) -> list[dict]` (line 963) — Part B, 4
  conditions. Read the full function body including its return statement (lines 963-974) to
  confirm, not assume: it returns the identical shape to `run_static_precheck`,
  `[{"condition": name, "status": status, "evidence": evidence}, ...]` — the module docstring's
  "same return shape as `run_static_precheck`" claim (line 964) checks out. Both aggregates can
  share one rendering function in the new CLI.

- `check_ticket_field_values_valid` (line 330) resolves the ticket path itself
  (`tickets/inprogress/{ticket_id}.md`), and via `tools/ticket_field_values.py` /
  `tools/generate_registry.py::parse_body_section` can extract the `## Tier` body field from a
  ticket file. This is the mechanism the new CLI can reuse to auto-detect `--tier` from
  `--ticket-id` alone, so the CLI's minimal invocation (`--ticket-id <TCK-ID>`, per AC #1's literal
  wording) does not also require a second mandatory `--tier` flag.

## Defect A fix — mechanism chosen

Implementer's call per the ticket's own note. Chose: **detect-then-fail-loudly**, not silent
idempotent skip, per Implementation Notes' explicit preference ("prefer failing loudly ... if the
choice is close — a silent dedupe is another mechanism that does not report what it did"). Design:
before calling `append_working_log_row()` inside `record_hand_orchestrated_closure.py`, read
`tickets/working_log.csv` via the existing tolerant parser (`working_log_parser.parse_working_log`,
not a raw `csv.reader` — this session's own prior work established that a naive reader can
misclassify known-malformed historical rows; reusing the tolerant parser avoids reintroducing that
class of bug) and check whether a `(ticket_id, title)` pair matching this call's own arguments
already exists among the kept (non-ambiguous) rows. If found: skip the append entirely (so the
row-count guarantee — "produces one row, not two" — holds unconditionally) and print an `ERROR:`
line to stderr naming the existing duplicate, then exit the process with a non-zero code. The run/
event monitoring writes (which happen earlier in `main()`) are unaffected either way — this defect
is specific to the working-log append step, not "monitoring write failure," so it is not governed
by CLAUDE.md's Hard Rule that a monitoring write failure must never fail the workflow (that rule is
about the run/events writes actually failing to land, not about refusing a detected duplicate).
