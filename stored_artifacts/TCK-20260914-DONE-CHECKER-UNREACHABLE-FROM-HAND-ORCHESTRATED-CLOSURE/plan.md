---
status: active
layer: ticket
authority: P1
audience: agent
artifact_type: plan
ticket_id: TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
phase: open
date: 2026-09-14
tags: [claude-md, process-improvement, workflows, data-quality]
---

# Plan — TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE

## Part 1 — `tools/gate_checks/done_checker_static.py`: CLI entry point + escape fix

### 1a. Fix the invalid escape sequence (AC #4)
Line 384's docstring is a plain `"""..."""` containing `\`` at line 391. Make it a raw string
(`r"""..."""`) — the simplest fix, and the convention already used elsewhere in this file for
docstrings containing backslashes (confirm during implementation; fall back to escaping the
backtick as `\\\`` only if a raw string breaks something else in that same docstring, e.g. a
trailing single backslash before the closing quotes).

### 1b. Add `--ticket-id` CLI (AC #1, #3)
New code at the bottom of the module, after all existing functions, strictly additive:

```python
def _resolve_tier(ticket_id: str, tier_override: str | None) -> str:
    """Auto-detect ## Tier from the ticket file (inprogress, else done) unless overridden."""
    if tier_override:
        return tier_override
    for candidate in (Path(f"tickets/inprogress/{ticket_id}.md"), Path(f"tickets/done/{ticket_id}.md")):
        if candidate.exists():
            body = _strip_frontmatter(candidate.read_text(encoding="utf-8"))
            # reuse ticket_field_values.check_body_field_enum or parse_body_section directly
            ...
    return "standard"  # last-resort default if the file can't be found/parsed; never crash the CLI


def _render_results(label: str, results: list[dict]) -> bool:
    """Print one line per condition, return True if any FAILed."""
    any_fail = False
    for r in results:
        marker = "FAIL" if r["status"] == "FAIL" else r["status"]
        if r["status"] == "FAIL":
            any_fail = True
        print(f"[{label}] {r['condition']}: {marker} — {r['evidence']}")
    return any_fail


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ticket-id", required=True)
    parser.add_argument("--tier", choices=["hotfix", "standard", "epic"], default=None,
                         help="Auto-detected from the ticket's own ## Tier body field if omitted.")
    parser.add_argument("--part", choices=["precheck", "finalize", "both"], default="both")
    parser.add_argument("--start-ts", default=None, help="Only used by --part precheck/both.")
    args = parser.parse_args(argv)

    tier = _resolve_tier(args.ticket_id, args.tier)
    any_fail = False
    if args.part in ("precheck", "both"):
        any_fail |= _render_results("precheck", run_static_precheck(args.ticket_id, tier, args.start_ts))
    if args.part in ("finalize", "both"):
        any_fail |= _render_results("finalize", run_finalize_selfcheck(args.ticket_id, tier))

    print(f"RESULT: {'FAIL' if any_fail else 'PASS'} for {args.ticket_id} (tier={tier})")
    return 1 if any_fail else 0


if __name__ == "__main__":
    sys.exit(main())
```

Needs `import argparse` added to the top-level imports (not currently imported). `_resolve_tier`
reuses `_strip_frontmatter` (already imported from `generate_registry`) plus
`ticket_field_values.parse_body_section`/`check_body_field_enum` — read those two functions'
exact signatures during implementation and call them directly rather than re-deriving tier
parsing by hand a second time.

This is purely additive — no existing function signature, import, or module-level name changes.
The `python3 -c "from ... import run_static_precheck ..."` / `run_finalize_selfcheck` call sites
in `implement-ticket.js` never touch `main()` or `__name__`.

### 1c. Tests (`tests/tools/test_done_checker_static.py`)
- `test_cli_prints_readable_output_and_exits_nonzero_on_known_failure` — build a tmp fixture with
  a real failing condition (e.g. two working_log rows for the same ticket_id, matching Defect A's
  own shape), invoke via `subprocess.run([sys.executable, "tools/gate_checks/done_checker_static.py",
  "--ticket-id", ..., ...], capture_output=True)`, assert `result.stdout` is non-empty (presence of
  output — the actual regression this ticket guards, not just the return code), assert
  `result.returncode != 0`, assert the failing condition's name appears in stdout.
- `test_cli_exits_zero_and_prints_pass_when_all_conditions_pass` — the mirror, all-green fixture.
- `test_cli_still_importable_and_callable_as_plain_functions` — `from
  gate_checks.done_checker_static import run_static_precheck, run_finalize_selfcheck`, call both
  directly (not via subprocess), assert they still return the pre-existing shape — pins the "must
  keep working unchanged" constraint at the Python-import level, not just by inspection.
- `test_no_syntax_warning_under_dash_w_error` — `subprocess.run([sys.executable, "-W", "error", "-B",
  "-c", "import sys; sys.path.insert(0, 'tools/gate_checks'); sys.path.insert(0, 'tools'); import
  done_checker_static"])`, assert `returncode == 0` (a `SyntaxError` under `-W error` would make
  this nonzero) — `-B` forces a fresh compile so the test cannot pass by accident via a cached
  `.pyc` the way a hand-run session originally missed the defect.

## Part 2 — `tools/agent-monitoring/record_hand_orchestrated_closure.py`: idempotency guard

### 2a. Add a read-only duplicate check
```python
import csv  # if not already needed elsewhere; parse_working_log is preferred, see below
...
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from working_log_parser import parse_working_log  # noqa: E402

def _existing_row_for(csv_path: Path, ticket_id: str, title: str) -> dict | None:
    """Read-only. Returns the first kept row matching (ticket_id, title), else None. Uses the
    tolerant parser (not a raw csv.reader) so a known-malformed historical row is never
    misread as a false match or a false miss."""
    if not csv_path.exists():
        return None
    result = parse_working_log(csv_path)
    for parsed in result.rows:
        if parsed.record is None:
            continue
        if (parsed.record.get("ticket_id", "").strip() == ticket_id
                and parsed.record.get("title", "").strip() == title):
            return parsed.record
    return None
```

### 2b. Wire it before the append (fails loudly, per Implementation Notes' stated preference)
Replace the existing `try: append_working_log_row(...) except OSError` block with:
```python
working_log_path = Path("tickets/working_log.csv")
existing = _existing_row_for(working_log_path, args.ticket_id, args.title)
if existing is not None:
    print(
        f"ERROR: {working_log_path} already has a row for (ticket_id={args.ticket_id!r}, "
        f"title={args.title!r}) at timestamp {existing.get('timestamp')!r} — refusing to append "
        "a duplicate. This is the double-write shape append_working_log_row() + this script "
        "produce when both are called for the same ticket close "
        "(TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE). The run/event "
        "monitoring records above were still written.",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    append_working_log_row(...)  # unchanged
    log_ok = True
except OSError as e:
    ...  # unchanged
```
`sys.exit(1)` here is not governed by CLAUDE.md's "monitoring write failure must never fail the
workflow" rule — that rule covers the run/events *writes actually failing*; this is a distinct,
deliberate refusal of a detected duplicate, after the run/event writes (which happen earlier in
`main()`) have already succeeded.

### 2c. Test (new or extend an existing test file for this module)
- `test_calling_append_then_closure_tool_for_same_ticket_refuses_duplicate_and_exits_nonzero` —
  call `append_working_log_row()` directly against a tmp CSV, then invoke
  `record_hand_orchestrated_closure.py`'s CLI (subprocess or direct `main()` call with a
  monkeypatched `Path("tickets/working_log.csv")` — check how the module resolves that path
  today; may need a `--log-path` override param added for testability, in which case add it as an
  optional CLI flag defaulting to the real path, purely additive) for the identical
  `(ticket_id, title)`. Assert: exactly one row remains in the CSV afterward (`AC` "produces one
  row, not two"), the process exits non-zero, stderr names the existing row.
- `test_different_title_same_ticket_id_is_not_treated_as_a_duplicate` — a reopen-with-different-
  title case should NOT trip this guard (this is a different defect class from
  `TCK-20260913-...-REJECTS-LEGITIMATE-REOPEN`'s own concern, but worth a negative test to pin the
  boundary precisely).

**Design note discovered while planning**: `record_hand_orchestrated_closure.py`'s `main()`
resolves `tickets/working_log.csv` via a bare `Path("tickets/working_log.csv")` (relative to CWD),
not an injectable parameter — confirm this during implementation and add a `--log-path` override
(default unchanged) if the existing test suite for this module already needs one, matching however
that suite currently handles CWD-relative paths in tests (check `tests/tools/` for an existing
`record_hand_orchestrated_closure` test file first, then follow its established pattern rather
than inventing a new one).

## Part 3 — CLAUDE.md cross-reference (AC #6)

Edit `CLAUDE.md`'s "After Work" section (two bullets, lines ~87-90 and ~98-102):
- Bullet 1 (`append_working_log_row()`) gains a clause: "... — for a hand-orchestrated closure,
  `tools/agent-monitoring/record_hand_orchestrated_closure.py` (below) already performs this
  append internally; do not call both for the same ticket close, or the row is written twice."
- Bullet 2 (`record_hand_orchestrated_closure.py`) gains a clause noting it already covers the
  working-log append, so the previous bullet's helper is not needed in addition to it.

Read the exact current text before editing (already captured in this ticket's own conversation
context) and word the edit so a session reading *either* bullet alone, without reading the other,
still gets warned.

## Part 4 — Warning on the adjacent ticket (AC #7)

Add a new subsection (not editing existing Scope/AC text) to
`tickets/todos/TCK-20260913-DONE-CHECKER-WORKING-LOG-ROW-COUNT-REJECTS-LEGITIMATE-REOPEN.md`,
named e.g. "## Cross-Gate Interaction Warning (added by
TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE)", stating: after this
ticket, `check_working_log_exactly_one_row` / the content-duplicate ratchet
(`working_log_content_duplicate_check.py`) are the only two mechanisms that catch the dual-writer
duplicate class; a fix here that drops the row-count assertion instead of teaching it to
distinguish a legitimate reopen from a duplicate would silently remove one of only two remaining
gates while reading as a pure improvement in its own diff (Finding 8's shape, reachability
findings doc section 7). Read that ticket's current text first so the new subsection doesn't
duplicate or contradict anything already there.

## Order of implementation
1. Part 1 (CLI + escape fix + tests) — self-contained, no dependency on the others.
2. Part 2 (idempotency guard + tests) — independent of Part 1.
3. Part 3 (CLAUDE.md) — trivial, no code dependency.
4. Part 4 (adjacent-ticket warning) — trivial, no code dependency.
5. Run the full relevant regression set together
   (`test_done_checker_static.py` + any new/extended `record_hand_orchestrated_closure` test file +
   `test_working_log_writer.py` for the sole-writer guard, to confirm the new read-only
   `parse_working_log` call in Part 2 does not trip it).
6. Document-Update phase: check whether `docs/ai/ticket-lifecycle.md`'s existing
   `done_checker_static` references need updating to mention the new CLI (advisory, not required
   by AC, but worth checking per the doc-staleness gate).
