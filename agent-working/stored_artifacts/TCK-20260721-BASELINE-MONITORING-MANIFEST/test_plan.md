---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260721-BASELINE-MONITORING-MANIFEST
artifact_type: test_plan
tags: [agent-monitoring, data-quality]
---

# Test Plan — TCK-20260721-BASELINE-MONITORING-MANIFEST

## Regression Surface

This ticket adds a new read-only tool and new fixtures; it does not modify any existing writer or
reader. The regression surface is: (a) prove the existing validator/tests still pass unmodified,
and (b) prove the new reader doesn't diverge from `validate.py`'s existing legacy-tolerance logic.

**Unit**
- `tests/tools/test_validate_agent_monitoring.py` — `compute_drift_report`,
  `compute_tool_count_drift_report`, vocabulary single-sourcing. Must remain green untouched; this
  ticket does not modify `validate.py`.

**Integration**
- `tests/tools/test_monitoring_writer_lockfile_candidate.py` — evidence-gathering harness for the
  (separate, not-yet-implemented) writer redesign; unrelated to this ticket's code but shares the
  `agent-monitoring/` real-corpus-path guard pattern (`_assert_not_real_corpus`) this ticket's own
  tests should reuse. Must remain green (untouched).
- `tests/agent_replay/test_no_mutation_snapshot.py` — the pre/post content-hash snapshot pattern
  this ticket's own "zero git diff" test reuses. Must remain green untouched.
- `tests/tools/test_monitoring_bypass_fix.py`, `tests/integrity/test_manifest_guards.py` — adjacent
  "manifest"-named tests in other subsystems (certification/integrity, not agent-monitoring);
  listed here only to confirm no naming collision with this ticket's new
  `tests/fixtures/agent_monitoring/` corpus or module names, not because this ticket touches them.

**No arena-combat surface** — this ticket has no combat/simulation code path.

## New Tests Required

Per AC, one test group per acceptance criterion:

1. **Manifest tool produces one record per JSONL file with the required fields**
   - Category: unit
   - Verifies: given the 3 real corpus paths (or 3 fixture-sized stand-ins), the manifest function
     returns exactly 3 records, each containing `line_count`, `byte_size`, `sha256`,
     `parser_result`/`validator_result`, and `legacy_warning_count`, keyed to the correct filename.
   - Location: `tests/tools/test_agent_monitoring_manifest.py`

2. **Reproducibility — byte-identical output on unchanged input, run twice**
   - Category: unit
   - Verifies: invoking the manifest function (or CLI, via `subprocess`) twice in a row against the
     same unchanged files produces byte-identical serialized output (`assert output_1 == output_2`).
     This test is also the concrete proof-point for Risk #2 in investigation.md (no wall-clock field
     leaking into the output) — if it's flaky/non-deterministic this test is the one that would catch
     it.
   - Location: `tests/tools/test_agent_monitoring_manifest.py`

3. **Zero git diff / no mutation of `agent-monitoring/*.jsonl`**
   - Category: integration (runs against the real repo tree, mirroring
     `test_no_mutation_snapshot.py`'s dirty-tree-aware design — never a `tmp_path` copy, which would
     make the assertion vacuous)
   - Verifies: SHA-256 content hash of all 3 real `agent-monitoring/*.jsonl` files, taken
     immediately before and immediately after running the manifest tool against the real corpus,
     are identical.
   - Location: `tests/tools/test_agent_monitoring_manifest.py` or a dedicated
     `tests/agent_replay/`-sibling module if the manifest tool lives under `tools/agent_replay/`
     rather than `tools/agent-monitoring/` (Plan phase decides module location).

4. **Fixture corpus — one fixture per documented legacy shape (6 total) + null-gap variants**
   - Category: unit/data — fixture files themselves, not a test per se, but existence + shape must
     be asserted.
   - Verifies: `tests/fixtures/agent_monitoring/` (or equivalent path chosen at Plan phase) contains
     one `.jsonl` fixture line (or file) per shape:
     - `shape1_started_finished_notes.jsonl` — `started_at`/`finished_at`/`status`/`phases_completed`/`notes`
       (real example: `TCK-20260613-DOC-DOMAIN-CONTRACTS`)
     - `shape2_final_status_no_end_ts.jsonl` — `final_status` present, `end_ts` key absent (real
       example: `TCK-20260610-WORKER-SINGLETON-GUARD`)
     - `shape3_ts_start_ts_end_result.jsonl` — `ts_start`/`ts_end`/`result`/`agent` (real example:
       `TCK-20260628-E41G-COHESION-SUSTAIN`)
     - `shape4_completed_at_status.jsonl` — `completed_at`/`status` (real example:
       `TCK-20260610-SENSE-PERCEPTION-GATE`)
     - `shape5_folder_epic_bare_status.jsonl` — `FOLDER-*`/`EPIC-*` `run_id` with a bare `status`
       field, no `final_status`/`start_ts`/`end_ts` (real example:
       `FOLDER-phase40-44-cleanup-authoring`) — **must use the bare-status population, not the
       65 `FOLDER-*`/`EPIC-*` records already matching current schema** (see investigation.md
       Anti-Drift Hazards)
     - `shape6_type_checker_exception.jsonl` — the single documented `TCK-20260623-TYPE-CHECKER`
       exception (`"outcome":"success"`, `"phase":"implement"`, no `end_ts`/`final_status`/`status`)
     - `tools_jsonl_phase_agent_null_gap.jsonl` — `run_id`/`seq` present, `phase`/`agent` keys
       absent (real example at `tools.jsonl:278`, `run_id=TCK-20260614-CERT-SAFE-SERIAL`, `seq=2`)
     - `tools_jsonl_interactive_null.jsonl` — `run_id`/`seq` both `null` (by-design, not legacy;
       real example at `tools.jsonl:1`)
     - `events_jsonl_tool_call_count_absent.jsonl` — event predating
       `TCK-20260708-AGENT-COST-OBSERVABILITY`, `tool_call_count`/`cost_proxy_score` keys absent
       (real example: `run_id=TCK-20260607-PATH-DRIFT-SRC`, `seq=1`)
     - `events_jsonl_reason_code_null.jsonl` — event predating
       `TCK-20260706-MONITORING-REASON-CODE`, no `reason_code` key (real example: same
       `TCK-20260607-PATH-DRIFT-SRC` record covers this too)
   - Location: `tests/fixtures/agent_monitoring/` (new directory)

5. **Legacy-reader test — correct parse + provenance classification per fixture shape**
   - Category: unit
   - Verifies: for each fixture above, the legacy-reader function returns a parsed record plus a
     schema-generation label matching the shape name (e.g. `"shape1"` … `"shape6"`,
     `"current"`, `"tools_phase_agent_null_gap"`, etc.) — one parametrized test case per shape, not
     one monolithic test, so a future regression pinpoints exactly which shape broke.
   - Location: `tests/tools/test_agent_monitoring_legacy_reader.py`

6. **Current Claude-written records remain readable — round-trip before/after**
   - Category: integration / architecture guard
   - Verifies: sample a set of known-current-schema real records (e.g. the most recent N lines of
     each real corpus file, or a fixture built from one) through the new reader both stand-alone and
     via `validate.py`'s existing `load_jsonl`/`_record_is_complete` path, asserting the two agree
     on completeness/parseability — i.e. the new reader is a superset, not a replacement, of
     `validate.py`'s existing tolerance.
   - Location: `tests/tools/test_agent_monitoring_legacy_reader.py`

7. **Streaming/bounded read — memory-bound proof for `tools.jsonl`**
   - Category: architecture guard
   - Verifies: either (a) a code-inspection-style guard asserting the manifest module's
     `tools.jsonl` code path never calls `.read_text()`/`.read_bytes()`/`.readlines()` on the full
     file (e.g. `ast`-based source scan, similar in spirit to other `tools/gate_checks/*_static.py`
     guards in this repo), or (b) an empirical bound using `resource.getrusage`/`tracemalloc` peak
     memory during a manifest run against a synthetic large fixture, asserting peak additional
     memory stays well under the file's own byte size (e.g. < 5 MB working set against an 18 MB+
     synthetic file). Prefer (a) for determinism; use (b) only if (a) proves too brittle to express
     — Plan phase decides. AC explicitly allows either "code review or a memory-bound test."
   - Location: `tests/tools/test_agent_monitoring_manifest.py`

## Scoped Pytest Commands

```
pytest tests/tools/test_agent_monitoring_manifest.py tests/tools/test_agent_monitoring_legacy_reader.py -v
pytest tests/tools/test_validate_agent_monitoring.py -v
pytest tests/tools/ -k "monitoring" -v
```

Never `pytest tests/`. This ticket's blast radius is `tools/agent-monitoring/`-adjacent tooling and
`tests/fixtures/agent_monitoring/` — scope to `tests/tools/` (where all other agent-monitoring tool
tests live) plus the specific new test files.

## Anti-Drift Test Guards

- **Real-corpus-path guard, reused from `test_monitoring_writer_lockfile_candidate.py`
  (`_assert_not_real_corpus`)**: every fixture-corpus test must assert it is reading from
  `tests/fixtures/agent_monitoring/`, never resolving to a path under the real `agent-monitoring/`
  directory — catches an accidental hardcoded real-corpus path silently creeping into a "fixture"
  test.
- **No-mutation snapshot test (item 3 above)** is itself the primary anti-drift guard for this
  entire ticket — it is the one test that would catch a future edit accidentally turning the
  manifest tool from read-only into a writer (e.g. someone "helpfully" adds a cache file under
  `agent-monitoring/` or rewrites a line while debugging).
- **Reproducibility test (item 2 above)** guards against a future edit introducing a non-deterministic
  field (wall-clock timestamp, dict-ordering-dependent hash, unsorted-set iteration in the
  legacy-warning count) into the manifest schema — this is the test that would catch that kind of
  silent behavior drift before it reaches a downstream consumer that diffs manifest output across
  runs.
- **Assert `validate.py`/`record_run.py`/`record_events.py`/`post_tool_hook.py` are byte-identical
  to their pre-ticket state** (e.g. `git diff --stat` scoped to those 4 paths returns empty, or a
  content-hash comparison at test time) — directly enforces the ticket's Out of Scope line ("No
  changes to any monitoring writer"). Cheap, explicit, and catches accidental scope creep into the
  production writer path that no other test here would otherwise notice.
- **Shape-5 population guard**: a dedicated assertion (or fixture-provenance comment, mirroring the
  real fixture file's sourcing-comment convention already used in
  `tests/fixtures/agent_replay/TCK-20260721-ORCHESTRATION-CONTRACT-ADR.yaml`) that the shape-5
  fixture record does NOT contain a `final_status` key — guards against someone later "fixing" the
  fixture to use one of the 65 current-schema `FOLDER-*`/`EPIC-*` records instead of the 7 genuinely
  legacy bare-`status` ones, which would silently stop exercising the legacy path (see
  investigation.md Anti-Drift Hazards).
- **`tools.jsonl` null-gap disambiguation guard**: two separate fixtures/test cases (not one) for
  "interactive null `run_id`/`seq`" vs. "`phase`/`agent` absent while `run_id`/`seq` present" — a
  single merged fixture would let a future change collapse these two distinct, differently-caused
  null patterns into one code path without any test noticing.
