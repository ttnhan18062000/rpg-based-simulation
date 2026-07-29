---
status: historical
layer: observability
authority: P2
audience: agent
ticket_id: TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT
artifact_type: investigation
tags: [observability, agent-monitoring, schema]
---

# Investigation — TCK-20260729-RETRIEVAL-EVENT-SCHEMA-EMIT

## Current Behavior

### `tools/agent-monitoring/record_events.py` (the write path this ticket must reuse)

- `REQUIRED = {"run_id", "seq", "ts", "phase", "agent", "summary", "status"}` (record_events.py:14).
- `validate_record()` (record_events.py:20-32) treats a field as missing if the key is absent
  **or** its value is `None` — a caller cannot satisfy REQUIRED with an explicit `null`.
- `VALID_STATUS = {"ok", "failed", "blocked", "skipped"}` (record_events.py:15) — enforced inside
  `validate_record()`.
- `main()` (record_events.py:86-157) is a CLI (`--data <json>`) that: parses records → validates →
  runs `warn_vocabulary_drift()` (non-blocking, stderr only) → truncates `summary` to 200 chars →
  computes `tool_call_count`/`cost_proxy_score` for `implement-ticket`-prefixed run_ids only
  (`compute_tool_stats()`, record_events.py:35-68) → calls `write_lines(EVENTS_FILE, lines)`
  (record_events.py:145). **Any key not in REQUIRED and not `tool_call_count`/`cost_proxy_score`
  passes through untouched** — confirmed by `tests/tools/test_record_events.py::
  test_execution_identity_fields_pass_through_unchanged` (already-landed test exercising
  `execution_id`/`provider`/`ticket_id` pass-through). This is the load-bearing precedent that lets
  this ticket add ~15 new optional fields with zero change to `record_events.py` itself.
- `warn_vocabulary_drift()` (record_events.py:71-83) looks up `infer_workflow(run_id)`
  (vocabulary.py:73-94); if it returns `None` (unrecognized prefix) the check is **skipped
  silently** — documented, tested behavior (vocabulary.py's own docstring: "Returns None if run_id
  matches no known prefix ... callers must treat None as 'skip the check silently'").

### `tools/agent-monitoring/writer.py` (the shared append primitive)

- `write_line(target_path, line)` / `write_lines(target_path, lines)` (writer.py:107-162): lock via
  `os.O_CREAT|os.O_EXCL` (Candidate 1 from `docs/ai/monitoring_writer_decision.md` §3), append-only
  (`open(target_path, "a")`), never raise — return `bool`, diagnostics go to
  `.writer_health.jsonl`. `write_lines` holds one lock for the whole batch (contiguous-block
  guarantee for `record_events.py`'s batch writes).
- Confirmed single-writer discipline by `tests/tools/test_monitoring_writer_single_source.py`:
  hardcodes exactly 3 call sites (`post_tool_hook.py`, `record_run.py`, `record_events.py`) that
  must import `write_line`/`write_lines` from `writer.py` and must not import `fcntl` or use
  `O_EXCL` themselves. **This test's `_CALL_SITES` list is not auto-discovered — it is a fixed
  literal list.** A new wrapper module this ticket adds is NOT covered by this existing test and
  will need its own analogous guard test (per AC4), not a modification of this file's hardcoded list.

### `tools/agent-monitoring/vocabulary.py` (phase/agent enforcement)

- `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` are keyed by workflow name (`implement-ticket`,
  `create-tickets`, `implement-epic`, `simq-audit`) — all four built by grepping
  `.claude/workflows/*.js`'s real `phase(...)`/`pushEvent(...)` call sites (vocabulary.py:9-13).
  None of the four represents "a standalone script invocation outside any workflow."
- `infer_workflow()` (vocabulary.py:73-94) matches on 4 disjoint run_id prefixes: `SIMQ-AUDIT-`,
  `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`, `TCK-`. Any other prefix returns `None`.
- `is_known_agent()` (vocabulary.py:66-70) checks literal membership or a registered prefix family
  (`WORKFLOW_AGENT_PREFIXES`, e.g. `create-tickets: ("investigate:",)`).

### `docs/agent-monitoring/schema.md` (authoritative shape doc)

- events.jsonl's 7-field example record + `tool_call_count`/`reason_code`/`cost_proxy_score` as the
  only currently-documented optional fields (schema.md:120-145). No `execution_id`/`provider` field
  exists in `runs.jsonl`/`events.jsonl` today (confirmed independently by
  `ticket_plan_structure_phase4.md`'s own grep: "verified: neither string appears in either file").
- **"Manual/ad hoc run_id convention" subsection (schema.md:374-376) — directly on point for this
  ticket's open question:** *"If hand-writing monitoring records outside the JS workflows (e.g. an
  `audit-maintenance`-style direct invocation), always reuse the exact ticket ID as `run_id`
  verbatim — never invent a suffix or a synthesized `run-{code}-{timestamp}` ID; doing so breaks
  the events/run-record join for that record permanently."*
- No event-family discriminator field exists anywhere in `events.jsonl` today — every record is
  implicitly "a workflow-phase event." This ticket's own `retrieval_schema_version` field is the
  first structural family marker (confirms Assumption #2 in the ticket body).

### `docs/observability/retrieval_retention_redaction_policy.md` (MAY/PROHIBITED list, already-resolved decision doc)

- MAY: content hashes, source/entity/ticket/run IDs, counts, reason codes, scores, latency,
  corpus/graph generation + retrieval version numbers, cache level/status.
- PROHIBITED: raw prompt text, raw retrieved chunk/source text, full unredacted tool payloads, any
  field reproducing source content rather than referencing it by hash/ID.
- Decision B: retrieval **events** (unlike caches) inherit `agent-monitoring/*.jsonl`'s
  retain-forever/append-only convention — no duration-based retention for events, ever. This is
  already resolved and out of this ticket's remit to re-litigate.
- Doc explicitly states (line 14): *"No changes land in ... any `tools/agent-monitoring/*.py`
  writer as part of this doc"* — i.e. this doc set the MAY/PROHIBITED contract but never wired
  anything; this ticket is the first to actually write a conforming record.

### `docs/ai/monitoring_writer_decision.md` §2 (execution identity — confirms Out of Scope)

- `execution_id`/`ticket_id`/`provider` are a **proposed future schema** (synthetic illustration
  only, §2, lines 132-142) — "No field is added to any real record as part of this document
  landing." Confirms this ticket's Out-of-Scope bullet ("No execution_id or provider fields...")
  is consistent with upstream decisions, not a new restriction invented here.
- Also states the `run-{code}-{unix_ts}` / `-REDESIGN` suffix conventions are pre-refactor
  artifacts, "not reproducible by current `.claude/workflows/*.js` code" — reinforcing schema.md's
  "reuse the ticket ID verbatim" rule as the only sanctioned hand-write convention today.

### `tools/agent-monitoring/post_tool_hook.py` (precedent for "no active workflow" handling — investigated per the CRITICAL OPEN QUESTION)

- Lines 45-63: reads `.claude/current_run`; on any failure (file absent, e.g. no workflow active
  during a bare `pytest` run) the `try/except Exception: pass` silently leaves `run_id = None`,
  `seq = None`, `phase = None`, `agent = None`, and the record is still written to `tools.jsonl`
  with those nulls (line 73-91).
- **This precedent does NOT transfer directly to `events.jsonl`.** `tools.jsonl`'s schema
  documents `run_id`/`seq`/`phase`/`agent` as **Nullable: Yes** (schema.md:271-275) specifically
  because "the tool call occurred outside an active workflow run." `events.jsonl`'s REQUIRED set
  (record_events.py:14) has no such allowance — `validate_record()` rejects a `None` in any of
  those 4 fields identically to a missing key. Null-passthrough is therefore not an option for a
  retrieval event; the wrapper must always supply real (non-null) string/int values for all 4 base
  fields, even for a standalone invocation.

### The 3 Phase 3 modules to instrument

- **`tools/hybrid_retrieval.py`**: `hybrid_fuse_and_filter()` (hybrid_retrieval.py:224-331) is the
  one natural wrapper point — orchestrates dense+lexical retrieval, filter, and RRF fusion, and
  returns `list[HybridResult]` (candidate_count = `len(row_by_id)` pre-fusion is not directly
  exposed; `len(results)` after truncation to `top_k` is the natural `selected_count`). No
  `retrieval_version`/`corpus_generation` concept exists in this module — those live in
  `tools/retrieval_cache.py` (see below). `authority`/`freshness` per-result values are on each
  `HybridResult` (lines 180-181), giving a direct source for `authority_counts`/`freshness_counts`.
  No latency measurement exists inside the module itself — a wrapper must time the call itself.
- **`tools/retrieval_cache.py`**: already owns `RETRIEVAL_VERSION = 1` (line 45) and
  `_corpus_generation()` (lines 183-191, reads `knowledge-index/manifest.json`'s `built_at`, falls
  back to `"no_manifest"` sentinel — never fabricates a timestamp). `check_query_cache()`/
  `check_index_cache()`/`check_packet_cache()` each return a dataclass with `.status` (`hit`/
  `miss`/`stale-rejected`, module constants `HIT`/`MISS`/`STALE_REJECTED`, lines 60-62) and
  `.reason_code` — directly maps onto the ticket's `cache_level`/`cache_status` fields (3 levels =
  3 distinct wrapper call sites or one dispatch-by-level wrapper).
- **`tools/context_packet_assembler.py`**: `assemble_context_packet()` (lines 266-291) returns a
  `ContextPacket` with `included`/`excluded_summary` — `len(included)` is `selected_count`,
  `excluded_summary`'s per-`(kind, reason)` counts map onto `exclusion_reason_counts`,
  `[c["hash"] for c in included]` maps onto `cited_source_hashes`. No `adequacy_verdict` concept
  exists anywhere in this module or its contract doc — this is a genuinely new judgment the wrapper
  must compute or the caller must supply (flagged as an open question below).

### `tools/agent-monitoring/generate_retro.py` / `query.py` (the "proof-of-queryability" target)

- Both files load `runs.jsonl`/`events.jsonl` via `load_jsonl()` (generate_retro.py:47-49) or the
  derived SQLite index (`query.py:29-52`, `agent-monitoring-index/monitoring.db`, built by
  `build_index.py`). Neither file today has any retrieval-specific field awareness — a new query
  function reading `cache_status`/`candidate_count`/`selected_count`/`cited_source_hashes` directly
  off the raw `events.jsonl` dicts (not the SQLite index, which has no schema awareness of the new
  optional columns beyond storing `raw_json` verbatim — confirmed by schema.md:17-24, the index
  stores `raw_json` per row so new optional fields are queryable via `json_extract` or Python-side
  `json.loads` without any index-schema migration) is the natural, minimal-footprint addition.

## Mechanics / Engine Constraints

Not applicable — `docs/mechanics/` and `docs/engine/` govern simulation laws (combat, economy,
strategic cognition, world evolution); this ticket touches only `tools/agent-monitoring/` and
`tools/{hybrid_retrieval,retrieval_cache,context_packet_assembler}.py`, none of which are part of
the simulation kernel or authoritative mutation pipeline. Confirmed by INFRA-293 through INFRA-296's
own `support_boundary` field: *"Agent-orchestration/retrieval tooling only — no simulation
behavior, Mechanics Bible chapter, or engine contract governs this module's semantics."* This
ticket inherits that same support boundary.

The one quasi-engine-contract dependency is `docs/engine/contracts/context_packet_contract.md`
(cited in Related Docs) — but only as the schema `context_packet_assembler.py` already implements;
this ticket does not modify that contract or its field list.

## Parity Ledger Overlap

`docs/parity_ledger/infrastructure.yaml`, all `status: verified`, `priority: P2`:

- **INFRA-293** — `tools/code_test_index.py` (TCK-20260729-DETERMINISTIC-CODE-INDEX). Listed in
  this ticket's Related Code Areas but **not** in the Scope's instrumentation bullet (only
  `hybrid_retrieval.py`/`retrieval_cache.py`/`context_packet_assembler.py` are named for
  instrumentation) — treat as reference-only, not an instrumentation target, unless Plan decides
  otherwise.
- **INFRA-294** — `tools/hybrid_retrieval.py` (TCK-20260729-HYBRID-RETRIEVAL-FUSION). Instrumented
  by this ticket. `test_path: tests/tools/test_hybrid_retrieval.py` exists and passes.
- **INFRA-295** — `tools/retrieval_cache.py` (TCK-20260729-RETRIEVAL-CACHE-LEVELS). Instrumented by
  this ticket. `test_path: tests/tools/test_retrieval_cache.py` exists and passes.
- **INFRA-296** — `tools/context_packet_assembler.py` (TCK-20260729-CONTEXT-PACKET-ASSEMBLY).
  Instrumented by this ticket. `test_path: tests/tools/test_context_packet_assembler.py` exists and
  passes.

No P0 entries in this overlap set — all four are P2, so no pre-existing hard test-pass gate beyond
the repo's general regression discipline. **This ticket should add a new INFRA-29x entry** (next
free ID after INFRA-296) for the new instrumented-wrapper + schema-extension work itself, `status:
verified`, `priority: P2` (matches the established pattern for this whole batch of
agent-tooling-infrastructure tickets — INFRA-281 through INFRA-296), `test_path` pointing at
whichever new test file houses AC4/AC5's wrapper-emission tests.

No entry in `docs/parity_ledger/infrastructure.yaml` currently references `events.jsonl`'s schema
itself (as opposed to the modules that will emit into it) — this ticket is the first to extend the
events.jsonl shape, so the new ledger entry's `text` should say so explicitly rather than implying
prior ledger coverage of the schema extension.

## Prior Work

- **TCK-20260729-HYBRID-RETRIEVAL-FUSION**, **TCK-20260729-RETRIEVAL-CACHE-LEVELS**,
  **TCK-20260729-CONTEXT-PACKET-ASSEMBLY** (all `stored_artifacts/`) — each explicitly deferred
  event emission to "Phase 4" in their own plan.md's Out-of-Scope/Do-NOT-touch sections (grepped:
  all three contain the literal line *"Any new `agent-monitoring/*.jsonl` event type (Phase 4)."*).
  This ticket is that deferred Phase 4 work — confirms scope boundary is intentional, not a gap.
- **`docs/plans/agent_infrastructure/context_efficient_agent_retrieval/
  ticket_plan_structure_phase4.md`** — the batch-scoping doc that produced this ticket. Resolves
  several things already so Plan should not re-derive them: (a) events stay `run_id`-scoped only,
  no `execution_id`/`provider` (RESOLVED, lines 60-70); (b) MAY/PROHIBITED fields are Phase 2's
  already-closed decision, not re-litigated here; (c) "Nothing built in this phase may be wired
  into any `.claude/workflows/*.js` file" — restated identically in this ticket's Out of Scope.
- **`docs/ai/monitoring_writer_decision.md`** — Candidate 1 (lock-file protocol via
  `writer.py`) is the already-evidenced, already-decided writer mechanism; explicitly forbids a new
  lock/queue/journal design, matching this ticket's Out of Scope.
- **TCK-20260721-MONITORING-WRITER-UNIFICATION** — landed the 3-call-site `writer.py` migration and
  its guard test (`test_monitoring_writer_single_source.py`), the direct template for AC4's
  "mirroring test_monitoring_writer_single_source.py's assertions" requirement.
- **TCK-20260708-AGENT-MONITORING-SCHEMA-ENFORCEMENT** — original `record_events.py` REQUIRED-set
  enforcement + warn-only vocabulary check, the mechanism this ticket must not weaken (AC2).
- No prior ticket has added a non-workflow, standalone-invocation event source to
  `events.jsonl` — this is a first for the schema, not a pattern-repeat.

## Risks and Open Questions

### CRITICAL — resolved by evidence, concrete recommendation below

**Question:** How should `run_id`/`seq`/`phase`/`agent` be populated for a retrieval event fired
from a standalone test/manual invocation of a Phase 3 module, with no `.claude/current_run`
workflow sidecar and no real workflow run to join to?

**Evidence gathered:**
1. `.claude/current_run`'s sidecar, when no workflow is active, simply does not exist (or is
   stale/absent) — `post_tool_hook.py`'s `except Exception: pass` (lines 53-63) is the only
   precedent, and it degrades to **nulling** `run_id`/`seq`/`phase`/`agent`. This precedent is
   schema-incompatible with `events.jsonl` (nullable in `tools.jsonl`, non-nullable in
   `events.jsonl`) and cannot be reused as-is.
2. No standalone tool in this repo writes to `runs.jsonl`/`events.jsonl` outside the JS-workflow
   flow today (`record_run.py` always takes an explicit `--run-id`-bearing `--data` payload;
   nothing self-generates one). The closest precedent is `docs/agent-monitoring/schema.md`'s
   documented "Manual/ad hoc run_id convention": *"always reuse the exact ticket ID as `run_id`
   verbatim — never invent a suffix or a synthesized `run-{code}-{timestamp}` ID."*
3. **Recommendation:** do NOT reuse *this* ticket's own ticket ID (or any real ticket ID) as the
   `run_id` for standalone retrieval-event test/demo invocations. Reusing a real `TCK-...` ID would
   make `infer_workflow()` classify it as `implement-ticket` and would interleave synthetic
   test-invocation events into that ticket's *real* Scope/Investigate/Plan/.../Finalize event
   stream in `events.jsonl` under the same `run_id` — exactly the kind of silent conflation
   schema.md's join-integrity concern is trying to prevent, just from the opposite direction (this
   isn't "inventing a suffix that breaks the join," it's "reusing a real join key for
   non-workflow data," which pollutes a real run's event history). Instead: mint a **new, explicit,
   self-describing `run_id` prefix reserved for standalone Phase 3 instrumentation** (e.g.
   `RETRIEVAL-EVENT-<slug>`), distinct from all 4 of `infer_workflow()`'s recognized prefixes
   (`SIMQ-AUDIT-`, `EPIC-`/`FOLDER-`, `CREATE-TICKETS-`, `TCK-`). This is directly sanctioned by
   `vocabulary.py`'s own documented contract: `infer_workflow()` returning `None` for "a future 5th
   workflow" is explicitly designed to "skip the check silently" (vocabulary.py:83-84,94), and
   `warn_vocabulary_drift()` is a no-op whenever `infer_workflow()` returns `None`
   (record_events.py:77-79). A brand-new, clearly-labeled prefix therefore (a) satisfies
   "never invent a `run-{code}-{timestamp}`-style ID" (this isn't that shape — it's a stable,
   documented, human-readable literal, not a synthesized timestamp hash), (b) never aliases onto
   or corrupts a real ticket's event stream, and (c) produces zero vocabulary-warning noise by the
   existing, tested fallthrough path rather than requiring any `vocabulary.py` edit. `seq` should
   be a small caller-supplied literal integer (starting at 1, incrementing per call within one
   demo/test run) — never computed from a timestamp or hash, mirroring `record_events.py`'s own
   contract of never inventing `seq` itself. `phase`/`agent` should be new, self-describing literal
   values (e.g. `phase="Retrieval"`, `agent="hybrid-retrieval-wrapper"` /
   `"retrieval-cache-wrapper"` / `"context-packet-wrapper"`) — since the new run_id prefix makes
   `infer_workflow()` return `None`, these never trigger a vocabulary warning and do **not** need
   to be added to `vocabulary.py`'s `WORKFLOW_PHASES`/`WORKFLOW_AGENTS` (which are correctly scoped
   to the 4 *real* workflows only; these standalone events are not phases of any of those 4).
   **This is a recommendation for Plan to adopt or explicitly override, not a silent assumption —
   flag it as a Plan-phase decision point.**

### Other open questions (non-blocking, but Plan should decide explicitly)

- **`adequacy_verdict`**: no such concept exists in any of the 3 Phase 3 modules or their contract
  docs. The wrapper (or its caller) must define what produces this value — e.g. a simple threshold
  on `selected_count`/`candidate_count` ratio, or a caller-supplied literal for test/demo purposes.
  Flag as genuinely new logic, not a pass-through of an existing field.
- **`latency_ms`**: none of the 3 modules self-report latency. The wrapper must time the call
  itself (`time.perf_counter()` around the wrapped function), not source it from inside the module.
- **Where the wrapper functions live**: the ticket allows either "call sites inside Phase 3's own
  test/manual-invocation paths" OR "new instrumented wrapper functions." A new module (e.g.
  `tools/retrieval_event_emitter.py`) that wraps all 3 Phase 3 modules is more testable and
  matches AC4's "new call-site/wrapper module(s)" language (plural, suggesting Plan may choose one
  shared wrapper module) — but Plan must decide the concrete file layout; this investigation does
  not prescribe it.
- **Emission path**: AC1 requires the record land "via record_events.py's validate_record()/
  write_lines() path" specifically (not just any `writer.write_line` call) — this means the wrapper
  should either import and call `record_events.validate_record()` + `record_events.write_lines()`
  (or `record_events`'s own `main()` via subprocess with `--data`) rather than bypassing validation
  entirely by calling `writer.write_line()` directly. AC4 says "via writer.py's write_line/
  write_lines" — both ACs are satisfiable simultaneously since `record_events.py` itself is the
  thing that calls `write_lines()`; Plan should make explicit which of the two integration shapes
  (direct `record_events` function import vs. subprocess CLI invocation) the wrapper uses.
- **`retrieval_schema_version` constant**: no existing precedent for a schema-version field
  anywhere in `agent-monitoring/*.jsonl` (confirmed — grep of `docs/agent-monitoring/schema.md`
  finds no version field). `tools/retrieval_cache.py::RETRIEVAL_VERSION = 1` is the module-owned
  cache-key version, a **different** concept (bumped on cache key/invalidation logic changes) from
  a hypothetical `retrieval_schema_version` (which should version the *event field shape itself*).
  Plan should define this as a new, independent integer constant, not conflate it with
  `RETRIEVAL_VERSION`.

## Anti-Drift Hazards

- **Do not modify `record_events.py`'s REQUIRED set or `VALID_STATUS`.** Ticket's own Out of Scope
  and AC2 both forbid this; the pass-through-unchanged behavior for extra fields is the entire
  mechanism this ticket relies on, and it already works without any code change there.
- **Do not touch `tests/tools/test_monitoring_writer_single_source.py`'s existing `_CALL_SITES`
  list.** It is intentionally scoped to exactly 3 files (`post_tool_hook.py`, `record_run.py`,
  `record_events.py`). A new wrapper module needs its **own**, separate guard test — adding the
  wrapper to this file's list would silently redefine what "the 3 call sites" means for an
  unrelated, already-shipped architecture guard.
- **Do not wire anything into `.claude/workflows/*.js`.** Both this ticket's Out of Scope and the
  batch-scoping doc (`ticket_plan_structure_phase4.md`) repeat this explicitly; AC5 requires a
  structural grep-based test proving zero references to any workflow file from the new module(s).
- **Do not add `execution_id`/`provider`/`ticket_id` fields to the new retrieval-event shape.**
  Confirmed as still out of scope by both this ticket and `docs/ai/monitoring_writer_decision.md`
  §2 (proposal-only, no real record uses it yet) — conflating this ticket's genuinely-new
  `retrieval_schema_version` family marker with that unrelated, still-hypothetical
  execution-identity proposal would be scope creep.
- **Do not let the new optional fields leak raw text.** `cited_source_hashes` must stay hashes
  (mirrors `context_packet_assembler.py`'s `Candidate.hash`/`ContextPacket.included[].hash`, never
  the underlying `text`) — a structural test (grep for suspicious field names, or an assertion that
  no new field's value length/shape resembles raw prose) is worth adding alongside AC3's
  no-execution_id/no-provider/no-raw-text structural test.
- **Do not compute `cache_status` independently of `retrieval_cache.py`'s own `HIT`/`MISS`/
  `STALE_REJECTED` constants** (retrieval_cache.py:60-62) — reuse those literal string values
  (`"hit"`/`"miss"`/`"stale-rejected"`) verbatim rather than re-deriving a parallel enum, to avoid a
  silent vocabulary mismatch between the cache module and the new event schema.
- **Do not let the new `generate_retro.py`/`query.py` function assume the SQLite index has been
  rebuilt with awareness of the new fields.** The index stores `raw_json` verbatim per row
  (schema.md:17-24) — the new fields are already queryable via `json.loads(raw_json)` or
  `json_extract` without any `build_index.py` schema migration; do not add unnecessary index-schema
  changes as part of proving queryability.
