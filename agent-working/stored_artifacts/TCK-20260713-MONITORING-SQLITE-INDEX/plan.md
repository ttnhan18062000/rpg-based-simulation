---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260713-MONITORING-SQLITE-INDEX
artifact_type: plan
tags: [agent-monitoring, data-quality, schema]
---

# Implementation Plan — TCK-20260713-MONITORING-SQLITE-INDEX

## Summary

Build `tools/agent-monitoring/build_index.py`, a new, on-demand, full-rebuild-only script that reads `agent-monitoring/{runs,events,tools}.jsonl` exactly once each (strictly read-only) and writes a gitignored SQLite database (`agent-monitoring-index/monitoring.db`, mirroring the `knowledge-index/` whole-directory-gitignore precedent) with `runs`, `events`, and `tools` tables. The approach reuses existing normalization logic by **import, not reimplementation**: `resolved_status` and completeness classification on the `runs` table call `generate_retro._resolve_status()` and `validate._record_is_complete()`/`LEGACY_COMPLETION_FIELDS`/`LEGACY_TERMINAL_STATUS_VALUES` directly, and all three tables derive a `workflow` column via `vocabulary.infer_workflow()` as a fallback when the raw record lacks one — giving downstream queries a ready-made join key without inventing new vocabulary. `validate.load_jsonl()` is reused verbatim for malformed-JSON-line tolerance (warn-to-stderr, skip). `tools.jsonl`'s three confirmed off-schema records are excluded from the `tools` table via a structural validity check (must have non-null `run_id`, `seq`, and a string `tool` field) with a stderr warning per skipped record — never silently dropped, never coerced. `events`/`tools` tables use a surrogate `id` primary key with a non-unique `(run_id, seq)` index, not a `UNIQUE(run_id, seq)` constraint, because live `events.jsonl` data contains historical `(run_id, seq)` duplicates from the pause/resume seq-collision bug that a unique constraint would crash on during rebuild. The Makefile gets one new target, `agent-monitoring-index`, following `knowledge-index:`'s interpreter-fallback shell pattern, placed in the agent-monitoring section and never wired into `test:`/`ci:`/`all:`.

Two scope clarifications carried over from investigation, applied here rather than left open: (1) AC5's "byte-identical... SQLite output" is implemented and tested as **row-count-identical per table** across two consecutive rebuilds — SQLite files are not guaranteed byte-stable across separate writes even with identical logical content (page layout/freelist bookkeeping), and AC5's own wording offers row-count-identical as the fallback form; this plan does not attempt byte-stable page layout as extra unjustified design cost. (2) `resolved_status`/completeness are computed as **Python columns at build/insert time** (via direct import of the existing functions), not as SQL generated columns/views — SQLite has no first-class way to call arbitrary Python normalization logic from a view without registering custom SQL functions, which adds complexity for no benefit over computing once at insert time.

## Steps

### Step 1 — Scaffold `build_index.py`: imports, CLI, no incremental flag
**Files:** `tools/agent-monitoring/build_index.py` (new), `tests/tools/test_build_index.py` (new, skeleton)
**Change:** Create the module with:
- Module docstring stating: reads the 3 JSONL files read-only, full-rebuild only, on-demand only, mirrors `tools/knowledge_search.py::cmd_build()`.
- `sys.path.insert(0, str(Path(__file__).resolve().parent))` (same pattern as `validate.py:21`) so sibling-module imports work when invoked as a script.
- Imports: `from validate import load_jsonl, LEGACY_COMPLETION_FIELDS, LEGACY_TERMINAL_STATUS_VALUES, _record_is_complete`; `from generate_retro import _resolve_status`; `from vocabulary import infer_workflow, CANONICAL_TIERS`. Do not redefine any of these.
- Path constants: `DEFAULT_RUNS_FILE = Path("agent-monitoring/runs.jsonl")`, `DEFAULT_EVENTS_FILE = Path("agent-monitoring/events.jsonl")`, `DEFAULT_TOOLS_FILE = Path("agent-monitoring/tools.jsonl")`, `DEFAULT_DB_PATH = Path("agent-monitoring-index/monitoring.db")`.
- `argparse` surface: `--runs-file`, `--events-file`, `--tools-file`, `--db-path`, all optional overrides defaulting to the constants above (needed so tests can point at fixture corpora instead of the live repo files). **No `--incremental` flag or mode of any kind.**
- `main()` stub wired to `sys.exit(main())` at the bottom; body filled in across Steps 2–6.
- Test file skeleton: imports `build_index` as a module, sets up `_REPO_ROOT`/`_MODULE_PATH` constants mirroring `tests/tools/test_knowledge_search.py`'s top-of-file setup.
**Do NOT touch:** `pre_tool_hook.py`, `post_tool_hook.py`, `record_run.py`, `record_events.py`, `writer.py` — no import of, or call into, any of these from `build_index.py`.
**Verify:** `test_build_index_never_touches_write_path_modules`, `test_build_index_imports_vocabulary_not_reencoded`, `test_no_incremental_build_flag_exists`.

### Step 2 — SQLite schema + full-rebuild scaffolding
**Files:** `tools/agent-monitoring/build_index.py`
**Change:** Add `_create_schema(conn)`:
```sql
CREATE TABLE runs (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    workflow TEXT,
    tier TEXT,
    start_ts TEXT,
    resolved_status TEXT,
    is_complete INTEGER,
    raw_json TEXT NOT NULL
);
CREATE INDEX idx_runs_run_id ON runs(run_id);

CREATE TABLE events (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    seq INTEGER,
    workflow TEXT,
    phase TEXT,
    agent TEXT,
    raw_json TEXT NOT NULL
);
CREATE INDEX idx_events_run_id_seq ON events(run_id, seq);

CREATE TABLE tools (
    id INTEGER PRIMARY KEY,
    run_id TEXT,
    seq INTEGER,
    workflow TEXT,
    tool TEXT NOT NULL,
    raw_json TEXT NOT NULL
);
CREATE INDEX idx_tools_run_id_seq ON tools(run_id, seq);
```
No `UNIQUE` constraint on `(run_id, seq)` for `events` or `tools` — deliberate, see Anti-Drift Notes. Add `build(args)` orchestration function: `db_path.parent.mkdir(parents=True, exist_ok=True)`; `if db_path.exists(): db_path.unlink()` (unconditional full rebuild, mirrors `knowledge_search.py:675-676`); fresh `sqlite3.connect(str(db_path))`; call `_create_schema(conn)`. Ingestion calls (Steps 3–5) and commit/close (Step 6) are wired in next.
**Do NOT touch:** Do not add any `ON CONFLICT`/upsert logic — this is a fresh database every run, never merged into an existing one.
**Verify:** No standalone test yet (schema alone isn't independently AC-mapped); confirmed together with Step 6's `test_build_creates_gitignored_sqlite_db`.

### Step 3 — Ingest `runs.jsonl`: `resolved_status` + completeness
**Files:** `tools/agent-monitoring/build_index.py`, `tests/tools/test_build_index.py`
**Change:** Add `_ingest_runs(conn, records)`. For each record from `load_jsonl(runs_path)` (reused verbatim from `validate.py` — do not reimplement the malformed-JSON warn-and-skip loop):
- `run_id = record.get("run_id")`
- `workflow = record.get("workflow") or infer_workflow(run_id)` (fallback only when the raw field is absent — same pattern `validate.py`/`generate_retro.py` already use elsewhere for other fields)
- `tier = record.get("tier")` (pass-through; optionally cross-check against `CANONICAL_TIERS` with a warn-only stderr note if unrecognized, mirroring the "warn-only vocabulary check" pattern `vocabulary.py`'s docstring references for `record_events.py` — informational only, never fatal, never mutates the value)
- `start_ts = record.get("start_ts")`
- `resolved_status = _resolve_status(record)` — call the imported function exactly as `generate_retro.py` does; do not add extra casing/spelling normalization
- `is_complete = 1 if _record_is_complete(record) else 0` — call the imported function exactly as `validate.py` does
- `raw_json = json.dumps(record, sort_keys=True)` — this serializes the **parsed-in-memory dict** into a SQLite column value; it is not a write to the source `runs.jsonl` file and does not affect AC2.
- `INSERT INTO runs (...) VALUES (...)`. **No dedup**: if the same `run_id` appears on multiple lines (known from `TCK-20260705-MONITORING-RUNID-JOIN`'s Class A findings), each line becomes its own row — dedup stays a consumer-side concern (`generate_retro.py` etc.), not this ticket's.
**Do NOT touch:** `generate_retro.py`, `validate.py` source files — import only. Do not attempt to resolve the `TCK-20260623-TYPE-CHECKER` 6th legacy shape's status — its `resolved_status` legitimately stays `NULL`; do not special-case it.
**Verify:** `test_resolved_status_matches_generate_retro_resolve_status`, `test_completeness_matches_validate_legacy_allowlists`, `test_type_checker_legacy_shape_does_not_crash_build`.

### Step 4 — Ingest `events.jsonl`: tolerate `(run_id, seq)` duplicates
**Files:** `tools/agent-monitoring/build_index.py`, `tests/tools/test_build_index.py`
**Change:** Add `_ingest_events(conn, records)`, same shape as Step 3: `run_id = record.get("run_id")`, `seq = record.get("seq")`, `workflow = record.get("workflow") or infer_workflow(run_id)`, `phase = record.get("phase")`, `agent = record.get("agent")`, `raw_json = json.dumps(record, sort_keys=True)`. `INSERT INTO events (...)`. Because Step 2's schema has no `UNIQUE(run_id, seq)` constraint, two records sharing the same `(run_id, seq)` (the documented pause/resume collision signature) insert as two distinct rows without error.
**Do NOT touch:** Do not call or reimplement `_normalize_phase()`/`_normalize_agent()`/`_canonicalize()`/`_is_legacy_event()` — phase/agent case-fold normalization is explicitly deferred to the sibling `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE` ticket per the investigation's Parity Ledger Overlap note; this ticket's Scope only requires `resolved_status` on the `runs` table, nothing normalized on `events`.
**Verify:** `test_events_table_tolerates_duplicate_run_id_seq`.

### Step 5 — Ingest `tools.jsonl`: skip-and-warn off-schema records
**Files:** `tools/agent-monitoring/build_index.py`, `tests/tools/test_build_index.py`
**Change:** Add `_ingest_tools(conn, records)`. A record is valid iff `record.get("run_id") is not None and record.get("seq") is not None and isinstance(record.get("tool"), str)`. This structural check (not a literal-content check) is what correctly excludes all 3 confirmed off-schema shapes without hardcoding their contents:
- `{"tool":"implement-epic","last_run":...,"result":...,"tickets":[...]}` — has `tool` but no `run_id`/`seq` → excluded
- `{"run_id":...,"ts":...,"tools_used":[...],...}` — has `run_id` but no `seq`/`tool` → excluded
- `{"session_id":...,"run_id":...,"seq":4,"ts":...}` — has `run_id`/`seq` but no `tool` → excluded

For each excluded record: `print(f"WARNING: tools.jsonl record skipped (missing run_id/seq/tool): {record!r}", file=sys.stderr)` (mirrors `validate.py`'s existing `WARNING:`-to-stderr convention at `validate.py:207`) and increment a `skipped_count`. For valid records: `run_id`, `seq`, `workflow = record.get("workflow") or infer_workflow(run_id)`, `tool = record["tool"]`, `raw_json`. `INSERT INTO tools (...)`.
**Do NOT touch:** Never coerce a missing `tool`/`run_id`/`seq` into a fabricated value (e.g. `"UNKNOWN"` or `-1`) to force an insert. Never rewrite `tools.jsonl` "in place" to fix these records — they stay exactly as-is in the source file.
**Verify:** `test_build_index_skips_offschema_tools_records`.

### Step 6 — Wire `main()` end-to-end: exit 0, read-only guarantee, row-count stability
**Files:** `tools/agent-monitoring/build_index.py`, `tests/tools/test_build_index.py`
**Change:** Complete `build(args)`/`main()`: parse args → read all 3 files via `load_jsonl()` (which only ever calls `Path.read_text()`, never `Path.write_text()`/`open(..., "w")` — confirm no code path anywhere in `build_index.py` opens `runs.jsonl`/`events.jsonl`/`tools.jsonl` for writing) → run Step 2's rebuild scaffolding → call `_ingest_runs`, `_ingest_events`, `_ingest_tools` in that order → `conn.commit()`; `conn.close()` → print a summary (`f"runs: {n} rows, events: {n} rows, tools: {n} rows ({skipped} skipped)"`) → `return 0`. `main()` returns the exit code; `if __name__ == "__main__": sys.exit(main())` at module bottom.
**Do NOT touch:** Nothing beyond wiring — no new normalization logic introduced here.
**Verify:** `test_build_creates_gitignored_sqlite_db` (AC1), `test_source_jsonl_files_byte_identical_after_build` (AC2 — sha256 of all 3 source files unchanged before/after), `test_build_twice_produces_same_row_counts` (AC5, row-count-identical form — see Summary's scope clarification).

### Step 7 — Makefile target
**Files:** `Makefile`
**Change:** Insert a new target immediately after the existing `agent-monitoring-epic-staleness:` target (before the `# ── Knowledge Search ─` comment block), following `knowledge-index:`'s (`Makefile:282-286`) interpreter-fallback shell pattern exactly:
```makefile
agent-monitoring-index: ## Rebuild the derived read-only SQLite index over agent-monitoring JSONL logs (on-demand only — not CI)
	$(shell for py in .venv/bin/python3 /home/vboxuser/Work/venv/bin/python3 python3; do [ -x "$$py" ] && echo "$$py" && break; done) \
	  tools/agent-monitoring/build_index.py
```
**Do NOT touch:** `test:`, `test-quick:`, `test-cov:`, `ci:`, `all:` targets — `agent-monitoring-index` must never appear as a dependency of any of them.
**Verify:** `test_makefile_has_agent_monitoring_index_target`, `test_makefile_agent_monitoring_index_calls_build_index`, `test_agent_monitoring_index_not_in_test_ci_all_targets`.

### Step 8 — `.gitignore` entry
**Files:** `.gitignore`
**Change:** Add, near the existing `knowledge-index/` entry (`.gitignore:263-264`):
```
# Agent-monitoring derived SQLite index (local only — rebuild with: make agent-monitoring-index)
agent-monitoring-index/
```
A whole-directory ignore for the new top-level `agent-monitoring-index/` directory — not a single-file ignore nested inside the tracked `agent-monitoring/` directory.
**Do NOT touch:** Do not add an ignore rule inside/under the tracked `agent-monitoring/` directory itself; the derived DB lives in its own new top-level directory.
**Verify:** `test_db_path_in_gitignore`.

## Scope Guards

- No migration of `query.py`, `validate.py`, or `generate_retro.py` to actually consume `build_index.py`'s output — three sibling tickets own that (`TCK-20260713-MONITORING-QUERY-INDEX-MIGRATE`, `-VALIDATE-INDEX-MIGRATE`, `-RETRO-INDEX-MIGRATE`).
- No change to the JSONL write path: `pre_tool_hook.py`, `post_tool_hook.py`, `record_run.py`, `record_events.py`, `writer.py` stay untouched, unimported, uncalled.
- No test coverage added to `query.py` itself (separate migration ticket's responsibility).
- No hook-triggered or automatic index build — strictly on-demand via CLI / `make agent-monitoring-index`.
- No incremental-build logic or `--incremental`-style flag, ever, in this script.
- No re-derivation of phase/agent/tier vocabulary inline anywhere in `build_index.py` — import from `vocabulary.py` only.
- No new terminal-status normalization beyond `validate.py`'s existing `LEGACY_TERMINAL_STATUS_VALUES`/`LEGACY_COMPLETION_FIELDS` (no further casing/spelling folding) — reuse the allowlist as-is per AC3/AC4's literal wording ("agrees with," "consistent with," not "improves on").
- No dedup of duplicate `run_id` rows in the `runs` table — stays a consumer-side concern.
- No `resolved_phase`/`resolved_agent` columns on the `events` table in this ticket — deferred to `TCK-20260713-MONITORING-RETRO-INDEX-MIGRATE`.
- No `UNIQUE(run_id, seq)` constraint on `events` or `tools` tables.
- No "fixing" the `TCK-20260623-TYPE-CHECKER` single-record 6th legacy shape — its unresolved `resolved_status` (`NULL`) is the correct, permanently-accepted outcome, not a bug.
- No write-back, reordering, or in-place correction of any of the 3 source JSONL files, including the 3 off-schema `tools.jsonl` records — they are excluded from the SQLite output only, never modified at the source.

## Dependency Map

- Step 1 is a prerequisite for every other step (defines the module, imports, and CLI surface).
- Step 2 (schema) is a prerequisite for Steps 3, 4, 5, 6 (nothing can `INSERT` before the tables exist).
- Steps 3, 4, 5 (per-file ingestion) are independent of each other — any order — but all three must land before Step 6.
- Step 6 (end-to-end wiring, exit code, read-only guarantee, row-count-stability) depends on Steps 1–5 all being complete.
- Steps 7 and 8 (Makefile, `.gitignore`) only require `build_index.py` to exist at its final path (true after Step 1); they are otherwise independent of Steps 2–6's internals and can be done in any order relative to each other.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — build reads all 3 JSONL files once each, writes gitignored SQLite with runs/events/tools tables, exits 0 | Steps 1, 2, 3, 4, 5, 6 | `test_build_creates_gitignored_sqlite_db` |
| AC2 — build never modifies the 3 source JSONL files (byte-identical before/after) | Steps 1, 3, 4, 5, 6 | `test_source_jsonl_files_byte_identical_after_build` |
| AC3 — `resolved_status` agrees with `generate_retro.py::_resolve_status()` for every row | Step 3 | `test_resolved_status_matches_generate_retro_resolve_status` |
| AC4 — completeness/terminal-status classification consistent with `validate.py`'s legacy allowlists, on the same fixture as `test_validate_agent_monitoring.py` | Step 3 | `test_completeness_matches_validate_legacy_allowlists` |
| AC5 — re-running twice with unchanged inputs produces row-count-identical output (this plan's scope clarification of "byte-identical," see Summary) | Step 6 | `test_build_twice_produces_same_row_counts` |
| AC6 — `make agent-monitoring-index` target defined; DB path in `.gitignore` | Steps 7, 8 | `test_makefile_has_agent_monitoring_index_target`, `test_makefile_agent_monitoring_index_calls_build_index`, `test_agent_monitoring_index_not_in_test_ci_all_targets`, `test_db_path_in_gitignore` |
| (supporting, not independently AC-numbered but required by test_plan.md) | Step 1 | `test_no_incremental_build_flag_exists`, `test_build_index_never_touches_write_path_modules`, `test_build_index_imports_vocabulary_not_reencoded` |
| (supporting) | Step 3 | `test_type_checker_legacy_shape_does_not_crash_build` |
| (supporting) | Step 4 | `test_events_table_tolerates_duplicate_run_id_seq` |
| (supporting) | Step 5 | `test_build_index_skips_offschema_tools_records` |

## Anti-Drift Notes

- **`(run_id, seq)` is not a safe unique key.** Historical `events.jsonl` data has duplicate `(run_id, seq)` pairs from the pause/resume seq-collision bug (`TCK-20260728-MONITORING-PAUSE-RESUME-SEQ-COLLISION`); a `UNIQUE(run_id, seq)` constraint on the `events` table would crash a full rebuild on real, already-collected data. Use a surrogate `id` primary key with a non-unique index instead — do not "fix" this by deduping during ingest, since deduping would be new normalization logic beyond this ticket's scope and would risk silently discarding a legitimate historical record.
- **`tools.jsonl`'s 3 off-schema records are structurally distinguishable, not content-distinguishable.** Filter on presence/type of `run_id`/`seq`/`tool`, not on matching the specific known record contents — this generalizes to any future off-schema record with the same shape-defect, not just the 3 currently observed.
- **`TCK-20260623-TYPE-CHECKER`'s unresolved status is a permanently-accepted exception**, documented in `docs/agent-monitoring/schema.md`'s Known Limitations section (per `TCK-20260705-MONITORING-RUNID-JOIN`'s investigation). `resolved_status = NULL` for this one record is correct; a future contributor "fixing" it by special-casing would itself be the bug.
- **`raw_json = json.dumps(record, sort_keys=True)` is not a write-back.** It serializes the in-memory parsed dict into a new SQLite column — the source JSONL file's bytes are never touched. Do not confuse this with AC2's byte-identical guarantee, which applies only to the 3 source files on disk.
- **Parity ledger entry is not part of this plan's steps.** Per the investigation's Parity Ledger Overlap section, this ticket's separate Parity workflow phase (not the Implement phase this plan governs) should add a new `INFRA-xxx` entry to `docs/parity_ledger/infrastructure.yaml` describing `build_index.py`'s normalization guarantee, with `test_path` pointing at `tests/tools/test_build_index.py`. Flagging here so it is not dropped, but it is out of scope for the implementer following this plan.
- **`docs/agent-monitoring/schema.md`'s Known Limitations section could optionally note the 3 off-schema `tools.jsonl` shapes** (a genuinely new finding per investigation, not previously documented) — this is not required by any AC or test in `test_plan.md`, so it is not a plan step; the implementer may add a short note there as a courtesy but must not treat it as blocking or in-scope work.
- **`CANONICAL_TIERS` cross-check in Step 3 is warn-only, never enforced/fatal** — an unrecognized `tier` value must still be inserted as-is, exactly like `record_events.py`'s existing warn-only vocabulary check. Do not turn this into a hard validation that could make the build exit non-zero on a legitimately-unrecognized-but-real tier value.

## Deviations

**Step 5 — `tools.jsonl` validity check: key presence, not value non-nullness.**

This plan's Step 5 specified the validity check as:

```python
record.get("run_id") is not None and record.get("seq") is not None and isinstance(record.get("tool"), str)
```

Implementation against a snapshot of the live `agent-monitoring/tools.jsonl` (67,726 valid lines) showed this literal expression does not implement the plan's own stated intent. This plan's Anti-Drift Notes section says: *"Filter on presence/type of `run_id`/`seq`/`tool`, not on matching the specific known record contents"* — but `record.get(...) is not None` cannot distinguish "key absent from the JSON object" from "key present with an explicit JSON `null` value"; both parse to Python `None` via `dict.get()`.

Live data has a third, non-off-schema record shape not called out by the plan's Step 5 text or the investigation's key-set audit in enough detail to catch this: interactive-use tool-call records (Bash/Read/Edit calls made outside a ticket workflow run) legitimately carry `"run_id": null, "seq": null` as **present keys with null values**, alongside a real string `"tool"` field. This is the same class of record `validate.py::compute_tool_count_drift_report()` already treats as legitimate-but-unattributed (its own guard is `if run_id and seq is not None: ...` to exclude them from a *count*, not to exclude them from `tools.jsonl` itself).

A key-set audit of the live corpus confirms exactly 3 key-sets are missing the `run_id`/`seq`/`tool` *keys* outright (the 3 previously-confirmed off-schema records, each count=1) versus 3 key-sets that always carry all three keys (61,349 + 4,762 + 1,607 = 67,718 records, some with null `run_id`/`seq` for interactive use, some with real values for run-scoped calls). The plan's literal `is not None` check would have silently dropped all ~30,372 null-run_id/null-seq records from the `tools` table — a much larger and more damaging exclusion than the plan intended or than AC1/Scope's "reads all 3 JSONL files" implies.

**Fix applied:** `_ingest_tools()` now checks `"run_id" not in record or "seq" not in record or not isinstance(record.get("tool"), str)` — key presence for `run_id`/`seq`, type check for `tool`. Verified against the live corpus snapshot: `tools: 67723 rows (3 skipped)`, matching `67726` total valid lines exactly, with the 3 skip warnings corresponding to the 3 previously-confirmed off-schema records only.

No other step deviated from this plan. The schema (Step 2), `runs`/`events` ingestion (Steps 3-4), `main()` wiring (Step 6), Makefile target (Step 7), and `.gitignore` entry (Step 8) were implemented exactly as specified.
