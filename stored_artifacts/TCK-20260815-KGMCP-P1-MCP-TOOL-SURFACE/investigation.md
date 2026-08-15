---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE
artifact_type: investigation
tags: [ai, mcp]
---

# Investigation — TCK-20260815-KGMCP-P1-MCP-TOOL-SURFACE

## Current Behavior

### `tools/knowledge_gateway_router.py` (DONE, frozen — INFRA-335)
Pure decision logic, no MCP/packet/cache code. Entry points:
- `route(query_text: str, requested_guarantee: Optional[str] = None) -> RoutingDecision` (`:392-433`) —
  top-level dispatcher: `_match_identifier()` first (ticket_id → parity_id → source_path →
  registered_doc_path → subsystem_id → symbol_name, `:364-389`), then `_classify_routing_shape()`
  keyword heuristic (`:350-358`), else `route_ambiguous()`.
- `route_ambiguous(query_text: str) -> RoutingDecision` (`:281-304`) — sequentially queries the
  bounded `{context_search, graphify}` set.
- `RoutingDecision` (`:315-323`, frozen dataclass): `providers_selected: list[str]`,
  `matched_identifier: Optional[IdentifierMatch]`, `routing_shape: Optional[str]`, `rationale: str`,
  `capability_constraints: list[CapabilityConstraint] = []`, `not_yet_routed: Optional[str] = None`,
  `providers_consulted: list[str] = []`.
- `match_symbol_name()` (`:98-118`) shells out to the real `graphify query` CLI (`subprocess.run`,
  `timeout=120`).

### `tools/knowledge_gateway_packet_assembly.py` (DONE, frozen — INFRA-336)
Top-level orchestrator: `assemble_packet(routing_decision, query_text: str, budget_requested: int) ->
PacketAssembly` (`:578-658`). Fixed order: `call_providers_for_routing_decision()` → `render_candidates()`
→ `deduplicate_statements()` → conditional `build_negative_claim_support()` → `build_conflicts()` →
`assemble_within_budget()` → conditional §16 budget-failure fallback.

`call_providers_for_routing_decision()` (`:159-194`) is the actual provider-calling layer: for
`"context_search"` it lazy-loads `tools/search_mcp.py` via `importlib.util` and calls
**`_sm._run_search(query_text)`** directly (`:172-173`); for `"graphify"` it lazy-loads
`tools/knowledge_gateway_router.py` and calls **`_kgr.match_symbol_name(query_text)`** directly
(`:179-181`). Neither call goes through `tools/hybrid_retrieval.py` or
`tools/context_packet_assembler.py` directly — those are two levels removed (see below).

`PacketAssembly` (`:551-566`, frozen dataclass) fields: `status`, `freshness`, `verification`,
`provenance_providers`, `providers_consulted_this_call`, `answer`, `statements`, `context`,
`evidence`, `conflicts`, `budget_requested`, `budget_returned`, `negative_claim_support`. This maps
1:1 onto `knowledge_context_response.schema.json`'s properties (see below) except `mode`
(request-echo, not produced by the assembler) and `cache`/`cache_key_version` (Phase 2 cache fields,
absent from `PacketAssembly` — correctly, since no cache exists yet).

### `tools/search_mcp.py` (DONE, frozen, must remain untouched — pattern to mirror)
264 lines. Structure this ticket's new server must reproduce:
- Sibling-module loading via `importlib.util.spec_from_file_location()` (`:31-45`), never a real
  package import — same convention `knowledge_gateway_router.py` and
  `knowledge_gateway_packet_assembly.py` already use.
- `_ensure_loaded()` (`:64-77`) lazy-loads the sentence-transformers model + BM25 index on first
  call, sets `_STATE.ready`.
- `_run_search(query, top_k=8, section=None, mode="hybrid") -> list[dict] | dict` (`:82-144`) is the
  core logic function, shared by the MCP tool and `--test` mode. **Line 106: it calls
  `_hr.hybrid_fuse_and_filter(conn=..., query_vec_bytes=..., query_tokens=..., bm25_obj=...,
  bm25_doc_ids=..., top_k=...)` directly, unwrapped** — this is the one and only real call site of
  `hybrid_fuse_and_filter()` in the whole context-search path today. Returns `{"error": ...}` dict on
  missing index.
- `_run_health() -> dict` (`:147-165`) — index status (`status`, `index_version`, `chunks`, `model`,
  or `{"status": "unavailable", "error": ..., "action": ...}`).
- `_run_mcp_server() -> int` (`:210-256`): imports `from mcp.server.fastmcp import FastMCP` inside a
  try/except (prints an install hint and returns 1 if `mcp` isn't installed); `server =
  FastMCP("knowledge-search")`; tools registered via `@server.tool()` decorator on thin wrapper
  functions that just call `_run_search`/`_run_health`; `server.run()` at the end (blocks, stdio
  transport).
- Entry point (`:261-264`): `--test` flag reads one JSON object from stdin and prints results
  (`_run_test_mode()`); otherwise runs the real MCP server.

### `.mcp.json` (real current shape — differs from what `tests/tools/test_search_mcp.py` expects)
```json
"knowledge-search": {
  "command": "bash",
  "args": ["tools/start_search_mcp.sh"],
  "env": {},
  "description": "Local semantic search over project docs, tickets, and investigations"
}
```
`tools/start_search_mcp.sh` is a portable venv-locator wrapper that ultimately execs
`python3 tools/search_mcp.py "$@"`. **This is the shape this ticket must mirror** — command=`bash`,
args=`["tools/<new-launcher>.sh"]` (or, if the Plan phase decides a launcher script is unwarranted for
a second server, a `python3`/direct-args form consistent with this file's actual current entry, not
with the stale test file below).

**Pre-existing test/reality mismatch (not this ticket's fault, not this ticket's job to fix):**
`tests/tools/test_search_mcp.py::TestMcpJson::test_command_is_python3` and
`::test_args_point_to_search_mcp` (`:55-64`) assert `entry["command"] == "python3"` and
`entry["args"][0].endswith("search_mcp.py")` — **both currently fail** against the real `.mcp.json`
(verified live: `2 failed, 2 passed` in `TestMcpJson`). The real entry uses the `bash`
`start_search_mcp.sh` wrapper, added after that test was written. This ticket's own new
`.mcp.json`-entry test must assert against the *real* shape (bash+wrapper-script, or whatever the new
entry's Plan-phase design settles on), not the stale test file's outdated expectation — and must not
"fix" the pre-existing `test_search_mcp.py` failures as a side effect (out of this ticket's scope; that
file's own tests are the KGMCP-TOOL-SURFACE ticket's regression surface only insofar as
`git diff --stat` must stay empty for `tools/search_mcp.py` itself, not for the pre-existing failing
test file).

### `tools/retrieval_events.py` — the 3 Wrapper functions
- `wrap_hybrid_retrieval(*, seq, summary, run_id=..., status="ok", events_file=None, ts=None,
  expansion_reason=None, expansion_count=None, **hybrid_kwargs)` (`:154-212`) — imports
  `hybrid_fuse_and_filter`/`candidate_k` from `tools/hybrid_retrieval.py` **fresh inside the
  function** and calls `hybrid_fuse_and_filter(**hybrid_kwargs)` directly. Requires the caller to
  already have `conn`, `query_vec_bytes`, `query_tokens`, `bm25_obj`, `bm25_doc_ids`, `top_k` —
  exactly the local state `search_mcp.py::_run_search()` builds for itself (SQLite connection with
  `sqlite_vec` loaded, real embedding vector, tokenized query, loaded BM25 object) and never exposes
  to any caller.
- `wrap_retrieval_cache_check(cache_level, *, seq, summary, ..., **check_kwargs)` (`:223-288`) —
  dispatches to `check_index_cache`/`check_query_cache`/`check_packet_cache` from
  `tools/retrieval_cache.py` by `cache_level`.
- `wrap_context_packet_assembly(*, seq, summary, ..., **assemble_kwargs)` (`:299-358`) — imports
  `assemble_context_packet` from **`tools/context_packet_assembler.py`** (not this epic's
  `knowledge_gateway_packet_assembly.py`) and calls it with `**assemble_kwargs`.
- All three require a caller-supplied `seq: int` (no default) — `emit_retrieval_event()`'s only
  required field with no module-level default — meaning any live call site must maintain its own
  monotonic counter across calls within one long-running FastMCP server process; `record_events.
  validate_record()` (`tools/agent-monitoring/record_events.py:20`) only checks field presence, not
  global `(run_id, seq)` uniqueness, so this is a caller-discipline concern, not a hard validation
  blocker.

### Contract schemas (Phase 0, frozen — `docs/engine/contracts/knowledge_gateway_mcp/`)
- `knowledge_context_request.schema.json`: draft-07, `additionalProperties: false`,
  `required: ["query"]`. Fields: `query` (string), `mode` (enum `answer`/`task_context`),
  `budget_tokens` (integer), `changed_paths` (array of string), `include_history` (boolean),
  `evidence_detail` (open string, no enum).
- `knowledge_context_response.schema.json`: draft-07, deliberately **not** `additionalProperties:
  false` at the top level (Design Decision D4 — the ERROR/PARTIAL shape is underspecified).
  `required`: `status`, `freshness`, `verification`, `provenance_providers`,
  `providers_consulted_this_call`. `status`/`freshness`/`verification` each `$ref` a distinct enum in
  `shared_enums.schema.json` (relative-file `$ref`, resolves correctly via
  `jsonschema.RefResolver(base_uri=<contracts-dir>.as_uri())`, verified live). `conflicts[]` items
  require `subject`/`claims`/`automatic_resolution`/`recommended_action`; `claims[]` items require
  `value`/`source_id`/`authority`/`valid_from`/`valid_to`. `allOf` conditional: `status == "ERROR"`
  requires an `error` object with `code`/`message`.
- `knowledge_status_response.schema.json`: draft-07, `additionalProperties: false`,
  `required: ["gateway_version", "reported_schema_version"]`. Full property list: `gateway_version`,
  `reported_schema_version`, `providers[]` (`provider_id`/`available`/`generation`),
  `cache_entry_counts[]` (`kind`/`freshness`/`count`), `cache_hit_rate`, `cache_miss_rate`,
  `cache_stale_rejection_rate`, `latency_summary_ms` (object: `lookup`, `evidence_validation`,
  `provider_fallback`, `packet_assembly`, `end_to_end` — all `type: number`, no null variant),
  `provider_fallback_rate`, `recent_invalidation_reasons[]`, `branch_scope`
  (`branch`/`working_tree_dirty`), `cache_rebuildable`.

### Provider capability descriptors (frozen)
- `provider_capabilities_context_search.json`: `adapter_version: null` (real, not a placeholder —
  `tests/tools/test_knowledge_gateway_contract_schemas.py:237-252` asserts this explicitly against
  `_run_health()`'s real shape).
- `provider_capabilities_graphify.json`: `adapter_version: "graphify-cli-0.8.39"`.

### `jsonschema` library availability
`jsonschema` 4.26.0 and `referencing` are both importable in `.venv` but **neither is declared** in
`pyproject.toml` (no `[project.dependencies]` or `[project.optional-dependencies]` entry). This
ticket's own acceptance criteria explicitly require "a real JSON Schema validator, not hand-written
assertions" — this is a deliberate departure from `tests/tools/test_knowledge_gateway_contract_schemas.py`'s
own precedent (that file's docstring: "no `jsonschema` library dependency... mirrors
`tools/parity_ledger_writer.py::validate_entry()`'s hand-rolled validation precedent"). Verified live
that `jsonschema.Draft7Validator` + `jsonschema.RefResolver(base_uri=..., referrer=...)` correctly
resolves the response schema's relative `$ref`s into `shared_enums.schema.json` (`RefResolver` is
deprecated as of jsonschema 4.18 in favor of the `referencing` library, but still functional and is
the only path tested here). Plan phase must decide: (a) declare `jsonschema` as a real dependency
(new `pyproject.toml` group, e.g. `[project.optional-dependencies.knowledge-gateway-mcp]` alongside
`search-mcp`), and (b) use the deprecated `RefResolver` API (simplest, works today) vs. the newer
`referencing`-library-based resolution (more future-proof, more code).

## Mechanics / Engine Constraints

This is agent-orchestration/knowledge-retrieval tooling, not simulation logic — none of
`docs/mechanics/`'s chapters constrain it. The governing laws live in
`docs/plans/knowledge-gateway-mcp-proposal.md` and `docs/engine/contracts/knowledge_gateway_mcp/`:

- **§9.1** (`knowledge_context`): request accepts only need-oriented hints
  (`query`/`mode`/`budget_tokens`/`changed_paths`/`include_history`/`evidence_detail`); must never
  expose provider weights, cache-level selection, semantic thresholds, provider forcing, or
  ranking-policy switches — enforced today by the request schema's `additionalProperties: false`.
  Every `answer` sentence must trace to a `statements[]` entry with real `evidence_ids`
  (already guaranteed upstream by `assemble_packet()`, per
  `test_every_answer_sentence_traces_to_a_real_statement_evidence_id` in the packet-assembly test
  suite) — this ticket must not alter or re-derive `answer`, only pass `PacketAssembly.answer`
  through.
- **§9.2** (`knowledge_status`): "should not expose provider weights, semantic thresholds, internal
  cache-level controls, or provider-selection switches" — enforced by the response schema's
  `additionalProperties: false`.
- **§9.3**: `knowledge_learn`/`knowledge_promote`/`knowledge_verify`/any invalidation tool must not be
  registered.
- **§2.1** (Ambient Utility Positioning): the new server must be ambiently available with no
  ticket/workflow metadata required — matches `.mcp.json`'s registration mechanism exactly (no
  special env vars needed beyond what `knowledge-search`'s entry already demonstrates).
- **§16** ("preserve direct provider tools and fail-open behavior"): `tools/search_mcp.py` and the
  `graphify` CLI must remain directly usable and untouched by this ticket.
- **`measurement_baseline_contract.md` §2** (P1 authority, Phase 0-frozen): defines the 5 latency
  measurement points' exact meaning/attachment-point/live-precedent status — this is the single most
  load-bearing doc for AC #4 (wrapper wiring), see Risks below.

## Docs Requiring Update

- `docs/parity_ledger/infrastructure.yaml`: add a new `INFRA-33x` entry (next after INFRA-336)
  documenting the real `knowledge_context`/`knowledge_status` FastMCP tools, the `.mcp.json`
  registration, and whichever subset of the 3 `retrieval_events.py` Wrapper functions end up
  genuinely wired — following the INFRA-334/335/336 KGMCP-infrastructure ledgering precedent
  exactly (same shard, same `support_boundary` framing: agent-orchestration tooling, no `src/`
  touched).
- `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md`: §2.3
  (Provider-fallback latency) and §2.4 (Packet-assembly latency) both currently say "no existing
  wrapper" / "implemented but not invoked by any live call site" — once this ticket wires a real call
  site (whichever one Plan phase settles on), those two subsections' "Live-precedent status"
  paragraphs become stale and must be updated to record the real invocation site and whether a live
  number now exists, per §2.6's own rule that a fixture/pre-gateway number must never be presented as
  if it were the real gateway's number.
- `docs/plans/knowledge-gateway-mcp-proposal.md` §20 Phase 1 checklist: if the proposal enumerates
  concrete per-ticket deliverables for Phase 1 (needs Plan-phase confirmation of exact line numbers),
  the `knowledge_context`/`knowledge_status` tool-surface bullet should be checked off/annotated with
  this ticket's ID, matching the existing pattern for INFRA-334/335/336's source tickets.

## Parity Ledger Overlap

- **INFRA-334** (`infrastructure.yaml`, `verified`, P2) — Phase 0 measurement baseline. Its own
  `v2_evidence` explicitly notes `kgmcp_baseline_runner.py` "calls `_run_search()` directly, never
  through `wrap_hybrid_retrieval`/`wrap_retrieval_cache_check`" — direct precedent that even Phase
  0's own measurement tooling deliberately bypassed the wrappers, i.e. this is not a fresh problem
  this ticket introduces.
- **INFRA-335** (`infrastructure.yaml`, `verified`, P1) — the router this ticket imports read-only,
  never modifies. `test_path: tests/tools/test_knowledge_gateway_router.py`.
- **INFRA-336** (`infrastructure.yaml`, `verified`, P1) — the packet assembler this ticket imports
  read-only, never modifies. `test_path: tests/tools/test_knowledge_gateway_packet_assembly.py`.
- No P0 entries touched. This ticket will need a **new** entry (next `INFRA-33x`) once implemented —
  not Investigate's job to create, flagged here for Plan/Implement.

## Prior Work

- `stored_artifacts/TCK-20260612-LOCAL-CTX-MCP/investigation.md` — the original `search_mcp.py`
  FastMCP-pattern ticket; confirms `.claude/settings.json`/`.mcp.json` merge-not-overwrite convention
  this ticket must also follow (only one new key under `mcpServers`).
- `stored_artifacts/TCK-20260814-KGMCP-CONTRACT-SCHEMAS/investigation.md` and its ticket file —
  Phase 0 schema-freeze investigation; establishes the hand-rolled (no-`jsonschema`-library)
  validation precedent this ticket's own AC deliberately departs from.
- `tickets/done/TCK-20260814-KGMCP-MEASUREMENT-BASELINE.md` +
  `docs/engine/contracts/knowledge_gateway_mcp/measurement_baseline_contract.md` — names the 3
  Wrapper functions as "implemented but not invoked" and is the authoritative, Phase-0-frozen
  definition of what each of the 5 latency measurement points actually means and which (if any)
  existing wrapper is real precedent for it. This is the single most important prior-work artifact
  for this ticket's AC #4.
- `tests/tools/test_knowledge_gateway_router.py` and `test_knowledge_gateway_packet_assembly.py` —
  established test conventions for this epic: `importlib.util.spec_from_file_location()` module
  loading, `monkeypatch` for capability-descriptor/subprocess isolation, explicit
  "module introduces zero MCP server code" / "module does not modify or import X" anti-drift guard
  tests per sibling ticket — this ticket's own test suite should add the mirror-image guard
  ("this new module does not modify `search_mcp.py`/`knowledge_gateway_router.py`/
  `knowledge_gateway_packet_assembly.py`").

## Risks and Open Questions

### 1. (BLOCKING — do not assume an answer) None of the 3 Wrapper functions have a clean, literal call site in this ticket's real Phase-1 data flow.

Evidence, function by function:

- **`wrap_hybrid_retrieval()`** wraps `hybrid_fuse_and_filter()`, whose only real call site in this
  repository is inside the frozen `search_mcp.py::_run_search()` (`:106-113`), using local state
  (`conn`, `query_vec_bytes`, `query_tokens`, `bm25_obj`, `bm25_doc_ids`) that `_run_search()` builds
  for itself and does not expose to any caller. `knowledge_gateway_packet_assembly.py::
  call_providers_for_routing_decision()` calls `_sm._run_search(query_text)` as a black box — it has
  no access to the kwargs `wrap_hybrid_retrieval()` requires. Using it for real would mean
  reimplementing `_run_search()`'s model-load/DB-open/tokenize/embed setup a second time inside the
  new gateway module, purely to substitute a wrapped call for the one `_run_search()` already makes
  internally — real duplication of frozen logic, with a parity-drift risk if `_run_search()` changes
  later. **`measurement_baseline_contract.md` §2.3 (Provider-fallback latency) explicitly states "no
  existing wrapper; this concept has no timed call site anywhere in this repository today"** —
  i.e., the Phase-0-frozen contract doc itself does not treat `wrap_hybrid_retrieval()` as
  provider-fallback-latency precedent, contradicting a naive assumption that it is.
- **`wrap_retrieval_cache_check()`** requires a real cache (`tools/retrieval_cache.py`'s
  `check_index_cache`/`check_query_cache`/`check_packet_cache`). This ticket's own Out of Scope says
  "Any caching" is excluded. `measurement_baseline_contract.md` §2.1/§2.2 confirm lookup and
  evidence-validation latency are Phase-2-cache-dependent concepts. **Does not apply pre-Phase-2.**
- **`wrap_context_packet_assembly()`** imports and calls `context_packet_assembler.py::
  assemble_context_packet(*, packet_id, corpus_generation, retrieval_version, budget_requested,
  included_candidates: list[Candidate], excluded=())` — verified by reading both modules: this is a
  **different, older packet-assembly system** (built for `TCK-20260729-CONTEXT-PACKET-ASSEMBLY`) with
  an incompatible signature from this epic's own `knowledge_gateway_packet_assembly.py::
  assemble_packet(routing_decision, query_text, budget_requested)`. Nothing in this ticket's real
  call path (`assemble_packet()`) ever touches `context_packet_assembler.py`.
  `measurement_baseline_contract.md` §2.4 cites `wrap_context_packet_assembly()` as "direct precedent
  for this measurement point's **instrumentation shape**" (i.e., the pattern — time the call, emit
  one event — not the literal function to call as-is). Calling the real
  `wrap_context_packet_assembly()` on real `context_packet_assembler.py` data would produce a latency
  number for the *wrong* packet assembler — measuring a subsystem this ticket's actual response never
  uses — which is exactly the "force-fit" the ticket's own AC #4 warns against.

**Net finding:** by function-for-function evidence, none of the 3 named wrappers cleanly wraps a
function this ticket's real `knowledge_context`/`knowledge_status` call path actually invokes,
without either (a) duplicating frozen setup logic (`wrap_hybrid_retrieval`), (b) requiring
out-of-scope caching (`wrap_retrieval_cache_check`), or (c) measuring an unrelated subsystem
(`wrap_context_packet_assembly`). This is a genuine tension with AC #4's literal wording ("are
invoked from this real call site, with a test proving the invocation actually happens"), which the
same AC's own hedge clause anticipates ("or the subset architecturally applicable... not force-fit
ones that don't"). **This must go to Plan phase as an explicit decision point**, with (at least) these
candidate resolutions, none of which Investigate should pick on its own:
  1. Accept a small, explicitly-documented duplication: the new gateway module builds its own
     `conn`/`query_vec_bytes`/`query_tokens`/`bm25_obj`/`bm25_doc_ids` (mirroring `_run_search()`'s
     setup) so it can genuinely call `wrap_hybrid_retrieval()` as a supplementary, real (not mocked)
     measurement — accepting the parity-drift risk as a documented, deliberate trade-off.
  2. Add a **4th, new** wrapper function to `tools/retrieval_events.py` (not one of the ticket's
     named 3) that mirrors `wrap_context_packet_assembly()`'s *shape* but times
     `knowledge_gateway_packet_assembly.py::assemble_packet()` — satisfying §2.4's own
     "instrumentation-shape precedent" framing, but not literally "invoking" one of the 3 pre-named
     functions as the AC's literal text requires.
  3. Invoke one or more of the 3 exactly as already written, on their own already-existing (but
     pipeline-unrelated) target functions, as a standalone real-but-redundant measurement probe
     never fed into the actual response — technically "a real invocation, not mocked," but produces
     a metric that measures the wrong thing.
  4. Escalate: report that AC #4 cannot be satisfied as literally scoped without one of the above
     compromises, and get an explicit epic-owner ruling before Plan proceeds.

### 2. `knowledge_status`'s cache-specific-field omission mechanism is constrained by the frozen schema's shape, narrowing the ticket's own "or a companion field" language.
`knowledge_status_response.schema.json` has `additionalProperties: false` at the top level, and every
declared property has a fixed, non-nullable `type` (`cache_hit_rate`/`cache_miss_rate`/
`cache_stale_rejection_rate`: `type: number`; `cache_entry_counts`: `type: array`;
`recent_invalidation_reasons`: `type: array`; `cache_rebuildable`: `type: boolean`; and within
`latency_summary_ms`, `lookup`/`evidence_validation`: `type: number`). None of these declares a
`["number","null"]`-style nullable variant or a string-marker alternative. **The only schema-valid way
to satisfy "never a bare 0/null that could be misread as real" is outright field omission** — a
sibling "companion field" documenting the omission is not possible at the top level without violating
`additionalProperties: false` (and freezing a new schema variant is out of this ticket's remit — the
schemas are Phase-0-frozen). This resolves the ticket's own stated Assumption/Open Question
("reuse as-is... or freeze a Phase-1 variant") in favor of **reuse-as-is with omission**, but the
"document the omission explicitly... in the response or a companion field" instruction must be
read as "omit from the response; document the omission in code/docstring/`knowledge_status`'s own
prose description," not as a literal extra JSON field.

### 3. §9.2's 5 latency-measurement fields are not all named `cache_*`, but 2 of the 5 are cache-domain concepts by substance.
The ticket's own Scope text names the cache-specific fields to omit as "cache entry counts,
hit/miss/stale-rejection rates, recent invalidation reasons, cache-rebuild-safety" (6 top-level
fields) but does not call out that **`latency_summary_ms.lookup` and `latency_summary_ms.
evidence_validation` are also cache-domain concepts** per `measurement_baseline_contract.md` §2.1/§2.2
(lookup = "cache-lookup step"; evidence-validation = cache-freshness/invalidation check, tied to
`evidence_cache_identity_contract.md`). Only `provider_fallback`, `packet_assembly`, and `end_to_end`
within `latency_summary_ms` are genuinely Phase-1-populable (subject to Risk #1's wrapper-fit question
for `provider_fallback`/`packet_assembly` specifically). If Plan/Implement only checks the 6
ticket-named fields and populates all 5 `latency_summary_ms` sub-fields uniformly, it will silently
violate the "never a fabricated value for a cache-specific field" rule for `lookup`/
`evidence_validation`.

### 4. `provider_fallback_rate` and provider "generation" require some accumulation/measurement state whose nature (in-memory-per-process vs. derived from `agent-monitoring/events.jsonl` history) is undetermined.
A meaningful "rate" needs more than one observation. Is this: (a) an in-memory counter reset each time
the FastMCP server process restarts (simplest, but never durable, and arguably "survives beyond the
current function call" within one process's lifetime — CLAUDE.md's Durable State Rule scope for this
is unclear for operational-telemetry counters vs. simulation state), or (b) derived after the fact
from real `retrieval_events.py`-emitted `events.jsonl` rows (only possible once Risk #1 is resolved
and events are actually being emitted)? Flagged, not resolved.

### 5. Pre-existing failing tests in `tests/tools/test_search_mcp.py::TestMcpJson` (2 of 4 tests) assert a stale `.mcp.json` shape.
Verified live (`.venv/bin/python3 -m pytest tests/tools/test_search_mcp.py::TestMcpJson -q` →
`2 failed, 2 passed`). Not this ticket's fault or job to fix — but the new `.mcp.json`-entry test this
ticket adds must assert against the *real* current `knowledge-search` entry shape (`bash` +
`start_search_mcp.sh`), not the stale expectations in that pre-existing failing test file.

## Anti-Drift Hazards

- **Do not modify `tools/search_mcp.py`, `tools/knowledge_gateway_router.py`, or
  `tools/knowledge_gateway_packet_assembly.py`.** All three are DONE/frozen dependencies this ticket
  only imports. `git diff --stat HEAD -- tools/search_mcp.py` must stay empty (explicit AC); the same
  discipline should extend to the router and packet-assembly modules even though the AC only names
  `search_mcp.py` literally.
- **Do not register `knowledge_learn`/`knowledge_promote`/`knowledge_verify`/any invalidation tool** —
  §9.3 explicit deferral, and AC #5 requires the registered-tool-name set to be exactly
  `{knowledge_context, knowledge_status}`.
- **Do not build any caching** (no new `retrieval_cache.db` table/migration, no in-process memoization
  of packet results) — explicit Out of Scope.
- **Do not touch CLAUDE.md/.claude/agents/*.md/.claude/skills/*.md** — explicit Out of Scope; the
  `.mcp.json` registration is the only "activation" mechanism, never an instruction-file edit.
- **Do not build the full §16 fail-open/failure-semantics test matrix** — that is
  `TCK-20260815-KGMCP-P1-FAILOPEN-TESTS`'s job; this ticket only needs to pass through
  router/assembler failures without swallowing them on the happy path.
- **Do not force-fit a wrapper call that doesn't correspond to a real operation in this ticket's
  pipeline** just to satisfy AC #4's literal wording — see Risk #1; this is the ticket's own explicit
  instruction and the single easiest place to accidentally produce a technically-passing but
  substantively-fabricated test.
- **Do not silently return `0`/`null` for a cache-specific `knowledge_status` field** — must be
  omitted (see Risk #2), and the same omission discipline applies to `latency_summary_ms.lookup`/
  `evidence_validation` even though they're not literally named "cache_*" (see Risk #3).
- **`context_search`'s `adapter_version` is genuinely `null`** in the frozen descriptor — a
  `knowledge_status` `providers[].generation` value of `null`/absent for `context_search` is the
  *correct*, real value, not a bug to "fix" by fabricating a version string.
