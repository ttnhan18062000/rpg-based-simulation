---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260619-E22B-TICK-INDEX
artifact_type: plan
tags: [tick-index, decision-trace, observability, plan]
---

# Plan — TCK-20260619-E22B-TICK-INDEX

## Ordered Steps

### Step 1 — Create `src/observability/cognition/tick_index.py`

**Files:** `src/observability/cognition/tick_index.py` (new)

Create `DecisionTraceIndex` class with:
- `__init__(self, run_dir: str)` — sets `_trace_path`, `_index_path`, `_index: dict[int, int]`
- `rebuild(self) -> None` — full scan of JSONL, stores first offset per tick, writes JSON sidecar
- `lookup(self, tick: int) -> list[dict]` — byte-seeks to offset, reads forward until tick changes
- `_load(self) -> None` — reads JSON sidecar, converts str keys → int
- `append_entry(self, tick: int, offset: int) -> None` — incremental update: adds new tick→offset
  to in-memory dict and re-serializes the sidecar (used from write_trace for crash recovery)

All file I/O wrapped in try/except — index failures are non-fatal.

**Scope guard:** No changes to `execute_brain()`, `AdventureDecisionPhase`, or any domain code.

**AC mapped:** "DecisionTraceIndex.lookup(tick=5) returns correct entries without reading from offset 0"

---

### Step 2 — Wire incremental index update into `DecisionTraceWriter.write_trace()`

**Files:** `src/observability/cognition/decision_trace_writer.py` (modify)

In `write_trace()`, after `_ensure_open()`:
1. Capture `offset = self._file.tell()` before writing the line.
2. After writing + flushing the line, call `self._index.append_entry(tick, offset)` — but only
   if `tick` not already in the index (first entity per tick wins — that's the seek target).
3. The `DecisionTraceIndex` instance is created lazily alongside the file open, or in `__init__`.

**Scope guard:** No change to the JSON entry format written to the file. Only observability metadata changes.

**AC mapped:** "decision_trace_index.json exists alongside decision_trace.jsonl after a run"

---

### Step 3 — Wire `rebuild()` into `DecisionTraceWriter.close()`

**Files:** `src/observability/cognition/decision_trace_writer.py` (modify)

In `close()`, after closing the file handle, call `self._index.rebuild()` — this provides a
clean, complete index at run end even if incremental updates were missed due to any error.
Wrap in try/except so index failure never fails the close.

**AC mapped:** "decision_trace_index.json exists alongside decision_trace.jsonl after a run" (guaranteed at close)

---

### Step 4 — Add tests to `tests/unit/observability/test_decision_trace.py`

**Files:** `tests/unit/observability/test_decision_trace.py` (modify — add tests)

Add the following tests (all new, no removals):
1. `test_tick_index_o1_lookup` — AC-required by name; verifies byte-seek correctness
2. `test_tick_index_file_exists_after_close` — sidecar written by close()
3. `test_tick_index_format_correctness` — string keys, int values, offsets match file positions
4. `test_tick_index_lookup_missing_tick` — returns [] for unknown tick
5. `test_tick_index_rebuild_idempotent` — rebuild() twice → identical result
6. `test_tick_index_load_from_disk` — _load() converts str→int keys correctly
7. `test_tick_index_incremental_vs_rebuild` — incremental + rebuild produce identical index

**Scope guard:** Do not modify or remove any existing E22A test. Only add new tests.

---

### Step 5 — Update parity ledger

**Files:** `docs/parity_ledger/infrastructure.yaml` (modify — append INFRA-212)

Add INFRA-212: tick index sidecar behavior. P1, status=verified, test_path pointing to
`test_tick_index_o1_lookup`.

---

### Step 6 — Update `docs/observability/decision_trace_contract.md`

**Files:** `docs/observability/decision_trace_contract.md` (modify)

Add a section "Tick Index Sidecar" describing:
- File location: `decision_trace_index.json` alongside `decision_trace.jsonl`
- Format: `{"<tick>": <byte_offset>, ...}` (string keys, int values)
- Semantics: first byte offset for that tick in the JSONL
- Implementation: `src/observability/cognition/tick_index.py::DecisionTraceIndex`
- Lifecycle: incremental during run, rebuilt on close

---

## Dependency Map

```
Step 1 (tick_index.py)
  └── Step 2 (wire into write_trace) — depends on Step 1
      └── Step 3 (wire rebuild into close) — depends on Step 1
          └── Step 4 (tests) — depends on Steps 1–3
              └── Step 5 (parity) — depends on Step 4 (needs test_path)
                  └── Step 6 (docs) — depends on Steps 1–3
```

## Scope Guards

- Do NOT modify `execute_brain()` (inherited guard from E22A)
- Do NOT modify `AdventureDecisionPhase` or any domain code
- Do NOT change the JSONL format of `decision_trace.jsonl`
- Do NOT expose the index through any API (E22C scope)
- Index failure must NEVER raise — always log and continue

## Acceptance Criteria → Steps

| AC | Step |
|---|---|
| `decision_trace_index.json` exists after run | Steps 2, 3 |
| Format: `{"1": 0, "2": 234, ...}` (str key, int value) | Step 1 |
| `lookup(tick=5)` returns correct entries without reading from offset 0 | Step 1 |
| `test_tick_index_o1_lookup` passes | Step 4 |

## Deviations

_None yet._
