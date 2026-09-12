---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260912-WORKING-LOG-APPEND-HELPER
artifact_type: test_plan
tags: [data-quality, process-improvement]
---

# Test Plan — TCK-20260912-WORKING-LOG-APPEND-HELPER

## Step 1/6 — `working_log_writer.py`

- Appending a row with a field containing a comma, a quote, and an embedded newline round-trips
  correctly through `working_log_parser.parse_working_log()` afterward — both modules agree on
  the format, not just "the writer ran without error."
- The appended row ends in a bare `\n`; zero `\r` bytes anywhere in it.
- Appends after existing content in a `tmp_path` fixture file — never truncates, never inserts
  before the header.
- Two consecutive appends both land, in order, at the bottom.

## Step 2 — the real caller

- `tests/tools/test_record_hand_orchestrated_closure.py`'s existing suite passes unmodified —
  proves the swap to `append_working_log_row()` preserved behavior exactly.

## Step 3 — Finalize pin

- `test_finalize_working_log_uses_helper_pin.py`: the helper call is present in
  `implement-ticket.js`'s source text, inside the Finalize phase block, before the staging-artifacts
  move instruction (step 5's own text) — mirrors `test_finalize_phase_status_instruction_pin.py`'s
  three-assertion shape (presence, phase-block containment, ordering).

## Step 4 — sole-writer guard

- Passes on the real repo tree: exactly one write-mode `open(`/`.open(` call whose path resolves
  to `tickets/working_log.csv`, and it is inside `working_log_writer.py`.
- Fails on a fixture tree with a second module opening the same path in append mode (proves the
  guard actually detects a second writer, not just that it currently reports zero).
- Does not false-positive on the parser's own read-only `open(path, newline="")` call, or on
  comments/docstrings mentioning the filename.

## Step 5 — CLAUDE.md

- No automated test (prose-only doc change); confirmed by direct read at Verify.

## Regression

```
pytest tests/tools/test_working_log_writer.py tests/tools/test_record_hand_orchestrated_closure.py tests/tools/test_finalize_working_log_uses_helper_pin.py tests/integrity/test_merge_union_no_cr_bytes.py -q
```
