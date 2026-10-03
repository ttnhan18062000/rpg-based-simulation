---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-BASELINE-MONITORING-MANIFEST
artifact_type: plan
tags: [agent-monitoring, data-quality]
---

# Implementation Plan — TCK-20260721-BASELINE-MONITORING-MANIFEST

## Summary

Build two new, read-only modules under `tools/agent-monitoring/` — a pure-function provenance
classifier (`legacy_reader.py`) and a streaming inventory tool (`manifest.py`) — backed by a
verbatim-real-data fixture corpus under `tests/fixtures/agent_monitoring/`. The classifier decides,
per record and per source file, which of the 6 documented legacy `runs.jsonl` shapes (or the
`tools.jsonl`/`events.jsonl` null-gap variants, or "current") a record belongs to; the manifest tool
reuses it to compute a deterministic `legacy_warning_count` per file alongside line count, byte
size, and a streamed SHA-256 hash. Every fixture is a byte-for-byte copy of a real corpus line
already identified in `investigation.md` — no synthetic data. Six Plan-phase decisions close the
open questions from investigation: the exact manifest record schema (no wall-clock field, so re-runs
are byte-identical), a single uniform streaming scan (one pass, chunked/line-lazy, used for all
three files — not just `tools.jsonl` — so no file's hash or parse path ever holds the full content in
memory), the legacy-warning counting rule (non-empty classifier output, excluding the by-design
`interactive_null` case), fixture provenance (verbatim real lines, source documented in a
`PROVENANCE.md`), and output location (script under `tools/agent-monitoring/`, output printed to
stdout by default, optional `--output` path guarded against ever resolving under the real
`agent-monitoring/` data directory). Nothing in this plan touches `validate.py`, `record_run.py`,
`record_events.py`, `post_tool_hook.py`, or any `agent-monitoring/*.jsonl` file.

## Decided (Plan-phase resolutions of investigation.md's 5 open questions)

1. **Manifest record schema** (deterministic, no wall-clock field):
   ```json
   {
     "file": "events.jsonl",
     "line_count": 3642,
     "byte_size": 1017335,
     "sha256": "9f2c...<64 hex chars>",
     "parser_result": {"parsed_ok": 3642, "parse_errors": 0},
     "legacy_warning_count": 214
   }
   ```
   `line_count` = `parsed_ok + parse_errors` (blank lines are skipped and not counted, matching
   `load_jsonl`'s existing `if not line: continue` behavior). The manifest tool's full output is a
   JSON array of exactly 3 such records, one per `agent-monitoring/*.jsonl` file, **sorted by
   filename** (`events.jsonl`, `runs.jsonl`, `tools.jsonl`), serialized with
   `json.dumps(records, indent=2, sort_keys=True)` plus a trailing newline. No field anywhere in the
   record or its envelope is time-of-run-dependent.

2. **Streaming approach**: one uniform streaming scanner, used for **all three** files (not a
   special case only for `tools.jsonl`) — open each file in binary mode, iterate `for line_bytes in
   f` (lazy, one physical line resident at a time regardless of file size), feed each `line_bytes`
   into a running `hashlib.sha256()` update (this reconstructs the exact whole-file hash since
   line-iteration preserves terminators and byte order), and separately attempt
   `json.loads(line_bytes.strip())` per non-blank line to classify it. This is simpler and safer
   than two separate code paths (one streaming, one using `read_text()`) — using it for the two
   small files too costs nothing and removes any chance of the anti-drift hazard ("both paths need
   the bounded-read treatment") being violated by an inconsistent implementation.

3. **Legacy-warning counting rule**: `legacy_warning_count` for a file = count of successfully
   parsed records where `classify_provenance(record, source)` returns a **non-empty** label set that
   is **not exactly `{"interactive_null"}`** (the by-design `tools.jsonl` interactive-call case is
   never a "warning"). Malformed JSON lines are already counted separately under
   `parser_result.parse_errors` and are not double-counted here.

4. **Output location**: script lives at `tools/agent-monitoring/manifest.py` (a tools-directory
   path, distinct from the `agent-monitoring/` data directory at repo root — the ticket's own
   Related Code Areas names this exact path). Default behavior: print the JSON array to stdout only.
   Optional `--output PATH` flag writes the same bytes to `PATH` instead, guarded by a local
   `_assert_safe_output_path()` helper (mirrors, but does not import,
   `test_monitoring_writer_lockfile_candidate.py`'s `_assert_not_real_corpus` — production code
   under `tools/` must not import from `tests/`) that raises if `PATH` resolves under the repo's
   `agent-monitoring/` directory. No default persisted file is created by this ticket.

5. **Fixture provenance**: every fixture file under `tests/fixtures/agent_monitoring/` is a verbatim
   byte-for-byte copy of one real line already located in `investigation.md`, saved as its own
   single-line `.jsonl` file. A `tests/fixtures/agent_monitoring/PROVENANCE.md` documents, per
   fixture file, the exact source file and locator (run_id or line number) it was copied from —
   mirroring the sourcing-comment convention in
   `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml` (JSONL has no comment
   syntax, so provenance goes in the sibling `.md` file instead of inline).

## Steps

### Step 1 — Provenance classifier (`legacy_reader.py`) + inline-dict unit tests
**Files:** `tools/agent-monitoring/legacy_reader.py` (new), `tests/tools/test_agent_monitoring_legacy_reader.py` (new, first section)
**Change:**
Create `tools/agent-monitoring/legacy_reader.py` with one pure function:

```python
def classify_provenance(record: dict, source: str) -> frozenset[str]:
    """source is one of 'runs', 'events', 'tools'. Returns a set of legacy-shape labels;
    an empty frozenset means the record matches the current schema for its source."""
```

Import `LEGACY_COMPLETION_FIELDS` and `LEGACY_TERMINAL_STATUS_VALUES` from
`tools/agent-monitoring/validate.py` (read-only import of existing module-level constants — do not
edit `validate.py`) to keep the classifier's notion of "legacy completion field" single-sourced with
the existing validator.

Classification rules, evaluated in this order (first match wins) per `source`:

- `source == "runs"`:
  1. `"outcome" in record and "final_status" not in record and "status" not in record` → `{"shape6_type_checker_exception"}`
  2. `str(record.get("run_id", "")).startswith(("FOLDER-", "EPIC-")) and "final_status" not in record and "start_ts" not in record and "end_ts" not in record` → `{"shape5_folder_epic_bare_status"}`
  3. `"started_at" in record and "finished_at" in record and "phases_completed" in record` → `{"shape1_started_finished_notes"}`
  4. `"final_status" in record and "end_ts" not in record` → `{"shape2_final_status_no_end_ts"}`
  5. `"ts_start" in record and "ts_end" in record and "result" in record` → `{"shape3_ts_start_ts_end_result"}`
  6. `"completed_at" in record and "finished_at" not in record and "final_status" not in record` → `{"shape4_completed_at_status"}`
  7. else (has `final_status` and `end_ts`, or otherwise matches current schema) → `frozenset()` ("current")
- `source == "tools"`:
  1. `record.get("run_id") is None and record.get("seq") is None` → `{"interactive_null"}`
  2. `"phase" not in record or "agent" not in record` → `{"tools_phase_agent_null_gap"}`
  3. else → `frozenset()`
- `source == "events"`:
  - labels = set(); if `"reason_code" not in record`: add `"events_reason_code_null"`; if
    `"tool_call_count" not in record`: add `"events_tool_call_count_absent"`; return
    `frozenset(labels)` (may contain 0, 1, or both labels — this is intentional, see Decided #3 and
    the real corpus example where one record predates both fields).

Add `tests/tools/test_agent_monitoring_legacy_reader.py` with a first block of unit tests using
**inline dict literals** (no file I/O, mirroring `test_validate_agent_monitoring.py`'s existing pure-function
test style) — one test per rule above, covering all 6 runs shapes + "current", both tools cases, and
both events cases (including a record missing both events fields at once).
**Do NOT touch:** `validate.py` (import only, no edits), `record_run.py`, `record_events.py`, `post_tool_hook.py`.
**Verify:** new inline-dict tests in `tests/tools/test_agent_monitoring_legacy_reader.py` pass; `tests/tools/test_validate_agent_monitoring.py` remains green and untouched (test_plan.md Regression Surface).

### Step 2 — Fixture corpus (verbatim real lines)
**Files:** `tests/fixtures/agent_monitoring/` (new directory, 8 new `.jsonl` files + `PROVENANCE.md`)
**Change:** Create the directory with exactly these 8 single-line fixture files, each containing the
byte-for-byte real line already located during investigation (no re-formatting, no key reordering,
no synthetic substitution):

| File | Verbatim content source |
|---|---|
| `shape1_started_finished_notes.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="TCK-20260613-DOC-DOMAIN-CONTRACTS"` |
| `shape2_final_status_no_end_ts.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="TCK-20260610-WORKER-SINGLETON-GUARD"` |
| `shape3_ts_start_ts_end_result.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="TCK-20260628-E41G-COHESION-SUSTAIN"` |
| `shape4_completed_at_status.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="TCK-20260610-SENSE-PERCEPTION-GATE"` |
| `shape5_folder_epic_bare_status.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="FOLDER-phase40-44-cleanup-authoring"` (the bare-`status` population — **not** one of the 65 current-schema `FOLDER-*`/`EPIC-*` records) |
| `shape6_type_checker_exception.jsonl` | `agent-monitoring/runs.jsonl`, `run_id="TCK-20260623-TYPE-CHECKER"` |
| `tools_jsonl_phase_agent_null_gap.jsonl` | `agent-monitoring/tools.jsonl:278` (`run_id="TCK-20260614-CERT-SAFE-SERIAL"`, `seq=2`) |
| `tools_jsonl_interactive_null.jsonl` | `agent-monitoring/tools.jsonl:1` (`run_id=null`, `seq=null`) |
| `events_jsonl_tool_call_count_absent.jsonl` | `agent-monitoring/events.jsonl`, `run_id="TCK-20260607-PATH-DRIFT-SRC"`, `seq=1` |
| `events_jsonl_reason_code_null.jsonl` | same line as above (this one real record predates both fields — copy it into both files verbatim; do not synthesize two different records) |

Exact content for the 6 `runs`-shaped fixtures and the `tools`/`events` fixtures is the literal text
already captured in this Plan phase's tool output (copy verbatim, one JSON object per line, no
trailing content beyond the single line + newline).

Create `tests/fixtures/agent_monitoring/PROVENANCE.md` listing, for each of the 10 files above, the
source file + locator (run_id or line number) it was copied from, and the one-sentence reason it
represents that shape (mirrors the sourcing-comment block at the top of
`tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`).
**Do NOT touch:** any `agent-monitoring/*.jsonl` file (read from, never write to). Do not add a 9th
"shape" fixture for any of the ~25 undocumented ad hoc key-sets investigation.md found — out of
scope per ticket AC (explicitly scoped to "all 6 documented legacy shapes").
**Verify:** files exist at the stated paths with exactly one JSON line each; no test yet references
them (Step 3 adds that).

### Step 3 — Fixture-backed legacy-reader tests
**Files:** `tests/tools/test_agent_monitoring_legacy_reader.py` (extend, second section)
**Change:** Add one parametrized test per fixture file from Step 2 (10 cases, one per file — not one
monolithic test, per test_plan.md's regression-pinpointing requirement): load the fixture's single
line, `json.loads` it, call `classify_provenance(record, source)` with the correct `source` for that
file, and assert the returned label set equals the expected shape label (or, for the two
`tools_jsonl_*` and two `events_jsonl_*` files, the expected label(s) per Step 1's rules — note
`tools_jsonl_interactive_null.jsonl` must assert `{"interactive_null"}` and must NOT be treated as a
`legacy_warning_count` contributor per Decided #3). Include the **shape-5 population guard** from
test_plan.md: assert the shape-5 fixture record does not contain a `final_status` key (protects
against a future edit swapping in one of the 65 current-schema `FOLDER-*`/`EPIC-*` records).
**Do NOT touch:** Step 1's classifier logic — this step only adds tests against fixture files, no
production-code changes.
**Verify:** `pytest tests/tools/test_agent_monitoring_legacy_reader.py -v` — all 10 parametrized
cases plus the shape-5 guard pass. Satisfies test_plan.md item 4 (fixture corpus existence + shape)
and item 5 (legacy-reader classification correctness).

### Step 4 — Round-trip readability test for current-schema records
**Files:** `tests/tools/test_agent_monitoring_legacy_reader.py` (extend, third section)
**Change:** Add a test that samples the most recent N (e.g. 20) real lines from each of
`agent-monitoring/runs.jsonl` and `agent-monitoring/events.jsonl` (read-only, via the Step 2-style
streaming scan or a simple `path.read_text().splitlines()[-20:]` since these two files are trivial
size), and for each sampled `runs.jsonl` record asserts: (a) `classify_provenance(record, "runs")`
returns `frozenset()` ("current" — these are recent records, expected to match current schema), and
(b) `validate.py`'s existing `_record_is_complete(record)` also returns a result consistent with
that classification (import `_record_is_complete` from `validate.py`, read-only). This is the
"new reader is a superset, not a replacement" architecture guard from test_plan.md item 6 — it
proves the new classifier doesn't disagree with the existing validator's tolerance for genuinely
current records.
**Do NOT touch:** `validate.py` (import only). Do not sample from `tools.jsonl` here — that file's
"current" shape check belongs to the manifest tool's own tests in Step 6, not this file-readability
check.
**Verify:** `pytest tests/tools/test_agent_monitoring_legacy_reader.py -v` — new round-trip cases
pass. Satisfies ticket AC "Current Claude-written monitoring records remain readable."

### Step 5 — Manifest tool (`manifest.py`)
**Files:** `tools/agent-monitoring/manifest.py` (new)
**Change:** Implement the streaming scanner and manifest-record assembly described in Decided #1–#4
above:
- `_scan_file(path: Path, source: str) -> dict`: opens `path` in binary mode once, iterates
  `for line_bytes in f` (lazy per-line, never `.read()`/`.read_text()`/`.readlines()` on the whole
  file), updates a running `hashlib.sha256()` with every `line_bytes` read (reconstructs the exact
  whole-file digest), and for each non-blank line attempts `json.loads(line_bytes.strip())`:
  incrementing `parsed_ok` on success (and calling
  `legacy_reader.classify_provenance(record, source)` to test membership per Decided #3's rule,
  incrementing `legacy_warning_count` when it applies) or `parse_errors` on `JSONDecodeError`.
  Returns the record dict shape from Decided #1 (`file`, `line_count`, `byte_size`, `sha256`,
  `parser_result`, `legacy_warning_count`); `byte_size` comes from `path.stat().st_size`, not from
  summing line lengths.
- `build_manifest(agent_monitoring_dir: Path) -> list[dict]`: calls `_scan_file` for
  `events.jsonl`, `runs.jsonl`, `tools.jsonl` (in that sorted order) with `source` set to
  `"events"`, `"runs"`, `"tools"` respectively, and returns the list.
- `main()`: CLI entry point — `python3 tools/agent-monitoring/manifest.py [--output PATH]`. Resolves
  `agent_monitoring_dir` to the real repo-root `agent-monitoring/` directory. Serializes
  `build_manifest(...)` via `json.dumps(records, indent=2, sort_keys=True)` + `"\n"`. Prints to
  stdout by default. If `--output PATH` is given, calls `_assert_safe_output_path(PATH)` (raises if
  `PATH` resolves under `<repo_root>/agent-monitoring/`) then writes the same bytes to `PATH`.
- Import `classify_provenance` from `tools/agent-monitoring/legacy_reader.py` (Step 1). Do not
  import from `validate.py` here (its constants are already consumed inside `legacy_reader.py`;
  `manifest.py` itself needs no direct `validate.py` dependency).
**Do NOT touch:** `validate.py`, `record_run.py`, `record_events.py`, `post_tool_hook.py`. This
module must never open any file in `agent-monitoring/` for writing, and must never call
`path.read_text()`, `path.read_bytes()`, or `path.readlines()` on `runs.jsonl`, `events.jsonl`, or
`tools.jsonl`.
**Verify:** manual run — `python3 tools/agent-monitoring/manifest.py` against the real repo prints a
3-record JSON array to stdout with no traceback (full automated verification in Steps 6–7).

### Step 6 — Manifest tool tests: shape, reproducibility, streaming guard
**Files:** `tests/tools/test_agent_monitoring_manifest.py` (new)
**Change:** Three test groups against the real `agent-monitoring/` corpus (read-only):
1. **Shape test** (AC1): call `build_manifest(real_agent_monitoring_dir)`, assert exactly 3 records
   returned, each with the 6 required keys (`file`, `line_count`, `byte_size`, `sha256`,
   `parser_result`, `legacy_warning_count`) and correct filenames.
2. **Reproducibility test** (AC2): invoke `manifest.py` via `subprocess.run([...])` twice in a row
   against the unchanged real corpus, capture stdout both times, assert
   `stdout_1 == stdout_2` byte-for-byte.
3. **Streaming guard** (AC7, static/code-review style — preferred per test_plan.md over an empirical
   memory-bound test): an `ast`-based source scan of `tools/agent-monitoring/manifest.py` asserting
   the module source contains no call to `.read_text()`, `.read_bytes()`, or `.readlines()` (mirrors
   the `tools/gate_checks/*_static.py` static-guard style already used elsewhere in this repo).
**Do NOT touch:** the real `agent-monitoring/*.jsonl` files — these tests only read them.
**Verify:** `pytest tests/tools/test_agent_monitoring_manifest.py -v` — all three groups pass.

### Step 7 — Zero-mutation integration test
**Files:** `tests/tools/test_agent_monitoring_manifest.py` (extend)
**Change:** Add a test mirroring `tests/agent_replay/test_no_mutation_snapshot.py`'s dirty-tree-aware
two-branch design, scoped to `agent-monitoring/*.jsonl` only (not `tickets/`): take a `git status
--porcelain -- agent-monitoring/` snapshot before running `manifest.py`'s `main()` (or the CLI via
`subprocess`) against the real corpus; if clean before, assert clean after; if already dirty
(the common case), fall back to a SHA-256 content-hash snapshot of all 3 real
`agent-monitoring/*.jsonl` files taken immediately before/after, and assert the hashes are
identical. Also add the **writer byte-identity guard** from test_plan.md's Anti-Drift Test Guards:
assert `validate.py`, `record_run.py`, `record_events.py`, `post_tool_hook.py` are unchanged
(content-hash or `git diff --stat` scoped to those 4 paths returns empty) — enforces the ticket's
Out of Scope line explicitly.
**Do NOT touch:** must run against the real repo tree, never a `tmp_path` copy (a copy would make
the assertion vacuous, per the precedent this step mirrors).
**Verify:** `pytest tests/tools/test_agent_monitoring_manifest.py -v` — new test passes. Satisfies
ticket AC3 ("zero git diff on `agent-monitoring/*.jsonl`").

## Scope Guards

- Do not modify `tools/agent-monitoring/validate.py`, `record_run.py`, `record_events.py`, or
  `post_tool_hook.py` — read-only imports of `validate.py`'s constants/functions only.
- Do not implement the shared writer module (`TCK-20260721-MONITORING-WRITER-UNIFICATION`'s scope,
  a later sibling ticket that depends on this ticket's manifest tool as its own entry criterion —
  do not pull that work forward).
- Do not modify, reorder, backfill, or delete any line in `agent-monitoring/runs.jsonl`,
  `agent-monitoring/events.jsonl`, or `agent-monitoring/tools.jsonl`. All new code only reads these
  files.
- Do not wire the manifest tool into any live hook (`.claude/`, `.codex/`) — out of scope per
  ticket.
- Do not expand fixture coverage beyond the 6 documented `runs.jsonl` shapes + the `tools.jsonl` and
  `events.jsonl` null-gap variants named in the ticket AC — the ~25 additional undocumented ad hoc
  shapes investigation.md found in the real corpus are explicitly out of scope (would need their own
  audit ticket, per investigation.md Risk #1).
- Do not let the shape-5 fixture use one of the 65 current-schema `FOLDER-*`/`EPIC-*` records — must
  be one of the 7 genuinely legacy bare-`status` records.
- Do not conflate the two `tools.jsonl` null-gap causes (`interactive_null` vs.
  `tools_phase_agent_null_gap`) into a single fixture or a single classifier branch.
- Do not add a wall-clock or any other non-deterministic field to the manifest record schema.
- Do not write the manifest tool's own output into `agent-monitoring/` — enforced in code via
  `_assert_safe_output_path()` in Step 5.

## Dependency Map

- Step 1 (classifier) — no dependencies.
- Step 2 (fixtures) — no dependencies (can proceed in parallel with Step 1).
- Step 3 (fixture-backed tests) — depends on Step 1 (classifier function) and Step 2 (fixture files).
- Step 4 (round-trip test) — depends on Step 1 (imports `classify_provenance` for the consistency
  assertion) and `validate.py` (pre-existing, unmodified).
- Step 5 (manifest.py) — depends on Step 1 (imports `classify_provenance` for
  `legacy_warning_count`).
- Step 6 (manifest tests: shape/reproducibility/streaming) — depends on Step 5.
- Step 7 (zero-mutation integration test) — depends on Step 5.

Recommended execution order: 1 → 2 → 3 → 4 → 5 → 6 → 7 (matches numbering; Steps 1 and 2 could run
in either order or in parallel since neither depends on the other).

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| Manifest tool produces one record per JSONL file (line count, byte size, SHA-256, parser result, legacy-warning count) | Step 5 | Step 6, shape test |
| Running the manifest tool twice against unchanged input produces byte-identical output | Step 5 (no wall-clock field, `sort_keys=True`) | Step 6, reproducibility test |
| Manifest tool run causes zero git diff on `agent-monitoring/*.jsonl` | Step 5 (read-only design) | Step 7, zero-mutation integration test |
| Fixture corpus contains one fixture per documented legacy shape (6 shapes + null-gap variants) | Step 2 | Step 3, existence + parametrized classification (asserted per fixture file) |
| Legacy-reader test asserts each fixture parses correctly and is classified with correct provenance | Step 1, Step 3 | Step 3, 10 parametrized cases + shape-5 guard |
| Current Claude-written monitoring records remain readable (round-trip) before and after the new reader is introduced | Step 4 | Step 4, round-trip test against `validate.py`'s `_record_is_complete` |
| Manifest tool avoids a full in-memory parse of `tools.jsonl` (streaming/bounded) | Step 5 (uniform streaming scanner for all 3 files) | Step 6, `ast`-based static streaming guard |

## Anti-Drift Notes

- The shape-5 real population split (7 genuinely legacy bare-`status` records vs. 65 already
  current-schema `FOLDER-*`/`EPIC-*` records) is the single easiest mistake to make silently — the
  classifier's rule order in Step 1 checks for **absence** of `final_status`/`start_ts`/`end_ts`,
  not the `run_id` prefix, specifically so the 65 current-schema records classify as `frozenset()`
  ("current") and never get miscounted as legacy warnings.
- `tools.jsonl`'s two null-gap causes are semantically different (by-design interactive call vs.
  genuine pre-`TCK-20260719-LIVE-PHASE-AGENT-LABEL` legacy gap) and must never be merged into one
  label or one fixture — `interactive_null` is explicitly excluded from `legacy_warning_count`
  (Decided #3); `tools_phase_agent_null_gap` is included.
- The streaming scanner (Step 5) must be used uniformly for all three files, not just `tools.jsonl`
  — using `validate.py`'s `load_jsonl` (full `read_text()`) anywhere inside `manifest.py` itself
  would violate the "both paths need the bounded-read treatment" hazard from investigation.md even
  though `runs.jsonl`/`events.jsonl` are individually small; `load_jsonl` reuse is instead exercised
  in Step 4's test, not inside the production manifest tool.
- `TCK-20260623-TYPE-CHECKER` is the one permanently-documented residual exception in
  `validate.py`/`schema.md` — it must classify as `shape6_type_checker_exception`, never fall through
  to an "unrecognized"/`other` bucket and never silently match another shape's rule (Step 1's rule
  order checks for it first, before any other `runs` rule, since it's the most narrowly identifiable
  signature — `outcome` present, `final_status`/`status` both absent).
- Every fixture file's content must be a verbatim copy — no key reordering, no whitespace
  normalization — of the real line it represents; `PROVENANCE.md` in Step 2 exists specifically so a
  future reader can verify a fixture against the live corpus if the real record's exact text is ever
  in doubt.
