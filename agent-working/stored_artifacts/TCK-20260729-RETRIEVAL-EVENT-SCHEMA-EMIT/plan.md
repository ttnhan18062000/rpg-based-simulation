---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
artifact_type: plan
tags: [observability, agent-monitoring, schema]
---

# Implementation Plan — TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT

## Summary

Add a new additive, versioned retrieval-event field set to `events.jsonl` and wire it up through
one new shared module, `tools/retrieval_events.py`, which owns the field-shape constant, the
`emit_retrieval_event()` helper (validates via `record_events.validate_record()` then writes via
`writer.write_lines()`, mirroring the other 3 call sites' direct-import pattern), and one thin
instrumentation wrapper per Phase 3 module (`wrap_hybrid_retrieval()`, `wrap_retrieval_cache_check()`,
`wrap_context_packet_assembly()`). No existing file's enforcement logic changes —
`record_events.py`'s REQUIRED set is untouched and already passes the ~15 new fields through
unmodified (proven precedent: `test_execution_identity_fields_pass_through_unchanged`). The
standalone-invocation provenance problem (no real `run_id`/`seq`/`phase`/`agent` for a
non-workflow test/manual call) is resolved by minting a new, explicit `RETRIEVAL-EVENT-<slug>`
`run_id` prefix that `vocabulary.py`'s `infer_workflow()` deliberately returns `None` for,
making `warn_vocabulary_drift()` a documented no-op rather than a suppressed warning. New tests
land in `tests/tools/test_retrieval_events.py` (schema + wrapper tests) plus small additive test
classes in the 3 modules' existing test files, and one new fixture-based query function in
`generate_retro.py` (or `query.py`) proves end-to-end queryability.

## Resolved Decisions

1. **Standalone-invocation provenance (`run_id`/`seq`/`phase`/`agent`)** — RESOLVED per
   investigation's grounded recommendation (investigation.md "CRITICAL — resolved by evidence"):
   - `run_id`: a new, explicit, self-describing prefix `"RETRIEVAL-EVENT-<slug>"`, where `<slug>`
     is the wrapped module's own slug (`"hybrid-retrieval"`, `"retrieval-cache"`,
     `"context-packet"`). Distinct from all 4 of `infer_workflow()`'s recognized prefixes
     (`SIMQ-AUDIT-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`, `TCK-`) — cited: vocabulary.py:86-94.
     This is a stable, human-readable literal, not a synthesized `run-{code}-{timestamp}` — it
     does not violate schema.md:374-376's "never invent a synthesized ID" rule (that rule targets
     hand-writing a *workflow-shaped* record with a fabricated join key; this is a genuinely new,
     labeled, non-workflow event family).
   - `seq`: a small caller-supplied literal `int`, starting at `1`, incrementing per call within
     one demo/test run — never a timestamp or hash (mirrors `record_events.py`'s own contract of
     never inventing `seq`).
   - `phase`: the literal `"Retrieval"` for every wrapper (a new, self-describing phase name, not
     one of the 4 workflows' real phases).
   - `agent`: a new, self-describing literal per wrapped module —
     `"hybrid-retrieval-wrapper"` / `"retrieval-cache-wrapper"` / `"context-packet-wrapper"`.
   - **Confirmed genuinely a no-op, not a suppressed warning:** `infer_workflow()`
     (vocabulary.py:73-94) returns `None` for any prefix outside the 4 known ones — its own
     docstring says "Returns `None` if run_id matches no known prefix (e.g. a future 5th
     workflow) ... callers must treat `None` as 'skip the check silently'."
     `warn_vocabulary_drift()` (record_events.py:71-83) reads: `workflow =
     infer_workflow(record.get("run_id", "")); if workflow is None: return` — the function
     returns immediately, before either of its two `WARNING:` print statements. There is no
     branch where a `None` workflow still evaluates `record["phase"] not in
     WORKFLOW_PHASES.get(workflow, set())` or the agent check. This is a designed, tested
     fallthrough (vocabulary.py's own docstring language: "e.g. a future 5th workflow"), not an
     incidental side effect — safe to rely on. None of the new `phase`/`agent` literals need
     registration in `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS`.

2. **Wrapper module location** — RESOLVED: one new shared module, `tools/retrieval_events.py`,
   flat alongside `hybrid_retrieval.py`, `retrieval_cache.py`, `context_packet_assembler.py`,
   `code_test_index.py` (this session's established precedent — all four live at `tools/` top
   level, no subpackage). Contains: the field-shape constant, `emit_retrieval_event()`, and the
   3 `wrap_*()` functions, in one file (not split across 3 files) — keeps the single-source-of-
   truth field constant colocated with every emission call site.

3. **Integration shape** — RESOLVED: `emit_retrieval_event()` imports `record_events.validate_record`
   and `writer.write_lines` directly (`sys.path.insert` against `tools/agent-monitoring/`, the
   same pattern `context_packet_assembler.py` already uses for its own `tools/`-relative import
   of `hybrid_retrieval`) — Python function calls, never `subprocess`/CLI. This matches every
   existing `tools/agent-monitoring/*.py` call site (`post_tool_hook.py`, `record_run.py`,
   `record_events.py` itself all import `writer.py` directly) and satisfies both AC1 ("via
   `record_events.py`'s `validate_record()`/`write_lines()` path") and AC4 ("via `writer.py`'s
   `write_line`/`write_lines`") simultaneously, since `record_events.validate_record()` is the
   validation gate and `writer.write_lines()` is the actual append call.

4. **`adequacy_verdict`** — RESOLVED as a simple, explicitly-scoped placeholder heuristic, not a
   quality model (ticket's Out of Scope: "no re-ranker, no sophisticated evaluation"):
   - `"insufficient"` if `selected_count == 0`
   - `"noisy"` if `selected_count > 0` and `candidate_count >= NOISY_RATIO_THRESHOLD * selected_count`
     (constant `NOISY_RATIO_THRESHOLD = 5`, defined and documented in `tools/retrieval_events.py`
     as a deliberately simple, tunable placeholder)
   - `"sufficient"` otherwise
   Documented inline as a placeholder, not a claim of real relevance/quality assessment.

5. **`latency_ms`** — RESOLVED: measured by each `wrap_*()` function itself via
   `time.perf_counter()` bracketing the wrapped call (`(time.perf_counter() - start) * 1000`),
   stdlib only, no new dependency. None of the 3 wrapped modules self-report latency
   (investigation.md confirms this for all 3).

6. **Naming collision** — RESOLVED: the new event-schema-version constant is named
   `retrieval_event_schema_version` (module-level `int`, starting at `1`, in
   `tools/retrieval_events.py`), explicitly distinct from `tools/retrieval_cache.py::
   RETRIEVAL_VERSION` (a different concept: the cache *key*-versioning constant, bumped on
   cache-key/invalidation logic changes). A comment in `tools/retrieval_events.py` states this
   distinction explicitly so a future reader does not conflate the two.

7. **`candidate_count` for the hybrid wrapper (implementation-level, non-blocking)** — `
   hybrid_fuse_and_filter()`'s return shape (`list[HybridResult]`) does not expose the pre-fusion
   union size, and Step 4 below must not modify that function's signature/return shape
   (investigation.md: "instrumentation wraps the call, it does not alter the wrapped function").
   RESOLVED: `wrap_hybrid_retrieval()` approximates `candidate_count` via
   `hybrid_retrieval.candidate_k(top_k)` (the already-public, already-bounded per-channel
   candidate formula) and documents inline that this is an upper-bound approximation of the
   pre-fusion pool, not the exact post-union count — consistent with `adequacy_verdict`'s
   "deliberately simple placeholder" framing (Decision 4). `selected_count = len(results)`
   (exact, from the wrapped call's real return value).

## Steps

### Step 1 — Create `tools/retrieval_events.py`: field-shape constant + schema version
**Files:** `tools/retrieval_events.py` (new)
**Change:** Create the module with:
- Module docstring stating scope/boundary (mirrors `retrieval_cache.py`'s docstring style):
  "no execution_id/provider fields, no `.claude/workflows/*.js` wiring, no new lock/queue/journal
  writer — reuses `writer.py`'s `write_line`/`write_lines` exclusively via `record_events.py`'s
  validation path."
- `retrieval_event_schema_version: int = 1` with the inline comment distinguishing it from
  `retrieval_cache.RETRIEVAL_VERSION` (Resolved Decision 6).
- `RETRIEVAL_EVENT_FIELDS: frozenset[str]` — the single source-of-truth constant listing exactly
  the 15 new retrieval-specific field names from the ticket's Scope bullet: `retrieval_version`,
  `corpus_generation`, `cache_level`, `cache_status`, `latency_ms`, `candidate_count`,
  `selected_count`, `source_kind_counts`, `authority_counts`, `freshness_counts`,
  `exclusion_reason_counts`, `cited_source_hashes`, `adequacy_verdict`, `expansion_reason`,
  `expansion_count`, plus the two optional fields `scenario`, `risk_tier`, plus
  `retrieval_event_schema_version` itself (17 total). Do NOT include `execution_id`, `provider`,
  or any of the 7 REQUIRED base fields in this constant — it is retrieval-specific fields only.
- `NOISY_RATIO_THRESHOLD: int = 5` and `compute_adequacy_verdict(selected_count: int,
  candidate_count: int) -> str` implementing Resolved Decision 4's 3-branch heuristic.
**Do NOT touch:** `record_events.py`, `writer.py`, `vocabulary.py` — no edits to any of the three
in this step.
**Verify:** New test in `tests/tools/test_retrieval_events.py` (created in Step 2) asserting
`RETRIEVAL_EVENT_FIELDS` contains exactly the expected field names and excludes
`execution_id`/`provider`/the 7 REQUIRED names.

### Step 2 — `emit_retrieval_event()` + AC1/AC2 tests
**Files:** `tools/retrieval_events.py`, `tests/tools/test_retrieval_events.py` (new)
**Change:** Add `emit_retrieval_event(*, run_id: str, seq: int, phase: str, agent: str, summary:
str, status: str = "ok", events_file: Path | None = None, **retrieval_fields) -> bool` to
`tools/retrieval_events.py`:
- `sys.path.insert(0, str(Path(__file__).resolve().parent / "agent-monitoring"))` then `from
  record_events import validate_record` and `from writer import write_lines` (mirrors
  `context_packet_assembler.py`'s existing `sys.path`-relative import pattern for a sibling
  `tools/` module).
- Reject any key in `retrieval_fields` not in `RETRIEVAL_EVENT_FIELDS` by raising `ValueError`
  immediately (loud-fail-on-bad-caller-usage, mirrors `retrieval_cache.py::
  _validate_may_list_kwargs`'s precedent for new code with no existing callers to protect).
- Build `record = {"run_id": run_id, "seq": seq, "ts": <iso timestamp, stdlib `datetime`>,
  "phase": phase, "agent": agent, "summary": summary, "status": status,
  "retrieval_event_schema_version": retrieval_event_schema_version, **retrieval_fields}`.
- Call `errors = validate_record(record)`; if non-empty, raise `ValueError(errors)` (never write a
  record record_events.py itself would reject — fail loud in the wrapper, not silently).
- Default `events_file` to `record_events.EVENTS_FILE` (relative `Path("agent-monitoring/
  events.jsonl")`) if not supplied, so tests can either pass an explicit `tmp_path`-scoped file OR
  rely on `monkeypatch.chdir(tmp_path)` (matches `test_record_events.py`'s existing pattern) —
  `record_events.EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)` before calling
  `write_lines(events_file, [json.dumps(record, separators=(",", ":"))])`.
- Return the `bool` from `write_lines()` verbatim (never raise on a write failure — matches
  CLAUDE.md's "monitoring write failure must never fail the workflow").
Add new test file `tests/tools/test_retrieval_events.py` with:
- `test_retrieval_event_contains_all_base_and_retrieval_fields` (AC1): build a full record via
  `emit_retrieval_event()` with all 7 base fields plus all `RETRIEVAL_EVENT_FIELDS`, write into a
  `tmp_path`-scoped file, read it back, assert every field round-trips exactly.
- `test_missing_base_field_still_rejected_with_new_fields_present` (AC2): call
  `emit_retrieval_event()` with all retrieval fields populated but `phase=None` (or omitted);
  assert it raises `ValueError` whose message reflects `validate_record()`'s own missing-fields
  error shape — proves the new fields cannot mask a missing base field.
- `test_record_events_required_set_immutability_guard`: literal-equality assertion
  `record_events.REQUIRED == {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}`
  (test_plan.md's anti-drift guard).
**Do NOT touch:** `tests/tools/test_record_events.py`'s existing test bodies/fixtures — this is a
new file, not an edit to that one (its own regression suite stays green unmodified per the test
plan's Regression Surface).
**Verify:** `pytest tests/tools/test_retrieval_events.py -v` (new tests above), plus
`pytest tests/tools/test_record_events.py -v` (unchanged regression).

### Step 3 — AC3 structural schema guard test
**Files:** `tests/tools/test_retrieval_events.py`
**Change:** Add `test_retrieval_event_schema_excludes_execution_id_provider_and_raw_text` (AC3):
iterate `retrieval_events.RETRIEVAL_EVENT_FIELDS` and assert `"execution_id" not in fields`,
`"provider" not in fields`, and none of `{"raw_prompt", "raw_text", "chunk_text",
"retrieved_content", "payload"}` appear. Separately assert `"cited_source_hashes"` is the only
content-adjacent field name, and add a helper assertion/fixture confirming a sample
`cited_source_hashes` value only contains hash-shaped strings (e.g. `all(len(h) == 64 and
all(c in "0123456789abcdef" for c in h) for h in sample)` for sha256-hex, matching
`context_packet_assembler.py`'s own hash convention) — never full text. Document inline (test
docstring or comment) the manual cross-reference to `docs/observability/
retrieval_retention_redaction_policy.md`'s MAY-list categories (hash/ID/count/reason-code/score/
latency/version/status), since that policy doc is prose, not machine-readable.
**Do NOT touch:** the redaction policy doc itself — this ticket only proves the new schema
conforms to it, it does not modify the policy (already-closed decision per investigation.md).
**Verify:** `pytest tests/tools/test_retrieval_events.py::test_retrieval_event_schema_excludes_execution_id_provider_and_raw_text -v`

### Step 4 — Single-source writer guard for the new module (mirrors, does not extend, the existing guard)
**Files:** `tests/tools/test_retrieval_event_wrapper_single_source.py` (new)
**Change:** New test file, structurally mirroring `tests/tools/
test_monitoring_writer_single_source.py` but scoped to exactly `tools/retrieval_events.py` (its
own `_CALL_SITES`-equivalent, a 1-item list, not an edit to the existing file's list):
- `"import fcntl" not in source` and `"from fcntl" not in source`
- `"O_EXCL" not in source`
- `"from writer import write_lines" in source` (or the exact import line Step 2 actually writes —
  match verbatim once Step 2 lands)
**Do NOT touch:** `tests/tools/test_monitoring_writer_single_source.py` — its `_CALL_SITES` list
stays exactly 3 entries (`post_tool_hook.py`, `record_run.py`, `record_events.py`). Do not add
`retrieval_events.py` to that list under any circumstance (investigation.md's explicit Anti-Drift
Hazard).
**Verify:** `pytest tests/tools/test_retrieval_event_wrapper_single_source.py -v` and
`pytest tests/tools/test_monitoring_writer_single_source.py -v` (unchanged, still 4/4 passing).

### Step 5 — `wrap_hybrid_retrieval()` + AC4 emission test
**Files:** `tools/retrieval_events.py`, `tests/tools/test_retrieval_events.py` (or a new class in
`tests/tools/test_hybrid_retrieval.py` — pick whichever the implementer finds cleaner; both are
acceptable per test_plan.md, keep it in one place)
**Change:** Add to `tools/retrieval_events.py`:
```
RUN_ID_HYBRID = "RETRIEVAL-EVENT-hybrid-retrieval"
AGENT_HYBRID = "hybrid-retrieval-wrapper"

def wrap_hybrid_retrieval(*, seq: int, summary: str, run_id: str = RUN_ID_HYBRID,
                           status: str = "ok", events_file=None, **hybrid_kwargs):
    from hybrid_retrieval import candidate_k, hybrid_fuse_and_filter
    start = time.perf_counter()
    results = hybrid_fuse_and_filter(**hybrid_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000
    selected_count = len(results)
    candidate_count = candidate_k(hybrid_kwargs["top_k"])  # approximation, see Resolved Decision 7
    source_kind_counts = Counter(r.kind for r in results)
    authority_counts = Counter(r.authority for r in results)
    freshness_counts = Counter(r.freshness for r in results)
    emit_retrieval_event(
        run_id=run_id, seq=seq, phase="Retrieval", agent=AGENT_HYBRID, summary=summary,
        status=status, events_file=events_file,
        latency_ms=latency_ms, candidate_count=candidate_count, selected_count=selected_count,
        source_kind_counts=dict(source_kind_counts), authority_counts=dict(authority_counts),
        freshness_counts=dict(freshness_counts),
        adequacy_verdict=compute_adequacy_verdict(selected_count, candidate_count),
    )
    return results
```
(Signature/body above is illustrative of the exact shape to implement — implementer should match
`hybrid_fuse_and_filter`'s real keyword-only signature from `tools/hybrid_retrieval.py:224-238`
exactly via `**hybrid_kwargs` passthrough, not reimplement it.)
Add `test_hybrid_retrieval_wrapper_emits_exactly_one_retrieval_event` (AC4) to
`tests/tools/test_retrieval_events.py`: using `test_hybrid_retrieval.py`'s existing fake
`conn`/`bm25_obj` fixtures (import or replicate the same fixture pattern), call
`wrap_hybrid_retrieval()` against a `tmp_path`-scoped events file, assert exactly 1 line appended,
and assert the line's `phase == "Retrieval"`, `agent == AGENT_HYBRID`,
`run_id.startswith("RETRIEVAL-EVENT-")`, and `source_kind_counts`/`authority_counts`/
`freshness_counts` match the real `HybridResult` list returned.
**Do NOT touch:** `hybrid_retrieval.py` — no signature change to `hybrid_fuse_and_filter()`,
`HybridResult`, or `candidate_k()`. The wrapper calls these unmodified.
**Verify:** the new AC4 test above, plus `pytest tests/tools/test_hybrid_retrieval.py -v`
(unchanged, full file green).

### Step 6 — `wrap_retrieval_cache_check()` + AC5 emission test (3 cache levels)
**Files:** `tools/retrieval_events.py`, `tests/tools/test_retrieval_events.py` (or a new class in
`tests/tools/test_retrieval_cache.py`)
**Change:** Add to `tools/retrieval_events.py`:
```
RUN_ID_CACHE = "RETRIEVAL-EVENT-retrieval-cache"
AGENT_CACHE = "retrieval-cache-wrapper"

def wrap_retrieval_cache_check(cache_level: str, *, seq: int, summary: str,
                                run_id: str = RUN_ID_CACHE, status: str = "ok",
                                events_file=None, **check_kwargs):
    from retrieval_cache import (
        INDEX_CACHE_CATEGORY, QUERY_CACHE_CATEGORY, PACKET_CACHE_CATEGORY,
        check_index_cache, check_query_cache, check_packet_cache,
    )
    dispatch = {
        INDEX_CACHE_CATEGORY: check_index_cache,
        QUERY_CACHE_CATEGORY: check_query_cache,
        PACKET_CACHE_CATEGORY: check_packet_cache,
    }
    start = time.perf_counter()
    result = dispatch[cache_level](**check_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000
    emit_retrieval_event(
        run_id=run_id, seq=seq, phase="Retrieval", agent=AGENT_CACHE, summary=summary,
        status=status, events_file=events_file,
        cache_level=cache_level, cache_status=result.status, latency_ms=latency_ms,
        **({"corpus_generation": check_kwargs["corpus_generation"]}
           if "corpus_generation" in check_kwargs else {}),
        **({"retrieval_version": check_kwargs["retrieval_version"]}
           if "retrieval_version" in check_kwargs else {}),
    )
    return result
```
(Illustrative shape — `cache_status` MUST be `result.status`, sourced verbatim from
`retrieval_cache.HIT`/`MISS`/`STALE_REJECTED`, never a re-literaled string, per
investigation.md's Anti-Drift Hazard and test_plan.md's "Cache-status literal-reuse guard".
`cache_level` values must be `retrieval_cache.INDEX_CACHE_CATEGORY`/`QUERY_CACHE_CATEGORY`/
`PACKET_CACHE_CATEGORY` imported constants, never re-literaled strings either.)
Add `test_retrieval_cache_wrapper_emits_correct_cache_status_per_level` (AC5), parametrized over
the 3 levels × {HIT, MISS, STALE_REJECTED} using `test_retrieval_cache.py`'s existing
`_isolated_cache_db`-style fixture (no real `knowledge-index/retrieval_cache.db` touched): assert
the emitted event's `cache_status` equals the imported constant by identity/equality and
`cache_level` matches the level under test.
**Do NOT touch:** `retrieval_cache.py` — no signature change to `check_index_cache`/
`check_query_cache`/`check_packet_cache`, no new column, no schema migration.
**Verify:** the new AC5 test above, plus `pytest tests/tools/test_retrieval_cache.py -v`
(unchanged, full file green, including the file's own "duration-is-not-behavior guard").

### Step 7 — `wrap_context_packet_assembly()` + supporting test
**Files:** `tools/retrieval_events.py`, `tests/tools/test_retrieval_events.py` (or a new class in
`tests/tools/test_context_packet_assembler.py`)
**Change:** Add to `tools/retrieval_events.py`:
```
RUN_ID_PACKET = "RETRIEVAL-EVENT-context-packet"
AGENT_PACKET = "context-packet-wrapper"

def wrap_context_packet_assembly(*, seq: int, summary: str, run_id: str = RUN_ID_PACKET,
                                  status: str = "ok", events_file=None, **assemble_kwargs):
    from context_packet_assembler import assemble_context_packet
    start = time.perf_counter()
    packet = assemble_context_packet(**assemble_kwargs)
    latency_ms = (time.perf_counter() - start) * 1000
    selected_count = len(packet.included)
    cited_source_hashes = [c["hash"] for c in packet.included]
    exclusion_reason_counts = {
        f'{row["kind"]}:{row["reason"]}': row["count"] for row in packet.excluded_summary
    }
    emit_retrieval_event(
        run_id=run_id, seq=seq, phase="Retrieval", agent=AGENT_PACKET, summary=summary,
        status=status, events_file=events_file,
        latency_ms=latency_ms, selected_count=selected_count,
        cited_source_hashes=cited_source_hashes,
        exclusion_reason_counts=exclusion_reason_counts,
        corpus_generation=packet.corpus_generation, retrieval_version=packet.retrieval_version,
        adequacy_verdict=compute_adequacy_verdict(selected_count, selected_count),
    )
    return packet
```
(Illustrative shape — for the packet wrapper, `candidate_count` has no natural pre-assembly
analogue exposed by `assemble_context_packet()`'s signature; do not fabricate one — omit
`candidate_count` from this wrapper's emitted event, or pass `len(included_candidates) +
len(excluded)` from `assemble_kwargs` if straightforward. `adequacy_verdict` here degenerates to
"sufficient"/"insufficient" only since no independent candidate pool size exists at this layer —
acceptable per Resolved Decision 4's "deliberately simple placeholder" framing.)
Add `test_context_packet_wrapper_reason_code_and_hash_counts`: exercise the wrapper with a small
fixture `Candidate` list, assert the emitted event's `exclusion_reason_counts` matches
`build_excluded_summary()`'s own aggregation and `cited_source_hashes` matches
`[c["hash"] for c in included]` exactly (compare as sets/sorted lists, order-independent).
**Do NOT touch:** `context_packet_assembler.py` — no change to `assemble_context_packet()`,
`Candidate`, `ContextPacket`, `build_included_entry()`, or `build_excluded_summary()`.
**Verify:** the new test above, plus `pytest tests/tools/test_context_packet_assembler.py -v`
(unchanged, full file green).

### Step 8 — AC6 structural guard: no workflow-file references
**Files:** `tests/tools/test_retrieval_event_wrapper_single_source.py` (extends Step 4's file) or
a new dedicated file
**Change:** Add `test_wrapper_module_never_references_workflow_files_or_pipeline_entry_points`
(AC6): grep `tools/retrieval_events.py`'s source for `.claude/workflows`, `pushEvent`,
`writeSidecar`, and any of the 4 known workflow `.js` filenames (`implement-ticket.js`,
`implement-epic.js`, `create-tickets.js`, `simq-audit.js`); assert zero matches.
**Do NOT touch:** any `.claude/workflows/*.js` file — this step only adds a test proving the new
module never references one.
**Verify:** the new AC6 test.

### Step 9 — AC7 proof-of-queryability function
**Files:** `tools/agent-monitoring/generate_retro.py` (preferred, per investigation.md's framing
of it as the natural home; `query.py` is an acceptable alternative if the implementer finds it a
cleaner fit — pick one, not both), `tests/tools/test_generate_retro.py` (extend if it exists,
else create following `test_hybrid_retrieval.py`'s `importlib.util.spec_from_file_location` load
pattern for a file with no `__init__.py` package wiring)
**Change:** Add `compute_retrieval_metrics(events: list[dict]) -> dict`:
- Filters `events` to only records containing `retrieval_event_schema_version` (skips ordinary
  workflow events without raising on missing keys).
- Groups by `cache_level`, computing hit/miss/stale-rejection rate from `cache_status`.
- Computes candidate-to-selected ratio (`selected_count / candidate_count`, guarding
  `candidate_count == 0` to avoid `ZeroDivisionError` — return `None` or `0.0` for that bucket,
  documented).
- Computes selected-to-cited ratio (`len(cited_source_hashes) / selected_count`, same
  zero-guard).
- Must be read-only: no `write_lines`/`write_line` call, no file opened in `"w"`/`"a"` mode
  (test_plan.md's "generate_retro/query non-mutation guard" — a source-grep test enforcing this).
Add `test_generate_retro_or_query_retrieval_metrics_function` (AC7): fixture list of
retrieval-shaped event dicts (not live `events.jsonl`), assert correct rates/ratios computed,
including the `candidate_count == 0` edge case and a mixed-fixture case (ordinary workflow events
interleaved with retrieval events) proving non-retrieval records are skipped, not crashed on.
**Do NOT touch:** `build_index.py` or the SQLite index schema — the function reads `raw_json` per
row (already stored verbatim, schema.md:17-24) or a plain fixture list; no index migration.
**Do NOT touch:** any existing metric-computation function in `generate_retro.py`/`query.py` —
this is an additive new function, not a rewrite of `compute_retro_metrics`/`filter_events`.
**Verify:** the new AC7 test, plus existing `generate_retro.py`/`query.py` test file(s) unchanged
(no existing test edited).

### Step 10 — Parity ledger entry
**Files:** `docs/parity_ledger/infrastructure.yaml`
**Change:** Append a new entry `INFRA-297` (next free ID after `INFRA-296`), `status: verified`,
`priority: P2`, `text` describing the new retrieval-event schema + `tools/retrieval_events.py`'s
3 wrapper functions + the `generate_retro.py`/`query.py` queryability function, explicitly stating
this is the first ledger entry referencing `events.jsonl`'s schema itself (not just a module that
emits into it) — per investigation.md's Parity Ledger Overlap note. `v2_evidence` cites
`tools/retrieval_events.py`'s line ranges for `RETRIEVAL_EVENT_FIELDS`, `emit_retrieval_event()`,
and the 3 `wrap_*()` functions (fill exact line numbers once Steps 1-9 land).
`test_path: tests/tools/test_retrieval_events.py`. `support_boundary` matches INFRA-293 through
INFRA-296's identical "agent-orchestration/retrieval tooling only" language.
**Do NOT touch:** INFRA-293 through INFRA-296's existing entries — additive append only.
**Verify:** `python3 tools/validate_frontmatter.py` (or the repo's YAML lint step) passes on the
edited file; no test asserts on ledger content directly, this step is docs-only.

## Scope Guards

Reiterated verbatim from the ticket's Out of Scope, plus investigation's anti-drift hazards:

- No `execution_id` or `provider` fields added to `runs.jsonl`/`events.jsonl` or the new
  retrieval-event shape.
- No wiring into any `.claude/workflows/*.js` file or existing pipeline entry point — emission is
  limited strictly to Phase 3 modules' own test/manual-invocation paths and the new instrumented
  wrapper functions in `tools/retrieval_events.py`.
- No live Codex pilot execution.
- No new dashboard frontend/UI surface; only the minimal proof-of-queryability function (Step 9) —
  full dashboard/retro views belong to the sibling ticket covering C3.
- No new lock/queue/journal writer mechanism — `tools/retrieval_events.py` must reuse
  `writer.py`'s `write_line`/`write_lines` exclusively (via `record_events.validate_record()` +
  `writer.write_lines()`), never `open()` a file directly, never import `fcntl`, never use
  `O_EXCL` itself.
- No changes to `record_events.py`'s REQUIRED base-field set (`run_id`, `seq`, `ts`, `phase`,
  `agent`, `summary`, `status`) — enforced by Step 2's literal-equality guard test.
- Do not modify `tests/tools/test_monitoring_writer_single_source.py`'s `_CALL_SITES` list (stays
  exactly 3 entries) — Step 4 adds a separate, new guard file instead.
- Do not modify `hybrid_retrieval.py`, `retrieval_cache.py`, or `context_packet_assembler.py`'s
  public signatures, dataclass shapes, or return types — instrumentation wraps these modules, it
  does not alter them (all three modules' existing test files must stay green unmodified).
- Do not add `retrieval_event_schema_version` (or any new field) to `record_events.py`'s REQUIRED
  set, or to `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` (the new `phase="Retrieval"`/
  `agent="*-wrapper"` literals are intentionally outside those 4-workflow-scoped dicts).
- Do not let `cache_status` be re-literaled — always import `retrieval_cache.HIT`/`MISS`/
  `STALE_REJECTED` and use them verbatim.
- Do not let any new field leak raw text — `cited_source_hashes` stays hash-shaped strings only,
  never full excerpt/chunk text.
- Do not assume the SQLite index (`agent-monitoring-index/monitoring.db`) needs a schema
  migration for Step 9 — it stores `raw_json` verbatim per row already.

## Dependency Map

- Step 1 (field constant + schema version) has no dependencies — first step.
- Step 2 (`emit_retrieval_event()` + AC1/AC2 tests) depends on Step 1 (`RETRIEVAL_EVENT_FIELDS`).
- Step 3 (AC3 structural guard) depends on Step 1 (`RETRIEVAL_EVENT_FIELDS`) only, not Step 2 —
  can run in parallel with Step 2 once Step 1 lands.
- Step 4 (single-source writer guard) depends on Step 2 (needs the real `from writer import
  write_lines` line to exist in `tools/retrieval_events.py` to assert against).
- Step 5 (`wrap_hybrid_retrieval`) depends on Step 2 (`emit_retrieval_event()`).
- Step 6 (`wrap_retrieval_cache_check`) depends on Step 2. Independent of Step 5.
- Step 7 (`wrap_context_packet_assembly`) depends on Step 2. Independent of Steps 5-6.
- Step 8 (AC6 grep guard) depends on Step 2 at minimum (module must exist); best run after Steps
  5-7 so the grep covers the module's final content, but does not strictly require them.
- Step 9 (AC7 query function) is independent of Steps 4-8 — only needs the retrieval-event field
  *shape* (Step 1), not the wrapper functions, since it operates on fixture event dicts. Can be
  done any time after Step 1.
- Step 10 (parity ledger) depends on all of Steps 1-9 being complete (needs final line numbers and
  test path).

Steps 5, 6, 7 are mutually independent and may be implemented/verified in any order once Step 2 is
done. Step 9 may be done in parallel with Steps 4-8.

## Acceptance Criteria Map

| AC from ticket | Implemented by step(s) | Verified by test |
|---|---|---|
| AC1 — record contains all 7 base + 15 new retrieval fields via `validate_record()`/`write_lines()` | Steps 1, 2 | `test_retrieval_event_contains_all_base_and_retrieval_fields` |
| AC2 — records missing a base field still rejected identically | Step 2 | `test_missing_base_field_still_rejected_with_new_fields_present` |
| AC3 — structural test: no `execution_id`/`provider`/raw-text field | Step 3 | `test_retrieval_event_schema_excludes_execution_id_provider_and_raw_text` |
| AC4 — hybrid wrapper appends exactly one event via `writer.py`, no new locking code | Steps 4, 5 | `test_hybrid_retrieval_wrapper_emits_exactly_one_retrieval_event`, `test_retrieval_event_wrapper_single_source.py`'s 3 guard tests |
| AC5 — cache wrapper emits correct `cache_status` per level (hit/miss/stale-rejected) | Step 6 | `test_retrieval_cache_wrapper_emits_correct_cache_status_per_level` (parametrized) |
| AC6 — structural test: zero references to `.claude/workflows/*.js` or pipeline entry points | Step 8 | `test_wrapper_module_never_references_workflow_files_or_pipeline_entry_points` |
| AC7 — new unit-tested query function reads cache rates + candidate/selected/cited ratios | Step 9 | `test_generate_retro_or_query_retrieval_metrics_function` |

## Anti-Drift Notes

- The entire mechanism this ticket relies on (extra fields pass through `validate_record()`
  untouched) already works with zero changes to `record_events.py` — resist any temptation to
  "improve" or refactor `validate_record()`/`REQUIRED`/`VALID_STATUS` while touching this area.
- `warn_vocabulary_drift()`'s no-op-on-`None`-workflow behavior (vocabulary.py:73-94,
  record_events.py:77-79) is load-bearing for Resolved Decision 1 — if a future change to
  `infer_workflow()` ever adds a 5th recognized prefix that happens to collide with
  `"RETRIEVAL-EVENT-"`, this ticket's events would suddenly start producing vocabulary warnings.
  Not a concern for this ticket's implementation, but worth a one-line comment in
  `tools/retrieval_events.py` noting the dependency.
- `cache_status` and `cache_level` values must always trace back to `retrieval_cache.py`'s
  literal constants by import, never by re-typing the string — this is asserted by a dedicated
  test (Step 6) specifically because a silent drift here (e.g. someone later renames
  `STALE_REJECTED`'s string value) would otherwise go undetected by any existing test.
- The `candidate_count` approximation in `wrap_hybrid_retrieval()` (Resolved Decision 7) is
  intentionally imprecise — do not let a future ticket "fix" this by modifying
  `hybrid_fuse_and_filter()`'s return shape without opening a new ticket; that's out of this
  ticket's scope and would touch a function `TCK-20260729-CONTEXT-PACKET-ASSEMBLY` has a
  documented hard dependency on (hybrid_retrieval.py:165-168's own comment).
- Every new test that exercises `emit_retrieval_event()` or any `wrap_*()` function MUST use
  `tmp_path`/`monkeypatch.chdir` — never let a test run against the real
  `agent-monitoring/events.jsonl` (test_plan.md's "No-real-run_id-pollution guard"). This is a
  correctness requirement for every new test in Steps 2-9, not just a suggestion.
- No Phase 3 module is wired into any workflow after this ticket — real retrieval-event volume in
  the live `agent-monitoring/events.jsonl` stays at zero after this ticket ships. This is expected
  (ticket's own Assumptions section) and must not be "fixed" by adding workflow wiring here.

## Deviations

- **Step 1's field count prose vs. the literal enumerated list**: Step 1 says
  "(17 total)" but its own enumeration is 15 retrieval-specific fields + 2 optional
  (`scenario`/`risk_tier`) + `retrieval_event_schema_version` itself = **18** distinct names.
  Implementation follows the literal enumerated field list (18 entries in
  `RETRIEVAL_EVENT_FIELDS`), not the "(17 total)" count, since the enumeration is the
  authoritative single source of truth and the count is prose commentary on it. No field from the
  enumerated list was dropped or added beyond what Step 1 names.
- Everything else (module layout, `emit_retrieval_event()`'s validation/write shape, the 3
  `RUN_ID_*`/`AGENT_*` wrapper pairs, `compute_retrieval_metrics()`'s home in `generate_retro.py`,
  the `INFRA-297` ledger entry) matches the plan's Steps 1-10 and Resolved Decisions 1-7 exactly —
  no other deviation.
