---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION
artifact_type: test_plan
tags: [data-quality, process-improvement]
---

# Test Plan — TCK-20260911-WORKING-LOG-LINE-ENDING-UNION-DUPLICATION

## Step 1 — writer

- Calling the closure script's working-log append against a `tmp_path` CSV writes a row that ends in
  `\n`, with no `\r` anywhere in the file.
- A field containing a comma, a quote, and an embedded newline still round-trips through
  `tools/working_log_parser.py` (quoting unchanged).
- Existing `record_hand_orchestrated_closure.py` tests pass unmodified.

## Step 2 — attributes

- `git check-attr` reports `text: set`, `eol: lf`, `merge: union` for `tickets/working_log.csv` and for a
  sample `agent-monitoring/data/<week>/tools.jsonl` path.
- `git add --renormalize` on those paths stages nothing (recorded in Implementation Notes).

## Step 3 — CR detector

- Passes on the real tree.
- Fails on a fixture copy with one `\r` injected, naming the file and line.

## Step 4 — reproduction (scratch repo)

- Without `eol=lf`: the merge produces the duplicate block. This proves the test reproduces the real bug.
- With `eol=lf`: no duplicate, no `\r` in the merged blob.
- Host git config can't leak in: `core.autocrlf=false` and identity are set inside the scratch repo.

## Regression

```
pytest tests/integrity/ tests/tools/test_record_hand_orchestrated_closure.py -q
```

