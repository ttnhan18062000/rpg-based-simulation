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

## Step 1/7 — `working_log_writer.py`

- Appending a row with a field containing a comma, a quote, and an embedded newline round-trips
  correctly through `working_log_parser.parse_working_log()` afterward — both modules agree on
  the format, not just "the writer ran without error."
- The appended row ends in a bare `\n`; zero `\r` bytes anywhere in it.
- Appends after existing content in a `tmp_path` fixture file — never truncates, never inserts
  before the header.
- Two consecutive appends both land, in order, at the bottom.
- CLI mode: `main()` with `--data-file <path>` reads a JSON file
  `{timestamp, ticket_id, title, status, summary, artifacts_path}` and appends the row — including
  a case where a field value itself contains a literal double quote, a comma, and an embedded
  newline, proving the file-based contract survives content that would break naive shell/Python
  string-embedding.

## Step 2 — the real caller

- `tests/tools/test_record_hand_orchestrated_closure.py`'s existing suite passes unmodified —
  proves the swap to `append_working_log_row()` preserved behavior exactly.

## Step 3 — Finalize pin

- `test_finalize_working_log_uses_helper_pin.py`: scope the search to the **Finalize agent's own
  prompt string** (the substring between the `` `Finalize ticket ${tid}` `` opening anchor and the
  `` Report each step: DONE / SKIPPED (reason).`, `` closing anchor — verified these two anchors
  exist and correctly bound the prompt, distinct from the 4 legitimate orchestrator-run `python3
  -c` post-Finalize self-checks that follow after the prompt closes), not the wider
  `phase('Finalize')` block. Within that scoped substring: `working_log_writer.py` and
  `--data-file` are both present, and step 4's own text precedes step 5's own text — mirrors
  `test_finalize_phase_status_instruction_pin.py`'s presence/containment/ordering shape. A 4th,
  negative assertion: the substring `python3 -c` does not appear anywhere within that same scoped
  prompt substring at all (not adjacency to `append_working_log_row(` — confirmed via direct read
  that literal adjacency would not fire on a realistic reintroduction, since an import/semicolon/
  quotes would separate the flag from the call).

## Step 4 — sole-writer guard (AST-based)

- Passes on the real repo tree: the AST walk over `tools/**/*.py` finds exactly one write-mode
  `open`/`.open` call whose resolved path argument equals `tickets/working_log.csv`, and it is in
  `working_log_writer.py`.
- **Positive-resolution proof, not assumed**: a dedicated unit test for the resolver itself, run
  against a small synthetic AST/source snippet shaped exactly like Step 1's own design (module
  constant, parameter default referencing it by name, `open(path, "a", ...)`) — proves the
  resolver actually chains through the parameter-default-to-module-constant hop, not just that the
  end-to-end test happens to pass for unrelated reasons.
- Fails on a fixture tree with a second module opening the same resolved path in append mode
  (proves the guard actually detects a second writer, not just that it currently reports one).
- Does not false-positive on: the parser's own read-only `open(path, newline="")` call (no write
  mode); a module opening a different file whose variable is also named `path`; comments/
  docstrings mentioning `working_log.csv` as plain text with no accompanying `open()` call.

## Step 5 — parity ledger

- `write_entry()` call for `INFRA-416` succeeds; the shard's derived index rebuild reports the
  same `entry_count` as before plus zero net new entries (an update, not an insert).
- **Field-preservation, automated, not just prose**: capture `INFRA-416`'s full entry dict before
  this step runs; after `write_entry()`, re-read the entry and assert every field except
  `v2_evidence`/`test_path` (`text`, `status`, `priority`, `divergence_note`, `proof_type`, and any
  other field present) is byte-identical to the captured pre-image. Directly targets Review round
  2's Finding 3 (`write_entry()` is a full-entry replace-by-id; a naively-constructed minimal dict
  would silently drop `text`/`support_boundary`/etc.).
- The two pre-existing `test_path` entries (`test_merge_union_no_cr_bytes.py`,
  `test_merge_union_crlf_duplication_repro.py`) still pass unmodified after Steps 1-2 land.

## Step 6 — CLAUDE.md

- No automated test (prose-only doc change); confirmed by direct read at Verify.

## Regression

```
pytest tests/tools/test_working_log_writer.py tests/tools/test_record_hand_orchestrated_closure.py tests/tools/test_finalize_working_log_uses_helper_pin.py tests/integrity/test_merge_union_no_cr_bytes.py tests/tools/test_parity_ledger_writer.py -q
```
