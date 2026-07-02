---
ticket_id: TCK-20260619-E22-DECISION-EXPLAIN
phase: plan
date: 2026-06-20
---

# Plan: Decision Explanation Model — Epic Scope

## Child Ticket Sequence

```
E22A (trace writer — LIGHT mode) ──► E22B (tick-index sidecar) ──► E22C (REST endpoints)
```

E22A must complete before E22B (index file is a sidecar to decision_trace.jsonl).
E22B must complete before E22C (REST endpoint reads via index for O(1) lookup).

## Child Ticket Summary

| Ticket | Scope | Deliverable |
|---|---|---|
| E22A-TRACE-WRITER | Add decision_trace.jsonl writer after execute_brain() in LIGHT mode | `src/observability/cognition/decision_trace_writer.py` (new) |
| E22B-TICK-INDEX | Build tick→byte-offset index sidecar on each write | `src/observability/cognition/tick_index.py` (new) + `decision_trace_index.json` |
| E22C-REST-API | Add 3 REST endpoints for entity decision queries | `src/api/routes/decisions.py` (new) |

## Acceptance Path

1. E22A: 10-tick LIGHT run produces `decision_trace.jsonl` with per-entity scored routes
2. E22B: `decision_trace_index.json` maps tick N → byte offset; O(1) seek verified
3. E22C: `GET /api/v1/observability/entities/7/decisions?tick=5` returns ranked routes with score breakdown
4. Create new doc: `docs/observability/decision_trace_contract.md` (schema + index format + REST contract)

## Key Design Decisions

- Write in LIGHT mode: follow `cognition_graph_snapshots.jsonl` writer pattern but lower the mode threshold
- One JSONL line per entity per tick (entity_id + tick + top-5 routes with full score breakdown)
- Index is rebuilt atomically on each flush (not incremental) — simpler and safe for short runs
- REST routes use synchronous file reads (no hot-path simulation pressure); presenter layer shapes the response
- Do NOT change execute_brain() — only add writer after it returns
