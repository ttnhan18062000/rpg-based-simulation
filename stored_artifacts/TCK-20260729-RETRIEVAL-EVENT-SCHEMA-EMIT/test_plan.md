---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
artifact_type: test_plan
tags: [observability, agent-monitoring, schema]
---

# Test Plan — TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT

## Regression Surface

Existing tests that must keep passing unchanged (no edits to their assertions or fixtures):

**Unit — agent-monitoring core**
- `tests/tools/test_record_events.py` — especially `test_valid_event_has_no_errors`,
  `test_missing_key_rejected`, `test_null_required_field_rejected_identically_to_missing_key`,
  `test_null_agent_rejected`, `test_null_summary_does_not_crash_and_is_reported`, the
  `TestExitCodeContract` class, `TestVocabularyWarning` class, and
  `test_execution_identity_fields_pass_through_unchanged` (the direct precedent this ticket's new
  fields rely on for pass-through behavior).
- `tests/tools/test_monitoring_writer_single_source.py` — all 4 tests, unmodified. The new wrapper
  module(s) this ticket adds are explicitly NOT added to this file's `_CALL_SITES` list (see Risks
  in investigation.md); a new, separate guard test covers the new module(s) instead.
- `tests/tools/test_monitoring_writer.py` — writer.py's own lock/retry/diagnostic behavior, unrelated
  to this ticket's schema change but must stay green since `writer.py` itself is not modified.

**Unit — Phase 3 modules being instrumented**
- `tests/tools/test_hybrid_retrieval.py` — full file. `hybrid_fuse_and_filter()`'s signature and
  return shape (`HybridResult`) must not change; instrumentation wraps the call, it does not alter
  the wrapped function.
- `tests/tools/test_retrieval_cache.py` — full file, including the "duration-is-not-behavior guard"
  documented at the top of that file (no test may assert eviction by elapsed time alone outside the
  3 `test_prune_*` tests). `check_query_cache`/`check_index_cache`/`check_packet_cache`/
  `write_*_cache` signatures must not change.
- `tests/tools/test_context_packet_assembler.py` — full file. `assemble_context_packet()`'s
  signature and `ContextPacket`/`Candidate` dataclass shapes must not change.

**Integration / downstream consumers (must stay unaffected by new optional fields)**
- `tests/tools/test_validate_agent_monitoring.py` (if present) — vocabulary single-source guard.
- Any existing `generate_retro.py`/`query.py` test file exercising retro metric computation or CLI
  filtering over `events.jsonl` — confirm new optional retrieval fields on a record do not break
  `_normalize_phase`/`_normalize_agent`/`compute_retro_metrics` or `query.py`'s `filter_events`.

## New Tests Required

Per acceptance criteria (ACs numbered as in the ticket):

1. **`test_retrieval_event_contains_all_base_and_retrieval_fields`** (AC1)
   Category: unit.
   Verifies: a record built with all 7 base fields (`run_id`, `seq`, `ts`, `phase`, `agent`,
   `summary`, `status`) plus the new retrieval fields (`retrieval_schema_version`,
   `corpus_generation`, `cache_level`, `cache_status`, `latency_ms`, `candidate_count`,
   `selected_count`, `source_kind_counts`, `authority_counts`, `freshness_counts`,
   `exclusion_reason_counts`, `cited_source_hashes`, `adequacy_verdict`, `expansion_reason`,
   `expansion_count`) passes `record_events.validate_record()` with `[]` errors, and that the
   written JSON line (via `write_lines` into a `tmp_path` file) round-trips every field exactly.
   Location: `tests/tools/test_record_events.py` (extends the existing file — same fixture/CLI
   pattern as `test_execution_identity_fields_pass_through_unchanged`) or a new
   `tests/tools/test_retrieval_event_schema.py` if the new wrapper module warrants its own file.

2. **`test_missing_base_field_still_rejected_with_new_fields_present`** (AC2)
   Category: unit / regression guard.
   Verifies: a record with all new retrieval fields populated but one base field
   (e.g. `phase`) missing or `None` is still rejected identically to today's behavior — same error
   shape as `test_null_required_field_rejected_identically_to_missing_key`, just with the new
   optional fields also present, proving they cannot mask a missing base field.
   Location: same file as #1.

3. **`test_retrieval_event_schema_excludes_execution_id_provider_and_raw_text`** (AC3)
   Category: architecture guard / structural.
   Verifies: iterate the new schema's defined field-name set (a single source-of-truth constant,
   e.g. `RETRIEVAL_EVENT_FIELDS`, that the wrapper module should expose) and assert
   `"execution_id" not in fields`, `"provider" not in fields`, and no field name matches a
   raw-content pattern (e.g. assert none of `{"raw_prompt", "raw_text", "chunk_text",
   "retrieved_content", "payload"}` appear, and that `cited_source_hashes` is the only
   content-adjacent field, containing hash-shaped strings only — not full text). Also assert the
   field set is a subset of `docs/observability/retrieval_retention_redaction_policy.md`'s MAY-list
   category shapes (hash/ID/count/reason-code/score/latency/version/status), documented inline in
   the test as a manual cross-reference since the policy doc is prose, not a machine-readable list.
   Location: new test file (or extends #1's file), colocated with the new wrapper module's tests.

4. **`test_hybrid_retrieval_wrapper_emits_exactly_one_retrieval_event`** (AC4)
   Category: integration.
   Verifies: exercising the new instrumented wrapper around `hybrid_fuse_and_filter()` (with a
   monkeypatched/fixture `conn`/`bm25_obj` mirroring `test_hybrid_retrieval.py`'s existing fakes)
   against a `tmp_path`-scoped `agent-monitoring/events.jsonl` appends **exactly one** new-shape
   line. Assert the file has exactly 1 line pre-call + N lines post-call = N+1 (or 0→1 for an empty
   starting file), and that the appended line's `phase`/`agent`/fields match the wrapper's inputs.
   Location: `tests/tools/test_hybrid_retrieval.py` (new test class) or the new wrapper module's own
   test file.

5. **`test_wrapper_module_no_new_locking_no_direct_file_open_no_fcntl`** (AC4)
   Category: architecture guard.
   Verifies (mirrors `test_monitoring_writer_single_source.py`'s pattern against the *new* wrapper
   module path(s), not the existing hardcoded `_CALL_SITES`): `"import fcntl" not in source`,
   `"from fcntl" not in source`, `"O_EXCL" not in source`, and the module contains
   `"from writer import"` (or equivalently imports `record_events.write_lines`/
   `record_events.validate_record`, per whichever integration shape Plan chooses — see
   investigation.md's "Emission path" open question).
   Location: new test file, e.g. `tests/tools/test_retrieval_event_wrapper_single_source.py`.

6. **`test_retrieval_cache_wrapper_emits_correct_cache_status_per_level`** (AC5)
   Category: integration, parametrized over the 3 cache levels.
   Verifies: exercising the new wrapper around `check_query_cache`/`check_index_cache`/
   `check_packet_cache` (using `test_retrieval_cache.py`'s existing `_isolated_cache_db` fixture
   pattern so no real `knowledge-index/retrieval_cache.db` is touched) for a HIT, a MISS, and a
   STALE_REJECTED case each emits a retrieval event whose `cache_status` field equals
   `retrieval_cache.HIT`/`MISS`/`STALE_REJECTED` verbatim (imported constants, never re-literaled
   strings, per investigation.md's Anti-Drift Hazards) and whose `cache_level` matches the level
   under test (`retrieval_index_cache`/`retrieval_query_cache`/`retrieval_packet_cache` — reusing
   `retrieval_cache.INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/`PACKET_CACHE_CATEGORY` constants).
   Location: `tests/tools/test_retrieval_cache.py` (new test class) or the new wrapper module's test
   file.

7. **`test_wrapper_module_never_references_workflow_files_or_pipeline_entry_points`** (AC6)
   Category: architecture guard / structural.
   Verifies: grep the source of every new call-site/wrapper module for `.claude/workflows` and for
   any known pipeline entry-point string (e.g. `implement-ticket.js`, `pushEvent`, `writeSidecar`)
   and assert zero matches. Mirrors this ticket's own Out-of-Scope guarantee and the sibling
   Phase 3 tickets' identical guard pattern.
   Location: new test file (can be combined with #5's file).

8. **`test_generate_retro_or_query_retrieval_metrics_function`** (AC7)
   Category: unit, fixture-based.
   Verifies: a new function in `generate_retro.py` or `query.py` (e.g.
   `compute_retrieval_metrics(events)` or `query_retrieval_events(...)`) reads a **fixture list of
   retrieval-shaped event dicts** (not live `events.jsonl`) and correctly computes: cache
   hit/miss/stale-rejection rate (grouped by `cache_level`), candidate-to-selected ratio
   (`selected_count / candidate_count`), and selected-to-cited ratio
   (`len(cited_source_hashes) / selected_count`). Include an edge case for `candidate_count == 0`
   (must not raise `ZeroDivisionError`) and a mixed-fixture case where some events are ordinary
   workflow events (no retrieval fields) interleaved with retrieval events, proving the function
   correctly skips/ignores non-retrieval records rather than crashing on missing keys.
   Location: `tests/tools/test_generate_retro.py` or `tests/tools/test_query.py` (extend whichever
   already exists; create if neither does, following `test_hybrid_retrieval.py`'s
   `importlib.util.spec_from_file_location` load pattern if the target file has no `__init__.py`
   package wiring).

9. **`test_context_packet_wrapper_reason_code_and_hash_counts`** (supports AC1/AC7 end-to-end proof)
   Category: integration.
   Verifies: exercising the new wrapper around `assemble_context_packet()` with a small fixture
   candidate list emits a retrieval event whose `exclusion_reason_counts` matches
   `build_excluded_summary()`'s own aggregation and whose `cited_source_hashes` matches
   `[c["hash"] for c in included]` exactly (order-independent — compare as sets/sorted lists).
   Location: `tests/tools/test_context_packet_assembler.py` (new test class) or the wrapper's own
   test file.

## Scoped Pytest Commands

```bash
# Core monitoring writer/schema regression
pytest tests/tools/test_record_events.py tests/tools/test_monitoring_writer.py \
  tests/tools/test_monitoring_writer_single_source.py -v

# Phase 3 modules being instrumented (must stay green, unmodified signatures)
pytest tests/tools/test_hybrid_retrieval.py tests/tools/test_retrieval_cache.py \
  tests/tools/test_context_packet_assembler.py -v

# New wrapper module + schema tests (exact file name(s) depend on Plan's chosen layout)
pytest tests/tools/test_retrieval_event_schema.py \
  tests/tools/test_retrieval_event_wrapper_single_source.py -v   # adjust to actual filenames chosen in Plan

# Downstream query/retro consumers
pytest tests/tools/test_generate_retro.py tests/tools/test_query.py -v   # if these files exist; else the new fixture-based test file from AC7

# Full agent-monitoring domain sweep (final check before Verify)
pytest tests/tools/ -k "monitoring or retrieval or record_events or writer" -v
```

Never run bare `pytest tests/`. Scope stays inside `tests/tools/` (the domain this ticket's
Related Code Areas live in) for the entire ticket.

## Anti-Drift Test Guards

- **`test_no_call_site_imports_fcntl`-style guard for the NEW module, not a rewrite of the existing
  one.** Confirms the existing 3-call-site guard (`test_monitoring_writer_single_source.py`) is
  never edited to add the wrapper — a diff touching that file's `_CALL_SITES` list should fail
  review, since AC4 explicitly asks for a test that *mirrors* it, not one that *extends* it.
- **`record_events.py` REQUIRED-set immutability guard**: assert
  `record_events.REQUIRED == {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}`
  verbatim (a literal set-equality assertion, not a subset check) in the new schema test file —
  catches any accidental widening of the base REQUIRED set to include a retrieval-specific field,
  which would be an undocumented breaking change to every existing workflow event.
- **Vocabulary-warning silence guard**: assert that emitting a retrieval event with the
  recommended new `run_id` prefix (e.g. `RETRIEVAL-EVENT-...`) produces **zero** stderr WARNING
  output from `warn_vocabulary_drift()` — proving the "let `infer_workflow()` return `None`"
  design choice actually avoids vocabulary noise rather than accidentally colliding with one of the
  4 known prefixes.
- **No-real-run_id-pollution guard**: assert that running the new wrapper's test/demo invocation
  does NOT write into the repo's real `agent-monitoring/events.jsonl` (every new test must use
  `tmp_path`/`monkeypatch.chdir`, exactly like `test_record_events.py`'s existing subprocess tests
  already do) — a regression here would corrupt the live monitoring corpus with synthetic
  test-invocation noise.
- **Cache-status literal-reuse guard**: a test asserting the wrapper's `cache_status` field values
  come from `retrieval_cache.HIT`/`MISS`/`STALE_REJECTED` by identity/equality to the imported
  constants (not re-typed string literals) — catches silent drift if `retrieval_cache.py`'s
  constant strings ever change.
- **generate_retro/query non-mutation guard**: assert the new retrieval-metrics query function is
  read-only — it must not call `write_lines`/`write_line`/open any file in `"w"`/`"a"` mode — a
  simple source-grep test, matching this repo's broader "decision logic reads state, does not
  mutate" architecture rule.
- **MAY/PROHIBITED field-set regression guard**: keep test #3 (AC3) as a standing regression test,
  not a one-time check — any future field addition to the retrieval-event shape must re-pass this
  test, so it should assert against the *current* field set by introspection (e.g. iterating a
  shared `RETRIEVAL_EVENT_FIELDS` constant) rather than a hardcoded list that silently goes stale.
