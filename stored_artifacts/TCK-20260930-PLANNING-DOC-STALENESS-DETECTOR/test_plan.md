---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260930-PLANNING-DOC-STALENESS-DETECTOR
artifact_type: test_plan
tags: [documentation]
---

# Test Plan

## Proof Plan
| AC | level | proof kind | oracle source | expected effect | selected commands |
|---|---|---|---|---|---|
| 1 | unit | regression | ticket AC1; ledger n/a (process tooling) | findings are `(doc_path, ticket, text)` tuples; CLI exit 0 with and without findings | `pytest tests/tools/test_planning_doc_staleness_check.py` |
| 2 | unit | regression | ticket AC2 (frozen copies of the two real cases) | both the idea doc and the "ready, schedule later" items are flagged | same |
| 3 | unit | architecture guard | ticket AC3 | file bytes and mtime unchanged after a run and after the CLI | same |
| 4 | prose | n/a | ticket AC4 | both design decisions recorded with rationale in the ticket and `docs/ai/ticket-lifecycle.md` | (read) |

Extra cases: unshipped item not flagged, already-resolved heading skipped, ticket older than the doc not matched, `## Disposition` closure not matched, `archive/` skipped, missing directories return [].

## Scoped Pytest Commands
`.venv/bin/python -m pytest tests/tools/test_planning_doc_staleness_check.py -q`
