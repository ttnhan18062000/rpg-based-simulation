---
status: open
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22B-TICK-INDEX
phase: open
date: 2026-06-20
tags: [decision-explanation, observability, tick-index, phase-2]
---

# TCK-20260619-E22B-TICK-INDEX

## Title
Epic 2.2B · Decision Trace Tick-Index Sidecar

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
`decision_trace.jsonl` (from E22A) is a sequential file. Random tick access requires a full scan. This ticket adds a sidecar `decision_trace_index.json` mapping `tick → byte_offset` so the REST API can do O(1) byte-seek reads without scanning the full file.

**Requires:** TCK-20260619-E22A-TRACE-WRITER

## Scope

### Create `src/observability/cognition/tick_index.py`

```python
class DecisionTraceIndex:
    """Maintains a tick→byte_offset sidecar for decision_trace.jsonl."""

    def __init__(self, run_dir: str):
        self._trace_path = os.path.join(run_dir, "decision_trace.jsonl")
        self._index_path = os.path.join(run_dir, "decision_trace_index.json")
        self._index: dict[int, int] = {}  # tick → byte offset

    def rebuild(self) -> None:
        """Scan decision_trace.jsonl and rebuild the full index."""
        self._index = {}
        with open(self._trace_path, "r") as f:
            while True:
                offset = f.tell()
                line = f.readline()
                if not line:
                    break
                try:
                    entry = json.loads(line)
                    tick = entry["tick"]
                    if tick not in self._index:
                        self._index[tick] = offset
                except (json.JSONDecodeError, KeyError):
                    continue
        with open(self._index_path, "w") as f:
            json.dump({str(k): v for k, v in self._index.items()}, f)

    def lookup(self, tick: int) -> list[dict]:
        """Return all entries for a given tick via byte-seek."""
        if not self._index:
            self._load()
        offset = self._index.get(tick)
        if offset is None:
            return []
        results = []
        with open(self._trace_path, "r") as f:
            f.seek(offset)
            while True:
                line = f.readline()
                if not line:
                    break
                try:
                    entry = json.loads(line)
                    if entry["tick"] != tick:
                        break  # past this tick's entries
                    results.append(entry)
                except (json.JSONDecodeError, KeyError):
                    break
        return results

    def _load(self) -> None:
        with open(self._index_path, "r") as f:
            raw = json.load(f)
        self._index = {int(k): v for k, v in raw.items()}
```

### Wire index rebuild into `DecisionTraceWriter`

After each `write_trace()` call (or every N writes for performance), call `index.rebuild()` to keep the sidecar current. Since `decision_trace.jsonl` is append-only, the index only needs to append the new tick→offset entry (not full rebuild on every write). Simpler: rebuild at run end (in `close()`), not on every write.

## Out of Scope
- REST API (E22C)
- Index compression

## Acceptance Criteria
- `decision_trace_index.json` exists alongside `decision_trace.jsonl` after a run
- Format: `{"1": 0, "2": 234, "3": 512, ...}` (tick as string key, byte offset as int)
- `DecisionTraceIndex.lookup(tick=5)` returns correct entries without reading from file offset 0
- `test_tick_index_o1_lookup` passes

## Related Tickets
- TCK-20260619-E22-DECISION-EXPLAIN (parent epic)
- TCK-20260619-E22A-TRACE-WRITER (required first)
- TCK-20260619-E22C-REST-API (blocked on this)

## Related Code Areas
- `src/observability/cognition/tick_index.py` (new)
- `src/observability/cognition/decision_trace_writer.py` (call index.rebuild() in close())

## Assumptions / Open Questions
- Should the index be rebuilt incrementally (on every write) or at run end? At run end is simpler. Incremental is better for long-running recovery — decide during implementation based on the run lifecycle.

## Test Summary
```bash
pytest tests/unit/observability/test_decision_trace.py::test_tick_index_o1_lookup -x -v
```

## Files Changed
_To be filled on completion._

## Completion Summary
_To be filled on completion._
