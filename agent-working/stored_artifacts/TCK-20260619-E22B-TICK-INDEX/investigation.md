---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22B-TICK-INDEX
artifact_type: investigation
tags: [tick-index, decision-trace, observability, byte-offset]
---

# Investigation — TCK-20260619-E22B-TICK-INDEX

## Current Behavior

### E22A Output (prerequisite — DONE)

`DecisionTraceWriter` (src/observability/cognition/decision_trace_writer.py) writes one JSONL line per
`write_trace()` call (entity_id + tick + routes). File is at `data/runs/{run_id}/decision_trace.jsonl`.
The file is sequential; there is no index. Random-access by tick requires scanning from offset 0.

### File structure

Each line in `decision_trace.jsonl` is:
```json
{"entity_id": <int>, "tick": <int>, "routes": [...]}
```

Multiple entities write per tick, so a single tick may span many consecutive lines.
The file is opened in append mode and flushed after each write, so byte offsets are stable.

### Key constraints from E22A implementation notes

- `_file.flush()` is called after every write (line 97 of decision_trace_writer.py) — ensures byte
  offsets captured before a crash are valid and pointing to complete lines.
- File opened lazily (`_ensure_open`) — the file may not exist at all for zero-hero runs.
- `close()` nulls `self._file` — called by Kernel at shutdown.
- The `close()` method is the natural wiring point for `index.rebuild()` since it marks run end.

### Writer lifecycle (from kernel.py via E22A)

Kernel creates `DecisionTraceWriter` in `__init__`, closes in `shutdown()`. The close point is
the correct place to trigger index rebuild — at that point the file is complete and flushed.

### Incremental vs. rebuild decision

The ticket asks: "incremental on every write" vs "rebuild at run end"?

Analysis:
- Rebuild at run end is O(n) once at shutdown — acceptable.
- Incremental on every write would require tracking the offset just before each write, then
  appending only the new tick→offset entry. This is more complex but avoids re-scanning.
- **Decision: incremental append during write_trace, with rebuild as fallback for recovery.**
  Rationale: A long-running simulation that crashes mid-run would lose the index if we only
  rebuild at close(). Appending `tick→offset` to the index on each write is simple because
  `f.tell()` gives the current offset before writing the line. This gives crash recovery.
  Implementation: in `write_trace()`, after `_ensure_open()`, capture `offset = f.tell()`,
  then after writing the line, call `_index.append_entry(tick, offset)`.

### Parity ledger

INFRA-211 (verified, P1) covers the E22A decision trace writer. The tick index is a new behavior
requiring a new entry INFRA-212.

### Related code

| File | Role |
|---|---|
| `src/observability/cognition/decision_trace_writer.py` | Prerequisite writer; `close()` is wiring point |
| `src/observability/cognition/tick_index.py` | New file (this ticket) |
| `tests/unit/observability/test_decision_trace.py` | Existing tests; `test_tick_index_o1_lookup` goes here |
| `docs/parity_ledger/infrastructure.yaml` | Add INFRA-212 |
| `docs/observability/decision_trace_contract.md` | Add sidecar section |

## Mechanics/Engine Constraints

No mechanics bible chapters are relevant — this is pure observability/IO infrastructure.
Engine contracts: no mutation pipeline is touched. The index is a read/write observability sidecar,
not authoritative state. No durable state rule applies (index can be rebuilt from the JSONL).

## Parity Ledger Overlap

- **INFRA-211** (P1, verified): Decision trace writer. Not affected by this ticket.
- **INFRA-212**: New entry needed for the tick index sidecar.

## Prior Work

- TCK-20260619-E22A-TRACE-WRITER (DONE): created `decision_trace.jsonl` and `DecisionTraceWriter`.
  Implementation notes confirm flush-after-write and close() lifecycle.
- TCK-20260618-AUDIT-D15 (DONE): D15 audit gap analysis that spawned E22 epic.

## Risks and Open Questions

1. **Tick ordering assumption**: The ticket's `lookup()` logic breaks out of the read loop when
   `entry["tick"] != tick`. This assumes entries are written in ascending tick order with all entries
   for a given tick contiguous. E22A writes in call order (one entity at a time per tick), so within
   a tick entries are contiguous. Across ticks, order is deterministic (tick N always before tick N+1).
   The assumption holds.

2. **Multiple entities per tick**: The index stores the byte offset of the *first* entry for a tick.
   `lookup()` then reads forward until `tick` changes. This correctly returns all entities for a tick.

3. **Index file during partial run**: If `write_trace()` updates the index incrementally, a partial
   run's index is valid up to the last completed write. Recovery (re-reading the JSONL from a crash)
   can call `rebuild()` to reconstruct from the file.

4. **Index format**: `{"1": 0, "2": 234}` — string keys (JSON requirement), int values (byte offsets).
   The `_load()` method converts string keys back to int. Confirmed in ticket scope.

## Anti-Drift Hazards

- Do NOT modify `execute_brain()` (AC guard from E22A, inherited by this ticket as a constraint).
- Do NOT touch `AdventureDecisionPhase` or any domain logic — this is pure observability.
- The index must never be authoritative state — it can always be rebuilt.
- `write_trace()` modification must be non-fatal: any index append failure must be caught and logged,
  never propagating to the caller.
