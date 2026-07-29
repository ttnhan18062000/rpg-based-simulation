---
status: historical
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
phase: done
date: 2026-07-29
tags: [observability, agent-monitoring, schema]
---

# TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT

## Title
Add versioned retrieval-event schema to events.jsonl and wire emission through the existing writer

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
The author wants a new, additive event shape appended to the existing events.jsonl file (not a new file) that records retrieval activity from the Phase 3 modules: scenario/risk_tier (if caller-supplied), corpus/graph generation, retrieval version, cache level/status, latency, candidate count, selected count, source-kind counts, authority/freshness counts, exclusion reason counts, cited-source hashes, adequacy verdict, and expansion reason/count. Because runs.jsonl/events.jsonl do not yet carry execution_id or provider fields, the event stays scoped to the existing run_id shape plus new retrieval-specific fields, following the already-resolved retention/redaction policy verbatim. This schema is only meaningful once wired up: call sites inside Phase 3's own test/manual-invocation paths (or new instrumented wrapper functions around tools/hybrid_retrieval.py, tools/retrieval_cache.py, or tools/context_packet_assembler.py) must actually emit it, invoking the already-decided, already-stress-tested writer (writer.py's write_line/write_lines) with no new lock/queue/journal design. This phase only observes manual/test invocations — it does not make retrieval events fire during real agent workflow runs.

## Scope
- Define a new additive, versioned retrieval-event field set (retrieval_schema_version, corpus_generation, cache_level, cache_status, latency_ms, candidate_count, selected_count, source_kind_counts, authority_counts, freshness_counts, exclusion_reason_counts, cited_source_hashes, adequacy_verdict, expansion_reason, expansion_count, plus optional scenario/risk_tier) layered on top of events.jsonl's existing 7 required fields (run_id, seq, ts, phase, agent, summary, status)
- Field inclusion follows the MAY-list (hashes/IDs/counts/reason codes/scores/latency/version numbers/cache status) and PROHIBITED-list (raw prompt/chunk/source text, unredacted payloads) verbatim from docs/observability/retrieval_retention_redaction_policy.md
- Instrument call sites or new instrumented wrapper functions in tools/hybrid_retrieval.py, tools/retrieval_cache.py, and tools/context_packet_assembler.py's own test/manual-invocation paths that emit the new event shape via writer.py's write_line/write_lines exclusively
- Add a minimal proof-of-queryability function in generate_retro.py or query.py showing the new shape is readable end-to-end (comprehensive dashboard views are out of scope, see sibling ticket)
- Regression coverage proving record_events.py's REQUIRED set and downstream consumers (generate_retro.py, query.py, build_index.py) are unaffected by the new optional fields

## Out of Scope
- No execution_id or provider fields added to runs.jsonl/events.jsonl or the new retrieval-event shape
- No wiring into any .claude/workflows/*.js file or existing pipeline entry point — emission is limited strictly to Phase 3 modules' own test/manual-invocation paths and new instrumented wrapper functions
- No live Codex pilot execution
- No new dashboard frontend/UI surface; only the minimal proof-of-queryability function described above — full dashboard/retro views belong to the sibling ticket covering C3
- No new lock/queue/journal writer mechanism — must reuse writer.py's write_line/write_lines exclusively, never open() a file directly
- No changes to record_events.py's REQUIRED base-field set (run_id, seq, ts, phase, agent, summary, status)

## Acceptance Criteria
- [x] A retrieval-event record written via record_events.py's validate_record()/write_lines() path contains all 7 base fields (run_id, seq, ts, phase, agent, summary, status) plus the new retrieval-specific fields (retrieval_version, corpus_generation, cache_level, cache_status, latency_ms, candidate_count, selected_count, source_kind_counts, authority_counts, freshness_counts, exclusion_reason_counts, cited_source_hashes, adequacy_verdict, expansion_reason, expansion_count)
- [x] Records missing any of the 7 base fields are still rejected identically to today's behavior (regression-tested)
- [x] A structural test asserts the new retrieval-event field schema contains no execution_id field, no provider field, and no raw-prompt/raw-retrieved-content-text field
- [x] Exercising a new instrumented wrapper around hybrid_fuse_and_filter() (or a manual/test invocation of tools/hybrid_retrieval.py) appends exactly one new-shape retrieval-event JSON line via writer.py's write_line/write_lines, verified by a test mirroring test_monitoring_writer_single_source.py's assertions (zero new locking code, no direct file opens, no fcntl import at the new call site)
- [x] Exercising retrieval_cache.py's check_query_cache/check_index_cache/check_packet_cache through the new manual/test call site emits a retrieval event whose cache_status field correctly reflects hit/miss/stale-rejected
- [x] A structural test greps the new call-site/wrapper module(s) for any reference to .claude/workflows/*.js or an existing pipeline entry point and asserts zero matches
- [x] generate_retro.py or query.py exposes at least one new unit-tested (fixture-based) query function reading cache hit/miss/stale-rejection rates and candidate-to-selected/selected-to-cited ratios from the new shape, proving the schema is queryable end-to-end

## Related Tickets
- TCK-20260728-RETRIEVAL-RETENTION-REDACTION
- TCK-20260728-CONTEXT-PACKET-SCHEMA
- TCK-20260728-PHASE0-PREREQ-CONFIRMATION
- TCK-20260729-DETERMINISTIC-CODE-INDEX
- TCK-20260729-HYBRID-RETRIEVAL-FUSION
- TCK-20260729-RETRIEVAL-CACHE-LEVELS
- TCK-20260729-CONTEXT-PACKET-ASSEMBLY
- TCK-20260721-MONITORING-WRITER-DECISION
- TCK-20260721-MONITORING-WRITER-UNIFICATION

## Related Docs
- docs/agent-monitoring/schema.md
- docs/observability/retrieval_retention_redaction_policy.md
- docs/engine/contracts/context_packet_contract.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/ticket_plan_structure_phase4.md
- docs/plans/agent_infrastructure/context_efficient_agent_retrieval/idea_context_efficient_agent_retrieval_observability.md
- docs/ai/monitoring_writer_decision.md
- docs/parity_ledger/infrastructure.yaml

## Related Stored Artifacts
None.

## Related Code Areas
- tools/agent-monitoring/record_events.py
- tools/agent-monitoring/writer.py
- tools/agent-monitoring/generate_retro.py
- tools/agent-monitoring/query.py
- tools/agent-monitoring/vocabulary.py
- tools/hybrid_retrieval.py
- tools/retrieval_cache.py
- tools/context_packet_assembler.py
- tools/code_test_index.py
- tests/tools/test_record_events.py
- tests/tools/test_retrieval_cache.py
- tests/tools/test_hybrid_retrieval.py
- tests/tools/test_monitoring_writer.py
- tests/tools/test_monitoring_writer_single_source.py

## Assumptions / Open Questions
- CRITICAL/UNRESOLVED: record_events.py's validate_record() REQUIRED set (run_id, seq, phase, agent, summary, status) is shaped for workflow-tracked agent calls; a retrieval event fired from a standalone manual/test invocation of a Phase 3 module (outside any .claude/current_run-tracked workflow) has no natural run_id/seq/phase/agent value, and docs/ai/monitoring_writer_decision.md forbids inventing a synthesized run-{code}-{timestamp} value — the Plan phase must explicitly decide how these four base fields are populated for a standalone retrieval-event call site rather than silently guessing an answer
- events.jsonl has no existing event-family discriminator field; every current record is a workflow-phase event consumed by generate_retro.py/query.py's normalization logic — adding a structurally different retrieval-event shape risks silent mis-parsing unless a family/kind marker (e.g. retrieval_schema_version or an explicit event_kind field) is added and those readers' unaffected behavior is verified
- "Versioned" implies a schema-version field/convention with no existing precedent in this repo — must be defined explicitly during planning (e.g. a retrieval_schema_version constant)
- record_events.py's warn_vocabulary_drift() will print non-blocking WARNING lines for any new phase/agent value not already registered in vocabulary.py — planning should decide whether to register new identifiers or accept/document the warning
- No Phase 3 module is wired into any workflow today, so real retrieval-event volume will be near-zero at ship time — this is expected and acceptable per the batch's own scope, not a defect to fix here

## Implementation Notes

Implemented all 10 plan steps as specified.

- **`tools/retrieval_events.py` (new)** — `retrieval_event_schema_version = 1` (distinct from
  `retrieval_cache.RETRIEVAL_VERSION`, comment states the distinction explicitly);
  `RETRIEVAL_EVENT_FIELDS` frozenset (18 field names: the 15 retrieval-specific fields, the 2
  optional `scenario`/`risk_tier` fields, plus `retrieval_event_schema_version` itself —
  excludes `execution_id`/`provider`/all 7 REQUIRED base fields); `NOISY_RATIO_THRESHOLD = 5` and
  `compute_adequacy_verdict()`'s 3-branch insufficient/noisy/sufficient heuristic;
  `emit_retrieval_event()` (validates via `record_events.validate_record()`, writes via
  `writer.write_lines()`, raises `ValueError` on an unknown retrieval field or a
  `validate_record()` rejection, returns `write_lines()`'s bool verbatim on infra failure);
  `wrap_hybrid_retrieval()` / `wrap_retrieval_cache_check()` / `wrap_context_packet_assembly()`,
  each with its own `RUN_ID_*`/`AGENT_*` literal pair (`RETRIEVAL-EVENT-<slug>` run_id prefix,
  `phase="Retrieval"`, a self-describing `*-wrapper` agent name) — none of the 4 known workflow
  prefixes, so `vocabulary.py::infer_workflow()` returns `None` and `warn_vocabulary_drift()` is
  a genuine no-op by design (confirmed by test).
- **`tools/agent-monitoring/generate_retro.py`** — added `compute_retrieval_metrics(events)`
  (read-only, fixture-tested, zero-division-guarded): filters to records carrying
  `retrieval_event_schema_version`, groups cache hit/miss/stale-rejection counts+rates by
  `cache_level`, and computes per-event candidate-to-selected and selected-to-cited ratios. No
  existing function in that file was modified.
- **`docs/parity_ledger/infrastructure.yaml`** — appended `INFRA-297` (P2, verified), the first
  ledger entry referencing `events.jsonl`'s schema itself rather than only a module that emits
  into it.
- New tests: `tests/tools/test_retrieval_events.py` (21 tests: field-shape constant, AC1/AC2
  emit tests, AC3 structural guard, AC4 hybrid-wrapper emission test, AC5 cache-wrapper tests
  parametrized across all 3 cache levels x HIT/MISS/STALE_REJECTED outcomes, and the
  context-packet wrapper test), `tests/tools/test_retrieval_event_wrapper_single_source.py` (4
  tests: no-fcntl/no-O_EXCL/imports-writer guard mirroring, but not extending,
  `test_monitoring_writer_single_source.py`'s `_CALL_SITES`; AC6's zero-workflow-reference grep
  guard), and a new `TestComputeRetrievalMetrics` class (9 tests) appended to
  `tests/tools/test_generate_retro.py`.
- No edits to `record_events.py`, `writer.py`, `vocabulary.py`,
  `test_monitoring_writer_single_source.py`'s `_CALL_SITES`, or any of `hybrid_retrieval.py`/
  `retrieval_cache.py`/`context_packet_assembler.py`'s public signatures/return shapes.

## Test Summary

`pytest tests/tools/test_record_events.py tests/tools/test_monitoring_writer.py \
tests/tools/test_monitoring_writer_single_source.py tests/tools/test_hybrid_retrieval.py \
tests/tools/test_retrieval_cache.py tests/tools/test_context_packet_assembler.py \
tests/tools/test_retrieval_events.py tests/tools/test_retrieval_event_wrapper_single_source.py \
tests/tools/test_generate_retro.py tests/tools/test_query.py -q` → **200 passed**.

Broader sweep `pytest tests/tools/ -k "monitoring or retrieval or record_events or writer" -q` →
210 passed, 1 pre-existing unrelated failure
(`test_build_index.py::TestMakeTarget::test_makefile_dry_run_agent_monitoring_index`, confirmed
via `git stash` to fail identically on the pre-ticket tree — a Makefile-timestamp flake, not
touched by this ticket).

`python3 tools/validate_frontmatter.py` passes on the ticket and all 3 staging artifacts. The new
`INFRA-297` parity-ledger entry individually validates against `docs/parity_ledger/schema.json`
(the ledger's pre-existing `INFRA-280` entry has an unrelated, pre-existing schema violation —
`proof_type: feature` is not in the schema's enum — confirmed present before this ticket's changes
and out of this ticket's scope to fix).

**Test-phase fix (order-dependent cross-file bug found and fixed):** running the scoped command
above with `test_retrieval_events.py` collected *before* `test_hybrid_retrieval.py` on the command
line intermittently failed one new test
(`TestWrapHybridRetrieval::test_wrapper_emits_exactly_one_retrieval_event`) with
`sqlite3.OperationalError: no such table: knowledge_vec`. Root cause: `test_hybrid_retrieval.py`
registers its own fresh `hybrid_retrieval` module object into `sys.modules["hybrid_retrieval"]` via
a custom `spec_from_file_location` loader during its own collection; when that collection happens
*after* `test_retrieval_events.py`'s own `import hybrid_retrieval as hr` (module-level, captured at
collection time), `hr` becomes stale relative to what `wrap_hybrid_retrieval()`'s deferred `from
hybrid_retrieval import ...` resolves at call time (post-collection) — so `monkeypatch.setattr(hr,
"_dense_candidates", ...)` silently patched the wrong module object, and the real
`_dense_candidates()` hit the real (test-fixture) SQLite connection's missing `knowledge_vec`
table. Fixed by patching via `sys.modules["hybrid_retrieval"]` (re-fetched at test-execution time,
after all collection has finished) instead of the possibly-stale `hr` reference. Confirmed fixed in
both collection orderings and the full scoped command (200 passed each).

## Files Changed

- `tools/retrieval_events.py` (new)
- `tools/agent-monitoring/generate_retro.py` (added `compute_retrieval_metrics()`)
- `tests/tools/test_retrieval_events.py` (new)
- `tests/tools/test_retrieval_event_wrapper_single_source.py` (new)
- `tests/tools/test_generate_retro.py` (added `TestComputeRetrievalMetrics`)
- `docs/parity_ledger/infrastructure.yaml` (appended `INFRA-297`)
- `docs/agent-monitoring/schema.md` (added a new "Retrieval-event field family (additive)" subsection documenting all 18 new fields and the run_id provenance scheme — added at Verify, per done-checker's finding that this doc gap broke the established per-field-addition documentation pattern)

## Completion Summary

All 7 acceptance criteria met: a retrieval event built via `emit_retrieval_event()` round-trips
all 7 base fields plus the 18-field retrieval-specific shape through
`record_events.validate_record()`/`writer.write_lines()` unchanged (AC1); a missing/null base
field is still rejected identically with the new fields present (AC2); a structural test proves
the schema excludes `execution_id`/`provider`/raw-text fields and that `cited_source_hashes` is
hash-shaped only (AC3); `wrap_hybrid_retrieval()` appends exactly one event via the shared writer
with no new locking code (AC4); `wrap_retrieval_cache_check()` emits the correct `cache_status`
for all 3 cache levels across HIT/MISS/STALE_REJECTED (AC5); a grep guard proves zero references
to any workflow orchestrator file or pipeline entry point (AC6); and
`compute_retrieval_metrics()` proves the new shape is queryable end-to-end via cache rates and
candidate/selected/cited ratios, both zero-division guarded (AC7). No Phase 3 module was wired
into any real workflow — real retrieval-event volume in the live `events.jsonl` stays at zero
after this ticket, as documented and expected. Architecture constraints held throughout: decision
logic stayed read-only, all durable writes went through `record_events.py`'s
validate-then-`writer.write_lines()` path, no raw domain model crossed an API boundary (this
ticket touches no API layer), and no new lock/queue/journal mechanism was introduced.
