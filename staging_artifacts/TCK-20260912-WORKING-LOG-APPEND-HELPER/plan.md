---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
artifact_type: plan
tags: [data-quality, process-improvement]
---

# Plan — TCK-20260912-WORKING-LOG-APPEND-HELPER

Evidence in `investigation.md`. Order: build the helper, switch the one real caller to it, point
the Finalize prose at it, add the sole-writer guard, update CLAUDE.md.

## Step 1 — The helper module

New `tools/working_log_writer.py` (beside the existing `tools/working_log_parser.py`, per the
ticket's own Assumptions — one owner, not a particular location, but pairing reader/writer by
name is the clearest signal of that ownership to a future reader).

```python
def append_working_log_row(
    timestamp: str, ticket_id: str, title: str, status: str, summary: str, artifacts_path: str,
    path: Path = Path("tickets/working_log.csv"),
) -> None:
```

- Opens `path` with `open(path, "a", newline="", encoding="utf-8")` (matches the existing call's
  `newline=""` — required for `csv.writer` to own line-ending control, not the platform).
- `csv.writer(f, quoting=csv.QUOTE_MINIMAL, lineterminator="\n")`, `.writerow([timestamp,
  ticket_id, title, status, summary, artifacts_path])` — the exact 6-column order
  `working_log_parser.HEADER_FIELDS` expects.
- No monitoring side effects (no run/event recording) — this module's only job is the CSV row,
  matching the ticket's explicit Out of Scope.
- Docstring names both call sites it will have (the closure script, `implement-ticket.js`'s
  Finalize) so it can't quietly drift into single-caller assumptions later.

## Step 2 — Switch the one real caller

`tools/agent-monitoring/record_hand_orchestrated_closure.py`: replace the inline `with
working_log_path.open(...) as f: csv.writer(...).writerow(...)` block with a call to
`append_working_log_row(...)`, passing the same 6 values in the same order. Keep the existing
`try/except OSError` / `log_ok` warning behavior around the call — this ticket does not change
error handling, only who performs the write.

## Step 3 — Point Finalize at the helper

`.claude/workflows/implement-ticket.js`'s Finalize step 4 (~line 1690): replace the per-field
prose description with an instruction to call the helper (`python3 -c "from working_log_writer
import append_working_log_row; append_working_log_row(...)"` or equivalent), passing the same 6
values Finalize already computes (`tid`, ticket title, `DONE`, a one-sentence summary,
`stored_artifacts/${tid}` or the hotfix no-staging-artifacts string). Keep the field-meaning
comments (what `timestamp`/`summary`/`artifacts_path` should contain) — only the *mechanism* of
writing changes, not what a Finalize agent must decide to put in each field.

Add a pin test, `tests/tools/test_finalize_working_log_uses_helper_pin.py`, mirroring
`test_finalize_phase_status_instruction_pin.py`'s raw-source-text pattern: asserts the helper
import/call text is present, inside the Finalize phase block, at the position step 4 occupies
(before step 5's staging-artifacts move, matching the JS's own step ordering).

## Step 4 — Sole-writer guard

New test in `tests/tools/test_working_log_writer.py` (or appended to an existing working-log test
file — Implement's call) that greps `tools/` and `.claude/workflows/` for any `open(` call whose
path argument resolves to `tickets/working_log.csv` in append/write mode, and asserts the only
match is inside `working_log_writer.py` itself. This is the ticket's actual point (per its own
Scope: "a test asserting no module other than the helper writes tickets/working_log.csv, so a
future second path fails in CI rather than on the next merge") — not a nice-to-have alongside the
unit tests, the mechanism that makes "one sanctioned writer" durable rather than aspirational.

## Step 5 — CLAUDE.md

Add one sentence to the After Work bullet about `tickets/working_log.csv`: append via
`tools/working_log_writer.py::append_working_log_row()`, never hand-roll the write (matching the
existing "never insert after the header" sentence's own register).

## Step 6 — Unit tests for the helper itself

`tests/tools/test_working_log_writer.py`:
- A field containing a comma, a quote, and an embedded newline round-trips correctly through
  `working_log_parser.parse_working_log()` afterward (proves the two modules agree on the format,
  not just that the writer runs).
- Output ends in a bare `\n`, zero `\r` bytes anywhere in the appended row.
- Appends after existing content, never truncates, never inserts before the header.
- `record_hand_orchestrated_closure.py`'s own existing tests (`tests/tools/
  test_record_hand_orchestrated_closure.py`) pass unmodified — confirms Step 2's swap preserved
  behavior exactly.

## Honesty in the Completion Summary (carried from the ticket's own Assumptions)

State plainly: this is one sanctioned writer plus a CI guard that catches a second write path
appearing, not a hard lock. An agent can still open the file directly and write to it; nothing in
the filesystem or harness prevents that. Claiming prevention would overstate what Step 4's guard
actually does (catch it in CI on the next run, not block it at the moment of writing).

## Out of Scope (carried from the ticket)

- The row format itself (columns, timestamp precision, quoting) — centralizing who writes it, not
  redesigning what is written.
- Monitoring run/event recording — stays with `record_hand_orchestrated_closure.py`.
- Retrofitting historical rows — PR #167 already normalized line endings on `main`.
- `agent-monitoring/data/*/*.jsonl` writers — `tools/agent-monitoring/writer.py` already owns those.

## Risks

- **Import path**: `record_hand_orchestrated_closure.py` already does `sys.path.insert(0,
  str(Path(__file__).resolve().parent))`-style imports for sibling modules in the same directory;
  `working_log_writer.py` lives one level up (`tools/`, not `tools/agent-monitoring/`), so the
  import needs its own path insert or a package-relative import — verify which convention the rest
  of `tools/agent-monitoring/*.py` already uses for `tools/`-level siblings (e.g.
  `working_log_parser` itself, if already imported anywhere under `agent-monitoring/`) before
  picking one.
- **Grep-based sole-writer guard false positives**: the guard must not flag the parser's own
  read-only `open(path, newline="")` calls, or comments/docstrings that merely *mention*
  `working_log.csv` — scope the grep to actual `open(`/`.open(` calls with a write-capable mode
  argument, not any line containing the filename.
